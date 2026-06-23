from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
BASE_DIR = os.path.dirname(__file__)
FILTROS_FILE = os.path.join(BASE_DIR, 'filtros.json')
ANUNCIOS_FILE = os.path.join(BASE_DIR, 'anuncios_encontrados.json')


def garantir_arquivo_filtros():
    """Garante que o arquivo de filtros existe."""
    if not os.path.exists(FILTROS_FILE):
        os.makedirs(os.path.dirname(FILTROS_FILE), exist_ok=True)
        with open(FILTROS_FILE, 'w', encoding='utf-8') as arquivo:
            json.dump([], arquivo, indent=2, ensure_ascii=False)


def garantir_arquivo_anuncios():
    """Garante que o arquivo de anúncios existe."""
    if not os.path.exists(ANUNCIOS_FILE):
        os.makedirs(os.path.dirname(ANUNCIOS_FILE), exist_ok=True)
        with open(ANUNCIOS_FILE, 'w', encoding='utf-8') as arquivo:
            json.dump([], arquivo, indent=2, ensure_ascii=False)


def padronizar_filtro(filtro):
    """Normaliza o filtro para os campos exigidos pelo painel."""
    return {
        'nome_filtro': filtro.get('nome_filtro') or filtro.get('nome', ''),
        'modelo': filtro.get('modelo', ''),
        'cor': filtro.get('cor', ''),
        'preco_min': filtro.get('preco_min') or filtro.get('preco_minimo', ''),
        'preco_max': filtro.get('preco_max') or filtro.get('preco_maximo', ''),
        'telegram_destino': filtro.get('telegram_destino') or filtro.get('telegram', ''),
    }


def carregar_filtros():
    """Lê os filtros do arquivo JSON e retorna uma lista de filtros padronizados."""
    garantir_arquivo_filtros()
    try:
        with open(FILTROS_FILE, 'r', encoding='utf-8') as arquivo:
            filtros = json.load(arquivo)
            return [padronizar_filtro(filtro) for filtro in filtros if isinstance(filtro, dict)]
    except (json.JSONDecodeError, OSError):
        salvar_filtros([])
        return []


def salvar_filtros(filtros):
    """Salva a lista de filtros no arquivo JSON de forma segura."""
    garantir_arquivo_filtros()
    with open(FILTROS_FILE, 'w', encoding='utf-8') as arquivo:
        json.dump(filtros, arquivo, indent=2, ensure_ascii=False)


def carregar_anuncios():
    """Lê os anúncios encontrados do arquivo JSON."""
    garantir_arquivo_anuncios()
    try:
        with open(ANUNCIOS_FILE, 'r', encoding='utf-8') as arquivo:
            dados = json.load(arquivo)
            return dados if isinstance(dados, list) else []
    except (json.JSONDecodeError, OSError):
        salvar_anuncios([])
        return []


def salvar_anuncios(anuncios):
    """Salva os anúncios encontrados no arquivo JSON."""
    garantir_arquivo_anuncios()
    with open(ANUNCIOS_FILE, 'w', encoding='utf-8') as arquivo:
        json.dump(anuncios, arquivo, indent=2, ensure_ascii=False)


def parse_data_hora(valor):
    """Tenta converter uma string data_hora no formato '%d/%m/%Y %H:%M:%S' para datetime.
    Se falhar, retorna datetime.min."""
    try:
        return datetime.strptime(valor, "%d/%m/%Y %H:%M:%S")
    except Exception:
        return datetime.min

def filtrar_anuncios(anuncios, termo: str = '', origem: str = 'all'):
    """Filtra os anúncios por texto e origem."""
    termo = termo.lower().strip()
    origem = origem.lower().strip()
    resultado = []

    for anuncio in anuncios:
        titulo = anuncio.get('titulo', '').lower()
        cidade = anuncio.get('cidade', '').lower()
        origem_anuncio = anuncio.get('origem', '').lower()

        if termo and termo not in titulo and termo not in cidade:
            continue

        # Novo filtro para Mercado Livre
        if origem == 'mercado_livre':
            # Corrigido: só aceita exatamente "Mercado Livre"
            if anuncio.get('origem') != 'Mercado Livre':
                continue
        elif origem != 'all' and origem != origem_anuncio:
            continue

        resultado.append(anuncio)

    return resultado


@app.route('/')
def index():
    """Rota principal do painel, com filtros e anúncios recentes."""
    filtros = carregar_filtros()
    anuncios_todos = carregar_anuncios()

    termo = request.args.get('q', '').strip()
    origem_atual = request.args.get('origem', 'all')

    # Se origem=webmotors, retorna lista vazia (ou poderia redirecionar para OLX)
    if origem_atual == 'webmotors':
        anuncios_filtrados = []
    else:
        anuncios_filtrados = filtrar_anuncios(anuncios_todos, termo, origem_atual)
        anuncios_filtrados.sort(key=lambda a: parse_data_hora(a.get("data_hora")), reverse=True)

    # Separação OLX e Mercado Livre
    if origem_atual == "mercado_livre":
        anuncios_olx = []
        anuncios_ml = [a for a in anuncios_todos if a.get('origem') == 'Mercado Livre']
    elif origem_atual == "olx":
        anuncios_olx = [a for a in anuncios_todos if a.get('origem') == 'OLX']
        anuncios_ml = []
    else:
        anuncios_olx = [a for a in anuncios_todos if a.get('origem') != 'Mercado Livre']
        anuncios_ml = [a for a in anuncios_todos if a.get('origem') == 'Mercado Livre']

    total_olx = len(anuncios_olx)
    total_ml = len(anuncios_ml)
    total_geral = len(anuncios_todos)

    return render_template(
        'index.html',
        filtros=filtros,
        anuncios=anuncios_filtrados,
        anuncios_olx=anuncios_olx,
        anuncios_ml=anuncios_ml,
        total_anuncios=len(anuncios_filtrados),
        search_query=termo,
        origem_atual=origem_atual,
        total_olx=total_olx,
        total_ml=total_ml,
        total_geral=total_geral,
        total_webmotors=0,
        total_combinado=total_olx,
        webmotors_json_path=None,
    )


@app.route('/salvar', methods=['POST'])
def salvar():
    """Rota que recebe o formulário e adiciona um novo filtro."""
    filtros = carregar_filtros()

    novo_filtro = {
        'nome_filtro': request.form.get('nome_filtro', '').strip(),
        'modelo': request.form.get('modelo', '').strip(),
        'cor': request.form.get('cor', '').strip(),
        'preco_min': request.form.get('preco_min', '').strip(),
        'preco_max': request.form.get('preco_max', '').strip(),
        'telegram_destino': request.form.get('telegram_destino', '').strip(),
    }

    filtros.append(novo_filtro)
    salvar_filtros(filtros)

    return redirect(url_for('index'))


@app.route('/excluir/<int:indice>', methods=['POST'])
def excluir(indice):
    """Rota para excluir um filtro existente pelo índice."""
    filtros = carregar_filtros()

    if 0 <= indice < len(filtros):
        filtros.pop(indice)
        salvar_filtros(filtros)

    return redirect(url_for('index'))


@app.route('/api/filtros', methods=['GET'])
def api_filtros():
    """Retorna os filtros cadastrados em formato JSON."""
    filtros = carregar_filtros()
    return jsonify(filtros)


if __name__ == '__main__':
    print('🚀 Iniciando painel Flask em http://127.0.0.1:5000')
    app.run(debug=True, host='127.0.0.1', port=5000)
