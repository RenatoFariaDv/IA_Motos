import json
from buscar_motos_ml import buscar_motos_ml

anuncios = buscar_motos_ml()
if not anuncios:
    print("Nenhum anúncio retornado")
else:
    anuncio = anuncios[0]
    mensagem = (
        "NOVA MOTO NO RADAR - MERCADO LIVRE\n"
        f"Título: {anuncio.get('titulo', '')}\n"
        f"Preço: {anuncio.get('preco', '')}\n"
        f"Link: {anuncio.get('link', '')}"
    )
    print(mensagem)