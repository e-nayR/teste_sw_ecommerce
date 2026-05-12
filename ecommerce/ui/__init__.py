"""
Pacote da camada de apresentação (UI) baseada em Jinja2.

Submódulos:
- ``ui_router``: APIRouter com prefix vazio, rotas HTML do front-end.

Este pacote serve a UI mínima do projeto. O JWT é transportado via
cookie HttpOnly (mesmo cookie definido por ``POST /api/login``); a UI
não manipula tokens em JavaScript.

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""
