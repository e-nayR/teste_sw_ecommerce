"""
Autenticação JWT — geração, validação e dependência FastAPI.

Objetivo: oferecer as primitivas de autenticação consumidas
pelos routers — geração e validação de JWT, hashing bcrypt
de senhas e a dependência ``get_current_user`` que resolve o
usuário autenticado a partir de um token (header ou cookie).

Posição na arquitetura: módulo de autenticação consumido por
``ecommerce.routers.auth_router`` (login) e por todos os
routers protegidos via ``Depends(get_current_user)``. A camada
de domínio (``ecommerce.carrinho`` etc.) permanece sem
dependência deste módulo.

Conceitos didáticos abordados: criptografia de senhas (bcrypt
com salt automático), tokens stateless (JWT), dependência
injetável (``get_current_user``), separação entre autenticação
(quem é o usuário) e autorização (o que ele pode fazer — fica
no router que conhece o domínio).

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
from datetime import datetime, timezone
from typing import Optional

# 2) Imports de bibliotecas de terceiros
import bcrypt
import jwt
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
from ecommerce.config import settings
from ecommerce.database import get_db
from ecommerce.models import Usuario


# ──────────────────────────────────────────────────────────────
# Hashing de senhas (bcrypt direto, sem passlib)
# ──────────────────────────────────────────────────────────────


def gerar_hash_senha(senha: str) -> bytes:
    """
    Gera o hash bcrypt da senha informada.

    Cada chamada produz um salt aleatório novo (``bcrypt.gensalt()``),
    incorporado ao próprio hash retornado.

    Parâmetros:
        senha: senha em texto puro (UTF-8).

    Retorno:
        Hash bcrypt em ``bytes`` (~60 bytes contendo salt + hash).
    """
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())


def verificar_senha(senha: str, hash_armazenado: bytes) -> bool:
    """
    Compara uma senha em texto puro com o hash armazenado.

    Parâmetros:
        senha: senha em texto puro.
        hash_armazenado: hash bcrypt previamente gerado.

    Retorno:
        ``True`` se a senha confere com o hash, ``False`` caso
        contrário ou em caso de erro (hash mal-formado).
    """
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), hash_armazenado)
    except (ValueError, TypeError):
        return False


# ──────────────────────────────────────────────────────────────
# JWT (PyJWT direto, sem python-jose)
# ──────────────────────────────────────────────────────────────


def criar_token(user_id: int) -> str:
    """
    Gera um JWT assinado para o usuário informado.

    O payload contém:

    - ``sub``: ``str(user_id)`` — identifica o usuário (subject).
    - ``iat``: timestamp UTC da emissão.
    - ``exp``: ``iat + JWT_EXPIRATION_MINUTES`` — expiração.

    Parâmetros:
        user_id: identificador inteiro do usuário.

    Retorno:
        Token JWT codificado como string.
    """
    agora = datetime.now(timezone.utc)
    iat_ts = int(agora.timestamp())
    exp_ts = iat_ts + settings.JWT_EXPIRATION_MINUTES * 60
    payload = {
        "sub": str(user_id),
        "iat": iat_ts,
        "exp": exp_ts,
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )


def validar_token(token: str) -> int:
    """
    Valida um JWT e retorna o ``user_id`` codificado nele.

    Parâmetros:
        token: JWT em formato string.

    Retorno:
        Identificador inteiro do usuário (``sub``).

    Levanta:
        HTTPException(401): token expirado, inválido, ou sem
        ``sub`` parseável como inteiro.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token expirado",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token inválido",
        )

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token sem identificador",
        )
    try:
        return int(sub)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token com identificador inválido",
        )


# ──────────────────────────────────────────────────────────────
# Dependência FastAPI: get_current_user
# ──────────────────────────────────────────────────────────────


def _extrair_token(
    authorization: Optional[str], access_token: Optional[str]
) -> str:
    """
    Extrai o token de uma das duas fontes — header tem prioridade.

    Quando ``Authorization`` está presente, deve usar o esquema
    ``Bearer``. Caso ausente, recorre ao cookie ``access_token``.
    Se ambas as fontes estiverem vazias, levanta HTTP 401.

    Parâmetros:
        authorization: valor do header ``Authorization``.
        access_token: valor do cookie ``access_token``.

    Retorno:
        Token em formato string.

    Levanta:
        HTTPException(401): nenhuma das duas fontes preenchida,
        ou header sem esquema ``Bearer``.
    """
    if authorization:
        if not authorization.lower().startswith("bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="header Authorization deve usar Bearer",
            )
        return authorization[7:].strip()
    if access_token:
        return access_token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="autenticação requerida",
    )


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Resolve o usuário autenticado a partir do token.

    O token pode vir em ``Authorization: Bearer <jwt>`` (header)
    ou no cookie ``access_token`` (configurado HttpOnly pela
    rota de login). O header tem prioridade quando ambos estão
    presentes.

    Parâmetros:
        authorization: header ``Authorization`` (opcional).
        access_token: cookie ``access_token`` (opcional).
        db: sessão SQLAlchemy injetada.

    Retorno:
        ``Usuario`` ORM correspondente ao ``sub`` do token.

    Levanta:
        HTTPException(401): token ausente, inválido, expirado
        ou usuário não localizado no banco.
    """
    token = _extrair_token(authorization, access_token)
    user_id = validar_token(token)
    usuario = db.get(Usuario, user_id)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="usuário não encontrado",
        )
    return usuario
