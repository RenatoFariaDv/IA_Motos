import os
from dotenv import load_dotenv
import requests

load_dotenv()
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
ID_RAFA = os.getenv("ID_RAFA")
ID_KAROL = os.getenv("ID_KAROL")
ID_DAVISON = os.getenv("ID_DAVISON")

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
            return True
        else:
            return False
    except Exception:
        return False

if __name__ == "__main__":
    mensagem = (
        "TESTE MERCADO LIVRE\n"
        "Se você recebeu esta mensagem, o envio está funcionando."
    )
    destinatarios = [
        (ID_RAFA, "Rafa"),
        (ID_KAROL, "Karol"),
        (ID_DAVISON, "Davison"),
    ]
    for chat_id, nome in destinatarios:
        if not chat_id:
            continue
        ok = enviar_telegram(chat_id, mensagem)
        if nome == "Davison":
            if ok:
                print(f"Mensagem enviada para Davison ({chat_id}) com sucesso.")
            else:
                print(f"Erro ao enviar mensagem para Davison ({chat_id}).")
        else:
            if ok:
                print(f"Mensagem enviada para {nome} ({chat_id}) com sucesso.")
            else:
                print(f"Falha ao enviar mensagem para {nome} ({chat_id}).")
