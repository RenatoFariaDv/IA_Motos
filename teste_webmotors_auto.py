import json
import os
import time
import random
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

def comportamento_humano(page):
    """Simula comportamento humano para evitar detecção"""
    # Movimentos aleatórios do mouse
    for _ in range(random.randint(3, 8)):
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        page.mouse.move(x, y)
        time.sleep(random.uniform(0.1, 0.5))

    # Scrolling humano
    page.evaluate("window.scrollTo(0, " + str(random.randint(200, 500)) + ")")
    time.sleep(random.uniform(1, 3))

    # Mais movimentos
    page.mouse.move(random.randint(200, 700), random.randint(300, 500))
    time.sleep(random.uniform(0.5, 2))

def tentar_captcha_automatico(page):
    """Tenta resolver CAPTCHA automaticamente"""
    try:
        # Procura pelo checkbox do reCAPTCHA
        captcha_selectors = [
            '[class*="recaptcha-checkbox"]',
            '.recaptcha-checkbox-border',
            '#recaptcha-anchor',
            '[data-sitekey] iframe',
            'iframe[src*="recaptcha"]'
        ]

        for selector in captcha_selectors:
            try:
                element = page.query_selector(selector)
                if element:
                    print(f"🎯 CAPTCHA encontrado com seletor: {selector}")
                    element.click()
                    time.sleep(3)

                    # Verifica se o CAPTCHA foi resolvido
                    if page.query_selector('.recaptcha-checkbox-checked'):
                        print("✅ CAPTCHA resolvido automaticamente!")
                        return True
                    else:
                        print("❌ CAPTCHA não foi resolvido")
                        return False
            except:
                continue

        print("🤷 Nenhum CAPTCHA detectado")
        return True  # Assume que não há CAPTCHA

    except Exception as e:
        print(f"❌ Erro ao tentar resolver CAPTCHA: {e}")
        return False

def buscar_motos_webmotors_automatico():
    """Versão que tenta ser totalmente automática"""

    # 1. Carrega a memória de anúncios passados
    vistos = carregar_vistos()

    # Lista de user agents para rotacionar
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]

    with sync_playwright() as p:
        # 2. Configuração do Navegador com stealth mode
        browser = p.chromium.launch(
            headless=False,  # Mantém visível para debug
            channel="chrome",
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )

        context = browser.new_context(
            user_agent=random.choice(user_agents),
            viewport={'width': 1920, 'height': 1080},
            locale='pt-BR',
            timezone_id='America/Sao_Paulo',
            permissions=['geolocation'],
            geolocation={'latitude': -23.5505, 'longitude': -46.6333},  # São Paulo
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )

        # Remove webdriver property
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        page.set_default_timeout(60000)

        url = "https://www.webmotors.com.br/motos/sp-sao-paulo"
        print(f"🔗 Acessando Webmotors SP: {url}\n")

        try:
            # 3. Navegação simulando humano
            print("🤖 Iniciando navegação stealth...")
            page.goto(url, wait_until="load")
            time.sleep(random.uniform(3, 6))

            # Comportamento humano inicial
            comportamento_humano(page)

            # Verifica se há CAPTCHA
            captcha_presente = page.query_selector('[class*="recaptcha"], iframe[src*="recaptcha"], [data-sitekey]')

            if captcha_presente:
                print("🚨 CAPTCHA detectado! Tentando resolução automática...")
                captcha_resolvido = tentar_captcha_automatico(page)

                if not captcha_resolvido:
                    print("❌ CAPTCHA não pôde ser resolvido automaticamente")
                    print("💡 Sugestão: Use a versão semi-automática ou resolva manualmente")
                    return
            else:
                print("✅ Nenhum CAPTCHA detectado")

            # Continua com comportamento humano
            comportamento_humano(page)

            # Rola a página lentamente para carregar anúncios
            print("📜 Carregando anúncios...")
            for i in range(8):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(random.uniform(2, 4))
                comportamento_humano(page)

            # Tira screenshot
            page.screenshot(path="debug_webmotors_auto.png")
            print("📸 Screenshot salvo: debug_webmotors_auto.png")

            # 4. Busca por anúncios
            print("\n🔍 Procurando anúncios...\n")

            seletores = [
                '[data-testid="card-desktop"]',
                '[data-testid*="vehicle"]',
                '.vehicle-card',
                '[class*="Card"]',
                'article',
                '.listing-item'
            ]

            cards = []
            seletor_usado = ""

            for seletor in seletores:
                cards = page.query_selector_all(seletor)
                if len(cards) > 0:
                    seletor_usado = seletor
                    print(f"✅ {seletor}: {len(cards)} anúncios encontrados")
                    break

            # Fallback: links de motos
            if len(cards) == 0:
                cards = page.query_selector_all('a[href*="moto"]')
                if len(cards) > 0:
                    seletor_usado = "links de motos"
                    print(f"✅ Links de motos: {len(cards)}")

            if len(cards) == 0:
                print("❌ Nenhum anúncio encontrado")
                return

            print(f"\n📊 Processando {len(cards)} anúncios (usando: {seletor_usado})\n")

            novos_encontrados = 0

            for i, card in enumerate(cards[:25]):
                try:
                    if seletor_usado == "links de motos":
                        link_elem = card
                        titulo = card.inner_text().strip()
                        href = card.get_attribute('href')
                        preco = "Preço não disponível"
                    else:
                        link_elem = card.query_selector('a') or card
                        titulo_elem = card.query_selector('h3, h2, [class*="title"]')
                        preco_elem = card.query_selector('[class*="price"], [class*="valor"]')

                        titulo = titulo_elem.inner_text().strip() if titulo_elem else "Título não encontrado"
                        href = link_elem.get_attribute('href') if link_elem else ""
                        preco = preco_elem.inner_text().strip() if preco_elem else "Preço não disponível"

                    if href and not href.startswith('http'):
                        href = f"https://www.webmotors.com.br{href}"

                    if href and titulo and len(titulo) > 5 and "moto" in titulo.lower():
                        if href not in vistos:
                            print(f"✨ NOVA MOTO: {titulo[:60]}")
                            print(f"   💰 {preco}")
                            print(f"   🔗 {href}\n")

                            vistos.append(href)
                            novos_encontrados += 1

                            if novos_encontrados >= 10:
                                break

                except Exception as e:
                    continue

            # 5. Salvamento
            if novos_encontrados > 0:
                salvar_vistos(vistos)
                print(f"✅ {novos_encontrados} novas motos salvas!")
            else:
                print("😴 Nenhuma moto nova encontrada")

        except Exception as e:
            print(f"❌ Erro: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    print("🚀 Robô Automático de Prospecção de Motos - Webmotors\n")
    buscar_motos_webmotors_automatico()