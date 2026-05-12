"""
Factory da aplicação FastAPI.

Objetivo: oferecer ``criar_app()``, factory pura que instancia
o ``FastAPI`` com middleware CORS condicional, registra os
exception handlers padronizados e inclui os 6 routers da API.

Posição na arquitetura: ponto de entrada da camada HTTP.
Consumido pelo ``uvicorn`` (modo ``--factory``) e por testes
de integração que precisam de uma instância nova da aplicação.

Conceitos didáticos abordados: factory pattern, ausência de
estado global no nível de módulo, ordem determinística de
configuração (CORS → handlers → routers).

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
from pathlib import Path

# 2) Imports de bibliotecas de terceiros
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
from ecommerce.config import settings
from ecommerce.errors import registrar_handlers
from ecommerce.routers import (
    auth_router,
    carrinho_router,
    checkout_router,
    health_router,
    pedidos_router,
    produtos_router,
)
from ecommerce.ui.ui_router import router as ui_router


def criar_app() -> FastAPI:
    """
    Instancia uma nova ``FastAPI`` configurada e pronta para
    servir.

    Ordem de configuração:

    1. Construção da ``FastAPI`` (título, versão, descrição).
    2. ``CORSMiddleware`` — registrado APENAS se
       ``settings.CORS_ORIGINS`` for não-vazio. Lista vazia
       significa same-origin only e nenhum middleware CORS.
    3. ``registrar_handlers(app)`` — antes dos routers, para
       capturar exceções de qualquer endpoint.
    4. Inclusão dos 6 routers da API (``prefix="/api"``).
    5. Inclusão do ``ui_router`` (rotas HTML, sem prefixo).
    6. Mount de arquivos estáticos em ``/static`` apontando para
       ``ecommerce/ui/static/``.

    Retorno:
        Instância ``FastAPI`` pronta para ``uvicorn`` rodar.
    """
    app = FastAPI(
        title="P0912 ECOMMERCE",
        version=settings.APP_VERSION,
        description=(
            "Plataforma e-commerce didática — disciplinas de "
            "Teste de Software e Gerência de Configuração e "
            "Dependência."
        ),
    )

    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    registrar_handlers(app)

    app.include_router(health_router)
    app.include_router(produtos_router)
    app.include_router(auth_router)
    app.include_router(carrinho_router)
    app.include_router(checkout_router)
    app.include_router(pedidos_router)
    app.include_router(ui_router)

    static_dir = Path(__file__).resolve().parent / "ui" / "static"
    app.mount(
        "/static",
        StaticFiles(directory=str(static_dir)),
        name="static",
    )

    return app
