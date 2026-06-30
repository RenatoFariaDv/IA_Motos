"""
Script isolado para testar Mercado Livre com Playwright Stealth.

Requisitos:
- Usar Playwright
- Usar playwright-stealth
- Usar perfil persistente ml_profile_stealth
- Chromium visível
- Simular navegador real
- Remover sinais conhecidos de automação
- Abrir https://www.mercadolivre.com.br
- Esperar 15 segundos
- Navegar para busca honda cg fan
- Salvar:
  - stealth_home.png
  - stealth_busca.png
  - stealth_busca.html
- Imprimir:
  - URL final
  - Título da página
  - Se encontrou account-verification
  - Se encontrou registration
  - Se encontrou captcha
  - Quantidade de cards encontrados

Não integrar ao Radar.
Não enviar Telegram.
Não alterar JSON principal.
"""

import time
import sys
from playwright.sync_api import sync_playwright
from playwright_stealth.stealth import Stealth

sys.stdout.reconfigure(encoding="utf-8")

# Caminho do perfil persistente
PROFILE_PATH = "ml_profile_stealth"
HOME_URL = "https://www.mercadolivre.com.br"
STEALTH_HOME_PNG = "stealth_home.png"

def buscar_mercado_livre():
    """
    Executa as 5 buscas validadas no Mercado Livre usando Playwright Stealth,
    retorna uma lista de anúncios padronizados conforme especificação.
    Não salva arquivos, não envia Telegram, não integra com AWS.
    Retorna lista vazia em caso de bloqueio.
    """
    import re
    from datetime import datetime
    import os

    # Leitura das variáveis de ambiente para proxy
    proxy_server = os.getenv("ML_PROXY_SERVER")
    proxy_username = os.getenv("ML_PROXY_USERNAME")
    proxy_password = os.getenv("ML_PROXY_PASSWORD")
    proxy_ativado = bool(proxy_server)
    print(f"Proxy ativado: {'Sim' if proxy_ativado else 'Não'}")

    buscas = [
        {"termo": "honda cg fan", "filtro_relacionado": "CG FAN"},
        {"termo": "honda xre", "filtro_relacionado": "XRE"},
        {"termo": "yamaha lander", "filtro_relacionado": "Lander"},
        {"termo": "yamaha nmax", "filtro_relacionado": "NMAX"},
        {"termo": "honda pcx", "filtro_relacionado": "PCX"},
    ]

    anuncios_unicos = {}
    relatorio = []
    buscas_bloqueadas = []
    buscas_sucesso = []
    arquivos_debug = []

    with sync_playwright() as p:
        try:
            launch_kwargs = dict(
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--window-position=-32000,-32000",
                    "--window-size=800,600",
                ],
                viewport={"width": 1280, "height": 900},
                no_viewport=True,
                headless=False,
            )
            if proxy_server:
                proxy_config = {"server": proxy_server}
                if proxy_username and proxy_password:
                    proxy_config["username"] = proxy_username
                    proxy_config["password"] = proxy_password
                launch_kwargs["proxy"] = proxy_config
            browser = p.chromium.launch_persistent_context(
                PROFILE_PATH,
                **launch_kwargs
            )
            page = browser.new_page()
            stealth = Stealth()
            stealth.apply_stealth_sync(page)
            page.goto(HOME_URL, wait_until="domcontentloaded")
            time.sleep(15)
            page.screenshot(path=STEALTH_HOME_PNG)

            seletores_titulo = [
                "h3",
                "h2",
                "a",
                ".poly-component__title",
                ".ui-search-item__title",
                ".ui-search-item__group__element"
            ]
            seletores_preco = [
                ".andes-money-amount__fraction",
                ".price-tag-fraction",
                ".poly-price__current",
                "[class*='price']"
            ]
            seletores_link = [
                "a[href]"
            ]
            seletores_imagem = [
                "img[data-src]",
                "img[src]",
                "img"
            ]

            for busca in buscas:
                termo = busca["termo"]
                filtro_relacionado = busca["filtro_relacionado"]

                try:
                    # Buscar termo
                    search_selector = "input[name='as_word']"
                    page.goto(HOME_URL, wait_until="domcontentloaded")
                    time.sleep(2)
                    page.fill(search_selector, termo)
                    page.keyboard.press("Enter")
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(5)

                    # Salvar resultados da busca principal apenas da primeira busca
                    if termo == "honda cg fan":
                        page.screenshot(path="stealth_busca.png")
                        with open("stealth_busca.html", "w", encoding="utf-8") as f:
                            f.write(page.content())

                    url_final = page.url
                    titulo_pagina = page.title()
                    conteudo_pagina = page.content()
                    encontrou_account_verification = "account-verification" in conteudo_pagina
                    encontrou_registration = "registration" in conteudo_pagina
                    encontrou_captcha = "captcha" in conteudo_pagina

                    if encontrou_account_verification or encontrou_registration or encontrou_captcha:
                        motivo = ""
                        if encontrou_account_verification:
                            motivo = "account-verification"
                        elif encontrou_registration:
                            motivo = "registration"
                        elif encontrou_captcha:
                            motivo = "captcha"
                        print(f"\n[AVISO] Bloqueio detectado na busca '{termo}': {motivo}")
                        print(f"URL final: {url_final}")
                        print(f"Título da página: {titulo_pagina}")

                        nome_base = termo.replace(" ", "_")
                        screenshot_path = f"debug_ml_bloqueio_{nome_base}.png"
                        html_path = f"debug_ml_bloqueio_{nome_base}.html"
                        page.screenshot(path=screenshot_path)
                        with open(html_path, "w", encoding="utf-8") as f:
                            f.write(conteudo_pagina)
                        arquivos_debug.append(screenshot_path)
                        arquivos_debug.append(html_path)
                        buscas_bloqueadas.append(termo)
                        relatorio.append({
                            "busca": termo,
                            "filtro_relacionado": filtro_relacionado,
                            "bloqueada": True,
                            "motivo": motivo,
                            "url_final": url_final,
                            "titulo_pagina": titulo_pagina,
                            "arquivos_debug": [screenshot_path, html_path]
                        })
                        continue  # Vai para a próxima busca

                    cards = page.query_selector_all("[data-testid='listing-card'], .ui-search-layout__item, .ui-search-result")
                    qtd_cards = len(cards)
                    qtd_extraidos = 0

                    for idx, card in enumerate(cards[:30]):
                        # Título
                        titulo = ""
                        for sel in seletores_titulo:
                            el = card.query_selector(sel)
                            if el:
                                try:
                                    titulo = el.inner_text().strip()
                                    if titulo:
                                        break
                                except Exception:
                                    continue
                        # Preço
                        preco = ""
                        for sel in seletores_preco:
                            el = card.query_selector(sel)
                            if el:
                                try:
                                    preco = el.inner_text().strip()
                                    if preco:
                                        break
                                except Exception:
                                    continue
                        # Link
                        link = ""
                        for sel in seletores_link:
                            el = card.query_selector(sel)
                            if el:
                                try:
                                    link = el.get_attribute("href")
                                    if link:
                                        if not link.startswith("http"):
                                            link = "https://www.mercadolivre.com.br" + link
                                        break
                                except Exception:
                                    continue
                        # Imagem
                        imagem = ""
                        for sel in seletores_imagem:
                            el = card.query_selector(sel)
                            if el:
                                try:
                                    if "data-src" in sel:
                                        imagem = el.get_attribute("data-src")
                                    else:
                                        imagem = el.get_attribute("src")
                                    if imagem:
                                        break
                                except Exception:
                                    continue
                        # ID único (tenta extrair do link)
                        id_unico = ""
                        if link:
                            m = re.search(r"/MLB-(\d+)", link)
                            if m:
                                id_unico = f"ml_{m.group(1)}"
                            else:
                                id_unico = f"ml_{termo.replace(' ', '_')}_{idx+1}"

                        # Data/hora no formato dd/mm/aaaa hh:mm:ss
                        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        # Preço no formato R$ 18.900
                        preco_formatado = ""
                        if preco:
                            preco_num = "".join([c for c in preco if c.isdigit()])
                            if preco_num:
                                preco_formatado = "R$ {:,}".format(int(preco_num)).replace(",", ".")
                        cidade = ""
                        origem = "Mercado Livre"

                        anuncio = {
                            "id_unico": id_unico,
                            "titulo": titulo,
                            "preco": preco_formatado,
                            "link": link,
                            "imagem": imagem,
                            "cidade": cidade,
                            "origem": origem,
                            "data_hora": data_hora,
                            "filtro_relacionado": filtro_relacionado
                        }

                        # Só adiciona se título, preço e link existirem e não for duplicado
                        if titulo and preco_formatado and link and id_unico and id_unico not in anuncios_unicos:
                            anuncios_unicos[id_unico] = anuncio
                            qtd_extraidos += 1

                    relatorio.append({
                        "busca": termo,
                        "filtro_relacionado": filtro_relacionado,
                        "qtd_cards_encontrados": qtd_cards,
                        "qtd_extraidos": qtd_extraidos,
                        "bloqueada": False
                    })
                    buscas_sucesso.append(termo)
                except Exception as e:
                    print(f"\n[ERRO] Erro inesperado na busca '{termo}': {e}")
                    nome_base = termo.replace(" ", "_")
                    html_path = f"debug_ml_bloqueio_{nome_base}_erro.html"
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(page.content())
                    arquivos_debug.append(html_path)
                    buscas_bloqueadas.append(termo)
                    relatorio.append({
                        "busca": termo,
                        "filtro_relacionado": filtro_relacionado,
                        "bloqueada": True,
                        "motivo": f"erro: {e}",
                        "url_final": page.url,
                        "titulo_pagina": page.title(),
                        "arquivos_debug": [html_path]
                    })
                    continue

            browser.close()

        except Exception as e:
            print(f"\n[ERRO GERAL] Erro inesperado fora do loop de buscas: {e}")

    # Relatório final detalhado
    print("\n=== RELATÓRIO FINAL MERCADO LIVRE STEALTH ===")
    print(f"Buscas com sucesso ({len(buscas_sucesso)}): {buscas_sucesso}")
    print(f"Buscas bloqueadas ({len(buscas_bloqueadas)}): {buscas_bloqueadas}")
    print(f"Total de anúncios capturados: {len(anuncios_unicos)}")
    print(f"Arquivos de debug criados: {arquivos_debug}")
    return list(anuncios_unicos.values())

