"""
Pacote de routers FastAPI da API ECOMMERCE.

Cada submódulo expõe um ``router: APIRouter`` com ``prefix="/api"``.
Este ``__init__`` re-exporta os routers para o import unificado a
partir de ``ecommerce.routers`` (consumido por ``ecommerce.api``).

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

from ecommerce.routers.auth_router import router as auth_router
from ecommerce.routers.carrinho_router import router as carrinho_router
from ecommerce.routers.checkout_router import router as checkout_router
from ecommerce.routers.health_router import router as health_router
from ecommerce.routers.pedidos_router import router as pedidos_router
from ecommerce.routers.produtos_router import router as produtos_router


__all__ = [
    "auth_router",
    "carrinho_router",
    "checkout_router",
    "health_router",
    "pedidos_router",
    "produtos_router",
]
