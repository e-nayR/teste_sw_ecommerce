"""
Modelos ORM do pacote ECOMMERCE (SQLAlchemy 2.0).

Objetivo: declarar as tabelas que materializam o domínio
persistido — usuários, carrinhos, itens de carrinho, pedidos
e itens de pedido — com tipagem moderna (``Mapped`` /
``mapped_column``).

Posição na arquitetura: camada de modelagem consumida por
``ecommerce.carrinho_persistencia``, pelos routers e pelo
``ecommerce.seed`` (via ``Base.metadata``). O Alembic
(``alembic/env.py``) também importa este módulo para registrar
as tabelas em ``Base.metadata`` antes do autogenerate.

Conceitos didáticos abordados: mapeamento objeto-relacional,
chaves estrangeiras, snapshot de preço (cópia do valor
unitário no momento da operação para preservar histórico em
caso de alteração futura do catálogo), separação entre domínio
e persistência.

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
from datetime import datetime, timezone
from typing import List

# 2) Imports de bibliotecas de terceiros
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
from ecommerce.database import Base


class Usuario(Base):
    """
    Usuário do sistema.

    Conceitos didáticos:
    - Identificação por chave primária inteira
    - Senha armazenada como hash binário (bcrypt)
    """

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    senha_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    carrinhos: Mapped[List["Carrinho"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )
    pedidos: Mapped[List["Pedido"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )


class Carrinho(Base):
    """
    Carrinho de compras vinculado a um usuário.

    Estratégia: um único carrinho ``ativo=True`` por usuário a
    cada momento. Carrinhos antigos são marcados ``ativo=False``
    após a finalização da compra.
    """

    __tablename__ = "carrinhos"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ativo: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    usuario: Mapped["Usuario"] = relationship(back_populates="carrinhos")
    itens: Mapped[List["ItemCarrinho"]] = relationship(
        back_populates="carrinho", cascade="all, delete-orphan"
    )


class ItemCarrinho(Base):
    """
    Item de carrinho — produto, quantidade e preço-snapshot.

    O ``preco_unitario_snapshot`` captura o preço no momento da
    adição do item, garantindo estabilidade do total mesmo se o
    catálogo for atualizado entre a adição e a finalização.
    """

    __tablename__ = "itens_carrinho"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    carrinho_id: Mapped[int] = mapped_column(
        ForeignKey("carrinhos.id"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    preco_unitario_snapshot: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    carrinho: Mapped["Carrinho"] = relationship(back_populates="itens")


class Pedido(Base):
    """
    Pedido finalizado pelo usuário.

    O ``id`` é inteiro auto-incrementado. O ``status`` segue o
    enum textual {``pendente``, ``aprovado``, ``recusado``}.
    """

    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    total: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    usuario: Mapped["Usuario"] = relationship(back_populates="pedidos")
    itens: Mapped[List["ItemPedido"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan"
    )


class ItemPedido(Base):
    """
    Item de pedido — produto, quantidade e preço-snapshot.

    O snapshot é congelado no momento da finalização da compra
    e nunca é atualizado, mesmo que o catálogo mude.
    """

    __tablename__ = "itens_pedido"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos.id"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    preco_unitario_snapshot: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    pedido: Mapped["Pedido"] = relationship(back_populates="itens")
