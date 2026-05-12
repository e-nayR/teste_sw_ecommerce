"""
Router HTML (Jinja2) da UI ECOMMERCE.

Objetivo: oferecer o front-end mínimo da aplicação — listagem de
produtos, login com cookie HttpOnly, carrinho, checkout, histórico
de pedidos e telas de sucesso/erro.

Posição na arquitetura: roteador sem prefixo (``prefix=""``)
incluído pela factory ``ecommerce.api.criar_app()``. Reutiliza as
funções dos routers REST (``carrinho_router``, ``checkout_router``)
chamando-as como funções Python comuns — os ``Depends(...)`` são
defaults inertes quando a função é invocada fora do contexto
FastAPI.

Conceitos didáticos abordados: separação UI/API, formulários HTML
com método POST + redirect 303, herança de templates Jinja2,
estados visuais (loading/sucesso/erro/vazio).

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
from pathlib import Path
from typing import Optional

# 2) Imports de bibliotecas de terceiros
from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    Form,
    HTTPException,
    Request,
)
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
from ecommerce.auth import (
    criar_token,
    validar_token,
    verificar_senha,
)
from ecommerce.carrinho_persistencia import (
    listar_itens,
    montar_carrinho_de_compras,
    obter_ou_criar_carrinho_ativo,
)
from ecommerce.config import settings
from ecommerce.database import get_db
from ecommerce.models import Pedido, Usuario
from ecommerce.produtos import PRODUTOS_DEMO, buscar_produto_por_id
from ecommerce.routers.carrinho_router import (
    _montar_carrinho_out,
    adicionar_item_ao_carrinho,
    esvaziar_carrinho,
)
from ecommerce.routers.checkout_router import finalizar_checkout
from ecommerce.routers.pedidos_router import _montar_pedido_out
from ecommerce.schemas import AdicionarItemIn, CheckoutIn


# ──────────────────────────────────────────────────────────────
# Templates Jinja2 (singleton de módulo)
# ──────────────────────────────────────────────────────────────

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


router = APIRouter(prefix="", tags=["ui"])


# ──────────────────────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────────────────────


def _resolver_usuario(
    access_token: Optional[str], db: Session
) -> Optional[Usuario]:
    """
    Resolve o usuário do cookie sem levantar 401.

    Retorna ``None`` se o cookie estiver ausente, expirado ou
    inválido — a UI então redireciona para ``/login``.
    """
    if not access_token:
        return None
    try:
        user_id = validar_token(access_token)
    except HTTPException:
        return None
    return db.get(Usuario, user_id)


def _redirect(url: str) -> RedirectResponse:
    """RedirectResponse com status 303 (See Other)."""
    return RedirectResponse(url=url, status_code=303)


def _ctx_base(usuario: Optional[Usuario]) -> dict:
    """Contexto comum para todos os templates."""
    return {
        "usuario": usuario,
        "app_name": "P0912 ECOMMERCE",
        "app_version": settings.APP_VERSION,
    }


# ──────────────────────────────────────────────────────────────
# Páginas públicas
# ──────────────────────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse)
def pagina_inicial(
    request: Request,
    erro: Optional[str] = None,
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """
    Página inicial — catálogo de produtos.

    Retorna a listagem completa de ``PRODUTOS_DEMO``. A página é
    pública (não requer autenticação), mas mostra o nome do
    usuário no header quando há cookie válido.
    """
    usuario = _resolver_usuario(access_token, db)
    contexto = {
        **_ctx_base(usuario),
        "request": request,
        "produtos": PRODUTOS_DEMO,
        "erro": erro,
    }
    return templates.TemplateResponse(request, "index.html", contexto)


@router.get("/login", response_class=HTMLResponse)
def get_login(
    request: Request,
    erro: Optional[str] = None,
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """
    Formulário de login.

    Se o usuário já estiver autenticado, redireciona para a
    página inicial.
    """
    usuario = _resolver_usuario(access_token, db)
    if usuario is not None:
        return _redirect("/")
    contexto = {
        **_ctx_base(None),
        "request": request,
        "erro": erro,
    }
    return templates.TemplateResponse(request, "login.html", contexto)


@router.post("/login")
def post_login(
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
) -> Response:
    """
    Processa o formulário de login.

    Em sucesso, define o cookie ``access_token`` e redireciona
    para ``/``. Em falha, redireciona para ``/login`` com
    ``?erro=credenciais_invalidas``.
    """
    stmt = select(Usuario).where(Usuario.email == email)
    usuario = db.execute(stmt).scalar_one_or_none()
    if usuario is None or not verificar_senha(senha, usuario.senha_hash):
        return _redirect("/login?erro=credenciais_invalidas")

    token = criar_token(usuario.id)
    response = _redirect("/")
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=settings.JWT_EXPIRATION_MINUTES * 60,
        httponly=True,
        samesite="lax",
        path="/",
        secure=False,
    )
    return response


@router.post("/logout")
def post_logout() -> Response:
    """Remove o cookie e redireciona para a página inicial."""
    response = _redirect("/")
    response.delete_cookie(key="access_token", path="/")
    return response


# ──────────────────────────────────────────────────────────────
# Páginas protegidas — exigem autenticação
# ──────────────────────────────────────────────────────────────


@router.get("/carrinho", response_class=HTMLResponse)
def pagina_carrinho(
    request: Request,
    erro: Optional[str] = None,
    desconto: float = 0.0,
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """
    Carrinho ativo do usuário, com preview opcional de desconto.

    O parâmetro ``desconto`` (query string) recalcula o total no
    momento da renderização — o desconto NÃO é persistido. Só é
    aplicado de fato no checkout.
    """
    usuario = _resolver_usuario(access_token, db)
    if usuario is None:
        return _redirect("/login?erro=autenticacao_requerida")

    carrinho_orm = obter_ou_criar_carrinho_ativo(db, usuario.id)
    carrinho_out = _montar_carrinho_out(db, carrinho_orm.id)

    # Preview de desconto: usa o domínio diretamente.
    carrinho_dominio = montar_carrinho_de_compras(db, carrinho_orm.id)
    total_sem = carrinho_dominio.calcular_total()
    total_com = carrinho_dominio.calcular_total(desconto)
    valor_desconto = total_sem - total_com

    contexto = {
        **_ctx_base(usuario),
        "request": request,
        "carrinho": carrinho_out,
        "total_sem_desconto": total_sem,
        "desconto_percentual": desconto,
        "valor_desconto": valor_desconto,
        "total_com_desconto": total_com,
        "erro": erro,
    }
    return templates.TemplateResponse(request, "carrinho.html", contexto)


@router.post("/carrinho/itens")
def post_adicionar_item(
    produto_id: int = Form(...),
    quantidade: int = Form(default=1),
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """
    Adiciona um item ao carrinho ativo via formulário HTML.
    """
    usuario = _resolver_usuario(access_token, db)
    if usuario is None:
        return _redirect("/login?erro=autenticacao_requerida")

    try:
        payload = AdicionarItemIn(
            produto_id=produto_id, quantidade=quantidade
        )
    except Exception:
        return _redirect("/?erro=quantidade_invalida")

    try:
        adicionar_item_ao_carrinho(payload, usuario=usuario, db=db)
    except HTTPException as exc:
        if exc.status_code == 404:
            return _redirect("/?erro=produto_nao_encontrado")
        return _redirect("/?erro=falha_ao_adicionar")
    return _redirect("/carrinho")


@router.post("/carrinho/limpar")
def post_limpar_carrinho(
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """Remove todos os itens do carrinho ativo."""
    usuario = _resolver_usuario(access_token, db)
    if usuario is None:
        return _redirect("/login?erro=autenticacao_requerida")
    esvaziar_carrinho(usuario=usuario, db=db)
    return _redirect("/carrinho")


@router.get("/checkout", response_class=HTMLResponse)
def pagina_checkout(
    request: Request,
    erro: Optional[str] = None,
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """Formulário de finalização de compra."""
    usuario = _resolver_usuario(access_token, db)
    if usuario is None:
        return _redirect("/login?erro=autenticacao_requerida")

    carrinho_orm = obter_ou_criar_carrinho_ativo(db, usuario.id)
    carrinho_out = _montar_carrinho_out(db, carrinho_orm.id)

    contexto = {
        **_ctx_base(usuario),
        "request": request,
        "carrinho": carrinho_out,
        "erro": erro,
    }
    return templates.TemplateResponse(request, "checkout.html", contexto)


@router.post("/checkout")
def post_checkout(
    cartao: str = Form(...),
    desconto_percentual: float = Form(default=0.0),
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """
    Processa o formulário de checkout.

    Em sucesso, redireciona para ``/sucesso?pedido_id=X``. Em
    falha, redireciona para ``/checkout?erro=...``.
    """
    usuario = _resolver_usuario(access_token, db)
    if usuario is None:
        return _redirect("/login?erro=autenticacao_requerida")

    try:
        payload = CheckoutIn(
            cartao=cartao, desconto_percentual=desconto_percentual
        )
    except Exception:
        return _redirect("/checkout?erro=dados_invalidos")

    try:
        resultado = finalizar_checkout(
            payload, usuario=usuario, db=db
        )
    except HTTPException as exc:
        if exc.status_code == 400:
            return _redirect("/checkout?erro=carrinho_vazio")
        if exc.status_code == 402:
            return _redirect("/erro?msg=pagamento_recusado")
        return _redirect("/erro?msg=falha_no_checkout")

    return _redirect(f"/sucesso?pedido_id={resultado.pedido_id}")


@router.get("/pedidos", response_class=HTMLResponse)
def pagina_pedidos(
    request: Request,
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """Histórico de pedidos do usuário autenticado."""
    usuario = _resolver_usuario(access_token, db)
    if usuario is None:
        return _redirect("/login?erro=autenticacao_requerida")

    stmt = (
        select(Pedido)
        .where(Pedido.usuario_id == usuario.id)
        .order_by(Pedido.id.desc())
    )
    pedidos_orm = list(db.execute(stmt).scalars().all())
    pedidos = [_montar_pedido_out(p) for p in pedidos_orm]

    contexto = {
        **_ctx_base(usuario),
        "request": request,
        "pedidos": pedidos,
    }
    return templates.TemplateResponse(request, "pedidos.html", contexto)


@router.get("/sucesso", response_class=HTMLResponse)
def pagina_sucesso(
    request: Request,
    pedido_id: Optional[int] = None,
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """Tela de confirmação de pedido aprovado."""
    usuario = _resolver_usuario(access_token, db)
    contexto = {
        **_ctx_base(usuario),
        "request": request,
        "pedido_id": pedido_id,
    }
    return templates.TemplateResponse(request, "sucesso.html", contexto)


@router.get("/erro", response_class=HTMLResponse)
def pagina_erro(
    request: Request,
    msg: Optional[str] = None,
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """Tela de erro genérica."""
    usuario = _resolver_usuario(access_token, db)
    contexto = {
        **_ctx_base(usuario),
        "request": request,
        "msg": msg or "ocorreu um erro inesperado",
    }
    return templates.TemplateResponse(request, "erro.html", contexto)
