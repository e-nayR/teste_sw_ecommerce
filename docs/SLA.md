# Acordo de Nível de Serviço (SLA) - Teste de Carga

Este documento define os critérios de aceitação para o desempenho do sistema P0912_ECOMMERCE sob carga, conforme os requisitos do Laboratório de Testes.

## 1. Metas de SLA

Para que o sistema seja considerado aprovado no Teste de Carga (Load Testing), ele deve cumprir as seguintes metas durante a **Rodada 4 (1000 usuários simultâneos por 30 minutos)**:

| ID | Métrica | Alvo (SLA) | Descrição |
|:---|:---|:---|:---|
| **SLA_01** | **Taxa de Sucesso** | > 99% | Menos de 1% das requisições podem resultar em erro (HTTP 5xx). |
| **SLA_02** | **Latência p95 (Leitura)** | < 500ms | 95% das chamadas de listagem de produtos devem responder em até 500ms. |
| **SLA_03** | **Latência p95 (Escrita)** | < 1500ms | 95% das chamadas de checkout/pagamento devem responder em até 1.5s. |
| **SLA_04** | **Vazão (Throughput)** | > 100 RPS | O sistema deve sustentar uma vazão mínima de 100 requisições por segundo. |

## 2. Condições de Teste

*   **Ambiente:** Execução local (venv) com banco de dados SQLite.
*   **Configuração:** `GATEWAY_DELAY_SECONDS=0` (simulando resposta instantânea do provedor de pagamento).
*   **Perfil de Carga:** Rampa progressiva de 250 a 1200 usuários.

## 3. Veredito

*   **PASS:** Todas as 4 metas acima foram atingidas na Rodada 4.
*   **FAIL:** Qualquer uma das metas não foi atingida. Requer análise de gargalo.
