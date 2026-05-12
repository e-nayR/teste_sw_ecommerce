"""
Menu interativo do projeto P0912_ECOMMERCE.

Ponto de entrada para o aluno: ``python menu.py`` na raiz do
repositório oferece acesso às operações comuns do ciclo de
desenvolvimento — subir a API, popular o banco demo, aplicar e
reverter migrations, verificar a configuração carregada do
``.env``.

Posição na arquitetura: script standalone (não pertence ao
pacote ``ecommerce``); imports da aplicação são feitos
preguiçosamente dentro das funções de cada opção, para que o
gate de versão e a tela de menu funcionem mesmo em casos de
``.env`` ausente ou inválido.

Convenções:
- PT-BR puro, sem internacionalização.
- Sem ``argparse`` / sem flags CLI. Apenas o loop interativo.
- Gate de versão: o programa encerra se a versão de Python
  não estiver no intervalo suportado (3.11.x a 3.14.x).

Disciplinas: Teste de Software · Gerência de Configuração e Dependência
Projeto: P0912_ECOMMERCE
"""

# 1) Imports da biblioteca padrão
import platform
import signal
import subprocess
import sys

# 2) Imports de bibliotecas de terceiros
# (nenhum — imports da aplicação são feitos preguiçosamente)

# 3) Filtros de warnings — antes dos imports locais (P9)
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 4) Imports locais
# (nenhum aqui — feitos lazy nas funções)


_VERSAO_PYTHON_MIN = (3, 11)
_VERSAO_PYTHON_MAX = (3, 14)


# ──────────────────────────────────────────────────────────────
# Gate de versão e helpers de UI
# ──────────────────────────────────────────────────────────────


def _verificar_versao_python() -> None:
    """
    Encerra com mensagem clara se a versão de Python estiver
    fora do intervalo suportado pelo projeto (3.11.x a 3.14.x).

    Justificativa do intervalo: o código foi originalmente
    desenvolvido em Python 3.11 e validado em 3.12; a partir
    de 3.13 a depreciação de ``datetime.utcnow`` ficou mais
    agressiva (já corrigido no projeto via
    ``datetime.now(timezone.utc)``), e em 3.14 algumas wheels
    de bibliotecas com C-extensions (``bcrypt``, ``cryptography``)
    podem demandar regeneração local do lock file.
    """
    atual = sys.version_info[:2]
    if not (_VERSAO_PYTHON_MIN <= atual <= _VERSAO_PYTHON_MAX):
        major, minor = atual
        min_major, min_minor = _VERSAO_PYTHON_MIN
        max_major, max_minor = _VERSAO_PYTHON_MAX
        print(
            f"ERRO: versão de Python incompatível ({major}.{minor}). "
            f"Este projeto suporta Python {min_major}.{min_minor} "
            f"até {max_major}.{max_minor}.",
            file=sys.stderr,
        )
        print(
            "Sugestão: instale via pyenv, asdf ou o instalador "
            "oficial em https://www.python.org/downloads/.",
            file=sys.stderr,
        )
        sys.exit(1)


def _exibir_menu() -> None:
    """Imprime o menu numerado padrão."""
    print()
    print("=" * 56)
    print(" P0912 ECOMMERCE — Menu interativo")
    print("=" * 56)
    print(" 1) Subir API (uvicorn)")
    print(" 2) Popular banco demo (seed)")
    print(" 3) Aplicar migrations (alembic upgrade head)")
    print(" 4) Reverter migrations (alembic downgrade base)")
    print(" 5) Verificar configuração (.env carregado)")
    print(" 0) Sair")
    print(" 6) Sair")
    print("=" * 56)


# ──────────────────────────────────────────────────────────────
# Implementação das opções
# ──────────────────────────────────────────────────────────────


def _opcao_subir_api() -> None:
    """
    Sobe ``uvicorn`` como subprocess e fica em primeiro plano até
    o usuário pressionar Ctrl+C, momento em que envia o sinal de
    término ao subprocess e aguarda seu encerramento.

    Em Windows, usa ``CREATE_NEW_PROCESS_GROUP`` + ``CTRL_BREAK_EVENT``.
    Em POSIX, usa ``SIGTERM`` direto.
    """
    from ecommerce.config import settings

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "ecommerce.api:criar_app",
        "--factory",
        "--host",
        settings.APP_HOST,
        "--port",
        str(settings.APP_PORT),
    ]

    print(
        f"Iniciando uvicorn em "
        f"http://{settings.APP_HOST}:{settings.APP_PORT}/"
    )
    print("Pressione Ctrl+C para parar.")

    popen_kwargs = {}
    is_windows = platform.system() == "Windows"
    if is_windows:
        # Permite enviar CTRL_BREAK_EVENT sem afetar este processo.
        popen_kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP
        )

    proc = subprocess.Popen(cmd, **popen_kwargs)
    try:
        proc.wait()
    except KeyboardInterrupt:
        print()
        print("Encerrando uvicorn...")
        if is_windows:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        print("uvicorn encerrado.")


