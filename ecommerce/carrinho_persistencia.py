"""
Repositório de persistência do carrinho.

Objetivo: oferecer as funções de leitura/escrita do carrinho
ativo no banco e a função-ponte ``montar_carrinho_de_compras``,
que reconstrói o objeto de domínio (``CarrinhoDeCompras``) a
partir do estado persistido. Esta ponte garante que a lógica
exercitada pelos testes unitários é exatamente a que executa
em produção.

Posição na arquitetura: camada de persistência entre os
modelos ORM (``ecommerce.models``) e a lógica de domínio
(``ecommerce.carrinho``). Consumido pelos routers de carrinho
e checkout.

Conceitos didáticos abordados: padrão Repository, ponte
domínio/persistência, snapshot de preço, separação de
responsabilidades.

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
from typing import List

# 2) Imports de bibliotecas de terceiros
from sqlalchemy import select
from sqlalchemy.orm import Session

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
from ecommerce.carrinho import CarrinhoDeCompras, Produto
from ecommerce.models import Carrinho, ItemCarrinho
from ecommerce.produtos import buscar_produto_por_id


def obter_ou_criar_carrinho_ativo(
    db: Session, usuario_id: int
) -> Carrinho:
    """
    Retorna o carrinho ativo do usuário; cria um novo se não
    existir.

    Parâmetros:
        db: sessão SQLAlchemy.
        usuario_id: identificador do usuário dono do carrinho.

    Retorno:
        ``Carrinho`` ORM ativo, persistido.
    """
    stmt = select(Carrinho).where(
        Carrinho.usuario_id == usuario_id,
        Carrinho.ativo.is_(True),
    )
    carrinho = db.execute(stmt).scalar_one_or_none()
    if carrinho is None:
        carrinho = Carrinho(usuario_id=usuario_id, ativo=True)
        db.add(carrinho)
        db.commit()
        db.refresh(carrinho)
    return carrinho


def adicionar_item(
    db: Session,
    carrinho_id: int,
    produto_id: int,
    quantidade: int,
) -> ItemCarrinho:
    """
    Adiciona um item ao carrinho, capturando snapshot do preço.

    Parâmetros:
        db: sessão SQLAlchemy.
        carrinho_id: identificador do carrinho.
        produto_id: identificador do produto a adicionar.
        quantidade: número de unidades.

    Retorno:
        ``ItemCarrinho`` persistido.

    Levanta:
        KeyError: ``produto_id`` ausente do catálogo.
        ValueError: ``quantidade`` fora do intervalo permitido.
    """
    if quantidade < 1:
        raise ValueError("Quantidade deve ser maior ou igual a 1.")

    produto = buscar_produto_por_id(produto_id)
    item = ItemCarrinho(
        carrinho_id=carrinho_id,
        produto_id=produto_id,
        quantidade=quantidade,
        preco_unitario_snapshot=float(produto["preco"]),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def listar_itens(db: Session, carrinho_id: int) -> List[ItemCarrinho]:
    """Retorna a lista de itens do carrinho informado."""
    stmt = select(ItemCarrinho).where(
        ItemCarrinho.carrinho_id == carrinho_id
    )
    return list(db.execute(stmt).scalars().all())


def limpar_carrinho(db: Session, carrinho_id: int) -> None:
    """Remove todos os itens do carrinho informado."""
    for item in listar_itens(db, carrinho_id):
        db.delete(item)
    db.commit()


def montar_carrinho_de_compras(
    db: Session, carrinho_id: int
) -> CarrinhoDeCompras:
    """
    Reconstrói o objeto de domínio ``CarrinhoDeCompras`` a partir
    do estado persistido.

    Cada ``ItemCarrinho`` é expandido em ``quantidade`` unidades
    de ``Produto`` (nome do catálogo, preço-snapshot do banco) e
    adicionado ao carrinho de domínio. Esse contrato garante
    que ``calcular_total`` é executado contra o mesmo objeto
    exercitado pelos testes unitários.

    Parâmetros:
        db: sessão SQLAlchemy.
        carrinho_id: identificador do carrinho persistido.

    Retorno:
        Instância de ``CarrinhoDeCompras`` (do módulo de domínio)
        com os produtos expandidos.
    """
    carrinho = CarrinhoDeCompras()
    for item in listar_itens(db, carrinho_id):
        try:
            catalogo = buscar_produto_por_id(item.produto_id)
            nome = catalogo["nome"]
        except KeyError:
            nome = f"Produto #{item.produto_id}"
        for _ in range(item.quantidade):
            carrinho.adicionar_produto(
                Produto(nome=nome, preco=item.preco_unitario_snapshot)
            )
    return carrinho
