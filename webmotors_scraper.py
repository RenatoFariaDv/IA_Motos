import asyncio
import json
import os
import re
import time
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

load_dotenv()

TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM", "").strip()
ID_DAVISON = os.getenv("ID_DAVISON", "").strip()
ID_RENATO = os.getenv("ID_RENATO", "").strip()
TELEGRAM_IDS = [id_ for id_ in [ID_DAVISON, ID_RENATO] if id_]

BASE_URL = "https://www.webmotors.com.br/motos/sp-sao-paulo"
VISTOS_FILE = "anuncios_webmotors.json"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


def validar_configuracao():
    if not TOKEN_TELEGRAM:
        raise ValueError("TOKEN_TELEGRAM não encontrado no arquivo .env")
    if not TELEGRAM_IDS:
        raise ValueError("ID_DAVISON e/ou ID_RENATO não encontrados no arquivo .env")


def carregar_vistos() -> list:
    if os.path.exists(VISTOS_FILE):
        try:
            with open(VISTOS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ Formato inválido em {VISTOS_FILE}. Criando lista vazia.")
    return []


def salvar_vistos(vistos: list):
    with open(VISTOS_FILE, "w", encoding="utf-8") as f:
        json.dump(vistos, f, ensure_ascii=False, indent=4)


def normalizar_link(link: str) -> str:
    if not link:
        return ""
    link = link.strip()
    if link.startswith("//"):
        link = "https:" + link
    if link.startswith("/"):
        link = urljoin(BASE_URL, link)
    if not link.startswith("http"):
        link = urljoin(BASE_URL, link)
    parsed = urlparse(link)
    return urlunparse(parsed._replace(query="", fragment=""))


def escape_markdown(text: str) -> str:
    escapes = r"_*[]()~`>#+-=|{}.!"
    return re.sub(rf"([{re.escape(escapes)}])", r"\\\1", text)


def enviar_telegram(mensagem: str) -> bool:
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    sucesso_total = True
    for chat_id in TELEGRAM_IDS:
        payload = {
            "chat_id": chat_id,
            "text": mensagem,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
        try:
            response = requests.post(url, data=payload, timeout=15)
            response.raise_for_status()
            print(f"✅ Mensagem entregue ao ID: {chat_id}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Falha ao enviar para {chat_id}: {e}")
            sucesso_total = False
    return sucesso_total


async def extrair_anuncios(page):
    # Extrai anúncios usando elementos de cartão do WebMotors.
    return await page.evaluate(
        """
        () => {
            const cardSelectors = [
                'div.CardVehicle',
                'div[class*="CardVehicle"]',
                'article',
                'div[class*="card"]'
            ];
            const cards = Array.from(document.querySelectorAll(cardSelectors.join(',')));
            const itens = [];
            const vistos = new Set();

            for (const card of cards) {
                const linkEl = card.querySelector('a[href*="/motos/"], a[href*="/comprar/"], a[href*="/moto"]');
                const href = linkEl ? (linkEl.href || linkEl.getAttribute('href')) : '';
                if (!href || href.length < 10) {
                    continue;
                }

                const link = href.split(/[?#]/)[0];
                if (vistos.has(link)) {
                    continue;
                }
                vistos.add(link);

                const titleEl = card.querySelector('h2, h3, h4, strong, [class*="title"], [class*="titulo"], [class*="name"], [class*="nome"]');
                const titulo = titleEl ? titleEl.innerText.trim() : (linkEl ? linkEl.innerText.trim() : 'Anúncio WebMotors');
                if (!titulo || titulo.length < 5) {
                    continue;
                }

                const precoEl = card.querySelector('strong, .price, [class*="price"], [class*="preco"], [class*="valor"]');
                const preco = precoEl ? precoEl.innerText.trim() : 'Consultar';

                const infoEls = Array.from(card.querySelectorAll('li, span, p'))
                    .map(el => el.innerText.trim())
                    .filter(Boolean);
                const info = Array.from(new Set(infoEls)).join(' | ').replace(/\\s+/g, ' ').trim();

                itens.push({ href: link, titulo, preco, info });
            }
            return itens.slice(0, 75);
        }
        """
    )


async def buscar_webmotors(vistos: list) -> int:
    print("🔎 Acessando WebMotors...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                channel="chrome",
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1366, "height": 768}
            )
            page = await context.new_page()
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )
            await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)

            # Role para baixo para carregar os cartões de anúncio dinamicamente.
            for i in range(4):
                await page.mouse.wheel(0, 2000)
                await page.wait_for_timeout(2500)

            html = await page.content()
            if "Access to this page has been denied" in html or "px-captcha" in html or "Pressione e segure" in html:
                print("⚠️ WebMotors está bloqueando o acesso via bot. O navegador foi aberto para permitir a verificação manual.")
                await page.screenshot(path="webmotors_captcha.png")
                print("📸 Captura salva em webmotors_captcha.png")
                print("⏳ Aguarde até 2 minutos e resolva o captcha manualmente no navegador aberto.")
                await page.wait_for_timeout(120000)
                html = await page.content()
                if "Access to this page has been denied" in html or "px-captcha" in html or "Pressione e segure" in html:
                    print("❌ O bloqueio persiste após a espera. O script vai tentar novamente no próximo ciclo.")
                    await context.close()
                    await browser.close()
                    return 0
                print("✅ Bloqueio removido ou captcha resolvido. Continuando a extração de anúncios...")

            anuncios = await extrair_anuncios(page)
            total_cards = len(anuncios)
            print(f"📄 Total de cards candidatos encontrados: {total_cards}")

            novos_encontrados = 0
            for anuncio in anuncios:
                link = normalizar_link(anuncio.get("href", ""))
                titulo = anuncio.get("titulo", "").strip()
                preco = anuncio.get("preco", "Consultar").strip() or "Consultar"
                info = anuncio.get("info", "").strip()

                if not link or not titulo or link in vistos:
                    continue
                if len(titulo) < 10:
                    continue

                mensagem = (
                    f"🏍️ *NOVA MOTO NO RADAR (WebMotors)!*\n\n"
                    f"*{escape_markdown(titulo)}*\n"
                    f"💰 Preço: {escape_markdown(preco)}\n"
                    f"{escape_markdown(info)}\n\n"
                    f"🔗 Ver anúncio:\n{link}\n\n"
                    f"[ABRIR NO WEBMOTORS]({escape_markdown(link)})"
                )

                if enviar_telegram(mensagem):
                    vistos.append(link)
                    novos_encontrados += 1
                    print(f"✨ Novidade detectada: {titulo}")
                    if novos_encontrados >= 10:
                        break

            await context.close()
            await browser.close()

            if novos_encontrados > 0:
                salvar_vistos(vistos)

            return novos_encontrados

    except PlaywrightTimeoutError:
        print("❌ Timeout ao carregar a página do WebMotors.")
    except Exception as e:
        print(f"❌ Erro ao buscar WebMotors: {e}")
    return 0


async def main():
    try:
        validar_configuracao()
    except ValueError as e:
        print(f"❌ {e}")
        return

    vistos = carregar_vistos()
    print("🚀 SISTEMA DE PROSPECÇÃO WEBMOTORS INICIADO")

    while True:
        novos = await buscar_webmotors(vistos)
        if novos == 0:
            print("⏳ Nenhuma moto nova encontrada agora. Aguarde 5 minutos.")
        else:
            print(f"✅ {novos} moto(s) nova(s) enviadas.")
        print("⏳ Aguardando 5 minutos para a próxima rodada...")
        time.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())