def _opcao_seed() -> None:
    """Popula o banco com dados demo (idempotente)."""
    from ecommerce.seed import main as seed_main

    seed_main()


def _opcao_alembic_upgrade() -> None:
    """Roda ``alembic upgrade head`` como subprocess."""
    cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
    rc = subprocess.run(cmd, check=False).returncode
    if rc != 0:
        print(f"alembic upgrade falhou (exit code {rc}).")


def _opcao_alembic_downgrade() -> None:
    """
    Roda ``alembic downgrade base`` como subprocess, com confirmação.

    Apaga TODAS as tabelas. Solicita digitação literal de ``sim``.
    """
    print(
        "ATENÇÃO: 'downgrade base' apaga TODAS as tabelas do banco."
    )
    try:
        resposta = input("Confirma? digite 'sim' para continuar: ")
    except (KeyboardInterrupt, EOFError):
        print()
        print("Operação cancelada.")
        return
    if resposta.strip().lower() != "sim":
        print("Operação cancelada.")
        return
    cmd = [sys.executable, "-m", "alembic", "downgrade", "base"]
    rc = subprocess.run(cmd, check=False).returncode
    if rc != 0:
        print(f"alembic downgrade falhou (exit code {rc}).")


def _opcao_verificar_config() -> None:
    """
    Imprime o conteúdo carregado de ``settings``.

    O ``JWT_SECRET`` é apresentado de forma mascarada (apenas
    indica se está configurado) — nunca em texto puro.
    """
    from ecommerce.config import settings

    secret_value = settings.JWT_SECRET.get_secret_value()
    secret_status = (
        "***** (configurado)" if secret_value else "(VAZIO!)"
    )

    print()
    print("Configuração carregada (.env):")
    print(f"  APP_VERSION                = {settings.APP_VERSION}")
    print(f"  APP_HOST                   = {settings.APP_HOST}")
    print(f"  APP_PORT                   = {settings.APP_PORT}")
    print(f"  DEBUG                      = {settings.DEBUG}")
    print(f"  LOG_LEVEL                  = {settings.LOG_LEVEL}")
    print(f"  LOG_FORMAT                 = {settings.LOG_FORMAT}")
    print(
        f"  PROJECT_ROOT               = "
        f"{settings.PROJECT_ROOT or '(usando BASE_DIR)'}"
    )
    print(f"  DATABASE_URL               = {settings.DATABASE_URL}")
    print(f"  JWT_ALGORITHM              = {settings.JWT_ALGORITHM}")
    print(
        f"  JWT_EXPIRATION_MINUTES     = "
        f"{settings.JWT_EXPIRATION_MINUTES}"
    )
    print(f"  JWT_SECRET                 = {secret_status}")
    print(
        f"  GATEWAY_DELAY_SECONDS      = "
        f"{settings.GATEWAY_DELAY_SECONDS}"
    )
    print(
        f"  GATEWAY_FORCAR_FALHA       = "
        f"{settings.GATEWAY_FORCAR_FALHA}"
    )
    print(f"  CORS_ORIGINS               = {settings.CORS_ORIGINS}")
    print(
        f"  RATE_LIMIT_ENABLED         = "
        f"{settings.RATE_LIMIT_ENABLED}"
    )
    print(
        f"  PEDIDOS_CONSULTA_GLOBAL    = "
        f"{settings.PEDIDOS_CONSULTA_GLOBAL}"
    )
    print(
        f"  PEDIDOS_RESPOSTA_DETALHADA = "
        f"{settings.PEDIDOS_RESPOSTA_DETALHADA}"
    )
    print(f"  DEMO_USER_EMAIL            = {settings.DEMO_USER_EMAIL}")
    print(
        f"  DEMO_USER_2_EMAIL          = "
        f"{settings.DEMO_USER_2_EMAIL}"
    )


# ──────────────────────────────────────────────────────────────
# Loop principal
# ──────────────────────────────────────────────────────────────


def main() -> int:
    """Loop interativo do menu."""
    _verificar_versao_python()

    _opcoes = {
        "1": _opcao_subir_api,
        "2": _opcao_seed,
        "3": _opcao_alembic_upgrade,
        "4": _opcao_alembic_downgrade,
        "5": _opcao_verificar_config,
    }

    while True:
        _exibir_menu()
        try:
            escolha = input("Opção: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            print("Saindo.")
            return 0

        if escolha in ("0", "6"):
            print("Saindo.")
            return 0

        handler = _opcoes.get(escolha)
        if handler is None:
            print(f"Opção inválida: {escolha!r}. Tente novamente.")
            continue

        try:
            handler()
        except SystemExit:
            raise
        except Exception as exc:
            print(f"Erro durante a operação: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    sys.exit(main())
