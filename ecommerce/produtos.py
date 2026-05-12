"""
Catálogo demo de produtos.

Objetivo: fornecer a lista canônica de produtos usados pelo
``ecommerce.seed`` para popular o banco e por consultas de
runtime que precisam do nome a partir do ``produto_id``.

Posição na arquitetura: módulo de dados estáticos consumido
por seed, routers (``produtos_router``, ``carrinho_router``,
``pedidos_router``) e por ``carrinho_persistencia``.

Conceitos didáticos abordados: separação dados/lógica, dados
imutáveis em escopo de módulo, lookup determinístico por
identificador.

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
from typing import Dict, List

# 2) Imports de bibliotecas de terceiros
# (nenhum)

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
# (nenhum)


PRODUTOS_DEMO: List[Dict] = [
    {"id": 1, "nome": "Notebook Dell Inspiron",    "preco": 3000.00, "estoque": 10},
    {"id": 2, "nome": "Teclado Mecânico Logitech", "preco":  500.00, "estoque": 20},
    {"id": 3, "nome": "Mouse Razer DeathAdder",    "preco":  300.00, "estoque": 25},
    {"id": 4, "nome": "Monitor LG 27 polegadas",   "preco": 1800.00, "estoque":  8},
    {"id": 5, "nome": "Headset HyperX Cloud II",   "preco":  650.00, "estoque": 15},
    {"id": 6, "nome": "Webcam Logitech C920",      "preco":  450.00, "estoque": 12},
    {"id": 7, "nome": "Cadeira Gamer DT3",         "preco": 1200.00, "estoque":  5},
    {"id": 8, "nome": "SSD Kingston 1TB",          "preco":  500.00, "estoque": 30},
]


def buscar_produto_por_id(produto_id: int) -> Dict:
    """
    Retorna o dicionário do produto com o ``id`` informado.

    Parâmetros:
        produto_id: identificador inteiro do produto.

    Retorno:
        Dicionário com chaves ``id``, ``nome``, ``preco``,
        ``estoque``.

    Levanta:
        KeyError: quando nenhum produto possui o ``id``
        informado.
    """
    for produto in PRODUTOS_DEMO:
        if produto["id"] == produto_id:
            return produto
    raise KeyError(
        f"Produto com id={produto_id} não encontrado no catálogo."
    )
