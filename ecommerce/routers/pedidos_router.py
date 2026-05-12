"""
Router de consulta de pedidos.

Objetivo: expor ``GET /api/pedidos`` (lista) e
``GET /api/pedidos/{pedido_id}`` (consulta por id).

Posição na arquitetura: router protegido (``get_current_user``)
que materializa pedidos persistidos como ``PedidoOut``,
resolvendo nomes de produto via ``PRODUTOS_DEMO``.

Conceitos didáticos abordados: serialização condicional de
DTOs (campos opcionais), separação ORM/DTO, lookup em fonte
estática.

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
from typing import List

# 2) Imports de bibliotecas de terceiros
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
from ecommerce.auth import get_current_user
from ecommerce.config import settings
from ecommerce.database import get_db
from ecommerce.models import Pedido, Usuario
from ecommerce.produtos import buscar_produto_por_id
from ecommerce.schemas import ItemPedidoOut, PedidoOut


router = APIRouter(prefix="/api", tags=["pedidos"])


# ──────────────────────────────────────────────────────────────
# Helper interno
# ──────────────────────────────────────────────────────────────


def _montar_pedido_out(pedido: Pedido) -> PedidoOut:
    """Monta o DTO ``PedidoOut`` a partir do modelo ORM."""
    itens_out: List[ItemPedidoOut] = []
    for item in pedido.itens:
        try:
            nome = buscar_produto_por_id(item.produto_id)["nome"]
        except KeyError:
            nome = f"Produto #{item.produto_id}"
        itens_out.append(
            ItemPedidoOut(
                produto_id=item.produto_id,
                nome_produto=nome,
                quantidade=item.quantidade,
                preco_unitario=item.preco_unitario_snapshot,
            )
        )

    usuario_id_payload = (
        pedido.usuario_id
        if settings.PEDIDOS_RESPOSTA_DETALHADA
        else None
    )

    return PedidoOut(
        id=pedido.id,
        usuario_id=usuario_id_payload,
        total=pedido.total,
        status=pedido.status,
        criado_em=pedido.criado_em,
        itens=itens_out,
    )


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────


@router.get("/pedidos", response_model=List[PedidoOut])
def listar_pedidos(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[PedidoOut]:
    """Lista os pedidos."""
    stmt = (
        select(Pedido)
        .where(Pedido.usuario_id == usuario.id)
        .order_by(Pedido.id.desc())
    )
    pedidos = list(db.execute(stmt).scalars().all())
    return [_montar_pedido_out(p) for p in pedidos]


@router.get("/pedidos/{pedido_id}", response_model=PedidoOut)
def consultar_pedido(
    pedido_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PedidoOut:
    """
    Retorna os dados de um pedido pelo seu identificador.

    Parâmetros:
        pedido_id: identificador inteiro do pedido.

    Retorno:
        ``PedidoOut`` com itens, total e status.

    Levanta:
        HTTPException(404): pedido não encontrado.
    """
    if settings.PEDIDOS_CONSULTA_GLOBAL:
        pedido = db.get(Pedido, pedido_id)
    else:
        stmt = select(Pedido).where(
            Pedido.id == pedido_id,
            Pedido.usuario_id == usuario.id,
        )
        pedido = db.execute(stmt).scalar_one_or_none()

    if pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="pedido não encontrado",
        )

    return _montar_pedido_out(pedido)
