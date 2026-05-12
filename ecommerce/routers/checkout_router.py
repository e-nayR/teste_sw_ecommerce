"""
Router da operação de checkout.

Objetivo: expor ``POST /api/checkout``, que finaliza a compra
do carrinho ativo do usuário cobrando do gateway de pagamento
e materializando o resultado como um ``Pedido`` (com seus
``ItemPedido``).

Posição na arquitetura: router protegido (``get_current_user``)
que orquestra três camadas — repositório
(``carrinho_persistencia``), domínio (``ecommerce.carrinho``,
``ecommerce.checkout``) e modelos ORM (``Pedido``,
``ItemPedido``). É o ponto onde o anexo do material original
se conecta ao banco de dados.

Fluxo determinístico:

1. Recuperar o carrinho ativo do usuário.
2. Reconstruir o ``CarrinhoDeCompras`` de domínio.
3. Pré-aplicar o desconto sobre os preços do carrinho de
   domínio (``finalizar_compra`` do anexo cobra o total via
   ``calcular_total()`` sem argumentos).
4. Chamar ``Checkout.finalizar_compra`` — pode levantar
   ``ValueError`` (gateway recusa) ou retornar string de
   sucesso.
5. SUCESSO: cria ``Pedido`` com ``status="aprovado"`` + um
   ``ItemPedido`` para cada ``ItemCarrinho`` (snapshot final
   do preço idêntico ao do item) e marca o carrinho como
   inativo. Os itens permanecem anexados ao carrinho inativo
   para auditoria.
6. FALHA: cria ``Pedido`` com ``status="recusado"`` + os
   mesmos ``ItemPedido`` (registro histórico), NÃO marca o
   carrinho como inativo (usuário pode tentar novamente) e
   levanta ``HTTPException(402)``.

Conceitos didáticos abordados: orquestração transacional,
atomicidade do checkout, separação domínio/persistência,
auditoria via registros históricos.

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
from datetime import datetime, timezone

# 2) Imports de bibliotecas de terceiros
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
from ecommerce.auth import get_current_user
from ecommerce.carrinho import CarrinhoDeCompras
from ecommerce.carrinho_persistencia import (
    listar_itens,
    montar_carrinho_de_compras,
    obter_ou_criar_carrinho_ativo,
)
from ecommerce.checkout import Checkout, GatewayDePagamento
from ecommerce.database import get_db
from ecommerce.models import ItemCarrinho, ItemPedido, Pedido, Usuario
from ecommerce.schemas import CheckoutIn, CheckoutOut


router = APIRouter(prefix="/api", tags=["checkout"])


# ──────────────────────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────────────────────


def _aplicar_desconto_no_dominio(
    carrinho_dominio: CarrinhoDeCompras, desconto_percentual: float
) -> None:
    """
    Multiplica o preço de cada produto pelo fator
    ``(100 - desconto) / 100``.

    Esta pré-aplicação garante que ``calcular_total()`` (sem
    argumentos), invocada pelo ``Checkout.finalizar_compra`` do
    anexo, retorne o total já com desconto — mantendo a
    consistência entre o valor cobrado pelo gateway e o valor
    registrado no ``Pedido``.
    """
    if desconto_percentual:
        fator = (100.0 - desconto_percentual) / 100.0
        for produto in carrinho_dominio.produtos:
            produto.preco = produto.preco * fator


def _gravar_pedido_e_itens(
    db: Session,
    *,
    usuario_id: int,
    total: float,
    status_pedido: str,
    itens_origem: list[ItemCarrinho],
) -> Pedido:
    """
    Cria um ``Pedido`` + os ``ItemPedido`` correspondentes.

    Cada ``ItemPedido`` recebe o snapshot final de preço,
    igual ao do ``ItemCarrinho`` de origem.
    """
    pedido = Pedido(
        usuario_id=usuario_id,
        total=total,
        status=status_pedido,
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)

    for item in itens_origem:
        db.add(
            ItemPedido(
                pedido_id=pedido.id,
                produto_id=item.produto_id,
                quantidade=item.quantidade,
                preco_unitario_snapshot=item.preco_unitario_snapshot,
            )
        )
    db.commit()
    return pedido


# ──────────────────────────────────────────────────────────────
# Endpoint
# ──────────────────────────────────────────────────────────────


@router.post(
    "/checkout",
    response_model=CheckoutOut,
    status_code=status.HTTP_200_OK,
)
def finalizar_checkout(
    payload: CheckoutIn,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CheckoutOut:
    """
    Finaliza a compra do carrinho ativo do usuário autenticado.

    Parâmetros:
        payload: ``CheckoutIn`` com ``cartao`` e
                 ``desconto_percentual``.

    Retorno:
        ``CheckoutOut`` com ``pedido_id``, ``resultado``,
        ``total`` e ``status``.

    Levanta:
        HTTPException(400): carrinho vazio.
        HTTPException(402): cobrança recusada pelo gateway —
        o ``Pedido`` recusado já foi gravado para auditoria.
    """
    carrinho_orm = obter_ou_criar_carrinho_ativo(db, usuario.id)
    itens_carrinho = listar_itens(db, carrinho_orm.id)
    if not itens_carrinho:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="carrinho vazio",
        )

    carrinho_dominio = montar_carrinho_de_compras(
        db, carrinho_orm.id
    )
    _aplicar_desconto_no_dominio(
        carrinho_dominio, payload.desconto_percentual
    )

    gateway = GatewayDePagamento()
    checkout_dominio = Checkout(gateway)

    try:
        resultado = checkout_dominio.finalizar_compra(
            carrinho_dominio, payload.cartao
        )
    except ValueError as exc:
        # ── FALHA ────────────────────────────────────────────
        # Pedido recusado registrado para auditoria; carrinho
        # permanece ativo para nova tentativa.
        total_recusado = carrinho_dominio.calcular_total()
        pedido = _gravar_pedido_e_itens(
            db,
            usuario_id=usuario.id,
            total=total_recusado,
            status_pedido="recusado",
            itens_origem=itens_carrinho,
        )
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(exc),
        )

    # ── SUCESSO ─────────────────────────────────────────────
    total_aprovado = carrinho_dominio.calcular_total()
    pedido = _gravar_pedido_e_itens(
        db,
        usuario_id=usuario.id,
        total=total_aprovado,
        status_pedido="aprovado",
        itens_origem=itens_carrinho,
    )

    # Carrinho fica histórico — itens permanecem anexados.
    carrinho_orm.ativo = False
    carrinho_orm.atualizado_em = datetime.now(timezone.utc)
    db.commit()

    return CheckoutOut(
        pedido_id=pedido.id,
        resultado=resultado,
        total=total_aprovado,
        status="aprovado",
    )
