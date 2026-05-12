# Arquitetura — P0912 ECOMMERCE

Documento de referência técnica para o aluno: descreve as camadas
da aplicação, os módulos do pacote `ecommerce/`, os endpoints
expostos e os princípios arquiteturais que guiam o código.

---

## 1. Visão geral em camadas

A aplicação é organizada em quatro camadas, com fluxo de
dependências sempre top-down (camadas superiores conhecem as
inferiores; o inverso nunca acontece):

```
   ┌────────────────────────────────────────────────────────────┐
   │  APRESENTAÇÃO (Jinja2)                                     │
   │  ecommerce/ui/  →  templates HTML + ui_router              │
   └─────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
   ┌────────────────────────────────────────────────────────────┐
   │  ADAPTADORES HTTP (FastAPI)                                │
   │  ecommerce/api.py  →  factory criar_app()                  │
   │  ecommerce/routers/  →  6 routers REST sob /api            │
   └─────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
   ┌────────────────────────────────────────────────────────────┐
   │  DOMÍNIO                                                   │
   │  ecommerce/carrinho.py    Produto, CarrinhoDeCompras       │
   │  ecommerce/checkout.py    GatewayDePagamento, Checkout     │
   │  ecommerce/produtos.py    catálogo demo                    │
   └─────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
   ┌────────────────────────────────────────────────────────────┐
   │  PERSISTÊNCIA                                              │
   │  ecommerce/carrinho_persistencia.py   adapter ORM↔domínio  │
   │  ecommerce/models.py                  ORM SQLAlchemy 2.0   │
   │  ecommerce/database.py                engine + session     │
   │  alembic/versions/                    migrations           │
   └─────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
                       ┌─────────────┐
                       │   SQLite    │
                       │ ecommerce.db│
                       └─────────────┘
```

A UI consome diretamente as funções dos routers REST como
funções Python — não há chamada HTTP interna entre as camadas
de apresentação e de adaptação. Isso mantém o overhead próximo
de zero e faz com que o cookie HttpOnly definido por
`POST /api/login` autentique tanto a UI quanto chamadas REST.

---

## 2. Módulos do pacote `ecommerce/`

| Módulo                        | Papel resumido                                                                          |
|-------------------------------|------------------------------------------------------------------------------------------|
| `__init__.py`                 | Marcador de pacote; expõe metadados básicos.                                            |
| `api.py`                      | Factory `criar_app()` — monta `FastAPI`, CORS condicional, handlers, routers, static.   |
| `auth.py`                     | JWT (`PyJWT`) + bcrypt; `criar_token`, `validar_token`, `verificar_senha`, `gerar_hash_senha`. |
| `carrinho.py`                 | Domínio: `Produto`, `CarrinhoDeCompras`, `adicionar_produto`, `calcular_total`. Sem dependência de ORM. |
| `carrinho_persistencia.py`    | Adapter: hidrata um `CarrinhoDeCompras` a partir do ORM e vice-versa.                    |
| `checkout.py`                 | Domínio: `GatewayDePagamento` (mock com delay configurável), `Checkout.finalizar_compra`. |
| `config.py`                   | `Settings` Pydantic; lê `.env`; `SecretStr` para JWT; toggles operacionais.             |
| `database.py`                 | Engine SQLAlchemy 2.0; `SessionLocal`; dependência `get_db()`.                          |
| `errors.py`                   | Exceções customizadas + handlers; formato de erro padronizado.                          |
| `models.py`                   | Modelos ORM: `Usuario`, `Carrinho`, `ItemCarrinho`, `Pedido`, `ItemPedido`.             |
| `produtos.py`                 | Catálogo demo (`PRODUTOS_DEMO`) + `buscar_produto_por_id`.                              |
| `schemas.py`                  | DTOs Pydantic: `LoginIn`, `TokenOut`, `UsuarioOut`, `CarrinhoOut`, `CheckoutIn`, `PedidoOut`, etc. |
| `seed.py`                     | Popula 2 usuários demo + 1 pedido inicial; idempotente; `python -m ecommerce.seed`.     |
| `routers/auth_router.py`      | `POST /api/login`, `GET /api/me`.                                                       |
| `routers/carrinho_router.py`  | Operações de carrinho sob `/api/carrinho/*`.                                            |
| `routers/checkout_router.py`  | `POST /api/checkout`.                                                                   |
| `routers/health_router.py`    | `GET /api/health`.                                                                      |
| `routers/pedidos_router.py`   | Histórico de pedidos sob `/api/pedidos`.                                                |
| `routers/produtos_router.py`  | `GET /api/produtos`, `GET /api/produtos/{id}`.                                          |
| `ui/ui_router.py`             | Rotas HTML (root, sem prefixo); reusa funções dos routers REST.                          |
| `ui/templates/*.html`         | 8 templates Jinja2 (com herança de `base.html`).                                         |
| `ui/static/{style.css,app.js}`| Estilos mínimos + JS de loading overlay.                                                |

