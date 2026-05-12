# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste
arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e o projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

## [0.1.0] — 2026-04-30

Entrega inicial do P0912 ECOMMERCE.

### Adicionado

#### API REST (sob `/api`)
- `GET /api/health` — health check com versão da aplicação e timestamp.
- `GET /api/produtos` e `GET /api/produtos/{id}` — catálogo demo.
- `POST /api/login` — autenticação retornando JWT em cookie HttpOnly.
- `GET /api/me` — dados do usuário autenticado.
- `GET /api/carrinho` — carrinho ativo do usuário.
- `POST /api/carrinho/itens` — adiciona item ao carrinho.
- `DELETE /api/carrinho/itens/{produto_id}` — remove item.
- `POST /api/carrinho/limpar` — esvazia o carrinho.
- `GET /api/carrinho/total` — totaliza, com preview opcional de desconto.
- `POST /api/checkout` — finaliza a compra via gateway simulado.
- `GET /api/pedidos` e `GET /api/pedidos/{id}` — histórico de pedidos.

#### UI Jinja2 (rotas no root)
- `GET /` — catálogo público com card por produto.
- `GET /login` + `POST /login` — formulário de autenticação.
- `POST /logout` — remove cookie e redireciona.
- `GET /carrinho` — carrinho do usuário com preview de desconto.
- `POST /carrinho/itens` e `POST /carrinho/limpar` — ações do carrinho.
- `GET /checkout` + `POST /checkout` — formulário de finalização.
- `GET /pedidos` — histórico do usuário.
- `GET /sucesso` e `GET /erro` — telas de confirmação e erro.
- Atributos `data-testid` em todos os elementos interativos para
  automação de testes de UI.
- Quatro estados visuais (loading, sucesso, erro, vazio) em todas
  as páginas relevantes.

#### Domínio
- `CarrinhoDeCompras` com adição de produtos e cálculo de total
  com desconto percentual.
- `Checkout` orquestrando `GatewayDePagamento` com tratamento de
  aprovação e recusa.

#### Persistência
- ORM SQLAlchemy 2.0 (`Mapped`, `mapped_column`).
- Modelos: `Usuario`, `Carrinho`, `ItemCarrinho`, `Pedido`,
  `ItemPedido`.
- Datetimes timezone-aware (`datetime.now(timezone.utc)`).
- Adapter `carrinho_persistencia.py` mediando ORM ↔ domínio.
- Migration inicial (`alembic/versions/001_initial_schema.py`).

#### Autenticação
- JWT via `PyJWT` (HS256), cookie HttpOnly + SameSite=Lax + Path=/.
- Hash de senha com `bcrypt` direto (sem `passlib`).
- O mesmo cookie autentica tanto a UI quanto a API REST.

#### Configuração
- `Settings` baseado em `pydantic-settings`, lendo `.env`.
- `SecretStr` para `JWT_SECRET`, `EmailStr` para emails demo.
- Toggles operacionais: `RATE_LIMIT_ENABLED`,
  `PEDIDOS_CONSULTA_GLOBAL`, `PEDIDOS_RESPOSTA_DETALHADA`,
  `GATEWAY_FORCAR_FALHA`.
- `APP_VERSION` configurável via `.env`.

#### Tooling e GC&D
- `menu.py` interativo na raiz (gate de Python 3.11, subprocess
  cross-platform Windows/POSIX).
- `requirements.txt` e `requirements-dev.txt` com pinning compatível.
- `requirements.lock` e `requirements-dev.lock` com hashes SHA-256
  via `pip-compile --generate-hashes`.
- `pyproject.toml` com configuração do pytest e nove markers
  (smoke, functional, integration, regression, stress, security,
  ui, fuzz, load).
- `.gitattributes` com normalização de line endings e
  `export-ignore` da pasta de material restrito.
- `pip-audit` listado em `requirements-dev.txt` para auditoria
  de pacotes.

#### Documentação
- `README.md` na raiz com onboarding completo.
- `tests/README.md` com instruções de execução por categoria.
- `docs/ARQUITETURA.md` com visão técnica das camadas.
- `docs/COMO_EXECUTAR_TESTES.md` com comandos por categoria.
- `LICENSE` (MIT).

[0.1.0]: https://example.com/repos/P0912_ECOMMERCE/releases/tag/v0.1.0
