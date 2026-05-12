# Testes — P0912 ECOMMERCE

Este diretório é o local de trabalho do aluno para todos os testes
do projeto, organizados por categoria conforme o material da
disciplina.

---

## Como rodar

A partir da raiz do repositório, com Python 3.11 e dependências de
desenvolvimento instaladas (`pip install -r requirements-dev.txt`):

```bash
# Roda apenas os testes de unidade (anexos do professor)
pytest tests/unit/

# Roda todos os testes coletados sob tests/
pytest

# Roda apenas testes de uma categoria via marker (ver pyproject.toml)
pytest -m smoke
pytest -m security
```

A configuração de descoberta (`testpaths`, `python_files`,
`markers`) está em `pyproject.toml` na raiz; este diretório não
contém `pytest.ini` próprio.

---

## ⚠️ Aviso (§9.5 da especificação)

Ao rodar `pytest tests/unit/` contra a implementação fornecida, o
resultado **esperado e correto** é:

```
6 passed, 5 failed
```

Os 5 testes que falham estão em `tests/unit/test_carrinho2.py` —
todos do `test_desconto_fora_intervalo` parametrizado.

**Estas falhas fazem parte do exercício**: a especificação prevê
que o método `CarrinhoDeCompras.calcular_total` deve levantar
`ValueError` quando o `desconto_percentual` estiver fora do
intervalo `[0, 100]`, mas a implementação atual NÃO valida esse
intervalo. Essa lacuna é um **bug de produção** que o aluno deve
descobrir e corrigir.

> **Importante**: a correção deve ser feita no **código produtivo**
> (`ecommerce/carrinho.py`), NÃO nos testes. Modificar os testes
> para que passem com o código quebrado descaracteriza o exercício.

---

## O que está aqui hoje

```
tests/
├── __init__.py
├── README.md                       ← este arquivo
├── unit/
│   ├── __init__.py
│   ├── test_carrinho.py            ← anexo do professor
│   ├── test_carrinho2.py           ← anexo do professor (5 falhas previstas)
│   └── test_checkout.py            ← anexo do professor
├── smoke/        (vazio)
├── functional/   (vazio)
├── integration/  (vazio)
├── regression/   (vazio)
├── stress/       (vazio)
├── security/     (vazio)
├── ui/           (vazio)
├── fuzz/         (vazio)
└── load/         (vazio)
```

---

## As 9 categorias (Aulas 2-9)

Cada pasta abaixo está vazia (apenas com `__init__.py`) e será
preenchida pelo aluno ao longo das aulas correspondentes do plano
da disciplina. Cada teste deve ser marcado com o `@pytest.mark.<cat>`
correspondente — os marcadores estão registrados em
`pyproject.toml`.

| Pasta            | Marker         | Foco resumido                                                |
|------------------|----------------|--------------------------------------------------------------|
| `smoke/`         | `smoke`        | Verificações rápidas de fumaça — a aplicação sobe? rotas básicas respondem? |
| `functional/`    | `functional`   | Testes de comportamento de uso normal — fluxos felizes da UI/API. |
| `integration/`   | `integration`  | Integração entre componentes — banco real, routers compostos, dependências reais. |
| `regression/`    | `regression`   | Casos previamente quebrados que não devem voltar — escudo contra retrocesso. |
| `stress/`        | `stress`       | Comportamento sob carga elevada e recursos escassos. |
| `security/`      | `security`     | Verificações de segurança — autenticação, autorização, escopo de dados, hardening. |
| `ui/`            | `ui`           | Camada Jinja2 — Playwright/Selenium contra a UI servida em `/`. |
| `fuzz/`          | `fuzz`         | Entradas randômicas/geradas — Schemathesis, Hypothesis, propriedades. |
| `load/`          | `load`         | Carga sustentada — Locust, k6 (script), métricas agregadas. |

**Não** há testes prontos nessas pastas — são deliberadamente
vazias para que o aluno escreva os seus a partir da especificação
e do material da aula.

---

## Convenções de nomenclatura

- Arquivos: `test_<assunto>.py`.
- Funções: `test_<comportamento_esperado>`.
- Classes (opcionais): `Test<Coisa>`.

Essas convenções estão configuradas em `pyproject.toml`:
`python_files = "test_*.py"`, `python_functions = "test_*"`,
`python_classes = "Test*"`.

---

## Notas finais

- Os 3 arquivos em `unit/` foram fornecidos pelo professor e devem
  ser preservados como estão. O ÚNICO ajuste autorizado em relação
  ao material original é a forma do `import` (de `from carrinho
  import …` para `from ecommerce.carrinho import …`), necessária
  porque o módulo passou a viver dentro do pacote `ecommerce`.
- Os testes de unidade rodam em milissegundos. Os testes de outras
  categorias (especialmente `load/` e `stress/`) podem demorar — o
  aluno deve usar `-m <marker>` para selecionar subconjuntos
  rápidos durante o desenvolvimento.
