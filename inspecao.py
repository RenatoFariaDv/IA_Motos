import time
from playwright.sync_api import sync_playwright

def inspecao_profunda():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.set_default_timeout(60000)

        url = "https://www.olx.com.br/autos-e-pecas/motos/estado-sp/sao-paulo-e-regiao"
        print(f"🔍 INSPEÇÃO PROFUNDA: {url}\n")

        try:
            page.goto(url, wait_until="load")
            time.sleep(3)

            # Fecha popups se existirem
            try:
                # Tenta fechar popup de cookies
                cookie_button = page.query_selector('button:has-text("Aceitar"), button:has-text("OK"), [data-testid*="cookie"]')
                if cookie_button:
                    cookie_button.click()
                    print("🍪 Popup de cookies fechado")
                    time.sleep(2)
            except:
                pass

            # Tenta fechar popup de localização
            try:
                location_button = page.query_selector('button:has-text("Agora não"), button:has-text("Fechar")')
                if location_button:
                    location_button.click()
                    print("📍 Popup de localização fechado")
                    time.sleep(2)
            except:
                pass

            # Carrega mais conteúdo rolando
            print("📜 Rolando página para carregar anúncios...")
            for i in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                print(f"   Scroll {i+1}/3 completo")

            # Tira screenshot final
            page.screenshot(path="inspecao_final.png")
            print("📸 Screenshot final: inspecao_final.png\n")

            # Análise detalhada da estrutura
            print("=" * 80)
            print("ESTRUTURA DA PÁGINA:")
            print("=" * 80)

            # Verifica se há anúncios por diferentes seletores
            seletores = [
                '[data-ds-component="DS-NewAdCard"]',
                '[data-testid*="ad-card"]',
                '.ad-card',
                '[class*="AdCard"]',
                'article',
                '[role="article"]',
                'div[data-ad-id]',
                'a[href*="anuncio"]',
                'a[href*="motos"][href*="olx.com.br"]'
            ]

            for seletor in seletores:
                elementos = page.query_selector_all(seletor)
                if len(elementos) > 0:
                    print(f"✅ {seletor}: {len(elementos)} elementos")
                    # Mostra exemplo do primeiro
                    if len(elementos) > 0:
                        elem = elementos[0]
                        texto = elem.inner_text().strip()[:100]
                        print(f"   📝 Exemplo: {texto}...")
                        try:
                            link = elem.query_selector('a')
                            if link:
                                href = link.get_attribute('href')
                                print(f"   🔗 Link: {href}")
                        except:
                            pass
                        print()
                else:
                    print(f"❌ {seletor}: 0 elementos")

            # Verifica se há elementos com preços
            print("\n" + "=" * 80)
            print("ELEMENTOS COM PREÇOS:")
            print("=" * 80)

            precos = page.query_selector_all('span:has-text("R$"), [class*="price"], [data-price]')
            print(f"💰 Elementos com preço encontrados: {len(precos)}")

            for i, preco in enumerate(precos[:5]):
                texto = preco.inner_text().strip()
                print(f"   {i+1}. {texto}")

            # Verifica estrutura geral
            print("\n" + "=" * 80)
            print("ESTRUTURA GERAL:")
            print("=" * 80)

            body_text = page.inner_text('body')[:500]
            print(f"📄 Texto da página (primeiros 500 chars):\n{body_text}...")

            print("\n✅ Inspeção completa! Verifique os screenshots.")

        except Exception as e:
            print(f"❌ Erro na inspeção: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    inspecao_profunda()