from playwright.sync_api import sync_playwright
import time
import random

def buscar_webmotors_stealth():
    with sync_playwright() as p:
        # Lança o Chrome real com o modo 'Stealth' manual (User Agent limpo)
        browser = p.chromium.launch(headless=False, channel="chrome")

        # Simula uma tela de resolução comum de monitor
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )

        page = context.new_page()
        url = "https://www.webmotors.com.br/motos/estoque/sp/sao-paulo"

        print(f"🕵️ Modo Stealth: Acessando Webmotors...")

        try:
            page.goto(url, wait_until="domcontentloaded")

            # Movimento Humano: Scrolling aleatório
            for _ in range(3):
                page.mouse.wheel(0, random.randint(300, 700))
                time.sleep(random.uniform(1, 3))

            # Captura para conferir se passou pela segurança
            page.screenshot(path="webmotors_stealth.png")
            print("📸 Verifique o arquivo 'webmotors_stealth.png' para ver se os anúncios carregaram.")

        except Exception as e:
            print(f"❌ Bloqueado pela Webmotors: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    buscar_webmotors_stealth()