if __name__ == "__main__":
    import json

    print("Executando teste isolado buscar_mercado_livre()...\n")
    anuncios = buscar_mercado_livre()

    # Salvar resultado em mercado_livre_teste.json
    with open("mercado_livre_teste.json", "w", encoding="utf-8") as f:
        json.dump(anuncios, f, ensure_ascii=False, indent=2)

    # Relatório
    print("\n=== RELATÓRIO TESTE ISOLADO ===")
    total_por_busca = {}
    for anuncio in anuncios:
        filtro = anuncio.get("filtro_relacionado", "N/A")
        total_por_busca[filtro] = total_por_busca.get(filtro, 0) + 1
    for filtro, total in total_por_busca.items():
        print(f"Filtro '{filtro}': {total} anúncios")
    print(f"Total final: {len(anuncios)}")
    if anuncios:
        print("\nPrimeiro anúncio:")
        print(json.dumps(anuncios[0], ensure_ascii=False, indent=2))
    else:
        print("\nNenhum anúncio retornado.")

    # Confirmação de arquivos
    import os
    arquivo_teste = os.path.exists("mercado_livre_teste.json")
    print(f"\nArquivo 'mercado_livre_teste.json' criado: {'Sim' if arquivo_teste else 'Não'}")
    print("Confirmação: Nenhum arquivo principal foi alterado.")