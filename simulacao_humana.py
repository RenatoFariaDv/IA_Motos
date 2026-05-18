import time
import random
from playwright.sync_api import sync_playwright

def teste_humano():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1366, 'height': 768}
        )
        page = context.new_page()
        page.set_default_timeout(60000)

        url = "https://www.olx.com.br/autos-e-pecas/motos/estado-sp/sao-paulo-e-regiao"
        print(f"🤖 SIMULAÇÃO HUMANA: {url}\n")

        try:
            # 1. Acesso inicial lento
            print("1️⃣ Fazendo acesso inicial...")
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(random.uniform(2, 4))

            # 2. Fecha popups se existirem
            print("2️⃣ Verificando popups...")
            popups = [
                'button:has-text("Aceitar")',
                'button:has-text("OK")',
                'button:has-text("Agora não")',
                'button:has-text("Fechar")',
                '[data-testid*="cookie"]',
                '[aria-label*="fechar"]'
            ]

            for popup_selector in popups:
                try:
                    popup = page.query_selector(popup_selector)
                    if popup and popup.is_visible():
                        popup.click()
                        print(f"   ✅ Popup fechado: {popup_selector}")
                        time.sleep(1)
                        break
                except:
                    continue

            # 3. Simula leitura da página
            print("3️⃣ Simulando leitura humana...")
            time.sleep(random.uniform(3, 6))

            # 4. Movimento do mouse (simula interesse)
            print("4️⃣ Movendo mouse...")
            page.mouse.move(random.randint(100, 1200), random.randint(100, 600))
            time.sleep(1)

            # 5. Rolagem gradual (como pessoa lendo)
            print("5️⃣ Rolando página gradualmente...")
            scroll_steps = 5
            for i in range(scroll_steps):
                scroll_amount = (page.evaluate("document.body.scrollHeight") // scroll_steps)
                page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                time.sleep(random.uniform(1, 3))
                print(f"   📜 Scroll {i+1}/{scroll_steps}")

            # 6. Pausa para carregamento dinâmico
            print("6️⃣ Aguardando carregamento dinâmico...")
            time.sleep(5)

            # 7. Análise final
            print("7️⃣ Analisando resultado final...")

            # Screenshot final
            page.screenshot(path="simulacao_humana.png")
            print("📸 Screenshot salvo: simulacao_humana.png")

            # Busca por anúncios
            anuncios = page.query_selector_all('[data-ds-component="DS-NewAdCard"]')
            print(f"🏍️  Anúncios encontrados: {len(anuncios)}")

            if len(anuncios) > 0:
                print("\n🎉 SUCESSO! Anúncios carregados:")
                for i, anuncio in enumerate(anuncios[:3]):
                    try:
                        titulo = anuncio.inner_text().strip()[:50]
                        link = anuncio.query_selector('a')
                        if link:
                            href = link.get_attribute('href')
                            print(f"   {i+1}. {titulo}...")
                            print(f"      🔗 {href}")
                    except:
                        continue
            else:
                print("\n❌ Ainda sem anúncios. Verificando alternativas...")

                # Verifica se há mensagem de erro ou captcha
                erros = page.query_selector_all('text=/erro|captcha|bloqueado|robot/i')
                if len(erros) > 0:
                    print("🚫 Detectado possível bloqueio:")
                    for erro in erros[:3]:
                        print(f"   ⚠️  {erro.inner_text().strip()}")

                # Última tentativa: busca por qualquer link que pareça anúncio
                possiveis_anuncios = page.query_selector_all('a[href*="olx.com.br"][href*="motos"]')
                print(f"🔍 Links possíveis de motos: {len(possiveis_anuncios)}")

                if len(possiveis_anuncios) > 0:
                    print("📋 Possíveis anúncios encontrados:")
                    for i, link in enumerate(possiveis_anuncios[:5]):
                        href = link.get_attribute('href')
                        texto = link.inner_text().strip()[:40]
                        if len(texto) > 5:
                            print(f"   {i+1}. {texto}... → {href}")

            print("\n✅ Simulação humana completa!")

        except Exception as e:
            print(f"❌ Erro na simulação: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    teste_humano()