from config_ml import mercado_livre_ativo
from integrador_mercado_livre import obter_anuncios_mercado_livre

def obter_anuncios_ml():
    try:
        if not mercado_livre_ativo():
            return []
        return obter_anuncios_mercado_livre()
    except Exception as e:
        print(e)
        return []

if __name__ == "__main__":
    anuncios = obter_anuncios_ml()
    print("total retornado:", len(anuncios))
    if anuncios:
        print("primeiro anúncio:", anuncios[0])
    else:
        print("primeiro anúncio: None")