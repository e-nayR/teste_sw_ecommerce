"""
DTOs Pydantic da API ECOMMERCE.

Objetivo: declarar todos os DTOs (Data Transfer Objects) que
representam payloads de entrada e saída da API REST. Centraliza
validações de campo (formato de email, intervalo de quantidade,
padrão regex de cartão).

Posição na arquitetura: módulo consumido pelos routers
(``ecommerce.routers.*``) para validar requisições e serializar
respostas. Não depende de modelos ORM (a conversão é feita nos
routers e no repositório).

Conceitos didáticos abordados: validação declarativa, separação
entre representação interna (modelos ORM) e externa (DTOs),
tipagem rigorosa com ``Literal`` e ``EmailStr``, opcionalidade
explícita.

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
from datetime import datetime
from typing import List, Literal, Optional

# 2) Imports de bibliotecas de terceiros
from pydantic import BaseModel, EmailStr, Field

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
# ``ErroOut`` é definido em ``ecommerce.errors`` (acoplado aos
# exception handlers). Re-exportado aqui para facilitar o
# import unificado a partir de ``ecommerce.schemas``.
from ecommerce.errors import ErroOut


# ──────────────────────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────────────────────


class HealthOut(BaseModel):
    """Resposta do health-check."""

    status: Literal["ok"]
    versao: str
    timestamp: datetime


# ──────────────────────────────────────────────────────────────
# Catálogo
# ──────────────────────────────────────────────────────────────


class ProdutoOut(BaseModel):
    """Produto exposto pela API."""

    id: int
    nome: str
    preco: float
    estoque: int


# ──────────────────────────────────────────────────────────────
# Autenticação
# ──────────────────────────────────────────────────────────────


class LoginIn(BaseModel):
    """Payload de login."""

    email: EmailStr
    senha: str = Field(min_length=1)


class LoginOut(BaseModel):
    """Resposta de login bem-sucedido."""

    access_token: str
    token_type: Literal["bearer"]
    expira_em_segundos: int


class UsuarioOut(BaseModel):
    """Usuário autenticado (resposta de ``GET /api/me``)."""

    id: int
    email: EmailStr
    nome: str


# ──────────────────────────────────────────────────────────────
# Carrinho
# ──────────────────────────────────────────────────────────────


class AdicionarItemIn(BaseModel):
    """Payload para adicionar item ao carrinho."""

    produto_id: int
    quantidade: int = Field(ge=1, le=100)


class ItemCarrinhoOut(BaseModel):
    """Item do carrinho com cálculo de subtotal."""

    produto_id: int
    nome_produto: str
    quantidade: int
    preco_unitario: float
    subtotal: float


class CarrinhoOut(BaseModel):
    """Resposta de listagem do carrinho."""

    itens: List[ItemCarrinhoOut]
    quantidade_itens: int
    total_sem_desconto: float


class TotalCarrinhoOut(BaseModel):
    """Resposta de cálculo de total com desconto."""

    total_sem_desconto: float
    desconto_percentual: float
    valor_desconto: float
    total_com_desconto: float


# ──────────────────────────────────────────────────────────────
# Checkout
# ──────────────────────────────────────────────────────────────


class CheckoutIn(BaseModel):
    """Payload de finalização de compra."""

    cartao: str = Field(pattern=r"^\d{4}-\d{4}-\d{4}-\d{4}$")
    desconto_percentual: float = 0


class CheckoutOut(BaseModel):
    """Resposta de checkout finalizado."""

    pedido_id: int
    resultado: str
    total: float
    status: Literal["aprovado", "recusado"]


# ──────────────────────────────────────────────────────────────
# Pedidos
# ──────────────────────────────────────────────────────────────


class ItemPedidoOut(BaseModel):
    """Item de um pedido (registro histórico)."""

    produto_id: int
    nome_produto: str
    quantidade: int
    preco_unitario: float


class PedidoOut(BaseModel):
    """
    Pedido finalizado, retornado pela API.

    Convenção: o campo ``usuario_id`` é opcional no schema. Sua
    inclusão no payload é decidida pelo router conforme o toggle
    ``settings.PEDIDOS_RESPOSTA_DETALHADA``.
    """

    id: int
    usuario_id: Optional[int] = None
    total: float
    status: str
    criado_em: datetime
    itens: List[ItemPedidoOut]


# ──────────────────────────────────────────────────────────────
# Re-export
# ──────────────────────────────────────────────────────────────


__all__ = [
    "HealthOut",
    "ProdutoOut",
    "LoginIn",
    "LoginOut",
    "UsuarioOut",
    "AdicionarItemIn",
    "ItemCarrinhoOut",
    "CarrinhoOut",
    "TotalCarrinhoOut",
    "CheckoutIn",
    "CheckoutOut",
    "PedidoOut",
    "ItemPedidoOut",
    "ErroOut",
]