---

## 3. Endpoints expostos

### 3.1 API REST (`/api/*`)

| Método | Caminho                                | Auth   | Propósito                                            |
|--------|----------------------------------------|--------|------------------------------------------------------|
| GET    | `/api/health`                          | —      | Health check (status, versão, timestamp).            |
| GET    | `/api/produtos`                        | —      | Lista o catálogo demo.                                |
| GET    | `/api/produtos/{produto_id}`           | —      | Detalhe de um produto.                                |
| POST   | `/api/login`                           | —      | Autentica e define cookie HttpOnly.                   |
| GET    | `/api/me`                              | JWT    | Dados do usuário autenticado.                         |
| GET    | `/api/carrinho`                        | JWT    | Carrinho ativo.                                       |
| POST   | `/api/carrinho/itens`                  | JWT    | Adiciona item ao carrinho.                            |
| DELETE | `/api/carrinho/itens/{produto_id}`     | JWT    | Remove item do carrinho.                              |
| POST   | `/api/carrinho/limpar`                 | JWT    | Esvazia o carrinho.                                   |
| GET    | `/api/carrinho/total`                  | JWT    | Total atual com preview de desconto.                  |
| POST   | `/api/checkout`                        | JWT    | Finaliza a compra via gateway simulado.               |
| GET    | `/api/pedidos`                         | JWT    | Histórico de pedidos do usuário.                      |
| GET    | `/api/pedidos/{pedido_id}`             | JWT    | Detalhe de um pedido.                                 |

### 3.2 UI HTML (root)

| Método | Caminho                | Auth   | Propósito                                              |
|--------|------------------------|--------|--------------------------------------------------------|
| GET    | `/`                    | —      | Catálogo público.                                      |
| GET    | `/login`               | —      | Formulário de login.                                   |
| POST   | `/login`               | —      | Autentica via form; define cookie e redireciona 303.   |
| POST   | `/logout`              | —      | Remove cookie e redireciona.                           |
| GET    | `/carrinho`            | JWT    | Carrinho com preview de desconto via querystring.      |
| POST   | `/carrinho/itens`      | JWT    | Adiciona item via form.                                |
| POST   | `/carrinho/limpar`     | JWT    | Esvazia o carrinho.                                    |
| GET    | `/checkout`            | JWT    | Formulário de finalização.                             |
| POST   | `/checkout`            | JWT    | Processa o checkout; redireciona para `/sucesso` ou `/erro`. |
| GET    | `/pedidos`             | JWT    | Histórico do usuário.                                  |
| GET    | `/sucesso`             | —      | Confirmação de compra aprovada.                        |
| GET    | `/erro`                | —      | Tela de erro genérica.                                 |

A documentação OpenAPI é servida em `/docs` (Swagger UI) e
`/redoc`. Os arquivos estáticos estão em `/static/*`.

---

## 4. Princípios arquiteturais (P1–P11)

O projeto adere a um conjunto de princípios não-negociáveis que
foram aplicados em cada decisão de design. Apresentação resumida:

- **P1 — Adoção integral do material original.** Os módulos
  `carrinho.py` e `checkout.py` foram adotados conforme entregues,
  sem refatorações estilísticas ou comportamentais não autorizadas.
- **P2 — KISS.** Preferência por soluções simples sobre soluções
  elegantes; menos camadas, menos abstrações, menos magia.
- **P3 — Foco no domínio do problema.** O domínio é a unidade
  de organização principal — não verbos técnicos como
  `controllers`, `services`, `helpers`.
- **P4 — Sem dependências de infraestrutura no domínio.**
  `carrinho.py` e `checkout.py` não conhecem ORM, HTTP nem JWT.
- **P5 — Zero hardcode.** Todas as configurações operacionais
  vêm de `Settings` (lendo `.env`); nada de `localhost:8000`
  embutido.
