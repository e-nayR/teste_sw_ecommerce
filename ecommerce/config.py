"""
Configuração da aplicação — carregamento de variáveis de ambiente.

Objetivo: centralizar todas as variáveis de configuração da
aplicação carregadas a partir do arquivo `.env`, com tipagem
rigorosa via Pydantic Settings.

Posição na arquitetura: módulo de baixo nível consumido por
todos os demais módulos do pacote `ecommerce`, exposto através
do singleton `settings` ou da função `get_settings()`.

Conceitos didáticos abordados: configuração externa (12-Fatores),
tipagem estática, validação declarativa, separação entre código
e configuração, mascaramento automático de segredos.

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated, List, Optional

# 2) Imports de bibliotecas de terceiros
from pydantic import EmailStr, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
# (este módulo não possui imports locais — ele é a base da pirâmide)


# Diretório base do código (raiz do repositório). É o fallback
# usado quando PROJECT_ROOT não está definido no `.env`.
BASE_DIR: Path = Path(__file__).resolve().parent.parent


def _resolver_raiz_runtime(project_root: Optional[str]) -> Path:
    """
    Resolve o diretório raiz para artefatos de runtime.

    Quando ``project_root`` é não-vazio e aponta para um diretório
    existente, retorna o caminho absoluto correspondente. Caso
    contrário, retorna ``BASE_DIR`` (raiz do repositório).

    Parâmetros:
        project_root: valor da variável ``PROJECT_ROOT`` lida do
                      arquivo ``.env`` (pode ser ``None`` ou string
                      vazia).

    Retorno:
        Caminho absoluto resolvido como ``pathlib.Path``.
    """
    if project_root:
        candidato = Path(project_root).expanduser().resolve()
        if candidato.exists() and candidato.is_dir():
            return candidato
    return BASE_DIR


class Settings(BaseSettings):
    """
    Configurações da aplicação carregadas a partir do `.env`.

    Objetivo: declarar, de forma tipada e validada, todas as
    variáveis de configuração consumidas pelos módulos do pacote
    ``ecommerce``.

    Conceitos didáticos:
    - Tipagem estática (Pydantic 2)
    - Validação declarativa (constraints em ``Field`` + validators)
    - Mascaramento automático de segredos (``SecretStr``)
    - Configuração externa por arquivo ``.env`` (12-Fatores)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Servidor ---
    APP_HOST: str = Field(default="127.0.0.1", min_length=1)
    APP_PORT: int = Field(default=8000, ge=1, le=65535)
    APP_VERSION: str = Field(default="0.1.0", min_length=1)
    DEBUG: bool = Field(default=True)

    # --- Logs ---
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")

    # --- Raiz para artefatos de runtime ---
    # Quando definida e válida, é usada para resolver o caminho do
    # banco SQLite, logs e uploads. Quando vazia, ``BASE_DIR`` é
    # usado como fallback transparente.
    PROJECT_ROOT: Optional[str] = Field(default=None)

    # --- Banco de Dados ---
    # Aceita o placeholder ``${PROJECT_ROOT}``, substituído pela
    # validação por ``PROJECT_ROOT`` (quando válido) ou ``BASE_DIR``.
    # Quando vazia, um caminho-padrão é montado a partir da raiz
    # de runtime.
    DATABASE_URL: str = Field(default="")

    # --- JWT ---
    JWT_SECRET: SecretStr = Field(default=SecretStr("secret"))
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_MINUTES: int = Field(default=15, ge=1, le=1440)

    # --- Usuários demo (seed) ---
    DEMO_USER_EMAIL: EmailStr = Field(default="aluno@uni7.edu.br")
    DEMO_USER_PASSWORD: str = Field(default="teste123", min_length=1)
    DEMO_USER_2_EMAIL: EmailStr = Field(default="aluno2@uni7.edu.br")
    DEMO_USER_2_PASSWORD: str = Field(default="teste456", min_length=1)

    # --- Gateway de pagamento ---
    # Tempo (em segundos) do ``time.sleep`` em ``cobrar`` que
    # simula latência de comunicação externa.
    GATEWAY_DELAY_SECONDS: float = Field(default=5.0, ge=0.0, le=60.0)
    # Quando True, ``cobrar`` retorna False (caminho HTTP 402).
    GATEWAY_FORCAR_FALHA: bool = Field(default=False)

    # --- CORS ---
    # ``NoDecode`` evita que pydantic-settings tente fazer parse
    # JSON do valor antes do ``field_validator`` rodar.
    CORS_ORIGINS: Annotated[List[str], NoDecode] = Field(default_factory=list)

    # --- Toggles de comportamento ---
    # Quando True, requisições são limitadas por taxa.
    RATE_LIMIT_ENABLED: bool = Field(default=False)
    # Quando True, a consulta de pedido por ID opera de forma
    # global, sem aplicar filtro por dono.
    PEDIDOS_CONSULTA_GLOBAL: bool = Field(default=True)
    # Quando True, o pedido é serializado em formato detalhado
    # (schema com mais campos).
    PEDIDOS_RESPOSTA_DETALHADA: bool = Field(default=True)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v):
        """Aceita string CSV (``'https://a,https://b'``) ou lista."""
        if isinstance(v, str):
            limpo = v.strip()
            if not limpo:
                return []
            return [item.strip() for item in limpo.split(",") if item.strip()]
        return v

    @model_validator(mode="after")
    def validate_paths(self) -> "Settings":
        """
        Valida paths e segredos; resolve ``${PROJECT_ROOT}`` em
        ``DATABASE_URL``. Falha rápido com mensagens em PT-BR.

        Verificações executadas:
            1. ``JWT_SECRET`` possui ao menos 1 caractere.
            2. ``PROJECT_ROOT``, quando definido, aponta para um
               diretório existente, do tipo diretório, e gravável.
            3. ``DATABASE_URL`` tem o placeholder ``${PROJECT_ROOT}``
               substituído pela raiz resolvida; se vazia, recebe
               um caminho-padrão a partir da raiz de runtime.
        """
        # 1) JWT_SECRET — não vazio
        if len(self.JWT_SECRET.get_secret_value()) < 1:
            raise ValueError(
                "Configuração inválida: JWT_SECRET não pode estar "
                "vazio. Defina JWT_SECRET no arquivo .env."
            )

        # 2) PROJECT_ROOT — quando definido, deve existir, ser
        # diretório e ser gravável. Caso contrário, falhar rápido.
        raiz_resolvida: Path = BASE_DIR
        if self.PROJECT_ROOT:
            candidato = Path(self.PROJECT_ROOT).expanduser().resolve()
            if not candidato.exists():
                raise ValueError(
                    f"Configuração inválida: PROJECT_ROOT '{candidato}' "
                    "não existe. Crie o diretório ou ajuste a variável "
                    "no arquivo .env."
                )
            if not candidato.is_dir():
                raise ValueError(
                    f"Configuração inválida: PROJECT_ROOT '{candidato}' "
                    "não é um diretório."
                )
            if not os.access(candidato, os.W_OK):
                raise ValueError(
                    f"Configuração inválida: PROJECT_ROOT '{candidato}' "
                    "não possui permissão de escrita."
                )
            raiz_resolvida = candidato

        # 3) DATABASE_URL — substituir placeholder ou aplicar
        # caminho-padrão a partir da raiz de runtime. Em todos os
        # casos, o path é normalizado via ``Path.as_posix()`` para
        # garantir separadores forward-slash consistentes (evita
        # barras mistas em Windows como
        # ``sqlite:///C:\Users\aluno/ecommerce.db``).
        url = self.DATABASE_URL
        if "${PROJECT_ROOT}" in url:
            self.DATABASE_URL = url.replace(
                "${PROJECT_ROOT}", raiz_resolvida.as_posix()
            )
        elif not url:
            db_path = (raiz_resolvida / "ecommerce.db").as_posix()
            self.DATABASE_URL = f"sqlite:///{db_path}"

        return self

    @property
    def raiz_runtime(self) -> Path:
        """Diretório raiz efetivo para artefatos de runtime."""
        return _resolver_raiz_runtime(self.PROJECT_ROOT)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Retorna a instância de Settings (cacheada por processo).

    Padrão recomendado para uso com FastAPI ``Depends``. Em
    testes, ``get_settings.cache_clear()`` permite recarregar
    as variáveis após alterar o ambiente.

    Retorno:
        Instância única de ``Settings`` para o processo atual.
    """
    return Settings()


# Singleton lazy de módulo: criado uma única vez na importação.
# Demais módulos consomem via ``from ecommerce.config import settings``.
settings: Settings = get_settings()
