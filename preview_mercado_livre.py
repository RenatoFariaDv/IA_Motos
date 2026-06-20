import json
from config_ml import mercado_livre_ativo
from integrador_mercado_livre import obter_anuncios_mercado_livre

def main():
    if not mercado_livre_ativo():
        print("Mercado Livre desativado")
        return

    anuncios = obter_anuncios_mercado_livre()
    with open("preview_mercado_livre.json", "w", encoding="utf-8") as f:
        json.dump(anuncios, f, ensure_ascii=False, indent=2)

    print("total retornado:", len(anuncios))
    if anuncios:
        print("primeiro anúncio:", anuncios[0])
    else:
        print("primeiro anúncio: Nenhum")

if __name__ == "__main__":
    main()