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
    import os
    import json

    anuncios = buscar_motos_ml()
    total_recebido = len(anuncios)

    # Carregar anúncios já salvos
    caminho_json = os.path.join("interface", "anuncios_encontrados.json")
    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            anuncios_salvos = json.load(f)
    except Exception:
        anuncios_salvos = []

    # Comparar duplicados apenas por link
    links_salvos = set(a.get("link") for a in anuncios_salvos if "link" in a)
    novos_anuncios = [a for a in anuncios if a.get("link") not in links_salvos]

    if novos_anuncios:
        anuncios_salvos.extend(novos_anuncios)
        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(anuncios_salvos, f, ensure_ascii=False, indent=2)

    print(f"total recebido: {total_recebido}")
    print(f"total novo salvo: {len(novos_anuncios)}")
    print(f"duplicados ignorados: {total_recebido - len(novos_anuncios)}")
