"""Schema inicial — usuarios, carrinhos, itens_carrinho, pedidos, itens_pedido.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-04-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------- usuarios --------
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("senha_hash", sa.LargeBinary(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_usuarios_email", "usuarios", ["email"], unique=True
    )

    # -------- carrinhos --------
    op.create_table(
        "carrinhos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
    )
    op.create_index(
        "ix_carrinhos_usuario_id", "carrinhos", ["usuario_id"]
    )

    # -------- itens_carrinho --------
    op.create_table(
        "itens_carrinho",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("carrinho_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column(
            "preco_unitario_snapshot", sa.Float(), nullable=False
        ),
        sa.ForeignKeyConstraint(["carrinho_id"], ["carrinhos.id"]),
    )
    op.create_index(
        "ix_itens_carrinho_carrinho_id",
        "itens_carrinho",
        ["carrinho_id"],
    )

    # -------- pedidos --------
    op.create_table(
        "pedidos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("total", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
    )
    op.create_index(
        "ix_pedidos_usuario_id", "pedidos", ["usuario_id"]
    )

    # -------- itens_pedido --------
    op.create_table(
        "itens_pedido",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pedido_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column(
            "preco_unitario_snapshot", sa.Float(), nullable=False
        ),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedidos.id"]),
    )
    op.create_index(
        "ix_itens_pedido_pedido_id", "itens_pedido", ["pedido_id"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_itens_pedido_pedido_id", table_name="itens_pedido"
    )
    op.drop_table("itens_pedido")

    op.drop_index("ix_pedidos_usuario_id", table_name="pedidos")
    op.drop_table("pedidos")

    op.drop_index(
        "ix_itens_carrinho_carrinho_id", table_name="itens_carrinho"
    )
    op.drop_table("itens_carrinho")

    op.drop_index(
        "ix_carrinhos_usuario_id", table_name="carrinhos"
    )
    op.drop_table("carrinhos")

    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.drop_table("usuarios")
