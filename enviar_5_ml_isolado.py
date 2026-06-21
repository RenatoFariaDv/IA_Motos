import os
import time
import requests
from dotenv import load_dotenv
from buscar_motos_ml import buscar_motos_ml

def main():
    load_dotenv()
    TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
    ID_RAFA = os.getenv("ID_RAFA")

    if not TOKEN_TELEGRAM or not ID_RAFA:
        print("Erro: TOKEN_TELEGRAM ou ID_RAFA não encontrados no .env")
        return

    try:
        anuncios = buscar_motos_ml()
    except Exception as e:
        print(f"Erro ao buscar anúncios: {e}")
        return

    total_recebido = len(anuncios)
    total_enviado = 0
    falhas = 0

    for anuncio in anuncios[:5]:
        titulo = anuncio.get("titulo") or anuncio.get("title") or ""
        preco = anuncio.get("preco") or anuncio.get("price") or ""
        link = anuncio.get("link") or anuncio.get("url") or ""

        mensagem = (
            "NOVA MOTO NO RADAR - MERCADO LIVRE\n\n"
            f"Titulo: {titulo}\n"
            f"Preco: {preco}\n"
            f"Link: {link}\n"
        )

        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        data = {
            "chat_id": ID_RAFA,
            "text": mensagem
        }

        try:
            resp = requests.post(url, data=data, timeout=10)
            if resp.status_code == 200 and resp.json().get("ok"):
                total_enviado += 1
            else:
                falhas += 1
        except Exception:
            falhas += 1

        time.sleep(1)

    print(f"total recebido: {total_recebido}")
    print(f"total enviado: {total_enviado}")
    print(f"falhas: {falhas}")

if __name__ == "__main__":
    main()