import asyncio
import sys

async def main():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright não está instalado. Instale com: pip install playwright")
        sys.exit(1)

    stealth = None
    try:
        from playwright_stealth import stealth_async
        stealth = stealth_async
    except ImportError:
        stealth = None

    user_data_dir = "ml_profile_stealth"
    url = "https://www.mercadolivre.com.br"

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        if stealth:
            await stealth(page)
        await page.goto(url)
        print("Faça login manualmente no navegador aberto.")
        print("Quando terminar, pressione Enter aqui no terminal para fechar o navegador.")
        input()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())