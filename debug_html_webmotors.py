import os
import time
import random
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from teste_webmotors_stealth import stealth_mode, comportamento_ultra_humano

USER_DATA_DIR = "chrome_profile"

def debug_webmotors():
    """Debug script para analisar estrutura HTML do WebMotors"""
    
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

        context.set_default_timeout(90000)
        page = context.pages[0] if context.pages else context.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        Stealth().apply_stealth_sync(page)
        stealth_mode(page)

        url = "https://www.webmotors.com.br/motos/estoque/sp/sao-paulo?idsuportevenda=online"
        print(f"🔗 Acessando: {url}\n")

        try:
            page.goto(url, wait_until="networkidle", timeout=120000)
            time.sleep(random.uniform(4, 7))
            comportamento_ultra_humano(page)

            # Scroll para carregar mais anúncios
            print("📜 Carregando anúncios com scroll...")
            for i in range(5):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(random.uniform(1.5, 3.5))
                print(f"  Scroll {i+1}/5")

            # Screenshot
            page.screenshot(path="debug_webmotors_html.png")
            print("📸 Screenshot salvo: debug_webmotors_html.png")

            # Salva HTML completo
            html = page.content()
            with open("debug_webmotors_html.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("💾 HTML completo salvo: debug_webmotors_html.html")

            # Análise de seletores
            print("\n🔍 Analisando seletores disponíveis...\n")

            seletores_test = [
                ('div[class*="card"]', 'divs com "card" na classe'),
                ('div[class*="Card"]', 'divs com "Card" na classe'),
                ('article', 'artigos genéricos'),
                ('li', 'itens de lista'),
                ('div[data-testid]', 'divs com data-testid'),
                ('[class*="vehicle"]', 'elementos com "vehicle"'),
                ('[class*="Vehicle"]', 'elementos com "Vehicle"'),
                ('[class*="anuncio"]', 'elementos com "anuncio"'),
                ('[class*="Anuncio"]', 'elementos com "Anuncio"'),
                ('div.CardVehicle', 'div.CardVehicle específico'),
                ('[data-qa]', 'elementos com data-qa'),
                ('div[class]', 'divs com qualquer classe (primeiros 20)'),
            ]

            for selector, descricao in seletores_test:
                try:
                    elements = page.query_selector_all(selector)
                    count = len(elements)
                    if count > 0:
                        print(f"✅ {descricao}")
                        print(f"   Seletor: {selector}")
                        print(f"   Encontrados: {count}")
                        
                        # Mostra primeiros 3 elementos
                        if count > 0:
                            for idx in range(min(3, count)):
                                try:
                                    text = elements[idx].text_content()[:100]
                                    print(f"     [{idx}] {text}...")
                                except:
                                    pass
                        print()
                except Exception as e:
                    pass

            # Análise do DOM
            print("\n📊 Análise do DOM...\n")
            
            body_classes = page.evaluate("() => document.body.className")
            print(f"Classes do body: {body_classes}\n")

            div_count = len(page.query_selector_all("div"))
            span_count = len(page.query_selector_all("span"))
            article_count = len(page.query_selector_all("article"))
            section_count = len(page.query_selector_all("section"))
            
            print(f"Total de divs: {div_count}")
            print(f"Total de spans: {span_count}")
            print(f"Total de articles: {article_count}")
            print(f"Total de sections: {section_count}\n")

            # Procura por texto de preço
            print("🔎 Procurando por texto de preço...\n")
            has_price = page.evaluate("""() => {
                const bodyText = document.body.innerText;
                return bodyText.includes('R$') || bodyText.includes('Consultar');
            }""")
            print(f"Página contém texto de preço: {has_price}\n")

            # Lista as classes mais comuns em divs
            print("📋 Classes mais comuns em divs:\n")
            top_classes = page.evaluate("""() => {
                const divs = document.querySelectorAll('div[class]');
                const classes = {};
                divs.forEach(div => {
                    const classList = div.className.split(' ').filter(c => c.length > 0);
                    classList.forEach(cls => {
                        classes[cls] = (classes[cls] || 0) + 1;
                    });
                });
                
                return Object.entries(classes)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 30)
                    .map(([cls, count]) => ({ class: cls, count }));
            }""")
            
            for item in top_classes:
                print(f"  .{item['class']}: {item['count']}")

            input("\n✋ Pressione ENTER para fechar o navegador...")
            context.close()

        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_webmotors()