- **P6 — Menu numerado.** Operações comuns acessíveis por um
  único `python menu.py`, sem flags CLI.
- **P7 — Português no domínio.** Variáveis, funções e classes
  do domínio em PT-BR; chaves técnicas (códigos de erro) em
  inglês.
- **P8 — Erro estruturado.** Toda resposta de erro segue o
  schema `ErroOut` com `codigo`, `mensagem`, `detalhes`.
- **P9 — Ordem canônica de imports.** Stdlib → terceiros →
  filtros de warnings → imports locais. Sempre com cabeçalho
  explicativo.
- **P10 — Preservação semântica do material original.** O
  comportamento herdado de `carrinho.py` e `checkout.py` é
  preservado como entregue, mesmo quando refatorações
  pareceriam atraentes. Esta fidelidade é essencial para que os
  testes anexos da disciplina rodem do mesmo modo em todas as
  cópias do projeto. Detalhes específicos sobre a preservação
  estão em `tests/README.md`.
- **P11 — Discrição no código produtivo.** Docstrings e
  comentários dentro de `ecommerce/` evitam antecipar o que o
  aluno descobrirá ao escrever os testes. Verificável por uma
  série de regex em CI; o resultado esperado é zero ocorrência
  das palavras-gatilho registradas no material da disciplina.

---

## 5. Fluxos típicos

### 5.1 Login

1. Usuário envia `POST /api/login` (ou submete o form em `/login`).
2. `auth_router` consulta `Usuario` por email; valida com
   `verificar_senha` (bcrypt).
3. Se OK, gera JWT via `criar_token` (HS256, expira em
   `JWT_EXPIRATION_MINUTES`).
4. Resposta inclui `Set-Cookie: access_token=…; HttpOnly; SameSite=Lax; Path=/`.
5. Próximas requisições enviam o cookie automaticamente
   (mesma origem), seja para a API REST ou para a UI.

### 5.2 Adicionar item ao carrinho

1. `POST /api/carrinho/itens` com `{produto_id, quantidade}`
   (ou form HTML em `/carrinho/itens`).
2. `carrinho_router` resolve o `Usuario` a partir do cookie.
3. `obter_ou_criar_carrinho_ativo` retorna o `Carrinho` ORM.
4. `ItemCarrinho` é inserido (ou tem quantidade incrementada).
5. Resposta retorna `CarrinhoOut` com itens, preço unitário,
   subtotal e total sem desconto.

### 5.3 Checkout

1. `POST /api/checkout` com `{cartao, desconto_percentual}`.
2. `checkout_router` monta um `CarrinhoDeCompras` (domínio) a
   partir do ORM.
3. O desconto é aplicado mutando os preços do carrinho de
   domínio efêmero (não persiste no ORM).
4. `Checkout(GatewayDePagamento(...)).finalizar_compra(...)` é
   invocado.
5. Em sucesso, o `Pedido` é criado com status `"aprovado"`,
   `ItemPedido`s são gravados, e o `Carrinho` ativo é desativado.
6. Em recusa, um `Pedido` com status `"recusado"` é gravado
   para auditoria; o carrinho continua ativo; HTTP 402.

---

## 6. Configuração via `.env`

Todas as chaves estão documentadas em `.env.example`. Resumo dos
principais grupos:

- **Aplicação**: `APP_VERSION`, `APP_HOST`, `APP_PORT`, `DEBUG`,
  `LOG_LEVEL`, `LOG_FORMAT`, `PROJECT_ROOT`.
- **Banco**: `DATABASE_URL` (default: SQLite em `${PROJECT_ROOT}/ecommerce.db`).
- **JWT**: `JWT_SECRET` (`SecretStr`), `JWT_ALGORITHM`,
  `JWT_EXPIRATION_MINUTES`.
- **Gateway simulado**: `GATEWAY_DELAY_SECONDS`,
  `GATEWAY_FORCAR_FALHA`.
- **CORS**: `CORS_ORIGINS` (JSON array).
- **Toggles operacionais**: `RATE_LIMIT_ENABLED`,
  `PEDIDOS_CONSULTA_GLOBAL`, `PEDIDOS_RESPOSTA_DETALHADA`.
- **Demo**: `DEMO_USER_EMAIL`, `DEMO_USER_PASSWORD`,
  `DEMO_USER_2_EMAIL`, `DEMO_USER_2_PASSWORD`.
