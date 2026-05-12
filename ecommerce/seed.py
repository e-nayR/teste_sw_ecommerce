"""
Seed de dados demo para o banco do ECOMMERCE.

Objetivo: popular o banco com 2 usuários demo e 1 pedido
histórico inicial, para que o aluno consiga interagir com a
API/UI sem precisar fazer cadastro nem checkout antes.

Posição na arquitetura: módulo invocável (``python -m
ecommerce.seed``) consumido pelo menu interativo
(``ecommerce/menu.py``) na opção "popular banco demo". Pode
ser executado múltiplas vezes — operações são idempotentes
(verificam existência antes de criar).

Conceitos didáticos abordados: idempotência, separação
schema/dados, ponto de entrada via ``python -m``.

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
import sys

# 2) Imports de bibliotecas de terceiros
from sqlalchemy import select
from sqlalchemy.orm import Session

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
from ecommerce.auth import gerar_hash_senha
from ecommerce.config import settings
from ecommerce.database import SessionLocal
from ecommerce.models import ItemPedido, Pedido, Usuario


def _ja_existe_usuario(db: Session, email: str) -> bool:
    """Retorna True se já houver um usuário com o email informado."""
    stmt = select(Usuario).where(Usuario.email == email)
    return db.execute(stmt).scalar_one_or_none() is not None


def _criar_usuario(
    db: Session, email: str, senha: str, nome: str
) -> Usuario:
    """Cria um usuário e retorna o registro persistido."""
    usuario = Usuario(
        email=email,
        senha_hash=gerar_hash_senha(senha),
        nome=nome,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def _ja_existe_pedido_para(db: Session, usuario_id: int) -> bool:
    """Retorna True se o usuário já tem ao menos um pedido."""
    stmt = select(Pedido).where(Pedido.usuario_id == usuario_id)
    return db.execute(stmt).first() is not None


def _criar_pedido_inicial(db: Session, usuario_id: int) -> Pedido:
    """
    Cria um pedido histórico de demonstração com 2 itens
    (Notebook + Teclado), status ``aprovado``.
    """
    pedido = Pedido(
        usuario_id=usuario_id,
        total=3500.0,
        status="aprovado",
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)

    db.add(
        ItemPedido(
            pedido_id=pedido.id,
            produto_id=1,
            quantidade=1,
            preco_unitario_snapshot=3000.0,
        )
    )
    db.add(
        ItemPedido(
            pedido_id=pedido.id,
            produto_id=2,
            quantidade=1,
            preco_unitario_snapshot=500.0,
        )
    )
    db.commit()
    db.refresh(pedido)
    return pedido


def seed(db: Session) -> dict:
    """
    Popula o banco com dados demo idempotentemente.

    Operações:
    - Cria ``DEMO_USER_EMAIL`` se ausente.
    - Cria ``DEMO_USER_2_EMAIL`` se ausente.
    - Cria 1 pedido histórico para o usuário 1 se ele ainda
      não tiver nenhum pedido.

    Parâmetros:
        db: sessão SQLAlchemy aberta.

    Retorno:
        Dicionário com contadores de criações realizadas.
    """
    contadores = {
        "usuarios_criados": 0,
        "pedidos_criados": 0,
    }

    # Usuário 1
    email1 = str(settings.DEMO_USER_EMAIL)
    if not _ja_existe_usuario(db, email1):
        _criar_usuario(
            db,
            email=email1,
            senha=settings.DEMO_USER_PASSWORD,
            nome="Aluno Demo 1",
        )
        contadores["usuarios_criados"] += 1

    # Usuário 2
    email2 = str(settings.DEMO_USER_2_EMAIL)
    if not _ja_existe_usuario(db, email2):
        _criar_usuario(
            db,
            email=email2,
            senha=settings.DEMO_USER_2_PASSWORD,
            nome="Aluno Demo 2",
        )
        contadores["usuarios_criados"] += 1

    # Pedido histórico inicial para o usuário 1
    stmt = select(Usuario).where(Usuario.email == email1)
    usuario1 = db.execute(stmt).scalar_one()
    if not _ja_existe_pedido_para(db, usuario1.id):
        _criar_pedido_inicial(db, usuario1.id)
        contadores["pedidos_criados"] += 1

    return contadores


def main() -> int:
    """Ponto de entrada para ``python -m ecommerce.seed``."""
    db = SessionLocal()
    try:
        contadores = seed(db)
    finally:
        db.close()

    print(
        f"Seed concluído: "
        f"{contadores['usuarios_criados']} usuário(s) criado(s), "
        f"{contadores['pedidos_criados']} pedido(s) criado(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
