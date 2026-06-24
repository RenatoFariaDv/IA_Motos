import json
import os

def normalizar_link(link):
    if not isinstance(link, str):
        return ""
    # Remove tudo após ? ou #
    for sep in ['?', '#']:
        idx = link.find(sep)
        if idx != -1:
            link = link[:idx]
    return link.strip()

def main():
    json_path = os.path.join("interface", "anuncios_encontrados.json")
    with open(json_path, "r", encoding="utf-8") as f:
        anuncios = json.load(f)

    total_original = len(anuncios)
    vistos_id = set()
    vistos_link = set()
    resultado = []
    for anuncio in anuncios:
        id_unico = anuncio.get("id_unico")
        link = anuncio.get("link") or anuncio.get("url") or ""
        link_norm = normalizar_link(link)
        if id_unico:
            if id_unico in vistos_id:
                continue
            vistos_id.add(id_unico)
            resultado.append(anuncio)
        else:
            if not link_norm or link_norm in vistos_link:
                continue
            vistos_link.add(link_norm)
            resultado.append(anuncio)

    total_final = len(resultado)
    total_removido = total_original - total_final

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"total original: {total_original}")
    print(f"total removido: {total_removido}")
    print(f"total final: {total_final}")

if __name__ == "__main__":
    main()