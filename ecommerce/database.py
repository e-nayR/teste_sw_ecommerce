"""
Camada de acesso ao banco de dados.

Objetivo: configurar o engine SQLAlchemy 2.0 sobre SQLite,
fornecer a fábrica de sessões (``SessionLocal``), a base
declarativa para os modelos ORM (``Base``) e a dependência
``get_db()`` consumida pelas rotas FastAPI.

Posição na arquitetura: camada de infraestrutura entre
``ecommerce.config`` (URL do banco) e ``ecommerce.models``
(definições ORM). É consumida por
``ecommerce.carrinho_persistencia``, pelos routers e pelo
``ecommerce.seed`` no carregamento inicial.

Conceitos didáticos abordados: separação infraestrutura/domínio,
factory de sessões, dependência injetável via FastAPI ``Depends``,
gerenciamento determinístico do ciclo de vida da conexão.

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
from typing import Generator

# 2) Imports de bibliotecas de terceiros
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
from ecommerce.config import settings


# Argumentos do engine variam por dialeto. Para SQLite usamos
# ``check_same_thread=False`` por compatibilidade com FastAPI
# (várias threads atendem requisições simultaneamente).
_connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite:")
    else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    echo=settings.DEBUG,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """
    Base declarativa SQLAlchemy 2.0 para todos os modelos ORM
    de ``ecommerce.models``.

    Conceitos didáticos:
    - Mapeamento objeto-relacional (ORM) com tipagem moderna
    - Modelo declarativo (subclasses de ``DeclarativeBase``)
    """


def get_db() -> Generator[Session, None, None]:
    """
    Fornece uma sessão SQLAlchemy para uma única requisição.

    Padrão de uso (FastAPI):
        ``db: Session = Depends(get_db)``.

    A sessão é fechada de forma garantida ao final do bloco,
    mesmo que a rota levante exceção.

    Retorno:
        Generator que entrega uma ``Session`` aberta e a fecha
        ao final.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
