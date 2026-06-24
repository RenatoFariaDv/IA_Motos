from integracao_ml_preview import obter_anuncios_ml

def gerar_chaves_anuncio(anuncio):
    """
    Gera lista de chaves únicas para deduplicação:
    - id:<id_unico>
    - link:<link limpo>
    - titulo_preco:<titulo normalizado>|<preco>
    """
    chaves = []
    id_unico = anuncio.get("id_unico")
    if id_unico and str(id_unico).strip():
        chaves.append("id:" + str(id_unico).strip())
    link = anuncio.get("link", "")
    if link:
        link_limpo = link.split("?")[0].split("#")[0]
        chaves.append("link:" + link_limpo)
    titulo = anuncio.get("titulo", "")
    preco = anuncio.get("preco", "")
    if titulo and preco:
        chaves.append("titulo_preco:" + titulo.lower().strip() + "|" + preco.strip())
    return chaves

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

    # Controle persistente de anúncios já enviados via Telegram (Mercado Livre)
    caminho_ml_enviados = os.path.join("interface", "ml_enviados.json")
    try:
        with open(caminho_ml_enviados, "r", encoding="utf-8") as f:
            ml_enviados = set(json.load(f))
    except Exception:
        ml_enviados = set()

    anuncios = buscar_motos_ml()
    total_recebido = len(anuncios)

    # Carregar anúncios já salvos
    caminho_json = os.path.join("interface", "anuncios_encontrados.json")
    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            anuncios_salvos = json.load(f)
    except Exception:
        anuncios_salvos = []

# Construir conjunto de chaves existentes (todas as chaves de todos os anúncios)
chaves_existentes = set()
for a in anuncios_salvos:
    for chave in gerar_chaves_anuncio(a):
        chaves_existentes.add(chave)

novos_anuncios = []
duplicados_ignorados = 0

for a in anuncios:
    # Forçar origem
    a["origem"] = "Mercado Livre"
    chaves_anuncio = gerar_chaves_anuncio(a)
    if any(chave in chaves_existentes for chave in chaves_anuncio):
        duplicados_ignorados += 1
        continue
    for chave in chaves_anuncio:
        chaves_existentes.add(chave)
    # Garantir campos mínimos
    for campo in ["titulo", "preco", "link", "imagem", "cidade", "data_hora", "filtro_relacionado", "id_unico"]:
        if campo not in a:
            a[campo] = ""
    novos_anuncios.append(a)

# Salvar JSON apenas uma vez
if novos_anuncios:
    anuncios_atualizados = anuncios_salvos + novos_anuncios
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(anuncios_atualizados, f, ensure_ascii=False, indent=2)
    # Reabrir o JSON e imprimir totais
    with open(caminho_json, "r", encoding="utf-8") as f:
        anuncios_apos_salvar = json.load(f)
    total_ml_apos_salvar = sum(1 for a in anuncios_apos_salvar if a.get("origem") == "Mercado Livre")
    print(f"ML no arquivo após salvar: {total_ml_apos_salvar}")
    print(f"TOTAL no arquivo após salvar: {len(anuncios_apos_salvar)}")
else:
    anuncios_atualizados = anuncios_salvos

print(f"total recebido: {total_recebido}")
print(f"total novo salvo: {len(novos_anuncios)}")
# Limite de envio Telegram
MAX_ENVIOS_TELEGRAM_ML = 10

# Filtrar anúncios realmente novos para Telegram (nenhuma chave já enviada)
anuncios_para_telegram = []
anuncios_para_telegram_chaves = []
for a in novos_anuncios:
    chaves_a = gerar_chaves_anuncio(a)
    if any(chave in ml_enviados for chave in chaves_a):
        continue
    anuncios_para_telegram.append(a)
    anuncios_para_telegram_chaves.append(chaves_a)
    if len(anuncios_para_telegram) >= MAX_ENVIOS_TELEGRAM_ML:
        break

print(f"total elegível telegram: {len(anuncios_para_telegram)}")
print(f"duplicados ignorados: {duplicados_ignorados}")

# Envio Telegram integrado
from dotenv import load_dotenv
import requests
import time

# Limite máximo de envios Telegram por rodada já definido acima

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

# Enviar Telegram apenas para anúncios realmente novos e registrar chaves após envio
for idx, anuncio in enumerate(anuncios_para_telegram):
    titulo = anuncio.get("titulo", "Sem título")
    preco = anuncio.get("preco", "Sem preço")
    link = anuncio.get("link", "")
    mensagem = (
        "NOVA MOTO NO RADAR - MERCADO LIVRE\n\n"
        f"Titulo: {titulo}\n"
        f"Preco: {preco}\n"
        f"Link: {link}\n"
    )
    enviado_com_sucesso = False
    for chat_id in [ID_RAFA, ID_KAROL, ID_DAVISON]:
        if not chat_id:
            continue
        ok, erro = enviar_telegram(chat_id, mensagem)
        if ok:
            print(f"Enviado para {chat_id}")
            total_enviado_telegram += 1
            enviado_com_sucesso = True
        else:
            print(f"Falha para {chat_id}: {erro}")
            falhas_telegram += 1
        time.sleep(1)
    # Após envio bem-sucedido para pelo menos um chat, registrar as chaves
    if enviado_com_sucesso:
        for chave in anuncios_para_telegram_chaves[idx]:
            ml_enviados.add(chave)
        # Salvar imediatamente para garantir persistência mesmo se houver erro depois
        try:
            with open(caminho_ml_enviados, "w", encoding="utf-8") as f:
                json.dump(sorted(list(ml_enviados)), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar ml_enviados.json: {e}")

print(f"total enviado telegram: {total_enviado_telegram}")
print(f"falhas telegram: {falhas_telegram}")
