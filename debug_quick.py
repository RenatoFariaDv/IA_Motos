import os
import time
import random
import shutil
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

def quick_debug():
    """Quick debug sem persistent context"""
    
    # Remove perfil corrompido se existir
    if os.path.exists("chrome_profile"):
        shutil.rmtree("chrome_profile")
        print("🧹 Perfil anterior removido\n")

    with sync_playwright() as p:
        print("🚀 Iniciando navegador...")
        browser = p.chromium.launch(
            headless=False,
            channel="chrome",
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
            ]
        )

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        
        page = context.new_page()
        Stealth().apply_stealth_sync(page)

        url = "https://www.webmotors.com.br/motos/estoque/sp/sao-paulo?idsuportevenda=online"
        print(f"🔗 Acessando: {url}\n")

        try:
            print("⏳ Carregando página...")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            print("⏳ Aguardando renderização...")
            time.sleep(3)
            
            print("📜 Scroll para carregar conteúdo...")
            for i in range(3):
                page.evaluate("window.scrollBy(0, 500)")
                time.sleep(1)
                print(f"  Scroll {i+1}/3")

            # Salva screenshot
            page.screenshot(path="debug_quick.png")
            print("\n📸 Screenshot salvo: debug_quick.png\n")

            # Salva HTML
            html = page.content()
            with open("debug_quick.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("💾 HTML salvo: debug_quick.html\n")

            # Procura por seletores
            print("🔍 Procurando seletores...\n")
            
            test_selectors = [
                'div.CardVehicle',
                '[class*="card"]',
                'article',
                'li',
                'div[data-testid]',
                '[data-qa]',
                'div[class*="vehicle" i]',
                'div[class*="anuncio" i]',
            ]

            for selector in test_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if len(elements) > 0:
                        print(f"✅ {selector}: {len(elements)} encontrados")
                except:
                    print(f"❌ {selector}: erro ao procurar")

            # Análise básica do HTML
            print("\n📊 Análise do DOM:")
            
            body_html = page.query_selector("body").inner_html()[:500]
            print(f"\nPrimeiros 500 caracteres do body:")
            print(body_html[:200] + "...")
            
            # Procura por padrões de preço
            if "R$" in page.content():
                print("\n✅ Página contém 'R$'")
            else:
                print("\n❌ Página não contém 'R$'")
                
            # Procura por elemento específico
            if page.query_selector(".CardVehicle"):
                print("✅ Encontrou .CardVehicle")
            else:
                print("❌ Não encontrou .CardVehicle")
                
            print("\n✅ Debug concluído. Verifique os arquivos gerados.")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    quick_debug()
