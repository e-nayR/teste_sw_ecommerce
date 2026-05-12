# Como executar os testes — P0912 ECOMMERCE

Este guia descreve **como rodar** cada uma das 9 categorias de
teste do material da disciplina. Os testes em si não estão
prontos — escrevê-los faz parte do exercício de cada aula.

---

## Pré-requisitos comuns

Com o virtualenv ativado e as dependências de desenvolvimento
instaladas:

```bash
pip install -r requirements-dev.txt
```

Você terá `pytest`, `httpx`, `locust`, `schemathesis`,
`playwright`, `pytest-playwright` e `pip-audit` disponíveis.

Para que a API esteja rodando durante testes que consomem HTTP
(integration, ui, fuzz, load, stress), abra **outro terminal** e
suba o servidor:

```bash
python menu.py
# escolha 1) Subir API
```

A configuração do `pytest` está em `pyproject.toml` na raiz —
markers, descoberta de arquivos e flags padrão. Não há
`pytest.ini` separado.

---

## 1. Smoke

Verificações rápidas para garantir que a aplicação subiu e
responde no caminho feliz mais elementar.

**Pasta:** `tests/smoke/`
**Marker:** `smoke`

```bash
pytest -m smoke
# ou apontando direto para a pasta:
pytest tests/smoke/
```

Sugestão de cobertura: `GET /api/health`, `GET /api/produtos`,
`GET /` (a página inicial da UI).

---

## 2. Functional

Testes de comportamento de uso normal — fluxos felizes ponta a
ponta, com asserts sobre o que a aplicação faz, não como faz.

**Pasta:** `tests/functional/`
**Marker:** `functional`

```bash
pytest -m functional
```

Use `pytest.mark.parametrize` para varrer combinações de
entrada (válidas, inválidas, fronteira). Considere alternar
toggles em `.env` antes de subir a API para cobrir cenários
específicos (ex.: `GATEWAY_FORCAR_FALHA=true` para testar a
resposta de pagamento recusado).

---

## 3. Integration

Verifica composição entre componentes — banco real, routers
encadeados, dependências reais. `httpx` é o cliente HTTP
recomendado:

```python
# Apenas exemplo de uso da ferramenta — não é um teste pronto.
import httpx
client = httpx.Client(base_url="http://127.0.0.1:8000")
```

**Pasta:** `tests/integration/`
**Marker:** `integration`

```bash
pytest -m integration
```

Fluxo típico a cobrir: login → adicionar item → checkout →
listar pedidos.

---

## 4. Regression

Casos previamente quebrados que não devem voltar a falhar.
Útil ao corrigir um defeito identificado: o teste vai junto da
correção e age como escudo contra retrocesso futuro.

**Pasta:** `tests/regression/`
**Marker:** `regression`

```bash
pytest -m regression
```

Considere snapshots de respostas (com `pytest-snapshot` ou
similar) para detectar mudanças não intencionais em formato de
saída.

---

## 5. Stress

Comportamento sob carga elevada e recursos escassos. A
ferramenta sugerida para cargas HTTP é o **Locust**.

**Pasta:** `tests/stress/`
**Marker:** `stress`

Locust não roda via `pytest`; é um processo separado. Você cria
um `locustfile.py` em `tests/stress/` descrevendo as tasks e:

```bash
locust -f tests/stress/locustfile.py --host http://127.0.0.1:8000
```

Abra `http://127.0.0.1:8089/` para iniciar o cenário com número
de usuários e taxa de spawn.

Para incluir checagens leves no fluxo Pytest (ex.: tempo de
resposta sob laço apertado), você pode marcar testes Python
com `@pytest.mark.stress` e rodá-los com:

```bash
pytest -m stress
```

---

## 6. Security

Verificações de segurança — autenticação, autorização, escopo
de dados, hardening, e auditoria de pacotes terceiros.

**Pasta:** `tests/security/`
**Marker:** `security`

Para testes funcionais de segurança:

```bash
pytest -m security
```

Para auditoria de pacotes (uma das atividades da disciplina de
Gerência de Configuração e Dependência):

```bash
# Auditoria contra o venv ativo
pip-audit

# Auditoria contra um arquivo de requirements específico
pip-audit -r requirements.txt
```

`pip-audit` consulta avisos públicos de segurança em pacotes
Python e reporta versões afetadas com sugestão de versão
corrigida.

---

## 7. UI

Testes ponta a ponta na camada Jinja2 servida em `/`,
acionando elementos pelos atributos `data-testid` espalhados
pelos templates. A ferramenta indicada é **Playwright**.

Setup inicial (uma vez por máquina, baixa os browsers):

```bash
playwright install
```

**Pasta:** `tests/ui/`
**Marker:** `ui`

```bash
pytest -m ui
```

`pytest-playwright` provê fixtures como `page`, `context` e
`browser`. Para depurar visualmente:

```bash
pytest -m ui --headed
```

Para gravar interações como ponto de partida:

```bash
playwright codegen http://127.0.0.1:8000
```

---

## 8. Fuzz

Entradas geradas randomicamente ou por geradores baseados em
schema, para encontrar caminhos não previstos. A ferramenta
sugerida é **Schemathesis**, que usa o `openapi.json` exposto
em `/openapi.json` para gerar requisições.

**Pasta:** `tests/fuzz/`
**Marker:** `fuzz`

Com a API rodando:

```bash
schemathesis run http://127.0.0.1:8000/openapi.json
```

Você também pode escrever testes de propriedade no estilo
Hypothesis dentro de `tests/fuzz/` e marcá-los com
`@pytest.mark.fuzz`:

```bash
pytest -m fuzz
```

---

## 9. Load

Carga sustentada com cenário definido (número de usuários,
taxa de spawn, duração), tipicamente com **Locust**.

**Pasta:** `tests/load/`
**Marker:** `load`

```bash
locust -f tests/load/locustfile.py \
       --host http://127.0.0.1:8000 \
       --headless \
       --users 100 \
       --spawn-rate 10 \
       --run-time 5m
```

A diferença prática para `stress/` é o objetivo: `load/` mede
o comportamento estacionário sob volume típico; `stress/`
empurra até quebrar.

---

## Selecionando subconjuntos

Os markers permitem combinações via expressão lógica:

```bash
# Tudo, exceto load e stress (quem demora):
pytest -m "not (load or stress)"

# Apenas testes de unit, smoke e security:
pytest -m "smoke or security" tests/unit/

# Por palavra-chave no nome:
pytest -k "checkout"
```

A flag `-q` reduz a verbosidade; `-v` aumenta; `-x` aborta no
primeiro fail; `--lf` reroda apenas os que falharam na última
execução.

---

## Estrutura esperada de cada categoria

Cada pasta `tests/<categoria>/` contém apenas um `__init__.py`
vazio neste momento — é onde você adicionará seus arquivos de
teste. As convenções (configuradas em `pyproject.toml`) são:

- Arquivos: `test_*.py`
- Funções: `test_*`
- Classes (opcional): `Test*`
- Cada teste deve ter o decorator `@pytest.mark.<categoria>`
  correspondente à pasta.

Boa sorte e bons testes.
