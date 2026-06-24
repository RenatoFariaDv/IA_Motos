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

    # Construir conjuntos de deduplicação
    ids_existentes = {a.get("id_unico") for a in anuncios_salvos if a.get("id_unico")}
    links_normalizados = {a.get("link", "").split("?")[0].split("#")[0] for a in anuncios_salvos if not a.get("id_unico") and a.get("link")}

    novos_anuncios = []
    duplicados_ignorados = 0

    for a in anuncios:
        id_unico = a.get("id_unico")
        link = a.get("link", "")
        link_normalizado = link.split("?")[0].split("#")[0]

        if id_unico:
            if id_unico in ids_existentes:
                duplicados_ignorados += 1
                continue
            ids_existentes.add(id_unico)
            novos_anuncios.append(a)
        else:
            if link_normalizado in links_normalizados:
                duplicados_ignorados += 1
                continue
            links_normalizados.add(link_normalizado)
            novos_anuncios.append(a)

    if novos_anuncios:
        anuncios_salvos.extend(novos_anuncios)
        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(anuncios_salvos, f, ensure_ascii=False, indent=2)

    print(f"total recebido: {total_recebido}")
    print(f"total novo salvo: {len(novos_anuncios)}")
    print(f"duplicados ignorados: {duplicados_ignorados}")