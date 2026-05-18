import json
import os
import time
from playwright.sync_api import sync_playwright

def analisar_webmotors():
    """Script para analisar a estrutura HTML do Webmotors e encontrar seletores corretos"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.set_default_timeout(60000)

        url = "https://www.webmotors.com.br/motos/sp-sao-paulo"
        print(f"🔍 Analisando Webmotors: {url}\n")

        try:
            page.goto(url, wait_until="load")
            time.sleep(10)  # Tempo extra para carregamento

            # Rola a página várias vezes para forçar carregamento
            for i in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(3)

            # Salva screenshot
            page.screenshot(path="analise_webmotors.png")
            print("📸 Screenshot salvo: analise_webmotors.png")

            # Análise da estrutura HTML
            print("\n🔎 ANÁLISE DA ESTRUTURA HTML:\n")

            # Procura por elementos que podem conter anúncios
            possiveis_seletores = [
                '[data-testid*="card"]',
                '[data-testid*="Card"]',
                '.card',
                '.Card',
                '[class*="card"]',
                '[class*="Card"]',
                'article',
                'div[role="article"]',
                '.ad',
                '.advertisement',
                '[data-type="ad"]',
                '.vehicle-card',
                '.moto-card',
                '.listing-item'
            ]

            for seletor in possiveis_seletores:
                elementos = page.query_selector_all(seletor)
                if len(elementos) > 0:
                    print(f"✅ {seletor}: {len(elementos)} elementos encontrados")
                    # Mostra exemplo do primeiro elemento
                    if len(elementos) > 0:
                        try:
                            html = elementos[0].inner_html()[:200]
                            print(f"   📄 HTML exemplo: {html}...\n")
                        except:
                            print("   ❌ Erro ao extrair HTML\n")
                else:
                    print(f"❌ {seletor}: 0 elementos")

            # Análise específica de texto que pode indicar anúncios
            print("\n🔎 PROCURANDO POR TEXTO RELACIONADO A MOTOS:\n")

            textos_chave = ["moto", "motocicleta", "yamaha", "honda", "kawasaki", "suzuki", "harley", "bmw"]

            for texto in textos_chave:
                elementos_com_texto = page.query_selector_all(f'text()="{texto}"')
                if len(elementos_com_texto) > 0:
                    print(f"✅ Texto '{texto}': {len(elementos_com_texto)} ocorrências")

            # Verifica se há algum iframe ou conteúdo carregado dinamicamente
            iframes = page.query_selector_all('iframe')
            print(f"\n🔎 IFRAMES ENCONTRADOS: {len(iframes)}")

            # Salva o HTML completo para análise manual
            html_completo = page.content()
            with open("webmotors_html.txt", "w", encoding="utf-8") as f:
                f.write(html_completo)
            print("💾 HTML completo salvo em: webmotors_html.txt")

            # Análise de classes CSS mais comuns
            print("\n🔎 ANÁLISE DE CLASSES CSS MAIS COMUNS:\n")
            classes_comuns = page.evaluate("""
                const elements = document.querySelectorAll('*');
                const classCount = {};

                elements.forEach(el => {
                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.split(' ');
                        classes.forEach(cls => {
                            if (cls.length > 3) {  // Ignora classes muito curtas
                                classCount[cls] = (classCount[cls] || 0) + 1;
                            }
                        });
                    }
                });

                // Retorna as 20 classes mais comuns
                return Object.entries(classCount)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 20);
            """)

            for classe, count in classes_comuns:
                print(f"📊 {classe}: {count} elementos")

        except Exception as e:
            print(f"❌ Erro na análise: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    print("🔬 ANÁLISE DETALHADA DO WEBMOTORS\n")
    analisar_webmotors()