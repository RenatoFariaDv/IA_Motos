from buscar_motos_ml import buscar_motos_ml

def main():
    anuncios = buscar_motos_ml()
    print("arquivo criado: processar_ml_isolado.py")
    print("total recebido:", len(anuncios))
    total_processado = 0
    for idx, anuncio in enumerate(anuncios[:5], 1):
        print(f"índice: {idx}")
        print(f"título: {anuncio.get('titulo', '')}")
        print(f"preço: {anuncio.get('preco', '')}")
        print(f"link: {anuncio.get('link', '')}")
        total_processado += 1
    print("total processado:", total_processado)

if __name__ == "__main__":
    main()