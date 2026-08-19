from typing import Any

from playwright.sync_api import (
    Browser,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


TEXTOS_ANUNCIO_REMOVIDO = (
    "a página não foi encontrada",
    "anúncio não encontrado",
    "este anúncio não está mais disponível",
    "não conseguimos localizar a página",
)


def pagina_indica_anuncio_removido(page: Page) -> bool:
    """
    Verifica se o conteúdo carregado indica que o anúncio foi removido.
    """
    try:
        titulo = page.title().casefold()
    except Exception:
        titulo = ""

    try:
        conteudo = page.locator("body").inner_text(
            timeout=5000,
        ).casefold()
    except Exception:
        conteudo = ""

    texto_completo = f"{titulo}\n{conteudo}"

    return any(
        texto in texto_completo
        for texto in TEXTOS_ANUNCIO_REMOVIDO
    )


def validar_link_olx(
    link: str,
    browser: Browser | None = None,
) -> dict[str, Any]:
    """
    Abre um anúncio da OLX em navegador real e retorna:

    {
        "link": "...",
        "status": "ATIVO" | "REMOVIDO" | "ERRO_VERIFICACAO",
        "url_final": "...",
        "erro": ""
    }
    """
    link = str(link).strip()

    resultado = {
        "link": link,
        "status": "ERRO_VERIFICACAO",
        "url_final": "",
        "erro": "",
    }

    if not link.startswith(("http://", "https://")):
        resultado["erro"] = "Link inválido."
        return resultado

    playwright_local = None
    navegador_local = None
    page = None

    try:
        if browser is None:
            playwright_local = sync_playwright().start()

            navegador_local = playwright_local.chromium.launch(
                headless=True,
            )

            browser = navegador_local

        contexto = browser.new_context(
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/150.0.0.0 Safari/537.36"
            ),
        )

        page = contexto.new_page()

        page.goto(
            link,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        page.wait_for_timeout(2500)

        resultado["url_final"] = page.url

        if pagina_indica_anuncio_removido(page):
            resultado["status"] = "REMOVIDO"
        else:
            resultado["status"] = "ATIVO"

        contexto.close()

    except PlaywrightTimeoutError:
        resultado["erro"] = "Tempo limite ao carregar o anúncio."

    except Exception as erro:
        resultado["erro"] = str(erro)

    finally:
        if page is not None:
            try:
                page.close()
            except Exception:
                pass

        if navegador_local is not None:
            try:
                navegador_local.close()
            except Exception:
                pass

        if playwright_local is not None:
            try:
                playwright_local.stop()
            except Exception:
                pass

    return resultado


if __name__ == "__main__":
    link_teste = input(
        "Cole o link da OLX para validar: "
    ).strip()

    validacao = validar_link_olx(link_teste)

    print("\nResultado:")
    print("Status:", validacao["status"])
    print("URL final:", validacao["url_final"])
    print("Erro:", validacao["erro"] or "Nenhum")