from integracao_ml_preview import obter_anuncios_ml

def buscar_motos_ml():
    try:
        anuncios = obter_anuncios_ml()
        print("total retornado:", len(anuncios))
        return anuncios
    except Exception as e:
        print("erro:", e)
        return []

if __name__ == "__main__":
    anuncios = buscar_motos_ml()
    if anuncios:
        print("primeiro anúncio:", anuncios[0])
    else:
        print("primeiro anúncio: None")