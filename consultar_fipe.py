import requests
import json
import os
from datetime import datetime

CACHE_PATH = os.path.join("interface", "fipe_motos.json")

def carregar_cache_fipe():
    try:
        if not os.path.exists(CACHE_PATH):
            return {}
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
        return cache
    except Exception:
        return {}

def salvar_cache_fipe(cache):
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar cache FIPE: {e}")

def gerar_chave_fipe(marca, modelo, ano):
    return f"{str(marca).strip().lower()} {str(modelo).strip().lower()} {str(ano).strip()}"

def consultar_fipe_moto(marca, modelo, ano):
    """
    Consulta valor FIPE de uma moto usando a API pública da FIPE, com cache local.
    Args:
        marca (str): Marca da moto (ex: 'Honda')
        modelo (str): Modelo da moto (ex: 'PCX')
        ano (str/int): Ano da moto (ex: '2022' ou 2022)
    Returns:
        dict: conforme especificação do objetivo
    """
    chave = gerar_chave_fipe(marca, modelo, ano)
    cache = carregar_cache_fipe()
    # Verifica se existe no cache e se está no formato correto
    if chave in cache and isinstance(cache[chave], dict) and "valor_fipe" in cache[chave]:
        resultado = dict(cache[chave])  # cópia para não alterar o cache original
        resultado["fonte"] = "cache local"
        resultado["encontrado"] = True
        return resultado

    # Se não existe ou está no formato antigo, consulta API
    try:
        # 1. Buscar lista de marcas de motos
        url_marcas = "https://parallelum.com.br/fipe/api/v1/motos/marcas"
        resp_marcas = requests.get(url_marcas, timeout=10)
        if resp_marcas.status_code != 200:
            return {"encontrado": False, "erro": "Falha ao consultar marcas FIPE"}
        marcas = resp_marcas.json()
        marca_id = None
        for m in marcas:
            if m["nome"].lower() == marca.lower():
                marca_id = m["codigo"]
                break
        if not marca_id:
            return {"encontrado": False, "erro": f"Marca '{marca}' não encontrada na FIPE"}

        # 2. Buscar modelos da marca
        url_modelos = f"https://parallelum.com.br/fipe/api/v1/motos/marcas/{marca_id}/modelos"
        resp_modelos = requests.get(url_modelos, timeout=10)
        if resp_modelos.status_code != 200:
            return {"encontrado": False, "erro": "Falha ao consultar modelos FIPE"}
        modelos = resp_modelos.json().get("modelos", [])
        modelo_id = None
        for mod in modelos:
            if modelo.lower() in mod["nome"].lower():
                modelo_id = mod["codigo"]
                break
        if not modelo_id:
            return {"encontrado": False, "erro": f"Modelo '{modelo}' não encontrado para marca '{marca}'"}

        # 3. Buscar anos disponíveis para o modelo
        url_anos = f"https://parallelum.com.br/fipe/api/v1/motos/marcas/{marca_id}/modelos/{modelo_id}/anos"
        resp_anos = requests.get(url_anos, timeout=10)
        if resp_anos.status_code != 200:
            return {"encontrado": False, "erro": "Falha ao consultar anos FIPE"}
        anos = resp_anos.json()
        ano_id = None
        ano_str = str(ano)
        for a in anos:
            if ano_str in a["nome"]:
                ano_id = a["codigo"]
                break
        if not ano_id:
            return {"encontrado": False, "erro": f"Ano '{ano}' não encontrado para modelo '{modelo}'"}

        # 4. Buscar valor FIPE
        url_valor = f"https://parallelum.com.br/fipe/api/v1/motos/marcas/{marca_id}/modelos/{modelo_id}/anos/{ano_id}"
        resp_valor = requests.get(url_valor, timeout=10)
        if resp_valor.status_code != 200:
            return {"encontrado": False, "erro": "Falha ao consultar valor FIPE"}
        dados = resp_valor.json()
        valor = dados.get("Valor")
        if not valor:
            return {"encontrado": False, "erro": "Valor FIPE não encontrado"}

        # Extrai valor numérico
        def valor_fipe_para_int(valor):
            if not isinstance(valor, str):
                return int(valor)
            valor = valor.replace("R$", "").replace(" ", "").replace(".", "").replace(",00", "")
            return int(valor)
        valor_numerico = valor_fipe_para_int(valor)

        resultado = {
            "encontrado": True,
            "marca": marca,
            "modelo": modelo,
            "ano": ano,
            "valor_fipe": valor_numerico,
            "fonte": "API publica Parallelum/FIPE",
            "ultima_atualizacao": datetime.now().strftime("%Y-%m-%d")
        }
        # Salva no cache no novo formato
        cache[chave] = {
            "valor_fipe": valor_numerico,
            "fonte": "API publica Parallelum/FIPE",
            "ultima_atualizacao": datetime.now().strftime("%Y-%m-%d")
        }
        salvar_cache_fipe(cache)
        return resultado
    except Exception as e:
        return {"encontrado": False, "erro": f"Erro inesperado: {str(e)}"}

# Teste ao final do arquivo
if __name__ == "__main__":
    print("Primeira consulta (deve consultar API):")
    resultado1 = consultar_fipe_moto("Honda", "PCX", 2022)
    print("consulta API")
    print(resultado1)
    print("\nSegunda consulta (deve usar cache):")
    resultado2 = consultar_fipe_moto("Honda", "PCX", 2022)
    print("consulta cache")
    print(resultado2)
    # Teste final: mostrar valor_fipe esperado
    print("\nTeste final: Honda PCX 2022 deve ter valor_fipe 16963")
    if resultado2.get("valor_fipe") == 16963:
        print("OK: valor_fipe correto (16963)")
    else:
        print(f"ERRO: valor_fipe retornado = {resultado2.get('valor_fipe')}")
