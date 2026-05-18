import json
import os
import time
from playwright.sync_api import sync_playwright

def analisar_webmotors_detalhado():
    """Análise detalhada da estrutura HTML do Webmotors"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale='pt-BR',
            timezone_id='America/Sao_Paulo'
        )

        page = context.new_page()
        page.set_default_timeout(60000)

        url = "https://www.webmotors.com.br/motos/sp-sao-paulo"
        print(f"🔬 ANÁLISE DETALHADA - Acessando: {url}\n")

        try:
            page.goto(url, wait_until="load")
            time.sleep(5)

            # Carrega anúncios
            print("📜 Carregando anúncios...")
            for i in range(8):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

            # Screenshot
            page.screenshot(path="analise_webmotors_detalhada.png")
            print("📸 Screenshot salvo: analise_webmotors_detalhada.png\n")

            # Análise de classes CSS mais comuns
            print("🔎 ANALISANDO CLASSES CSS MAIS COMUNS:\n")

            classes_count = page.evaluate("""
                const elements = document.querySelectorAll('*');
                const classMap = {};

                elements.forEach(el => {
                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.split(' ');
                        classes.forEach(cls => {
                            if (cls.length > 2) {  // Classes maiores que 2 caracteres
                                classMap[cls] = (classMap[cls] || 0) + 1;
                            }
                        });
                    }
                });

                // Retorna top 30 classes
                return Object.entries(classMap)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 30);
            """)

            for classe, count in classes_count:
                print(f"📊 {classe}: {count} elementos")

            print("\n" + "="*60 + "\n")

            # Busca por possíveis containers de anúncios
            print("🔍 BUSCANDO POSSÍVEIS CONTAINERS DE ANÚNCIOS:\n")

            container_selectors = [
                'main',
                '[role="main"]',
                '.container',
                '.content',
                '#content',
                '.main-content',
                '.results',
                '.search-results',
                '.listings',
                '.vehicles',
                '.motos',
                '[data-testid*="results"]',
                '[data-testid*="list"]',
                '[class*="result"]',
                '[class*="list"]',
                '[class*="vehicle"]',
                '[class*="moto"]'
            ]

            for selector in container_selectors:
                elements = page.query_selector_all(selector)
                if len(elements) > 0:
                    print(f"✅ {selector}: {len(elements)} containers")
                    if len(elements) <= 5:  # Mostra apenas se não for muito
                        for i, el in enumerate(elements):
                            try:
                                html_preview = el.inner_html()[:150].replace('\n', ' ')
                                print(f"   📄 Container {i+1}: {html_preview}...")
                            except:
                                print(f"   📄 Container {i+1}: [erro ao ler]")
                    print()

            print("="*60 + "\n")

            # Busca específica por links de motos
            print("🔗 BUSCANDO LINKS DE MOTOS:\n")

            moto_links = page.query_selector_all('a[href*="moto"]')
            print(f"🔗 Links com 'moto': {len(moto_links)}")

            for i, link in enumerate(moto_links[:10]):
                try:
                    href = link.get_attribute('href')
                    text = link.inner_text().strip()
                    print(f"   {i+1}. {text[:50]} -> {href}")
                except:
                    print(f"   {i+1}. [erro]")

            print()

            # Busca por data-testid attributes
            print("🎯 BUSCANDO DATA-TESTID ATRIBUTOS:\n")

            data_testids = page.evaluate("""
                const elements = document.querySelectorAll('[data-testid]');
                const testids = {};

                elements.forEach(el => {
                    const testid = el.getAttribute('data-testid');
                    testids[testid] = (testids[testid] || 0) + 1;
                });

                return Object.entries(testids).sort((a, b) => b[1] - a[1]);
            """)

            for testid, count in data_testids:
                print(f"🎯 {testid}: {count} elementos")

            print("\n" + "="*60 + "\n")

            # Análise de estrutura de preços
            print("💰 BUSCANDO ELEMENTOS DE PREÇO:\n")

            price_selectors = [
                '[class*="price"]',
                '[class*="valor"]',
                '[class*="preco"]',
                '[data-testid*="price"]',
                'span:contains("R$")',
                'div:contains("R$")',
                '.price',
                '.valor'
            ]

            for selector in price_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if len(elements) > 0:
                        print(f"✅ {selector}: {len(elements)} elementos")
                        # Mostra alguns exemplos
                        for i, el in enumerate(elements[:3]):
                            try:
                                text = el.inner_text().strip()
                                print(f"   💰 Exemplo {i+1}: {text}")
                            except:
                                pass
                except:
                    print(f"❌ {selector}: erro na busca")

            # Salva HTML completo para análise manual
            html_content = page.content()
            with open("webmotors_analise_completa.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("\n💾 HTML completo salvo: webmotors_analise_completa.html")
            print("📋 Use este arquivo para analisar a estrutura completa da página")

        except Exception as e:
            print(f"❌ Erro na análise: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    print("🔬 ANÁLISE DETALHADA DO WEBMOTORS\n")
    analisar_webmotors_detalhado()