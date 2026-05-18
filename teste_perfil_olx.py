import json
import os
import time
import re
import requests
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# =========================================================
# CONFIGURAÇÕES
# =========================================================
load_dotenv()

TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
ID_DAVISON = os.getenv("ID_DAVISON")
ID_RENATO = os.getenv("ID_RENATO")

if not TOKEN_TELEGRAM or not ID_DAVISON:
    raise ValueError("❌ ERRO: Credenciais não configuradas no .env!")

DESTINATARIOS = [id_ for id_ in [ID_DAVISON, ID_RENATO] if id_]

ARQUIVO_MEMORIA = "anuncios_vistos.json"
URL_OLX = "https://www.olx.com.br/autos-e-pecas/motos/estado-sp/sao-paulo-e-regiao"
INTERVALO_SEGUNDOS = 300
MAX_ANUNCIOS_ANALISAR = 25
MAX_NOVIDADES_POR_RODADA = 10
MAX_VISTOS_SALVOS = 500

# =========================================================
# UTILITÁRIOS
# =========================================================
def escapar_markdown(texto: str) -> str:
    if not texto:
        return ""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', texto)

def normalizar_url(url: str) -> str:
    if not url:
        return ""
    return url.split("?")[0].strip()

# =========================================================
# TELEGRAM
# =========================================================
def enviar_telegram(mensagem: str) -> bool:
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    sucesso_total = True

    for chat_id in DESTINATARIOS:
        payload = {
            "chat_id": chat_id,
            "text": mensagem,
            "parse_mode": "Markdown"
        }

        try:
            response = requests.post(url, data=payload, timeout=15)
            response.raise_for_status()
            print(f"✅ Mensagem entregue ao ID: {chat_id}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Falha ao enviar para {chat_id}: {e}")
            sucesso_total = False

    return sucesso_total

# =========================================================
# MEMÓRIA
# =========================================================
def carregar_vistos() -> list:
    if os.path.exists(ARQUIVO_MEMORIA):
        try:
            with open(ARQUIVO_MEMORIA, "r", encoding="utf-8") as f:
                dados = json.load(f)
                return dados if isinstance(dados, list) else []
        except Exception as e:
            print(f"⚠️ Erro ao carregar memória: {e}")
            return []
    return []

def salvar_vistos(vistos: list) -> None:
    vistos = vistos[-MAX_VISTOS_SALVOS:]
    try:
        with open(ARQUIVO_MEMORIA, "w", encoding="utf-8") as f:
            json.dump(vistos, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Erro ao salvar memória: {e}")

# =========================================================
# SCRAPING OLX
# =========================================================
def buscar_motos_sp():
    vistos = carregar_vistos()
    novos_encontrados = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        print(f"\n[{time.strftime('%H:%M:%S')}] 🔗 Acessando OLX SP...")

        try:
            page.goto(URL_OLX, wait_until="load")
            time.sleep(5)  # Espera inicial

            # Scroll progressivo, simulando comportamento humano
            for i in range(6):  # 6 scrolls, ajustável conforme necessidade
                page.mouse.wheel(0, 1500)  # Scroll para baixo
                time.sleep(3)  # pausa para carregar mais conteúdo

            # Diagnóstico do HTML
            print(f"📄 TÍTULO DA PÁGINA: {page.title()}")
            html = page.content()
            print(f"📦 HTML recebido (primeiros 3000 chars):\n{html[:3000]}\n")

            # Agora tenta localizar os cards
            cards = page.locator('[data-testid="adcard-container"]')
            total_cards = cards.count()

            print(f"🧾 Total de cards encontrados: {total_cards}")

            if total_cards == 0:
                print("⚠️ Nenhum card encontrado. Verifique o HTML acima.")
                return

            limite = min(total_cards, MAX_ANUNCIOS_ANALISAR)

            for i in range(limite):
                try:
                    card = cards.nth(i)

                    link_elem = card.locator('a[data-testid="adcard-link"]').first
                    titulo_elem = card.locator('h2').first
                    preco_elem = card.locator('h3').first

                    href = normalizar_url(link_elem.get_attribute("href"))
                    titulo = titulo_elem.inner_text().strip()
                    preco = preco_elem.inner_text().strip() if preco_elem.count() > 0 else "Consultar"

                    if not href or not titulo or len(titulo) < 5:
                        continue

                    if href in vistos:
                        continue

                    print(f"✨ NOVIDADE DETECTADA: {titulo}")

                    msg = (
                        f"🏍️ *NOVA MOTO NO RADAR!*\n\n"
                        f"🔥 *{escapar_markdown(titulo)}*\n"
                        f"💰 Preço: {escapar_markdown(preco)}\n\n"
                        f"🔗 [VER ANÚNCIO NA OLX]({href})"
                    )

                    if enviar_telegram(msg):
                        vistos.append(href)
                        novos_encontrados += 1
                        time.sleep(1)

                    if novos_encontrados >= MAX_NOVIDADES_POR_RODADA:
                        break

                except Exception as e:
                    print(f"⚠️ Erro ao processar card {i}: {e}")
                    continue

            if novos_encontrados > 0:
                salvar_vistos(vistos)
                print(f"✅ {novos_encontrados} novos anúncios enviados!")
            else:
                print("😴 Nenhuma moto nova encontrada agora.")

        except Exception as e:
            print(f"❌ Erro na varredura: {e}")

        finally:
            browser.close()

# =========================================================
# LOOP PRINCIPAL
# =========================================================
if __name__ == "__main__":
    print("🚀 SISTEMA DE PROSPECÇÃO INICIADO")

    # limpa memória só para teste
    if os.path.exists(ARQUIVO_MEMORIA):
        os.remove(ARQUIVO_MEMORIA)
        print("🧹 Memória limpa para novo teste.")

    while True:
        buscar_motos_sp()
        print(f"⏳ Aguardando {INTERVALO_SEGUNDOS // 60} minutos para a próxima rodada...")
        time.sleep(INTERVALO_SEGUNDOS)