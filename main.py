import json
import os
import time
import re
import requests
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from config_ml import mercado_livre_ativo
from buscar_motos_ml import buscar_motos_ml

load_dotenv()

TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
ID_RAFA = os.getenv("ID_RAFA")
ID_KAROL = os.getenv("ID_KAROL")

if not TOKEN_TELEGRAM:
    raise ValueError("❌ ERRO: TOKEN_TELEGRAM não configurado no .env!")
if not ID_RAFA:
    raise ValueError("❌ ERRO: ID_RAFA não configurado no .env!")
if not ID_KAROL:
    raise ValueError("❌ ERRO: ID_KAROL não configurado no .env!")

NOMES_TELEGRAM = {
    ID_RAFA: "Rafa",
    ID_KAROL: "Karol",
}

DESTINATARIOS_PADRAO = [id_ for id_ in [ID_RAFA, ID_KAROL] if id_]

if not DESTINATARIOS_PADRAO:
    raise ValueError("❌ ERRO: Nenhum destinatário configurado no .env!")

BASE_DIR = os.path.dirname(__file__)
ARQUIVO_MEMORIA = os.path.join(BASE_DIR, "anuncios_vistos.json")
ARQUIVO_FILTROS = os.path.join(BASE_DIR, "interface", "filtros.json")
ARQUIVO_ANUNCIOS = os.path.join(BASE_DIR, "interface", "anuncios_encontrados.json")
URL_OLX = "https://www.olx.com.br/autos-e-pecas/motos/estado-sp/sao-paulo-e-regiao"
MAX_PAGINAS_OLX = 3


def montar_url_olx(pagina: int) -> str:
    if pagina == 1:
        return URL_OLX
    return f"{URL_OLX}?o={pagina}"


INTERVALO_SEGUNDOS = 300
MAX_ANUNCIOS_ANALISAR = 25
MAX_NOVIDADES_POR_RODADA = 999
ENVIAR_APENAS_COMPATIVEIS = False
MAX_VISTOS_SALVOS = 500


def escapar_markdown(texto: str) -> str:
    if not texto:
        return ""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', texto)


def normalizar_url(url: str) -> str:
    if not url:
        return ""
    return url.split("?")[0].strip()


def enviar_telegram(mensagem: str, destinatarios: list = None) -> bool:
    """Envia mensagem para destinatários específicos ou padrão."""
    if destinatarios is None:
        destinatarios = DESTINATARIOS_PADRAO

    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    sucesso_total = True

    for chat_id in destinatarios:
        nome_destino = NOMES_TELEGRAM.get(chat_id, chat_id)
        payload = {
            "chat_id": chat_id,
            "text": mensagem,
            "parse_mode": "Markdown"
        }

        try:
            response = requests.post(url, data=payload, timeout=15)
            response.raise_for_status()
            print(f"✅ Mensagem enviada para {nome_destino}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Falha ao enviar para {nome_destino}: {e}")
            sucesso_total = False

    return sucesso_total


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


