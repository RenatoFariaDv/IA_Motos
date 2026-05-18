import os
import time
import random
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv
from teste_webmotors_stealth import stealth_mode, comportamento_ultra_humano
import re

load_dotenv()

USER_DATA_DIR = "chrome_profile"
URL_WEBMOTORS = "https://www.webmotors.com.br/motos/estoque/sp/sao-paulo?idsuportevenda=online"

def debug_cards():
    """Debug detalhado da estrutura de cards"""
    
    profile_path = Path(USER_DATA_DIR).resolve()
    profile_path.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(profile_path),
            headless=False,
            channel="chrome",
            ignore_default_args=["--enable-automation"],
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor,IsolateOrigins,site-per-process',
                '--disable-ipc-flooding-protection',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--start-maximized',
            ]
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        Stealth().apply_stealth_sync(page)
        stealth_mode(page)

        print(f"Acessando: {URL_WEBMOTORS}\n")

        try:
            page.goto(URL_WEBMOTORS, wait_until="networkidle", timeout=120000)
            time.sleep(3)
            comportamento_ultra_humano(page)

            content = page.content()
            
            # Detecta CAPTCHA
            if "px-captcha" in content or "captcha" in content:
                print("CAPTCHA detectado. Resolva manualmente e pressione ENTER aqui...")
                input()
                
                # Aguarda cardVehicle aparecer
                print("Aguardando cards carregar...")
                try:
                    page.wait_for_selector("div.CardVehicle", timeout=300000)
                    print("Cards apareceram!")
                except:
                    print("Timeout aguardando cards")

            # Scroll para carregar mais
            for i in range(3):
                page.evaluate("window.scrollBy(0, 500)")
                time.sleep(1)

            content = page.content()
            
            # Salva HTML
            with open("debug_full_cards.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("\nHTML completo salvo: debug_full_cards.html")

            # Teste vários seletores
            print("\nTestando seletores:")
            selectors = [
                "div.CardVehicle",
                "[class*='card']",
                "[class*='Card']",
                "article",
                "li",
                "div[data-testid]",
            ]

            for selector in selectors:
                count = page.locator(selector).count()
                print(f"  {selector}: {count}")

            # Se encontrou cards, analisa o primeiro
            if page.locator("div.CardVehicle").count() > 0:
                card = page.locator("div.CardVehicle").nth(0)
                html = card.inner_html()
                
                print("\n" + "="*80)
                print("PRIMEIRO CARD HTML:")
                print("="*80)
                print(html[:2000])
                print("..."  if len(html) > 2000 else "")
                
                # Tenta extrair dados
                print("\n" + "="*80)
                print("DADOS EXTRAÍDOS:")
                print("="*80)
                
                text = card.inner_text()
                print(f"\nTEXTO:\n{text[:500]}\n")
                
                # Links
                links = card.locator("a").all()
                print(f"\nLINKS ENCONTRADOS: {len(links)}")
                for idx, link in enumerate(links[:3]):
                    href = link.get_attribute("href")
                    txt = link.inner_text()
                    print(f"  [{idx}] {txt[:50]} -> {href[:100]}")
                
                # Imagens
                imgs = card.locator("img").all()
                print(f"\nIMAGENS ENCONTRADAS: {len(imgs)}")
                for idx, img in enumerate(imgs[:3]):
                    src = img.get_attribute("src") or img.get_attribute("data-src")
                    alt = img.get_attribute("alt")
                    print(f"  [{idx}] alt={alt} src={src[:80] if src else 'None'}")
                
                # Preços (busca por R$)
                if "R$" in text:
                    matches = re.findall(r'R\$[\s\d.,]+', text)
                    print(f"\nPREÇOS ENCONTRADOS: {matches[:3]}")
                else:
                    print(f"\nPREÇOS: Nenhum 'R$' encontrado")

            print("\n" + "="*80)
            print("Debug concluído. Arquivos salvos:")
            print("  - debug_full_cards.html")
            
        except Exception as e:
            print(f"Erro: {e}")
            import traceback
            traceback.print_exc()
        finally:
            context.close()

if __name__ == "__main__":
    debug_cards()
