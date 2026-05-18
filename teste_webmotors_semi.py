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

def buscar_motos_webmotors_semiautomatico():
    """Versão semi-automática que pausa para resolver CAPTCHA"""

    # 1. Carrega a memória de anúncios passados
    vistos = carregar_vistos()

    with sync_playwright() as p:
        # 2. Configuração do Navegador com mais headers para parecer humano
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale='pt-BR',
            timezone_id='America/Sao_Paulo'
        )

        # Adiciona cookies e headers para parecer mais humano
        context.add_cookies([
            {
                'name': 'language',
                'value': 'pt-BR',
                'domain': '.webmotors.com.br',
                'path': '/'
            }
        ])

        page = context.new_page()
        page.set_default_timeout(60000)

        url = "https://www.webmotors.com.br/motos/sp-sao-paulo"
        print(f"🔗 Acessando Webmotors SP: {url}\n")

        try:
            # 3. Navegação simulando comportamento humano
            page.goto(url, wait_until="load")
            time.sleep(3)  # Pausa inicial

            # Simula movimento do mouse e scrolling humano
            page.mouse.move(100, 100)
            time.sleep(1)
            page.mouse.move(200, 200)
            time.sleep(1)

            print("🤖 SISTEMA ANTI-ROBÔ DETECTADO!")
            print("📋 Instruções para continuar:")
            print("   1. Na janela do Chrome que abriu, você verá uma verificação")
            print("   2. Clique em 'Não sou um robô' se aparecer")
            print("   3. Resolva qualquer quebra-cabeça ou CAPTCHA")
            print("   4. Aguarde os anúncios carregarem")
            print("   5. Pressione ENTER aqui quando estiver pronto")
            print("   ⚠️  IMPORTANTE: Digite apenas ENTER, não execute outros comandos!")
            print()

            try:
                input("Pressione ENTER após resolver a verificação: ")
            except KeyboardInterrupt:
                print("\n❌ Operação cancelada pelo usuário")
                return

            print("✅ Verificação resolvida! Continuando...\n")

            # Simula mais comportamento humano
            page.evaluate("window.scrollTo(0, 300)")
            time.sleep(2)
            page.evaluate("window.scrollTo(0, 600)")
            time.sleep(2)

            # Rola lentamente para carregar mais anúncios
            for i in range(5):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

            # Tira screenshot para verificar se anúncios carregaram
            page.screenshot(path="debug_webmotors_verificado.png")
            print("📸 Screenshot salvo: debug_webmotors_verificado.png")

            # 4. Busca por anúncios com múltiplas estratégias
            print("\n🔍 Procurando anúncios...\n")

            # Estratégia 1: Seletores específicos do Webmotors
            seletores = [
                '[data-testid="card-desktop"]',
                '[data-testid*="vehicle"]',
                '.vehicle-card',
                '.card-vehicle',
                '[class*="Card"]',
                'article[data-type="vehicle"]',
                '.listing-item'
            ]

            cards = []
            seletor_encontrado = ""

            for seletor in seletores:
                cards = page.query_selector_all(seletor)
                if len(cards) > 0:
                    seletor_encontrado = seletor
                    print(f"✅ {seletor}: {len(cards)} anúncios encontrados")
                    break

            # Estratégia 2: Se não encontrou, busca por links de motos
            if len(cards) == 0:
                print("🔄 Tentativa alternativa: procurando links de motos...")
                moto_links = page.query_selector_all('a[href*="moto"]')
                if len(moto_links) > 0:
                    cards = moto_links
                    seletor_encontrado = "links de motos"
                    print(f"✅ Links de motos encontrados: {len(cards)}")

            # Estratégia 3: Busca geral por qualquer link que pareça anúncio
            if len(cards) == 0:
                print("🔄 Última tentativa: procurando qualquer anúncio...")
                todos_links = page.query_selector_all('a[href*="anuncio"], a[href*="vehicle"], a[href*="moto"]')
                if len(todos_links) > 0:
                    cards = todos_links
                    seletor_encontrado = "links genéricos"
                    print(f"✅ Links genéricos encontrados: {len(cards)}")

            if len(cards) == 0:
                print("❌ Nenhum anúncio encontrado. Verifique se a página carregou corretamente.")
                return

            print(f"\n📊 Processando {len(cards)} anúncios candidatos (usando: {seletor_encontrado})\n")

            novos_encontrados = 0
            links_processados = []

            for i, card in enumerate(cards[:30]):  # Limita para não sobrecarregar
                try:
                    # Extrai informações dependendo da estratégia usada
                    if seletor_encontrado == "links de motos" or seletor_encontrado == "links genéricos":
                        # Para links diretos
                        link_elem = card
                        titulo = card.inner_text().strip()
                        href = card.get_attribute('href')

                        if href and not href.startswith('http'):
                            href = f"https://www.webmotors.com.br{href}"

                        preco = "Preço não disponível"

                        # Tenta encontrar preço no elemento pai
                        try:
                            preco_elem = card.query_selector('xpath=ancestor::*[1]//*[contains(text(), "R$")]')
                            if preco_elem:
                                preco = preco_elem.inner_text().strip()
                        except:
                            pass

                    else:
                        # Para cards estruturados
                        link_elem = card.query_selector('a') or card
                        titulo_elem = card.query_selector('h3, h2, [class*="title"], [data-testid*="title"]')
                        preco_elem = card.query_selector('[class*="price"], [class*="valor"], [data-testid*="price"]')

                        titulo = titulo_elem.inner_text().strip() if titulo_elem else "Título não encontrado"
                        href = link_elem.get_attribute('href') if link_elem else ""
                        preco = preco_elem.inner_text().strip() if preco_elem else "Preço não disponível"

                        if href and not href.startswith('http'):
                            href = f"https://www.webmotors.com.br{href}"

                    # Valida se é um anúncio válido
                    if href and titulo and len(titulo) > 5 and "moto" in titulo.lower():
                        links_processados.append(href)

                        # Verifica se é anúncio novo
                        if href not in vistos:
                            print(f"✨ NOVA MOTO ENCONTRADA:")
                            print(f"   📝 {titulo[:70]}")
                            print(f"   💰 {preco}")
                            print(f"   🔗 {href}\n")

                            vistos.append(href)
                            novos_encontrados += 1

                            if novos_encontrados >= 15:  # Limite maior para Webmotors
                                break

                except Exception as e:
                    continue

            # 5. Finalização e Salvamento
            if novos_encontrados > 0:
                salvar_vistos(vistos)
                print(f"✅ {novos_encontrados} novas motos adicionadas à memória!")
            else:
                print("😴 Nenhuma moto nova encontrada desta vez.")
                if len(links_processados) > 0:
                    print(f"\n📋 DEBUG - {len(links_processados)} links processados:")
                    for link in links_processados[:3]:
                        print(f"   → {link}")

        except Exception as e:
            print(f"❌ Erro na varredura: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    print("🚀 Robô Semi-Automático de Prospecção de Motos - Webmotors\n")
    buscar_motos_webmotors_semiautomatico()