"""
Router do endpoint de health-check.

Objetivo: expor ``GET /api/health`` para verificação de
disponibilidade da aplicação.

Posição na arquitetura: router público (sem autenticação),
consumido por orquestradores externos (Docker healthcheck,
ferramentas de monitoramento, smoke-tests E2E).

Conceitos didáticos abordados: endpoints públicos, padrão de
liveness probe.

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
from datetime import datetime, timezone

# 2) Imports de bibliotecas de terceiros
from fastapi import APIRouter

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
from ecommerce.config import settings
from ecommerce.schemas import HealthOut


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    """
    Retorna o status de saúde da aplicação.

    Retorno:
        ``HealthOut`` com status fixo ``"ok"``, versão da
        aplicação e timestamp UTC atual.
    """
    return HealthOut(
        status="ok",
        versao=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc),
    )
