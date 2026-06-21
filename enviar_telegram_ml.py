from buscar_motos_ml import buscar_motos_ml

def gerar_mensagem_ml():
    anuncios = buscar_motos_ml()
    if not anuncios:
        return "Nenhum anúncio retornado"
    anuncio = anuncios[0]
    mensagem = (
        "NOVA MOTO NO RADAR - MERCADO LIVRE\n"
        f"Titulo: {anuncio.get('titulo', '')}\n"
        f"Preco: {anuncio.get('preco', '')}\n"
        f"Link: {anuncio.get('link', '')}"
    )
    return mensagem

if __name__ == "__main__":
    mensagem = gerar_mensagem_ml()
    print(mensagem)