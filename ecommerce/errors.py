"""
Formato padronizado de erro da API.

Objetivo: centralizar o DTO ``ErroOut`` e os exception handlers
que asseguram resposta consistente para todos os erros HTTP da
aplicação.

Posição na arquitetura: módulo consumido por ``ecommerce.api``
(factory ``criar_app``) ao registrar os handlers de exceção.
As rotas levantam ``HTTPException``, ``RequestValidationError``
ou ``ValueError`` e os handlers convertem para ``ErroOut``.

Conceitos didáticos abordados: padronização de respostas,
desacoplamento entre representação interna do erro e payload
de resposta, internacionalização parcial (chaves em inglês,
mensagens em PT-BR para o usuário).

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
from typing import Optional

# 2) Imports de bibliotecas de terceiros
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
# (nenhum)


class ErroOut(BaseModel):
    """
    DTO padronizado para respostas de erro.

    Convenção:
    - ``detail`` e ``code``: chaves em inglês (compat com
      FastAPI default e ferramentas de fuzz).
    - ``mensagem``: descrição legível em PT-BR.
    - ``campo``: campo causador, quando aplicável (validação).
    """

    detail: str
    code: str
    mensagem: str
    campo: Optional[str] = None


def _resposta_erro(
    *,
    http_status: int,
    detail: str,
    code: str,
    mensagem: str,
    campo: Optional[str] = None,
) -> JSONResponse:
    """Monta a JSONResponse padrão a partir do ErroOut."""
    payload = ErroOut(
        detail=detail, code=code, mensagem=mensagem, campo=campo
    ).model_dump()
    return JSONResponse(status_code=http_status, content=payload)


def _mensagem_para_status(http_status: int, detail: str) -> str:
    """Mapa HTTP-status → mensagem PT-BR amigável."""
    mapa = {
        400: "Requisição inválida.",
        401: "Autenticação requerida ou inválida.",
        402: "Pagamento recusado pelo provedor.",
        404: "Recurso não encontrado.",
        422: "Falha de validação dos dados de entrada.",
    }
    return mapa.get(http_status, detail)


async def _handler_http_exception(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handler para HTTPException — preserva o ``status_code``."""
    detail = (
        str(exc.detail) if exc.detail is not None else "http_error"
    )
    code = detail.upper().replace(" ", "_")
    return _resposta_erro(
        http_status=exc.status_code,
        detail=detail,
        code=code,
        mensagem=_mensagem_para_status(exc.status_code, detail),
    )


async def _handler_request_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handler para RequestValidationError (HTTP 422)."""
    erros = exc.errors()
    primeiro = erros[0] if erros else {}
    campo = ".".join(str(x) for x in primeiro.get("loc", [])) or None
    msg = primeiro.get("msg", "Falha de validação.")
    return _resposta_erro(
        http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="validation_failed",
        code="INVALID_INPUT",
        mensagem=f"Falha de validação: {msg}",
        campo=campo,
    )


async def _handler_value_error(
    request: Request, exc: ValueError
) -> JSONResponse:
    """Handler para ``ValueError`` não tratado — vira HTTP 400."""
    return _resposta_erro(
        http_status=status.HTTP_400_BAD_REQUEST,
        detail="bad_request",
        code="BAD_REQUEST",
        mensagem=str(exc) or "Requisição inválida.",
    )


def registrar_handlers(app: FastAPI) -> None:
    """
    Registra os exception handlers padrão na aplicação FastAPI.

    Parâmetros:
        app: instância ``FastAPI`` retornada por ``criar_app()``.
    """
    app.add_exception_handler(
        StarletteHTTPException, _handler_http_exception
    )
    app.add_exception_handler(
        RequestValidationError, _handler_request_validation_error
    )
    app.add_exception_handler(ValueError, _handler_value_error)
