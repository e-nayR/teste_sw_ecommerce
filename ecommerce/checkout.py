"""
Operação de finalização da compra (checkout) e gateway de
pagamento.

Objetivo: orquestrar a cobrança do total do carrinho contra um
gateway externo de pagamento, retornando uma mensagem de
sucesso ou levantando exceção em caso de recusa.

Posição na arquitetura: módulo de aplicação que depende de
``ecommerce.carrinho`` (objeto carrinho do domínio) e do
gateway abstrato (injetado via construtor — ``Checkout(gateway)``).
A camada HTTP (``ecommerce.routers.checkout_router``) consome
este módulo sem reimplementar lógica de negócio.

Conceitos didáticos abordados: injeção de dependência (gateway
no construtor), separação de responsabilidades (orquestração no
``Checkout``, infraestrutura no ``GatewayDePagamento``),
configurabilidade externa via ``settings``.

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
import time

# 2) Imports de bibliotecas de terceiros
# (nenhum)

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
from ecommerce.config import settings


class GatewayDePagamento:
    """
    Cliente para um gateway externo de pagamento.

    Objetivo: encapsular a chamada de cobrança contra o
    provedor financeiro, expondo uma interface estável para o
    ``Checkout``.

    Conceitos didáticos:
    - Adapter (camada de abstração sobre serviço externo)
    - Configurabilidade (latência simulada e modo de falha
      controlados via ``settings``)
    """

    def cobrar(self, valor, cartao):
        """
        Solicita ao gateway a cobrança de um valor em um cartão.

        Parâmetros:
            valor: valor monetário a ser cobrado.
            cartao: identificador do cartão do cliente.

        Retorno:
            ``True`` quando a cobrança é aceita pelo gateway,
            ``False`` caso contrário.
        """
        print(f"\nConectando ao banco para cobrar R$ {valor}...")
        time.sleep(settings.GATEWAY_DELAY_SECONDS)
        if settings.GATEWAY_FORCAR_FALHA:
            return False
        return True


class Checkout:
    """
    Orquestra a finalização da compra de um carrinho.

    Objetivo: reunir o cálculo do total e a chamada ao gateway,
    devolvendo o resultado para a camada HTTP.

    Conceitos didáticos:
    - Injeção de dependência (gateway recebido no construtor)
    - Composição sobre herança
    - Testabilidade (gateway pode ser substituído por dublê em
      testes unitários)
    """

    def __init__(self, gateway: GatewayDePagamento):
        """
        Inicializa o Checkout com o gateway de pagamento.

        Parâmetros:
            gateway: instância (ou dublê) de ``GatewayDePagamento``.
        """
        self.gateway = gateway

    def finalizar_compra(self, carrinho, cartao):
        """
        Finaliza a compra do carrinho cobrando do cartão.

        Parâmetros:
            carrinho: ``CarrinhoDeCompras`` com os produtos do
                      cliente.
            cartao: identificador do cartão do cliente.

        Retorno:
            String descritiva do resultado em caso de sucesso
            (``"Sucesso: Grátis"`` ou
            ``"Sucesso: Pagamento aprovado"``).

        Levanta:
            ValueError: quando o gateway recusa a cobrança.
        """
        total = carrinho.calcular_total()

        if total <= 0:
            return "Sucesso: Grátis"

        sucesso = self.gateway.cobrar(total, cartao)

        if sucesso:
            return "Sucesso: Pagamento aprovado"
        else:
            raise ValueError("Pagamento recusado pelo banco")
