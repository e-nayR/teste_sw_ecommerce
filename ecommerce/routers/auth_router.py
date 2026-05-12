"""
Router de autenticação.

Objetivo: expor ``POST /api/login`` (autenticação por email +
senha, retornando JWT no body e em cookie HttpOnly),
``POST /api/logout`` (remove o cookie) e ``GET /api/me``
(retorna o usuário autenticado).

Posição na arquitetura: router que conecta o módulo
``ecommerce.auth`` (geração/validação de JWT, hashing) à API
HTTP. Após o login, qualquer router protegido por
``Depends(get_current_user)`` aceita tanto o header
``Authorization`` quanto o cookie ``access_token``.

Conceitos didáticos abordados: cookie HttpOnly como mitigação
contra XSS, dupla forma de transporte de token (header e
cookie), separação entre login (autenticação) e identidade
(``GET /api/me``).

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
# (nenhum)

# 2) Imports de bibliotecas de terceiros
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
from ecommerce.auth import (
    criar_token,
    get_current_user,
    verificar_senha,
)
from ecommerce.config import settings
from ecommerce.database import get_db
from ecommerce.models import Usuario
from ecommerce.schemas import LoginIn, LoginOut, UsuarioOut


router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/login", response_model=LoginOut)
def login(
    payload: LoginIn,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginOut:
    """
    Autentica o usuário e devolve um JWT no body e em cookie.

    O cookie ``access_token`` é definido com ``HttpOnly``,
    ``SameSite=Lax`` e ``Path=/``, com ``Max-Age`` igual a
    ``JWT_EXPIRATION_MINUTES * 60``. Em ambiente local
    (``http://localhost``) o atributo ``Secure`` não é definido.

    Parâmetros:
        payload: ``LoginIn`` com email e senha.
        response: objeto FastAPI ``Response`` (injetado).
        db: sessão SQLAlchemy.

    Retorno:
        ``LoginOut`` com ``access_token``, ``token_type`` e
        ``expira_em_segundos``.

    Levanta:
        HTTPException(401): credenciais inválidas.
    """
    stmt = select(Usuario).where(Usuario.email == payload.email)
    usuario = db.execute(stmt).scalar_one_or_none()
    if usuario is None or not verificar_senha(
        payload.senha, usuario.senha_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="email ou senha inválidos",
        )

    token = criar_token(usuario.id)
    expira_segundos = settings.JWT_EXPIRATION_MINUTES * 60

    response.set_cookie(
        key="access_token",
        value=token,
        max_age=expira_segundos,
        httponly=True,
        samesite="lax",
        path="/",
        secure=False,
    )

    return LoginOut(
        access_token=token,
        token_type="bearer",
        expira_em_segundos=expira_segundos,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(response: Response) -> dict:
    """
    Remove o cookie ``access_token`` do navegador.

    Não há revogação server-side do token — quem possuir o JWT
    em mãos pode continuar usando até o ``exp``.

    Retorno:
        ``{"detail": "logout realizado"}``.
    """
    response.delete_cookie(key="access_token", path="/")
    return {"detail": "logout realizado"}


@router.get("/me", response_model=UsuarioOut)
def me(usuario: Usuario = Depends(get_current_user)) -> UsuarioOut:
    """
    Retorna os dados do usuário autenticado.

    Parâmetros:
        usuario: ``Usuario`` ORM resolvido pela dependência
                 ``get_current_user``.

    Retorno:
        ``UsuarioOut`` com ``id``, ``email`` e ``nome``.
    """
    return UsuarioOut(
        id=usuario.id, email=usuario.email, nome=usuario.nome
    )
