import json
import os
import time
from playwright.sync_api import sync_playwright

# Nome do arquivo que guarda os anúncios que o robô já viu
ARQUIVO_MEMORIA = "anuncios_vistos.json"

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

def buscar_motos_sp():
    # 1. Carrega a memória de anúncios passados
    vistos = carregar_vistos()

    with sync_playwright() as p:
        # 2. Configuração do Navegador (Usa o Chrome instalado para evitar bloqueios)
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.set_default_timeout(60000)

        url = "https://www.olx.com.br/autos-e-pecas/motos/estado-sp/sao-paulo-e-regiao"
        print(f"🔗 Acessando OLX SP: {url}\n")

        try:
            # 3. Navegação e carregamento completo
            page.goto(url, wait_until="load")
            time.sleep(8)  # Aumentado para garantir carregamento dos anúncios

            # Rola a página para forçar carregamento dinâmico
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            time.sleep(3)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)

            # Tira screenshot para verificar se anúncios carregaram
            page.screenshot(path="debug_final.png")
            print("📸 Screenshot salvo: debug_final.png")

            # 4. Busca específica por cards de anúncios
            # Agora usando o seletor correto baseado na análise do HTML
            cards = page.query_selector_all('section.olx-adcard')
            print(f"🏍️  Anúncios encontrados: {len(cards)}")

            novos_encontrados = 0
            links_encontrados = []

            print(f"\n📊 Total de anúncios candidatos: {len(cards)}\n")

            for i, card in enumerate(cards[:20]):  # Limita para não sobrecarregar
                try:
                    # Extrai informações do anúncio usando os seletores corretos
                    link_elem = card.query_selector('a[data-testid="adcard-link"]')
                    titulo_elem = card.query_selector('h2.olx-adcard__title')
                    preco_elem = card.query_selector('h3.olx-adcard__price')

                    if link_elem and titulo_elem:
                        href = link_elem.get_attribute('href')
                        titulo = titulo_elem.inner_text().strip()

                        # Extrai preço se existir
                        preco = "Preço não disponível"
                        if preco_elem:
                            preco = preco_elem.inner_text().strip()

                        if href and titulo and len(titulo) > 5:
                            links_encontrados.append(href)

                            # Verifica se é anúncio novo
                            if href not in vistos:
                                print(f"✨ NOVIDADE: {titulo[:60]}")
                                print(f"   💰 Preço: {preco}")
                                print(f"   🔗 {href}\n")

                                vistos.append(href)
                                novos_encontrados += 1

                                if novos_encontrados >= 10:
                                    break
                except Exception as e:
                    continue

            # 6. Finalização e Salvamento
            if novos_encontrados > 0:
                salvar_vistos(vistos)
                print(f"✓ {novos_encontrados} novos anúncios adicionados à memória.")
            else:
                print("😴 Nenhuma moto nova encontrada agora.")
                if len(links_encontrados) > 0:
                    print(f"\n📋 DEBUG - {len(links_encontrados)} links de anúncios detectados:")
                    for link in links_encontrados[:5]:
                        print(f"   → {link}")
                else:
                    print("\n⚠️  Nenhum anúncio detectado. Verifique se a página carregou corretamente.")

        except Exception as e:
            print(f"❌ Erro na varredura: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    print("🚀 Teste único do Robô de Prospecção de Motos (CORRIGIDO)\n")
    buscar_motos_sp()