import time
from playwright.sync_api import sync_playwright

def teste_debug():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.set_default_timeout(60000)

        url = "https://www.olx.com.br/autos-e-pecas/motos/estado-sp/sao-paulo-e-regiao"
        print(f"🔗 Acessando: {url}\n")

        try:
            page.goto(url, wait_until="load")
            time.sleep(5)

            # Pega TODOS os links
            links = page.query_selector_all('a')
            print(f"📊 Total de links na página: {len(links)}\n")

            print("=" * 80)
            print("ANALISANDO TODOS OS LINKS (mostrando os 30 primeiros):")
            print("=" * 80 + "\n")

            contador = 0
            for i, link in enumerate(links):
                href = link.get_attribute('href')
                texto = link.inner_text().strip()

                # Mostra tudo que tem texto
                if href and texto and len(texto) > 0:
                    print(f"{contador + 1}. TEXTO: {texto[:50]}")
                    print(f"   URL: {href}")
                    print(f"   ---")

                    contador += 1
                    if contador >= 30:
                        break

            print("\n" + "=" * 80)
            print("ANÁLISE DE PADRÕES:")
            print("=" * 80 + "\n")

            padroes = {
                '/anuncio/': 0,
                '/motos/': 0,
                '/m/': 0,
                'olx.com.br': 0,
            }

            for link in links:
                href = link.get_attribute('href')
                if href:
                    for padrao in padroes:
                        if padrao in href:
                            padroes[padrao] += 1

            for padrao, count in padroes.items():
                print(f"  • Links com '{padrao}': {count}")

            print("\n✅ Debug completo! Verifique os padrões acima.")

        except Exception as e:
            print(f"❌ Erro: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    teste_debug()