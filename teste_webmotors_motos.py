import json
import os
import time
import re
import requests
import random
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv
from teste_webmotors_stealth import stealth_mode, comportamento_ultra_humano

# =========================================================
# CONFIGURAÇÕES
# =========================================================
load_dotenv()

TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
ID_DAVISON = os.getenv("ID_DAVISON")
ID_RENATO = os.getenv("ID_RENATO")
PROXY_WEBMOTORS = os.getenv("PROXY_WEBMOTORS") or os.getenv("PROXY_URL")
USER_DATA_DIR = os.getenv("WM_USER_DATA_DIR") or "chrome_profile"

DESTINATARIOS = [ID_DAVISON, ID_RENATO]
ARQUIVO_MEMORIA_WM = "vistos_webmotors.json"
URL_WEBMOTORS = "https://www.webmotors.com.br/motos/estoque/sp/sao-paulo?idsuportevenda=online"

def escapar_markdown(texto: str) -> str:
    if not texto: return ""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', texto)

def enviar_telegram(mensagem: str):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    for chat_id in DESTINATARIOS:
        if not chat_id:
            continue
        payload = {"chat_id": chat_id, "text": mensagem}
        try:
            requests.post(url, data=payload, timeout=15)
            print(f"✅ Notificação enviada para: {chat_id}")
        except Exception as e:
            print(f"❌ Erro Telegram: {e}")


def enviar_telegram_foto(photo_url: str, caption: str):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto"
    for chat_id in DESTINATARIOS:
        if not chat_id:
            continue
        payload = {"chat_id": chat_id, "photo": photo_url, "caption": caption}
        try:
            requests.post(url, data=payload, timeout=15)
            print(f"✅ Foto enviada para: {chat_id}")
        except Exception as e:
            print(f"❌ Erro ao enviar foto para {chat_id}: {e}")


def segurar_botao_perimeterx(page, hold_seconds: float = 5.0) -> bool:
    """Tenta segurar o botão de verificação PerimeterX automaticamente."""
    selectors = [
        "text=/Pressione e segure/i",
        "text=/Press & Hold/i",
        ".px-captcha-error-button",
        "#px-captcha",
        "div[role='button']",
    ]

    button = None
    for selector in selectors:
        try:
            locator = page.locator(selector)
            if locator.count() > 0:
                button = locator.first
                break
        except Exception:
            continue

    if not button:
        return False

    try:
        box = button.bounding_box()
        if not box:
            return False

        x = box["x"] + box["width"] / 2
        y = box["y"] + box["height"] / 2
        page.mouse.move(x, y)
        page.mouse.down()
        time.sleep(hold_seconds)
        page.mouse.up()

        print(f"✅ Botão de verificação segurado por {hold_seconds}s")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao segurar botão: {e}")
        return False


