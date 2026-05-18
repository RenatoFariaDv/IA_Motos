import re

# Lê um dos HTMLs já salvos e procura por padrões de estrutura
html_files = ["webmotors_page.html", "inspecao_webmotors.html"]

for html_file in html_files:
    try:
        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()
        
        print(f"\n📄 Analisando: {html_file}\n")
        
        # Procura por padrões
        patterns = {
            "CardVehicle": r'class="[^"]*CardVehicle[^"]*"',
            "vehicle-card": r'class="[^"]*vehicle-card[^"]*"',
            "anuncio": r'class="[^"]*anuncio[^"]*"',
            "data-testid": r'data-testid="[^"]*"',
            "data-qa": r'data-qa="[^"]*"',
            "preço/R$": r'R\$[^<]*',
            "moto em href": r'href="[^"]*moto[^"]*"',
        }
        
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                print(f"✅ {pattern_name}: {len(matches)} encontrados")
                # Mostra primeiros 3 únicos
                unique = list(set(matches))[:3]
                for match in unique:
                    print(f"   {match[:80]}")
            else:
                print(f"❌ {pattern_name}: nenhum encontrado")
        
        # Conta tags principais
        divs = len(re.findall(r'<div', html))
        articles = len(re.findall(r'<article', html))
        lis = len(re.findall(r'<li', html))
        
        print(f"\n📊 Contagem:")
        print(f"   DIVs: {divs}")
        print(f"   ARTICLEs: {articles}")
        print(f"   LIs: {lis}")
        
        # Procura pela estrutura genérica
        if '<div' in html:
            # Extrai primeiros divs com classe
            div_classes = re.findall(r'<div[^>]*class="([^"]*)"', html)
            if div_classes:
                print(f"\n🏷️ Primeiras classes de DIV:")
                for cls in div_classes[:10]:
                    print(f"   .{cls}")
                    
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {html_file}")
    except Exception as e:
        print(f"❌ Erro ao processar {html_file}: {e}")
