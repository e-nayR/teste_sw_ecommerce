# P0912 ECOMMERCE

Plataforma e-commerce mínima usada como sistema-cobaia nas
disciplinas **Teste de Software** e **Gerência de Configuração e
Dependência** do curso de Sistemas de Informação da UNI7. 

prof. ARAÚJO.
aplicação implementa um catálogo de produtos, carrinho de
compras, checkout com gateway simulado, autenticação por JWT em
cookie HttpOnly e uma UI Jinja2 mínima — tudo construído em
FastAPI + SQLAlchemy + SQLite + Alembic.

---

## Pré-requisitos

- **Python 3.11.x até 3.14.x** — instalável via [pyenv](https://github.com/pyenv/pyenv),
  [asdf](https://asdf-vm.com/) ou pelo
  [instalador oficial](https://www.python.org/downloads/).
  Outras versões NÃO são suportadas; o `menu.py` fará o gate na
  primeira execução.
- **Git** — para clonar o repositório.
- **Sistema operacional** — Linux, macOS ou Windows. O projeto é
  testado em ambos POSIX e Windows.

---

## Setup passo a passo

```bash
# 1. Clonar o repositório
git clone <URL_DO_REPOSITORIO>
cd P0912_ECOMMERCE

# 2. Criar e ativar virtualenv (Python 3.11 a 3.14)
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows (cmd):
.venv\Scripts\activate.bat
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 3. Instalar dependências de desenvolvimento
pip install -r requirements-dev.txt

# 4. Copiar o template de variáveis de ambiente
cp .env.example .env
# Edite .env se quiser ajustar PROJECT_ROOT, JWT_SECRET etc.

# 5. Rodar o menu interativo
python menu.py
```

Pelo menu, a sequência típica para começar a usar é:

1. Opção **3** — Aplica as migrations (cria as tabelas).
2. Opção **2** — Popula o banco com dados demo (2 usuários e 1 pedido inicial).
3. Opção **1** — Sobe a API; abra `http://127.0.0.1:8000/` no navegador.

---

## Nota sobre `requirements.lock` (importante)

Esta versão do projeto **não inclui** os arquivos
`requirements.lock` / `requirements-dev.lock` pré-gerados,
pois marcadores `python_version` variam entre 3.11, 3.12, 3.13
e 3.14. Para garantir reprodutibilidade da sua instalação,
regere os locks localmente na sua versão de Python:

```bash
pip install pip-tools
pip-compile --generate-hashes requirements.txt     -o requirements.lock
pip-compile --generate-hashes requirements-dev.txt -o requirements-dev.lock
pip install --require-hashes -r requirements-dev.lock
```

Para o setup descrito acima (`pip install -r requirements-dev.txt`),
sem `--require-hashes`, qualquer versão Python 3.11.x a 3.14.x
compatível com os ranges declarados em `requirements*.txt` funciona.

---

## Como usar o menu

`python menu.py` exibe um menu numerado. Cada opção:

| Opção | Ação                                                                              |
|-------|-----------------------------------------------------------------------------------|
| **1** | Sobe `uvicorn` em `http://APP_HOST:APP_PORT/` (Ctrl+C para parar).                |
| **2** | Roda o seed (`python -m ecommerce.seed`) — idempotente, pode rodar várias vezes.  |
| **3** | Aplica `alembic upgrade head` — cria/atualiza o schema.                           |
| **4** | Roda `alembic downgrade base` (apaga TUDO; pede confirmação literal `'sim'`).     |
| **5** | Imprime as variáveis carregadas do `.env`. `JWT_SECRET` é mascarado.              |
| **0** ou **6** | Sai do menu.                                                             |

Não há flags de linha de comando — só o loop interativo.

---

## Estrutura do repositório

```
P0912_ECOMMERCE/
├── menu.py                       # Ponto de entrada interativo
├── requirements.txt              # Deps de runtime
├── requirements-dev.txt          # Deps de runtime + teste/auditoria
├── requirements.lock             # Lock com hashes (regerar em 3.11)
├── requirements-dev.lock         # Lock dev com hashes
├── pyproject.toml                # Config do pytest
├── alembic.ini                   # Config do Alembic
├── alembic/                      # Migrations
├── ecommerce/                    # Pacote da aplicação
│   ├── api.py                    #   factory FastAPI
│   ├── auth.py                   #   JWT + bcrypt
│   ├── carrinho.py               #   domínio do carrinho
│   ├── checkout.py               #   domínio do checkout
│   ├── carrinho_persistencia.py  #   adapter ORM ↔ domínio
│   ├── config.py                 #   Settings Pydantic
│   ├── database.py               #   engine + session
│   ├── errors.py                 #   exceções e handlers
│   ├── models.py                 #   ORM SQLAlchemy 2.0
│   ├── produtos.py               #   catálogo demo
│   ├── schemas.py                #   DTOs Pydantic
│   ├── seed.py                   #   popula dados demo
│   ├── routers/                  #   6 routers REST sob /api
│   └── ui/                       #   templates Jinja2 + static + ui_router
├── tests/                        # Testes (ver tests/README.md)
├── docs/
│   ├── ARQUITETURA.md            # Visão técnica das camadas
│   └── COMO_EXECUTAR_TESTES.md   # Guia das 9 categorias de teste
├── .env.example                  # Template de variáveis
├── .gitattributes
├── .gitignore
├── .python-version
├── CHANGELOG.md                  # Histórico de versões
├── LICENSE                       # MIT
└── README.md                     # Este arquivo
```

---

## Documentação adicional

- **[`tests/README.md`](tests/README.md)** — como executar os
  testes anexos do professor; estrutura das 9 categorias.
- **[`docs/COMO_EXECUTAR_TESTES.md`](docs/COMO_EXECUTAR_TESTES.md)**
  — comandos para cada categoria (Smoke, Functional, Integration,
  Regression, Stress, Security, UI, Fuzz, Load).
- **[`docs/ARQUITETURA.md`](docs/ARQUITETURA.md)** — diagrama de
  camadas, descrição dos módulos, lista de endpoints, princípios.
- **[`CHANGELOG.md`](CHANGELOG.md)** — histórico de versões.

---

## Licença

Distribuído sob a [Licença MIT](LICENSE).

Prof. ARAÚJO