def garantir_arquivo_anuncios() -> None:
    """Cria o arquivo de anúncios encontrados se não existir."""
    if not os.path.exists(ARQUIVO_ANUNCIOS):
        os.makedirs(os.path.dirname(ARQUIVO_ANUNCIOS), exist_ok=True)
        with open(ARQUIVO_ANUNCIOS, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def carregar_anuncios() -> list:
    """Carrega o histórico de anúncios encontrados do painel."""
    garantir_arquivo_anuncios()
    try:
        with open(ARQUIVO_ANUNCIOS, "r", encoding="utf-8") as f:
            dados = json.load(f)
            return dados if isinstance(dados, list) else []
    except Exception as e:
        print(f"⚠️ Erro ao carregar anúncios encontrados: {e}")
        return []


def salvar_anuncios(anuncios: list) -> None:
    """Salva o histórico de anúncios encontrados no painel."""
    garantir_arquivo_anuncios()
    try:
        with open(ARQUIVO_ANUNCIOS, "w", encoding="utf-8") as f:
            json.dump(anuncios, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Erro ao salvar anúncios encontrados: {e}")


def carregar_filtros() -> list:
    """Carrega os filtros do arquivo filtros.json."""
    if os.path.exists(ARQUIVO_FILTROS):
        try:
            with open(ARQUIVO_FILTROS, "r", encoding="utf-8") as f:
                dados = json.load(f)
                return dados if isinstance(dados, list) else []
        except Exception as e:
            print(f"⚠️ Erro ao carregar filtros: {e}")
            return []
    return []


def extrair_preco_numerico(preco_str: str) -> float:
    """Extrai o valor numérico do preço em formato brasileiro."""
    if not preco_str:
        return 0.0

    texto = preco_str.strip().lower()
    if texto in {"consultar", "sob consulta", "n/a", "não informado"}:
        return 0.0

    # Remove tudo exceto dígitos, vírgulas e pontos
    preco_limpo = re.sub(r'[^\d,\.]', '', texto)

    if ',' in preco_limpo:
        # Formato brasileiro: 15.000,00 ou 15.000
        preco_limpo = preco_limpo.replace('.', '').replace(',', '.')
    else:
        # Caso apenas pontos: assume separadores de milhar
        if preco_limpo.count('.') > 1:
            preco_limpo = preco_limpo.replace('.', '')

    try:
        return float(preco_limpo)
    except ValueError:
        return 0.0


def extrair_url_srcset(srcset: str) -> str:
    """Extrai a primeira URL válida de um atributo srcset."""
    if not srcset:
        return ""
    partes = [p.strip() for p in srcset.split(',') if p.strip()]
    if not partes:
        return ""
    primeira = partes[0].split()[0]
    return primeira


def validar_url_imagem(url: str) -> str:
    """Normaliza e valida URLs de imagem, ignorando placeholders e base64."""
    if not url:
        return ""
    url = url.strip()
    if not url:
        return ""
    origem = url.lower()
    if origem.startswith(('data:', 'blob:', 'javascript:', 'mailto:')):
        return ""
    if any(token in origem for token in ['placeholder', 'spinner', 'blank', 'transparent', 'empty', 'icon', 'logo', 'avatar']):
        return ""
    if url.startswith('//'):
        url = 'https:' + url
    if url.startswith('/'):
        url = 'https://www.olx.com.br' + url
    if not url.lower().startswith(('http://', 'https://')):
        url = 'https://www.olx.com.br/' + url.lstrip('/')
    return url


def extrair_imagem_do_card(card) -> str:
    """Extrai a primeira imagem principal válida de um card OLX."""
    for selector in ['img[src]', 'img']:
        imagens = card.locator(selector)
        total = imagens.count()
        for index in range(total):
            imagem = imagens.nth(index)
            for atributo in ['src', 'data-src', 'srcset']:
                valor = imagem.get_attribute(atributo)
                if not valor:
                    continue
                if atributo == 'srcset':
                    valor = extrair_url_srcset(valor)
                url_valida = validar_url_imagem(valor)
                if url_valida:
                    return url_valida
    return ""


def extrair_cidade_do_card(card) -> str:
    """Tenta extrair a cidade/região do card OLX."""
    seletores = [
        'span[data-testid="adcard-location"]',
        'p[data-testid="adcard-location"]',
        'div[data-testid="adcard-location"]',
        '[data-testid*="location"]',
    ]
    for seletor in seletores:
        elemento = card.locator(seletor)
        if elemento.count() > 0:
            texto = elemento.first.inner_text().strip()
            if texto:
                return texto
    return ""


def anuncio_compativel(anuncio: dict, filtros: list) -> tuple[bool, dict]:
    """
    Verifica se o anúncio é compatível com algum filtro.
    Retorna (compatível, filtro_correspondente)
    """
    titulo = anuncio.get('titulo', '').lower()
    preco_str = anuncio.get('preco', '')
    preco = extrair_preco_numerico(preco_str)

    for filtro in filtros:
        modelo_filtro = filtro.get('modelo', '').lower().strip()
        preco_min = filtro.get('preco_min', '')
        preco_max = filtro.get('preco_max', '')
        cor_filtro = filtro.get('cor', '').lower().strip()

        # Verifica modelo (se especificado)
        if modelo_filtro and modelo_filtro not in titulo:
            continue

        # Verifica preço mínimo
        if preco_min:
            try:
                min_valor = float(preco_min)
                if preco < min_valor:
                    continue
            except ValueError:
                pass  # Ignora se não conseguir converter

        # Verifica preço máximo
        if preco_max:
            try:
                max_valor = float(preco_max)
                if preco > max_valor:
                    continue
            except ValueError:
                pass  # Ignora se não conseguir converter

        # Verifica cor (se especificada e não for "todas")
        if cor_filtro and cor_filtro not in ['todas', 'qualquer', '']:
            # Por enquanto, não temos extração de cor do anúncio
            # Futuramente podemos implementar busca na descrição
            pass

        # Se passou todas as verificações, é compatível
        return True, filtro

    return False, {}


def executar_mercado_livre():
    if not mercado_livre_ativo():
        print("[ML] Mercado Livre desativado")
        return

    try:
        buscar_motos_ml()
    except Exception as e:
        print(f"[ML] Erro: {e}")

def buscar_motos_sp():
    vistos = carregar_vistos()
    filtros = carregar_filtros()
    anuncios_salvos = carregar_anuncios()
    links_salvos = {anuncio.get('link') for anuncio in anuncios_salvos if anuncio.get('link')}
    novos_encontrados = 0
    novos_salvos = 0

    print(f"📋 Carregados {len(filtros)} filtros do painel")
    print(f"📄 Total de páginas OLX para varrer: {MAX_PAGINAS_OLX}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )

        page = context.new_page()

        for pagina_atual in range(1, MAX_PAGINAS_OLX + 1):
            url_pagina = montar_url_olx(pagina_atual)

            print(f"\n🌐 Página OLX {pagina_atual}/{MAX_PAGINAS_OLX}")
            print(f"[{time.strftime('%H:%M:%S')}] 🔗 Acessando {url_pagina}")

            try:
                page.goto(url_pagina, wait_until="domcontentloaded", timeout=60000)
                time.sleep(10)
                page.wait_for_selector("section.olx-adcard", timeout=30000)

                for i in range(6):
                    page.mouse.wheel(0, 1500)
                    time.sleep(3)

                print(f"📄 Página carregada: {page.title()}")

                cards = page.locator("section.olx-adcard")
                total_cards = cards.count()

                print(f"🧾 Total de cards encontrados: {total_cards}")

                if total_cards == 0:
                    print("⚠️ Nenhum anúncio encontrado nesta página.")
                    if pagina_atual < MAX_PAGINAS_OLX:
                        print("⏳ Aguardando 5 segundos antes da próxima página...")
                        time.sleep(5)
                    continue

                limite = min(total_cards, MAX_ANUNCIOS_ANALISAR)

                for i in range(limite):
                    try:
                        card = cards.nth(i)

                        link_elem = card.locator('a[data-testid="adcard-link"]').first
                        titulo_elem = card.locator("h2").first
                        preco_elem = card.locator("h3").first

                        href = normalizar_url(link_elem.get_attribute("href"))
                        titulo = titulo_elem.inner_text().strip()
                        preco = preco_elem.inner_text().strip() if preco_elem.count() > 0 else "Consultar"

                        if not href or not titulo or len(titulo) < 5:
                            continue

                        if href in vistos:
                            print(f"♻️ Anúncio repetido ignorado: {titulo[:50]}...")
                            continue

                        print(f"🆕 Anúncio novo encontrado: {titulo[:50]}...")

                        imagem = extrair_imagem_do_card(card)
                        cidade = extrair_cidade_do_card(card)

                        if imagem:
                            print(f"🖼️ Extraída imagem: {imagem}")
                        else:
                            print(f"⚠️ Não foi possível extrair imagem para: {titulo} | {href}")

                        # Cria dicionário do anúncio
                        anuncio = {
                            'titulo': titulo,
                            'preco': preco,
                            'link': href,
                            'imagem': imagem,
                            'cidade': cidade,
                            'origem': 'OLX',
                            'data_hora': time.strftime('%d/%m/%Y %H:%M:%S'),
                            'filtro_relacionado': ''
                        }

                        # Verifica compatibilidade com filtros
                        compativel, filtro_match = anuncio_compativel(anuncio, filtros)

                        if compativel:
                            anuncio['filtro_relacionado'] = filtro_match.get('nome_filtro', '')
                            telegram_destino = filtro_match.get('telegram_destino', '')
                            nome_filtro = filtro_match.get('nome_filtro', 'Desconhecido')
                            print(f"[✓] {titulo[:50]}... - Compatível com filtro '{nome_filtro}'")
                        else:
                            anuncio['filtro_relacionado'] = 'Todos'
                            telegram_destino = ''
                            print(f"[~] {titulo[:50]}... - Sem filtro específico")

                            if ENVIAR_APENAS_COMPATIVEIS:
                                print(f"[✗] {titulo[:50]}... - Ignorado (ENVIAR_APENAS_COMPATIVEIS=True)")
                                continue

                        # Prepara mensagem com dados do anúncio
                        mensagem = (
                            f"🏍️ *NOVA MOTO NO RADAR!*\n\n"
                            f"🔥 *{escapar_markdown(titulo)}*\n"
                            f"💰 Preço: {escapar_markdown(preco)}\n\n"
                            f"🔗 [VER ANÚNCIO NA OLX]({href})"
                        )

                        # Define destinatários do Telegram
                        if telegram_destino:
                            destino_envio = [telegram_destino]
                        else:
                            destino_envio = DESTINATARIOS_PADRAO

                        # Envia para o Telegram
                        if enviar_telegram(mensagem, destino_envio):
                            print(f"📤 Enviado ao Telegram: {destino_envio}")
                            vistos.append(href)
                            novos_encontrados += 1
                            time.sleep(1)
                        else:
                            print(f"[✗] Falha ao enviar para Telegram")

                        # Salva no painel se ainda não estiver salvo
                        if href not in links_salvos:
                            anuncios_salvos.append(anuncio)
                            links_salvos.add(href)
                            novos_salvos += 1
                            print(f"💾 Salvo no painel: {titulo[:50]}...")

                        if novos_encontrados >= MAX_NOVIDADES_POR_RODADA:
                            print(f"🏁 Atingido limite de {MAX_NOVIDADES_POR_RODADA} novidades. Parando...")
                            break

                    except Exception as e:
                        print(f"⚠️ Erro ao processar card {i}: {e}")
                        continue

                if novos_encontrados >= MAX_NOVIDADES_POR_RODADA:
                    break

            except Exception as e:
                print(f"❌ Erro na página {pagina_atual}/{MAX_PAGINAS_OLX}: {e}")

            if pagina_atual < MAX_PAGINAS_OLX and novos_encontrados < MAX_NOVIDADES_POR_RODADA:
                print("⏳ Aguardando 5 segundos antes da próxima página...")
                time.sleep(5)

    # Após processar todas as páginas
    if novos_salvos > 0:
        salvar_anuncios(anuncios_salvos)
        print(f"💾 {novos_salvos} novos anúncios salvos no histórico")

    if novos_encontrados > 0:
        salvar_vistos(vistos)
        print(f"✅ {novos_encontrados} novos anúncios enviados!")
    else:
        print("😴 Nenhuma moto nova encontrada agora.")


if __name__ == "__main__":
    print("🚀 SISTEMA DE PROSPECÇÃO INICIADO")

    while True:
        buscar_motos_sp()
        executar_mercado_livre()
        print(f"⏳ Aguardando {INTERVALO_SEGUNDOS // 60} minutos para a próxima rodada...")
        time.sleep(INTERVALO_SEGUNDOS)