def buscar_webmotors():
    if os.path.exists(ARQUIVO_MEMORIA_WM):
        try:
            with open(ARQUIVO_MEMORIA_WM, "r", encoding="utf-8") as f:
                vistos = json.load(f)
        except: vistos = []
    else: vistos = []

    novos_encontrados = 0

    with sync_playwright() as p:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
        ]

        proxy = None
        if PROXY_WEBMOTORS:
            proxy = {"server": PROXY_WEBMOTORS}
            print(f"🌐 Usando proxy WebMotors: {PROXY_WEBMOTORS}")

        browser = p.chromium.launch(
            headless=False,
            channel="chrome",
            ignore_default_args=["--enable-automation"],
            proxy=proxy,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor,IsolateOrigins,site-per-process',
                '--disable-ipc-flooding-protection',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--start-maximized',
            ]
        )

        context = browser.new_context(
            user_agent=random.choice(user_agents),
            viewport={"width": 1920, "height": 1080},
            locale='pt-BR',
            timezone_id='America/Sao_Paulo',
            geolocation={'latitude': -23.5505, 'longitude': -46.6333},
            permissions=['geolocation'],
            proxy=proxy,
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
            }
        )
        context.grant_permissions(['geolocation'], origin='https://www.webmotors.com.br')
        context.set_default_timeout(90000)
        context.set_default_navigation_timeout(90000)

        page = context.pages[0] if context.pages else context.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        Stealth().apply_stealth_sync(page)
        stealth_mode(page)

        page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
        })

        Stealth().apply_stealth_sync(page)
        stealth_mode(page)

        print(f"\n[{time.strftime('%H:%M:%S')}] 🔗 Acessando WebMotors...")
        
        try:
            # Warm-up em site neutro para criar sessão mais natural
            page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=60000)
            time.sleep(random.uniform(2.5, 4.5))
            comportamento_ultra_humano(page)
            
            page.goto(URL_WEBMOTORS, wait_until="networkidle", timeout=120000)
            time.sleep(random.uniform(4, 7))
            comportamento_ultra_humano(page)

            print(f"📍 URL atual: {page.url}")
            print(f"📰 Título: {page.title()}")

            content = page.content()
            if "px-captcha" in content or "captcha" in content:
                print("\n🚨 BLOQUEIO PERIMETERX DETECTADO!")
                print("ℹ️  WebMotors está bloqueando com CAPTCHA.")
                print("� Tentando segurar o botão automaticamente...")

                if segurar_botao_perimeterx(page, hold_seconds=random.uniform(4.5, 6.5)):
                    try:
                        page.wait_for_selector("div.CardVehicle", timeout=120000)
                        print("✅ CAPTCHA superado! Continuando...")
                    except Exception:
                        print("⚠️ Falha ao detectar cards após segurar o botão.")
                else:
                    print("⚠️ Não encontrei o botão para segurar automaticamente.")

                if page.locator("div.CardVehicle").count() == 0:
                    print("\n📋 Opções:")
                    print("   1. Resolva manualmente no navegador aberto")
                    print("   2. Pressione o botão de verificação se aparecer")
                    print("   3. Aguarde até 3 minutos enquanto o script tenta...")
                    print()
                    try:
                        page.wait_for_selector("div.CardVehicle", timeout=180000)
                        print("✅ CAPTCHA superado manualmente! Continuando...")
                    except Exception:
                        print("❌ Bloqueio persistente. Não consegui contornar automaticamente.")
                        print("💡 Tente novamente em alguns minutos.")
                        context.close()
                        return

            time.sleep(3)
            for i in range(2):
                page.mouse.wheel(0, 1500)
                time.sleep(2)

            print("🔎 Verificando vários seletores de anúncio...")
            selectors = [
                "div.CardVehicle",
                "[data-testid*='card']",
                "[data-testid*='vehicle']",
                ".vehicle-card",
                "[class*='Card__Container']",
                "article[data-type='vehicle']",
                ".listing-item",
                "div[class*='card']",
                "[class*='vehicle']",
                "li[class*='card']",
            ]

            cards = None
            for selector in selectors:
                locator = page.locator(selector)
                count = locator.count()
                print(f"   {selector}: {count}")
                if count > 0 and cards is None:
                    cards = locator

            if cards is None:
                print("❌ Nenhum anúncio encontrado em seletores padrões.")
                if "R$" in content:
                    print("⚠️ A página contém preços, mas seletor não correspondeu.")
                    # Tenta extrair via HTML bruto
                    print("\n🔧 Tentando extração alternativa...")
                    with open("debug_card_structure.html", "w", encoding="utf-8") as f:
                        f.write(content)
                    print("💾 HTML salvo em: debug_card_structure.html")
                else:
                    print("⚠️ A página não parece conter anúncios ativos.")
                context.close()
                return

            total = cards.count()
            print(f"✅ Total de cards usados: {total}")
            
            # Debug: salva HTML dos cards
            if total > 0:
                try:
                    first_card_html = cards.nth(0).inner_html()
                    print(f"\n🔍 Estrutura do primeiro card (primeiros 500 chars):")
                    print(first_card_html[:500])
                    print("...")
                except Exception as e:
                    print(f"⚠️ Erro ao inspecionar card: {e}")

            for i in range(min(total, 15)):
                try:
                    card = cards.nth(i)
                    
                    # Estratégia 1: Procura por h2 para título
                    titulo = None
                    if card.locator("h2").count() > 0:
                        titulo = card.locator("h2").inner_text().strip()
                    else:
                        # Estratégia 2: Procura por qualquer texto dentro do card
                        try:
                            titulo = card.inner_text().split('\n')[0][:100]
                        except:
                            titulo = f"Moto #{i+1}"

                    # Estratégia para preço
                    preco = None
                    try:
                        if card.locator("strong").count() > 1:
                            preco = card.locator("strong").nth(1).inner_text().strip()
                        elif card.locator("strong").count() > 0:
                            preco = card.locator("strong").first.inner_text().strip()
                    except:
                        pass
                    
                    if not preco:
                        # Procura por R$ no texto
                        text = card.inner_text()
                        if "R$" in text:
                            import re as re_module
                            match = re_module.search(r'R\$[\s\d.,]+', text)
                            if match:
                                preco = match.group(0)
                    
                    if not preco:
                        preco = "Consultar"

                    # Estratégia para link
                    link = None
                    try:
                        if card.locator("a").count() > 0:
                            link = card.locator("a").first.get_attribute("href")
                    except:
                        pass
                    
                    if not link:
                        print(f"⚠️ Card {i}: sem link encontrado, pulando...")
                        continue
                    
                    if link and not link.startswith("http"):
                        link = "https://www.webmotors.com.br" + link

                    # Estratégia para imagem
                    image_url = None
                    try:
                        if card.locator("img").count() > 0:
                            image_url = card.locator("img").first.get_attribute("src")
                            if not image_url:
                                image_url = card.locator("img").first.get_attribute("data-src")
                            if not image_url:
                                image_url = card.locator("img").first.get_attribute("data-original")
                            if image_url and image_url.startswith("//"):
                                image_url = "https:" + image_url
                    except:
                        pass

                    if link and link not in vistos:
                        print(f"✨ NOVA MOTO: {titulo}")
                        print(f"   Preço: {preco}")
                        print(f"   Link: {link[:80]}...")
                        caption = (
                            f"🏍️ WEBMOTORS: NOVIDADE!\n\n"
                            f"🔥 {titulo}\n"
                            f"💰 Preço: {preco}\n"
                            f"🔗 {link}"
                        )

                        if image_url:
                            try:
                                enviar_telegram_foto(image_url, caption)
                            except Exception as e:
                                print(f"   ⚠️ Erro ao enviar foto: {e}")
                                enviar_telegram(caption)
                        else:
                            enviar_telegram(caption)

                        vistos.append(link)
                        novos_encontrados += 1
                        time.sleep(1)
                except Exception as e:
                    print(f"⚠️ Erro ao processar card {i}: {e}")
                    continue

            with open(ARQUIVO_MEMORIA_WM, "w", encoding="utf-8") as f:
                json.dump(vistos[-500:], f, indent=4)

        except Exception as e:
            print(f"❌ Erro: {e}")
        finally:
            context.close()

if __name__ == "__main__":
    if os.path.exists(ARQUIVO_MEMORIA_WM):
        os.remove(ARQUIVO_MEMORIA_WM)

    while True:
        buscar_webmotors()
        print(f"\n⏳ Próxima checagem em 10 minutos...")
        time.sleep(600)