"""
Router das operações de carrinho.

Objetivo: expor ``GET /api/carrinho`` (listagem),
``POST /api/carrinho/itens`` (adicionar),
``DELETE /api/carrinho`` (limpar) e
``GET /api/carrinho/total`` (cálculo com desconto opcional).

Posição na arquitetura: router protegido (``get_current_user``)
que orquestra a camada de persistência
(``ecommerce.carrinho_persistencia``) e a camada de domínio
(``ecommerce.carrinho``). O nome do produto não é persistido
nas tabelas — é resolvido por lookup em ``PRODUTOS_DEMO`` para
montar o DTO de resposta.

Conceitos didáticos abordados: separação repositório/router,
composição de DTOs a partir de modelos ORM + dados estáticos,
atualização explícita do timestamp ``atualizado_em``.

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
from datetime import datetime, timezone
from typing import List

# 2) Imports de bibliotecas de terceiros
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
from ecommerce.auth import get_current_user
from ecommerce.carrinho_persistencia import (
    adicionar_item,
    limpar_carrinho,
    listar_itens,
    montar_carrinho_de_compras,
    obter_ou_criar_carrinho_ativo,
)
from ecommerce.database import get_db
from ecommerce.models import ItemCarrinho, Usuario
from ecommerce.produtos import buscar_produto_por_id
from ecommerce.schemas import (
    AdicionarItemIn,
    CarrinhoOut,
    ItemCarrinhoOut,
    TotalCarrinhoOut,
)


router = APIRouter(prefix="/api", tags=["carrinho"])


# ──────────────────────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────────────────────


def _montar_item_out(item: ItemCarrinho) -> ItemCarrinhoOut:
    """
    Converte um ``ItemCarrinho`` ORM para ``ItemCarrinhoOut``.

    O ``nome_produto`` é resolvido por lookup em ``PRODUTOS_DEMO``;
    caso o produto não exista mais no catálogo, usa o rótulo
    ``"Produto #<id>"`` como fallback.
    """
    try:
        nome = buscar_produto_por_id(item.produto_id)["nome"]
    except KeyError:
        nome = f"Produto #{item.produto_id}"
    return ItemCarrinhoOut(
        produto_id=item.produto_id,
        nome_produto=nome,
        quantidade=item.quantidade,
        preco_unitario=item.preco_unitario_snapshot,
        subtotal=item.preco_unitario_snapshot * item.quantidade,
    )


def _montar_carrinho_out(
    db: Session, carrinho_id: int
) -> CarrinhoOut:
    """Monta o DTO ``CarrinhoOut`` a partir do estado persistido."""
    itens_orm = listar_itens(db, carrinho_id)
    itens_out = [_montar_item_out(item) for item in itens_orm]
    total = sum(item.subtotal for item in itens_out)
    return CarrinhoOut(
        itens=itens_out,
        quantidade_itens=sum(item.quantidade for item in itens_out),
        total_sem_desconto=total,
    )


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────


@router.get("/carrinho", response_model=CarrinhoOut)
def listar_carrinho(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CarrinhoOut:
    """
    Retorna o carrinho ativo do usuário autenticado.

    Cria um novo carrinho vazio se ainda não houver um carrinho
    ativo para o usuário.

    Retorno:
        ``CarrinhoOut`` com itens, quantidade total e total sem
        desconto.
    """
    carrinho_orm = obter_ou_criar_carrinho_ativo(db, usuario.id)
    return _montar_carrinho_out(db, carrinho_orm.id)


@router.post(
    "/carrinho/itens",
    response_model=CarrinhoOut,
    status_code=status.HTTP_201_CREATED,
)
def adicionar_item_ao_carrinho(
    payload: AdicionarItemIn,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CarrinhoOut:
    """
    Adiciona um item ao carrinho ativo.

    Captura o preço-snapshot do produto no momento da adição.

    Parâmetros:
        payload: ``AdicionarItemIn`` com ``produto_id`` e
                 ``quantidade``.

    Retorno:
        ``CarrinhoOut`` atualizado.

    Levanta:
        HTTPException(404): ``produto_id`` ausente do catálogo.
    """
    try:
        buscar_produto_por_id(payload.produto_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="produto não encontrado",
        )

    carrinho_orm = obter_ou_criar_carrinho_ativo(db, usuario.id)
    adicionar_item(
        db, carrinho_orm.id, payload.produto_id, payload.quantidade
    )

    # ``onupdate`` do ORM não dispara em INSERT de itens-filhos —
    # atualizamos explicitamente para refletir atividade no
    # carrinho.
    carrinho_orm.atualizado_em = datetime.now(timezone.utc)
    db.commit()

    return _montar_carrinho_out(db, carrinho_orm.id)


@router.delete("/carrinho", response_model=CarrinhoOut)
def esvaziar_carrinho(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CarrinhoOut:
    """
    Remove todos os itens do carrinho ativo.

    Retorno:
        ``CarrinhoOut`` vazio (carrinho permanece ativo).
    """
    carrinho_orm = obter_ou_criar_carrinho_ativo(db, usuario.id)
    limpar_carrinho(db, carrinho_orm.id)

    carrinho_orm.atualizado_em = datetime.now(timezone.utc)
    db.commit()

    return _montar_carrinho_out(db, carrinho_orm.id)


@router.get("/carrinho/total", response_model=TotalCarrinhoOut)
def calcular_total_do_carrinho(
    desconto_percentual: float = Query(default=0),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TotalCarrinhoOut:
    """
    Calcula o total do carrinho ativo com desconto opcional.

    Parâmetros:
        desconto_percentual: percentual de desconto (default 0).

    Retorno:
        ``TotalCarrinhoOut`` com total sem desconto, percentual,
        valor de desconto e total com desconto.
    """
    carrinho_orm = obter_ou_criar_carrinho_ativo(db, usuario.id)
    carrinho_dominio = montar_carrinho_de_compras(
        db, carrinho_orm.id
    )

    total_sem = carrinho_dominio.calcular_total()
    total_com = carrinho_dominio.calcular_total(desconto_percentual)
    valor_desconto = total_sem - total_com

    return TotalCarrinhoOut(
        total_sem_desconto=total_sem,
        desconto_percentual=desconto_percentual,
        valor_desconto=valor_desconto,
        total_com_desconto=total_com,
    )
