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

    # Envio Telegram integrado
    from dotenv import load_dotenv
    import requests
    import time

    load_dotenv()
    TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
    ID_RAFA = os.getenv("ID_RAFA")
    ID_KAROL = os.getenv("ID_KAROL")
    ID_DAVISON = os.getenv("ID_DAVISON")

    total_enviado_telegram = 0
    falhas_telegram = 0

    def enviar_telegram(chat_id, mensagem):
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": mensagem,
            "disable_notification": False
        }
        try:
            resp = requests.post(url, data=data, timeout=10)
            if resp.status_code == 200 and resp.json().get("ok"):
                return True, None
            else:
                return False, f"Status: {resp.status_code}, Resp: {resp.text}"
        except Exception as e:
            return False, str(e)

    for anuncio in novos_anuncios:
        titulo = anuncio.get("titulo", "Sem título")
        preco = anuncio.get("preco", "Sem preço")
        link = anuncio.get("link", "")
        mensagem = (
            "NOVA MOTO NO RADAR - MERCADO LIVRE\n\n"
            f"Titulo: {titulo}\n"
            f"Preco: {preco}\n"
            f"Link: {link}\n"
        )
        for chat_id in [ID_RAFA, ID_KAROL, ID_DAVISON]:
            if not chat_id:
                continue
            ok, erro = enviar_telegram(chat_id, mensagem)
            if ok:
                print(f"Enviado para {chat_id}")
                total_enviado_telegram += 1
            else:
                print(f"Falha para {chat_id}: {erro}")
                falhas_telegram += 1
            time.sleep(1)

    print(f"total enviado telegram: {total_enviado_telegram}")
    print(f"falhas telegram: {falhas_telegram}")
