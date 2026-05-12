"""
Router do catálogo de produtos.

Objetivo: expor ``GET /api/produtos`` (lista completa) e
``GET /api/produtos/{produto_id}`` (consulta por id) a partir
da fonte estática ``ecommerce.produtos.PRODUTOS_DEMO``.

Posição na arquitetura: router público (sem autenticação),
consumido pela UI Jinja2, por clientes externos (Postman,
testes) e como pré-condição para adicionar itens ao carrinho.

Conceitos didáticos abordados: separação dados/apresentação,
serialização via DTO Pydantic, tratamento padronizado de
``KeyError`` → HTTP 404.

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
from typing import List

# 2) Imports de bibliotecas de terceiros
from fastapi import APIRouter, HTTPException, status

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
from ecommerce.produtos import PRODUTOS_DEMO, buscar_produto_por_id
from ecommerce.schemas import ProdutoOut


router = APIRouter(prefix="/api", tags=["produtos"])


@router.get("/produtos", response_model=List[ProdutoOut])
def listar_produtos() -> List[ProdutoOut]:
    """
    Retorna a lista completa de produtos do catálogo.

    Retorno:
        Lista de ``ProdutoOut``.
    """
    return [ProdutoOut(**produto) for produto in PRODUTOS_DEMO]


@router.get("/produtos/{produto_id}", response_model=ProdutoOut)
def obter_produto(produto_id: int) -> ProdutoOut:
    """
    Retorna o produto identificado por ``produto_id``.

    Parâmetros:
        produto_id: identificador inteiro do produto.

    Retorno:
        ``ProdutoOut`` correspondente ao identificador.

    Levanta:
        HTTPException(404): produto não encontrado.
    """
    try:
        produto = buscar_produto_por_id(produto_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="produto não encontrado",
        )
    return ProdutoOut(**produto)
