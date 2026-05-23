# Plano de Teste de Carga (Load Testing) - v2

**Equipe:** 09  
**Sistema:** P0912_ECOMMERCE  
**Data:** 23/05/2026  

## 1. Objetivo
Validar a estabilidade e o tempo de resposta do sistema sob condições crescentes de carga, garantindo que o sistema suporte até 1200 usuários simultâneos e atenda aos SLAs definidos.

## 2. Escopo de Teste
O teste foca no "Caminho Crítico" de negócio:
1.  Autenticação (`/api/login`)
2.  Navegação no catálogo (`/api/produtos`)
3.  Gestão de carrinho (`/api/carrinho/itens`)
4.  Finalização de compra (`/api/checkout`)

## 3. Estratégia de Execução (Rampa)
Conforme exigido na ficha de avaliação, o teste será dividido em 5 rodadas progressivas:

| Rodada | Usuários Simultâneos | Duração | Objetivo |
|:---:|:---:|:---:|:---|
| 1 | 250 | 5 min | Carga leve - Baseline de performance. |
| 2 | 500 | 5 min | Carga moderada. |
| 3 | 750 | 5 min | Carga alta - Limite esperado de conforto. |
| 4 | 1000 | 30 min | **Veredito Formal** - Estabilidade prolongada. |
| 5 | 1200 | 5 min | Pico de carga - Stress preventivo. |

## 4. Configuração do Ambiente
*   **Ferramenta:** Locust
*   **Arquivo de Teste:** `tests/load/locustfile_load.py`
*   **Variáveis de Ambiente (.env):**
    *   `GATEWAY_DELAY_SECONDS=0`
    *   `GATEWAY_FORCAR_FALHA=false`

## 5. Critérios de Aceitação (SLAs)
Os resultados serão comparados com o arquivo `docs/SLA.md`. O veredicto será baseado na performance observada na **Rodada 4**.

## 6. Comandos para Execução
Para rodar o teste via CLI e gerar os relatórios:
```bash
locust -f tests/load/locustfile_load.py --host http://localhost:8000 --csv docs/relatorios/load_results
```
