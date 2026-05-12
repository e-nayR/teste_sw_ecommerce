"""
Modelos de domínio do carrinho de compras.

Objetivo: representar produtos e o carrinho do cliente, com
agregação de preços e suporte a desconto percentual sobre o
valor total.

Posição na arquitetura: módulo de domínio puro, sem dependência
de banco de dados ou framework web. É consumido por
``ecommerce.carrinho_persistencia`` (camada de persistência) e
por ``ecommerce.checkout`` (operação de finalização da compra).

Conceitos didáticos abordados: encapsulamento, composição
(carrinho contém produtos), separação entre domínio e
infraestrutura, testabilidade by design.

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
# (nenhum necessário — domínio puro)

# 2) Imports de bibliotecas de terceiros
# (nenhum)

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
# (nenhum)


class Produto:
    """
    Representa um produto comercializável.

    Objetivo: encapsular o par (nome, preço) que identifica
    economicamente um item do catálogo, sem acoplamento com
    persistência ou apresentação.

    Conceitos didáticos:
    - Encapsulamento (estado interno em atributos públicos
      simples)
    - Modelo de domínio puro (sem framework externo)
    """

    def __init__(self, nome, preco):
        """
        Inicializa um produto.

        Parâmetros:
            nome: nome do produto.
            preco: preço unitário em reais.
        """
        self.nome = nome
        self.preco = preco


class CarrinhoDeCompras:
    """
    Representa o carrinho de compras de um cliente.

    Objetivo: agregar produtos selecionados pelo usuário e
    calcular o valor total da compra, com suporte a desconto
    percentual.

    Conceitos didáticos:
    - Encapsulamento (estado interno em ``self.produtos``)
    - Composição (carrinho contém produtos)
    - Testabilidade (estado e comportamento facilmente
      verificáveis em isolamento)
    """

    def __init__(self):
        """Inicializa um carrinho vazio."""
        self.produtos = []

    def adicionar_produto(self, produto):
        """
        Adiciona um produto ao carrinho.

        Parâmetros:
            produto: instância de ``Produto`` a ser adicionada.
        """
        self.produtos.append(produto)

    def calcular_total(self, desconto_percentual: float = 0) -> float:
        """
        Calcula o total do carrinho aplicando um desconto opcional.

        Objetivo: somar o preço de todos os produtos do carrinho
        e aplicar um desconto percentual sobre o valor agregado.

        Parâmetros:
            desconto_percentual: percentual de desconto a aplicar.
                                  Valor padrão: 0 (sem desconto).

        Retorno:
            Valor total da compra após desconto, em reais.
        """
        total = sum(produto.preco for produto in self.produtos)
        valor_desconto = total * (desconto_percentual / 100)
        return total - valor_desconto
