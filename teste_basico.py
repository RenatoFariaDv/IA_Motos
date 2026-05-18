import urllib.request
import urllib.parse
import re
import time

def teste_basico():
    print("🌐 TESTE BÁSICO COM URLLIB\n")

    url = "https://www.olx.com.br/autos-e-pecas/motos/estado-sp/sao-paulo-e-regiao"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
    }

    try:
        print(f"📡 Fazendo request para: {url}")

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8', errors='ignore')

        print(f"📊 Status code: {response.status}")
        print(f"📏 Tamanho da resposta: {len(html)} caracteres\n")

        # Procura por anúncios no HTML
        anuncios_ds = len(re.findall(r'data-ds-component="DS-NewAdCard"', html))
        print(f"🏍️  Anúncios DS-NewAdCard: {anuncios_ds}")

        # Procura por links de motos
        links_motos = re.findall(r'href="([^"]*motos[^"]*olx\.com\.br[^"]*)"', html)
        print(f"🔗 Links de motos encontrados: {len(links_motos)}")

        if len(links_motos) > 0:
            print("\n📋 Exemplos de links:")
            for i, link in enumerate(links_motos[:5]):
                print(f"   {i+1}. {link}")

        # Procura por preços
        precos = re.findall(r'R\$\s*[\d.,]+', html)
        print(f"\n💰 Preços encontrados: {len(precos)}")

        if len(precos) > 0:
            print("📋 Exemplos de preços:")
            for i, preco in enumerate(precos[:5]):
                print(f"   {i+1}. {preco}")

        # Salva HTML para análise
        with open('pagina_urllib.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("\n💾 HTML salvo: pagina_urllib.html")

        # Verifica se há indícios de bloqueio
        if 'captcha' in html.lower() or 'robot' in html.lower() or 'bloqueado' in html.lower():
            print("\n🚫 POSSÍVEL BLOQUEIO DETECTADO!")
        else:
            print("\n✅ Sem indícios óbvios de bloqueio")

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    teste_basico()