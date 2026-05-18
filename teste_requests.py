import time
import requests
from bs4 import BeautifulSoup

def teste_requests():
    print("🌐 TESTANDO COM REQUESTS DIRETO\n")

    url = "https://www.olx.com.br/autos-e-pecas/motos/estado-sp/sao-paulo-e-regiao"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        print(f"📡 Fazendo request para: {url}")
        response = requests.get(url, headers=headers, timeout=30)

        print(f"📊 Status code: {response.status_code}")
        print(f"📏 Tamanho da resposta: {len(response.text)} caracteres\n")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Procura por anúncios na estrutura HTML
            anuncios = soup.find_all('div', {'data-ds-component': 'DS-NewAdCard'})
            print(f"🏍️  Anúncios encontrados (DS-NewAdCard): {len(anuncios)}")

            if len(anuncios) == 0:
                # Tenta outros seletores
                anuncios = soup.find_all('a', href=lambda x: x and 'motos' in x and 'olx.com.br' in x)
                print(f"🔗 Links alternativos: {len(anuncios)}")

                # Mostra alguns exemplos
                if len(anuncios) > 0:
                    print("\n📋 Exemplos encontrados:")
                    for i, anuncio in enumerate(anuncios[:5]):
                        titulo = anuncio.get_text().strip()[:50]
                        link = anuncio.get('href')
                        print(f"   {i+1}. {titulo}...")
                        print(f"      🔗 {link}")

            # Verifica se há preços
            precos = soup.find_all(text=lambda x: x and 'R$' in x)
            print(f"\n💰 Elementos com 'R$': {len(precos)}")

            if len(precos) > 0:
                print("📋 Exemplos de preços:")
                for i, preco in enumerate(precos[:3]):
                    print(f"   {i+1}. {preco.strip()}")

            # Salva HTML para análise
            with open('pagina_requests.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("\n💾 HTML salvo: pagina_requests.html")

        else:
            print(f"❌ Request falhou com status {response.status_code}")

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    teste_requests()