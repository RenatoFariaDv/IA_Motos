import os
import time
import random
import shutil
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import re

def clean_chrome_profile():
    """Remove perfil corrompido"""
    try:
        if os.path.exists("chrome_profile"):
            # Tenta forçar remover
            for root, dirs, files in os.walk("chrome_profile", topdown=False):
                for f in files:
                    try:
                        os.remove(os.path.join(root, f))
                    except:
                        pass
            shutil.rmtree("chrome_profile", ignore_errors=True)
        print("Chrome profile limpo\n")
    except:
        pass

def debug_cards_simples():
    """Debug sem persistent context"""
    
    clean_chrome_profile()
    
    with sync_playwright() as p:
        print("Iniciando navegador simples...")
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

        URL = "https://www.webmotors.com.br/motos/estoque/sp/sao-paulo?idsuportevenda=online"
        print(f"Acessando: {URL}\n")

        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            print("Pagina carregou. Aguarde se houver CAPTCHA e pressione ENTER...")
            input()
            
            # Após resolver CAPTCHA, aguarda os cards aparecerem
            print("Aguardando cards aparecerem...")
            try:
                page.wait_for_selector("div.CardVehicle", timeout=30000)
                print("✅ Cards detectados!")
            except Exception as e:
                print(f"⚠️ Timeout aguardando CardVehicle: {e}")
                print("Continuando mesmo assim...")
            
            time.sleep(2)
            
            # Scroll para carregar mais
            print("Fazendo scroll...")
            for i in range(3):
                page.evaluate("window.scrollBy(0, 500)")
                time.sleep(1)

            content = page.content()
            
            # Salva HTML
            with open("debug_full_cards.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("\nHTML completo salvo: debug_full_cards.html")

            # Teste seletores
            print("\nTestando seletores:")
            selectors = [
                "div.CardVehicle",
                "[class*='CardVehicle']",
                "[class*='card']",
                "[class*='Card']",
                "article",
                "li",
            ]

            for selector in selectors:
                count = page.locator(selector).count()
                print(f"  {selector}: {count}")

            # Se encontrou CardVehicle
            if page.locator("div.CardVehicle").count() > 0:
                print("\n" + "="*80)
                print("ENCONTROU div.CardVehicle!")
                print("="*80)
                
                card = page.locator("div.CardVehicle").nth(0)
                html = card.inner_html()
                
                print("\nPRIMEIRO CARD HTML (primeiros 1500 chars):")
                print(html[:1500])
                print("..." if len(html) > 1500 else "")
                
                # Extrai dados
                text = card.inner_text()
                print(f"\nTEXTO DO CARD:\n{text}\n")
                
                # Links
                links = card.locator("a").all()
                print(f"LINKS: {len(links)} encontrados")
                for idx, link in enumerate(links[:3]):
                    href = link.get_attribute("href")
                    txt = link.inner_text()[:50]
                    print(f"  [{idx}] {txt} -> {href}")
                
                # Imagens
                imgs = card.locator("img").all()
                print(f"\nIMAGENS: {len(imgs)} encontradas")
                for idx, img in enumerate(imgs[:2]):
                    src = img.get_attribute("src") or img.get_attribute("data-src")
                    alt = img.get_attribute("alt")
                    print(f"  [{idx}] alt='{alt}' src='{src[:80] if src else 'None'}'")
                
                # Precos
                if "R$" in text:
                    prices = re.findall(r'R\$[\s\d.,]+', text)
                    print(f"\nPRECOS: {prices[:3]}")
                else:
                    print(f"\nPRECOS: Nenhum encontrado")
            else:
                print("\n" + "="*80)
                print("NÃO encontrou div.CardVehicle")
                print("="*80)
                
                # Se tem R$, mostra onde
                if "R$" in content:
                    print("\nMas a página TEM 'R$' no conteúdo!")
                    prices = re.findall(r'R\$[\s\d.,]+', content)
                    print(f"Encontrados {len(prices)} preços")
                    print(f"Exemplos: {prices[:5]}")
                else:
                    print("\nA página não tem nenhum 'R$'")
                    print("Provavelmente ainda está com bloqueio ou captcha")

        except Exception as e:
            print(f"Erro: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()
            print("\nDebug concluído")

if __name__ == "__main__":
    debug_cards_simples()
