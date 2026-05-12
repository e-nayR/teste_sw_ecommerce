"""
Configuração de execução do Alembic — bind para o engine do
ECOMMERCE.

Lê a ``DATABASE_URL`` do módulo ``ecommerce.config`` (já
resolvida com ``pathlib`` e a substituição do placeholder
``${PROJECT_ROOT}`` aplicada pela validação do ``Settings``)
e usa ``Base.metadata`` para o autogenerate.
"""

# 1) Imports da biblioteca padrão
import sys
from logging.config import fileConfig
from pathlib import Path

# 2) Imports de bibliotecas de terceiros
from alembic import context
from sqlalchemy import engine_from_config, pool

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
# Adiciona a raiz do repositório ao sys.path para permitir que
# o ``alembic`` (executado via menu opção 3) encontre o pacote
# ``ecommerce`` mesmo quando o cwd não for a raiz.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ecommerce.config import settings  # noqa: E402
from ecommerce.database import Base  # noqa: E402
from ecommerce import models  # noqa: F401, E402  (registra os modelos)


config = context.config

# Sobrescreve a sqlalchemy.url do alembic.ini com o valor já
# resolvido em ecommerce.config (path absoluto via pathlib +
# placeholder ${PROJECT_ROOT} substituído).
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Executa migrations no modo offline (gera SQL sem conectar)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrations no modo online (conecta ao engine)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # ``render_as_batch=True`` é requerido pelo SQLite para
        # ALTER TABLE com restrições (necessário em migrations
        # futuras de evolução de schema).
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
