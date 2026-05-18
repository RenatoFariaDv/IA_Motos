import json
import os
import time
from playwright.sync_api import sync_playwright

def inspecionar_webmotors():
    """Script simples para inspecionar a estrutura do Webmotors"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )

        page = context.new_page()
        page.set_default_timeout(30000)

        # Vamos tentar diferentes URLs
        urls = [
            "https://www.webmotors.com.br/motos/sp-sao-paulo",
            "https://www.webmotors.com.br/motos/estoque/sp/sao-paulo",
            "https://www.webmotors.com.br/motos"
        ]

        for url in urls:
            print(f"🔗 Testando URL: {url}")

            try:
                page.goto(url, wait_until="load")
                time.sleep(5)

                # Carrega anúncios
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

                # Verifica se há anúncios
                all_links = page.query_selector_all('a')
                moto_links = page.query_selector_all('a[href*="moto"]')

                print(f"   📊 Total de links na página: {len(all_links)}")
                print(f"   🏍️  Links com 'moto': {len(moto_links)}")

                if len(moto_links) > 0:
                    print("   ✅ ENCONTROU LINKS DE MOTOS!")
                    for i, link in enumerate(moto_links[:5]):
                        try:
                            href = link.get_attribute('href')
                            text = link.inner_text().strip()[:50]
                            print(f"      {i+1}. {text} -> {href}")
                        except:
                            pass
                    break
                else:
                    print("   ❌ Nenhum link de moto encontrado")

            except Exception as e:
                print(f"   ❌ Erro: {e}")

            print()

        # Análise final
        print("🔍 ANÁLISE FINAL:")
        print("=" * 50)

        # Busca por qualquer elemento que possa conter anúncios
        possible_selectors = [
            'article',
            '.card',
            '[class*="item"]',
            '[class*="vehicle"]',
            '[data-type="vehicle"]',
            '.result',
            '.listing'
        ]

        for selector in possible_selectors:
            elements = page.query_selector_all(selector)
            if len(elements) > 0:
                print(f"✅ {selector}: {len(elements)} elementos")
                # Mostra preview do primeiro
                try:
                    preview = elements[0].inner_html()[:200]
                    print(f"   📄 Preview: {preview}...")
                except:
                    pass
            else:
                print(f"❌ {selector}: 0 elementos")

        # Salva screenshot e HTML
        page.screenshot(path="inspecao_webmotors.png")
        html = page.content()
        with open("inspecao_webmotors.html", "w", encoding="utf-8") as f:
            f.write(html)

        print("\n📸 Screenshot salvo: inspecao_webmotors.png")
        print("💾 HTML salvo: inspecao_webmotors.html")
        print("📋 Analise estes arquivos para entender a estrutura!")

        browser.close()

if __name__ == "__main__":
    print("🔍 INSPEÇÃO DO WEBMOTORS\n")
    inspecionar_webmotors()