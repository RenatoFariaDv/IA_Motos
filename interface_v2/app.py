# interface_v2/app.py
# Painel web para IA_Motos - Nova interface v2
import os
import json
from flask import Flask, render_template, send_from_directory, request, make_response, abort, url_for
from datetime import datetime

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../interface/anuncios_encontrados.json"))

def load_json():
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Formato inválido: esperado uma lista de anúncios.")
        return data, None
    except Exception as e:
        return None, str(e)

def parse_data_hora(valor):
    """Converte string dd/mm/aaaa HH:MM:SS para datetime. Retorna datetime.min se falhar."""
    try:
        return datetime.strptime(valor, "%d/%m/%Y %H:%M:%S")
    except Exception:
        return datetime.min

def filter_and_sort(anuncios, search=None):
    olx_anuncios = [a for a in anuncios if a.get("origem") == "OLX"]
    if search:
        olx_anuncios = [a for a in olx_anuncios if search.lower() in (a.get("titulo") or "").lower()]
    olx_anuncios.sort(key=lambda x: parse_data_hora(x.get("data_hora", "")), reverse=True)
    return olx_anuncios

def count_novos_hoje(anuncios):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y")

    return sum(
        1 for a in anuncios
        if a.get("origem") == "OLX"
        and a.get("data_hora", "").startswith(hoje)
    )

def get_last_update():
    try:
        ts = os.path.getmtime(JSON_PATH)
        from datetime import datetime, timedelta
        return (
            datetime.fromtimestamp(ts) - timedelta(hours=3)
        ).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "N/A"

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/")
def index():
    search = request.args.get("q", "").strip()
    anuncios, error = load_json()

    if error:
        return render_template(
            "index.html",
            error=error,
            total_geral=0,
            total_olx=0,
            novos_hoje=0,
            ultimo_anuncio="N/A",
            ultima_atualizacao=get_last_update(),
            anuncios=[],
            search=search
        )

    total_geral = len(anuncios)
    olx_anuncios = filter_and_sort(anuncios, search)
    total_olx = len([a for a in anuncios if a.get("origem") == "OLX"])
    novos_hoje = count_novos_hoje(anuncios)
    ultimo_anuncio = olx_anuncios[0].get("data_hora", "N/A") if olx_anuncios else "N/A"

    return render_template(
        "index.html",
        error=None,
        total_geral=total_geral,
        total_olx=total_olx,
        novos_hoje=novos_hoje,
        ultimo_anuncio=ultimo_anuncio,
        ultima_atualizacao=get_last_update(),
        anuncios=olx_anuncios,
        search=search
    )

@app.route("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
