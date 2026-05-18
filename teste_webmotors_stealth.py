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

def stealth_mode(page):
    """Aplica técnicas de stealth para evitar detecção"""
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['pt-BR', 'pt'],
        });
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32',
        });
        Object.defineProperty(navigator, 'product', {
            get: () => 'Gecko',
        });
        Object.defineProperty(navigator, 'vendor', {
            get: () => 'Google Inc.',
        });
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8,
        });
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8,
        });
        Object.defineProperty(navigator, 'maxTouchPoints', {
            get: () => 0,
        });
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                downlink: 10,
                rtt: 50,
                saveData: false,
                type: 'ethernet'
            }),
        });
        Object.defineProperty(screen, 'availWidth', {
            get: () => 1920,
        });
        Object.defineProperty(screen, 'availHeight', {
            get: () => 1080,
        });
        Object.defineProperty(window, 'devicePixelRatio', {
            get: () => 1,
        });

        Object.defineProperty(window, 'chrome', {
            get: () => ({
                runtime: {},
                loadTimes: () => {},
                csi: () => {},
                app: {},
                webstore: {},
            }),
        });

        const originalQuery = window.navigator.permissions.query.bind(window.navigator.permissions);
        window.navigator.permissions.query = (parameters) => {
            if (parameters.name === 'notifications') {
                return Promise.resolve({ state: Notification.permission });
            }
            return originalQuery(parameters);
        };
    """)

def comportamento_ultra_humano(page):
    """Simula comportamento extremamente humano"""
    # Movimentos de mouse mais naturais
    pontos = [
        (400, 300), (450, 320), (500, 350), (550, 380), (600, 400),
        (650, 420), (700, 440), (750, 460), (800, 480)
    ]

    for x, y in pontos:
        page.mouse.move(x, y)
        time.sleep(random.uniform(0.1, 0.3))

    # Typing simulation (invisível)
    page.keyboard.press('ArrowDown')
    time.sleep(0.1)
    page.keyboard.press('ArrowUp')
    time.sleep(0.1)

    # Scrolling mais humano
    for i in range(3):
        scroll_amount = random.randint(100, 300)
        page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        time.sleep(random.uniform(0.8, 2.0))

def tentar_burlar_captcha(page):
    """Tenta várias técnicas para burlar CAPTCHA"""
    try:
        # Técnica 1: Aguardar e tentar novamente
        time.sleep(5)

        # Técnica 2: Recarregar página se necessário
        if page.query_selector('.recaptcha-error'):
            print("🔄 Recarregando página devido a erro no CAPTCHA...")
            page.reload()
            time.sleep(3)

        # Técnica 3: Tentar clicar no CAPTCHA invisível
        captcha_iframe = page.query_selector('iframe[src*="recaptcha"]')
        if captcha_iframe:
            print("🎯 CAPTCHA iframe encontrado, tentando bypass...")

            # Muda para o frame do CAPTCHA
            frame = captcha_iframe.content_frame()
            if frame:
                checkbox = frame.query_selector('#recaptcha-anchor')
                if checkbox:
                    checkbox.click()
                    time.sleep(3)

                    # Verifica se foi marcado
                    if frame.query_selector('.recaptcha-checkbox-checked'):
                        print("✅ CAPTCHA burlado com sucesso!")
                        return True

        # Técnica 4: Usar cookies de sessão válida (se existirem)
        try:
            cookies = page.context.cookies()
            if any('recaptcha' in cookie['name'].lower() for cookie in cookies):
                print("🍪 Cookies de reCAPTCHA encontrados")
        except:
            pass

        return False

    except Exception as e:
        print(f"❌ Erro ao tentar burlar CAPTCHA: {e}")
        return False

def buscar_motos_webmotors_ultra_stealth():
    """Versão ultra-stealth com máxima tentativa de automação"""

    vistos = carregar_vistos()

    # User agents premium
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
    ]

    with sync_playwright() as p:
        # Configuração stealth máxima
        browser = p.chromium.launch(
            headless=False,
            channel="chrome",
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-ipc-flooding-protection',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows'
            ]
        )

        context = browser.new_context(
            user_agent=random.choice(user_agents),
            viewport={'width': 1920, 'height': 1080},
            locale='pt-BR',
            timezone_id='America/Sao_Paulo',
            permissions=['geolocation'],
            geolocation={'latitude': -23.5505, 'longitude': -46.6333},
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'max-age=0',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'DNT': '1'
            }
        )

        page = context.new_page()
        stealth_mode(page)
        page.set_default_timeout(60000)

        url = "https://www.webmotors.com.br/motos/sp-sao-paulo"
        print(f"🔗 Acessando Webmotors SP (modo stealth): {url}\n")

        try:
            # Navegação stealth
            print("🕵️ Iniciando navegação stealth...")
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(random.uniform(4, 7))

            # Comportamento ultra-humano
            comportamento_ultra_humano(page)

            # Verifica CAPTCHA
            captcha_detected = False
            captcha_selectors = [
                'iframe[src*="recaptcha"]',
                '.recaptcha',
                '[class*="recaptcha"]',
                '[data-sitekey]'
            ]

            for selector in captcha_selectors:
                if page.query_selector(selector):
                    captcha_detected = True
                    print(f"🚨 CAPTCHA detectado: {selector}")
                    break

            if captcha_detected:
                print("🎯 Tentando técnicas anti-CAPTCHA...")
                captcha_bypassed = tentar_burlar_captcha(page)

                if not captcha_bypassed:
                    print("❌ CAPTCHA não pôde ser burlado automaticamente")
                    print("💡 Alternativas:")
                    print("   1. Use a versão semi-automática")
                    print("   2. Execute durante horários de menos tráfego")
                    print("   3. Use VPN ou proxy")
                    return
            else:
                print("✅ Sem CAPTCHA detectado!")

            # Continua carregamento
            print("📜 Carregando anúncios dinamicamente...")
            for i in range(10):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(random.uniform(1.5, 3.5))
                comportamento_ultra_humano(page)

            # Screenshot
            page.screenshot(path="debug_webmotors_stealth.png")
            print("📸 Screenshot salvo: debug_webmotors_stealth.png")

            # Busca anúncios
            print("\n🔍 Procurando anúncios...\n")

            seletores_prioridade = [
                '[data-testid="card-desktop"]',
                '[data-testid*="vehicle"]',
                '.vehicle-card',
                '[class*="Card__Container"]',
                'article[data-type="vehicle"]',
                '.listing-item'
            ]

            cards = []
            seletor_funcionou = ""

            for seletor in seletores_prioridade:
                cards = page.query_selector_all(seletor)
                if len(cards) > 0:
                    seletor_funcionou = seletor
                    print(f"✅ {seletor}: {len(cards)} anúncios")
                    break

            # Fallback múltiplo
            if len(cards) == 0:
                fallbacks = [
                    ('a[href*="moto"]', 'links de motos'),
                    ('a[href*="anuncio"]', 'links de anúncios'),
                    ('[class*="vehicle"]', 'elementos vehicle'),
                    ('article', 'artigos genéricos')
                ]

                for fallback_selector, nome in fallbacks:
                    cards = page.query_selector_all(fallback_selector)
                    if len(cards) > 0:
                        seletor_funcionou = nome
                        print(f"✅ Fallback: {nome} - {len(cards)}")
                        break

            if len(cards) == 0:
                print("❌ Nenhum anúncio encontrado")
                return

            print(f"\n📊 Processando {len(cards)} anúncios ({seletor_funcionou})\n")

            novos_encontrados = 0

            for i, card in enumerate(cards[:30]):
                try:
                    if "link" in seletor_funcionou:
                        link_elem = card
                        titulo = card.inner_text().strip()
                        href = card.get_attribute('href')
                        preco = "Preço não disponível"

                        # Busca preço no contexto
                        try:
                            parent = card.query_selector('xpath=ancestor::*[1]')
                            if parent:
                                preco_elem = parent.query_selector('[class*="price"], [class*="valor"]')
                                if preco_elem:
                                    preco = preco_elem.inner_text().strip()
                        except:
                            pass
                    else:
                        link_elem = card.query_selector('a') or card
                        titulo_elem = card.query_selector('h3, h2, [class*="title"], [data-testid*="title"]')
                        preco_elem = card.query_selector('[class*="price"], [class*="valor"], [data-testid*="price"]')

                        titulo = titulo_elem.inner_text().strip() if titulo_elem else card.inner_text().strip()
                        href = link_elem.get_attribute('href') if link_elem else ""
                        preco = preco_elem.inner_text().strip() if preco_elem else "Preço não disponível"

                    if href and not href.startswith('http'):
                        href = f"https://www.webmotors.com.br{href}"

                    if (href and titulo and len(titulo) > 5 and
                        any(keyword in titulo.lower() for keyword in ['moto', 'motocicleta', 'yamaha', 'honda', 'kawasaki', 'bmw', 'harley'])):

                        if href not in vistos:
                            print(f"🏍️ NOVA MOTO ENCONTRADA:")
                            print(f"   📝 {titulo[:70]}")
                            print(f"   💰 {preco}")
                            print(f"   🔗 {href}\n")

                            vistos.append(href)
                            novos_encontrados += 1

                            if novos_encontrados >= 15:
                                break

                except Exception as e:
                    continue

            # Salvamento
            if novos_encontrados > 0:
                salvar_vistos(vistos)
                print(f"🎉 {novos_encontrados} novas motos adicionadas à memória!")
            else:
                print("😴 Nenhuma moto nova encontrada")

        except Exception as e:
            print(f"❌ Erro na execução: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    print("🕵️ Robô ULTRA STEALTH de Prospecção de Motos - Webmotors\n")
    buscar_motos_webmotors_ultra_stealth()