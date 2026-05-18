import json
import os
import time
from playwright.sync_api import sync_playwright

# Nome do arquivo que guarda os anúncios que o robô já viu
ARQUIVO_MEMORIA = "anuncios_webmotors.json"

def carregar_vistos():
    """Lê o arquivo JSON com os links já processados."""
    if os.path.exists(ARQUIVO_MEMORIA):
        with open(ARQUIVO_MEMORIA, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def salvar_vistos(vistos):
    """Salva a lista atualizada de links no arquivo JSON."""
    with open(ARQUIVO_MEMORIA, "w", encoding="utf-8") as f:
        json.dump(vistos, f, ensure_ascii=False, indent=4)

def buscar_motos_webmotors_seguro():
    """Versão segura que trata erros e dá orientações claras"""

    # 1. Carrega a memória de anúncios passados
    vistos = carregar_vistos()

    with sync_playwright() as p:
        # 2. Configuração do Navegador
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
        print(f"🔗 Acessando Webmotors SP: {url}\n")

        try:
            # 3. Navegação inicial
            print("🌐 Carregando página...")
            page.goto(url, wait_until="load")
            time.sleep(3)

            # Verifica se há CAPTCHA imediatamente
            captcha_selectors = [
                'iframe[src*="recaptcha"]',
                '.recaptcha',
                '[class*="recaptcha"]',
                '[data-sitekey]'
            ]

            captcha_detected = any(page.query_selector(selector) for selector in captcha_selectors)

            if captcha_detected:
                print("🤖 CAPTCHA DETECTADO!")
                print("=" * 50)
                print("📋 INSTRUÇÕES PARA CONTINUAR:")
                print("   1. Na janela do Chrome que abriu, localize o CAPTCHA")
                print("   2. Clique na caixa 'Não sou um robô'")
                print("   3. Se aparecer imagens, selecione todas as motos/motocicletas")
                print("   4. Aguarde os anúncios carregarem completamente")
                print("   5. DIGITE APENAS 'OK' E PRESSIONE ENTER (nada mais!)")
                print("=" * 50)
                print()

                resposta = ""
                while resposta.lower() != "ok":
                    try:
                        resposta = input("Digite 'OK' quando terminar: ").strip()
                        if resposta.lower() != "ok":
                            print("❌ Digite apenas 'OK' para continuar...")
                    except KeyboardInterrupt:
                        print("\n❌ Operação cancelada!")
                        return
                    except EOFError:
                        print("\n❌ Entrada inválida!")
                        return

                print("✅ CAPTCHA resolvido! Continuando...\n")
            else:
                print("✅ Sem CAPTCHA detectado, continuando automaticamente...\n")

            # 4. Carrega anúncios com scrolling
            print("📜 Carregando anúncios...")
            for i in range(6):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                print(f"   ⬇️  Rolagem {i+1}/6 completada")

            # Screenshot para verificação
            page.screenshot(path="webmotors_pronto.png")
            print("📸 Screenshot salvo: webmotors_pronto.png")

            # 5. Busca anúncios
            print("\n🔍 Procurando anúncios de motos...\n")

            # Tenta múltiplos seletores
            seletores = [
                '[data-testid="card-desktop"]',
                '.Card__Container-sc-1v0r5ui-0',
                '[data-testid*="card"]',
                '.card',
                'article',
                '.vehicle-card'
            ]

            cards = []
            seletor_usado = ""

            for seletor in seletores:
                cards = page.query_selector_all(seletor)
                if len(cards) > 0:
                    seletor_usado = seletor
                    print(f"✅ Encontrados {len(cards)} anúncios usando: {seletor}")
                    break

            # Fallback para links
            if len(cards) == 0:
                cards = page.query_selector_all('a[href*="moto"]')
                if len(cards) > 0:
                    seletor_usado = "links de motos"
                    print(f"✅ Encontrados {len(cards)} links de motos")

            if len(cards) == 0:
                print("❌ Nenhum anúncio encontrado. Verifique se a página carregou corretamente.")
                return

            print(f"\n📊 Processando {len(cards)} itens encontrados...\n")

            novos_encontrados = 0

            for i, card in enumerate(cards[:25]):  # Limita para não sobrecarregar
                try:
                    if seletor_usado == "links de motos":
                        # Para links diretos
                        link_elem = card
                        titulo = card.inner_text().strip()
                        href = card.get_attribute('href')
                        preco = "Preço não disponível"
                    else:
                        # Para cards estruturados
                        link_elem = card.query_selector('a') or card
                        titulo_elem = card.query_selector('h3, h2, [class*="title"]')
                        preco_elem = card.query_selector('[class*="price"], [class*="valor"]')

                        titulo = titulo_elem.inner_text().strip() if titulo_elem else "Título não encontrado"
                        href = link_elem.get_attribute('href') if link_elem else ""
                        preco = preco_elem.inner_text().strip() if preco_elem else "Preço não disponível"

                    if href and not href.startswith('http'):
                        href = f"https://www.webmotors.com.br{href}"

                    # Valida se é anúncio de moto
                    if (href and titulo and len(titulo) > 5 and
                        any(keyword in titulo.lower() for keyword in ['moto', 'motocicleta', 'yamaha', 'honda', 'kawasaki', 'bmw', 'harley', 'suzuki'])):

                        if href not in vistos:
                            print(f"🏍️  NOVA MOTO #{novos_encontrados+1}:")
                            print(f"   📝 {titulo[:70]}")
                            print(f"   💰 {preco}")
                            print(f"   🔗 {href}\n")

                            vistos.append(href)
                            novos_encontrados += 1

                            if novos_encontrados >= 10:
                                break

                except Exception as e:
                    continue

            # 6. Finalização
            if novos_encontrados > 0:
                salvar_vistos(vistos)
                print(f"🎉 SUCESSO! {novos_encontrados} novas motos adicionadas à memória!")
            else:
                print("😴 Nenhuma moto nova encontrada desta vez.")

        except Exception as e:
            print(f"❌ Erro durante a execução: {e}")
            print("💡 Dica: Tente novamente ou use um horário diferente")
        finally:
            try:
                browser.close()
                print("🔒 Navegador fechado com segurança.")
            except:
                print("⚠️  Navegador já estava fechado.")

if __name__ == "__main__":
    print("🚀 Robô Seguro de Prospecção de Motos - Webmotors\n")
    buscar_motos_webmotors_seguro()