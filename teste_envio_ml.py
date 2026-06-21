import os
from enviar_telegram_ml import gerar_mensagem_ml
import requests
from dotenv import load_dotenv

load_dotenv()

def enviar_telegram_texto_simples(mensagem):
    token = os.getenv("TOKEN_TELEGRAM")
    chat_id = os.getenv("ID_RAFA")
    if not token or not chat_id:
        print("TOKEN_TELEGRAM ou ID_RAFA não definido nas variáveis de ambiente. Configure no .env.")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            print(f"Erro ao enviar mensagem. Status code: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
    except Exception as e:
        print(f"Exceção ao enviar mensagem: {e}")
        return False

def main():
    mensagem = gerar_mensagem_ml()
    print("Mensagem gerada pelo Mercado Livre:")
    print("-" * 40)
    print(mensagem)
    print("-" * 40)
    confirm = input("Deseja enviar esta mensagem para o Telegram de teste? (s/N): ").strip().lower()
    envio_realizado = False

    if confirm == "s":
        envio_realizado = enviar_telegram_texto_simples(mensagem)
        if envio_realizado:
            print("Mensagem enviada para o Telegram de teste.")
    else:
        print("Envio cancelado pelo usuário.")

    print("\nResumo:")
    print(f"- arquivo alterado: teste_envio_ml.py")
    print(f"- envio realizado: {envio_realizado}")
    print(f"- mensagem utilizada:\n{mensagem}")

if __name__ == "__main__":
    main()
