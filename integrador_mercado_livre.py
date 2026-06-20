from mercado_livre_playwright_stealth import buscar_mercado_livre

def obter_anuncios_mercado_livre():
    try:
        anuncios = buscar_mercado_livre()
        return anuncios
    except Exception as e:
        print(f"Erro ao obter anúncios do Mercado Livre: {e}")
        return []

if __name__ == "__main__":
    anuncios = obter_anuncios_mercado_livre()
    print("Arquivo criado: Sim")
    print("total retornado:", len(anuncios))
    if anuncios:
        print("primeiro anúncio encontrado:", anuncios[0])
    else:
        print("primeiro anúncio encontrado: Nenhum")