import re

def extrair_preco(valor):
    """
    Extrai o preço de uma string ou número.
    Exemplos válidos: "R$ 18.500", "18500", "18.500", "R$18.500"
    Retorna int ou None.
    """
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return int(valor)
    if isinstance(valor, str):
        # Remove R$, espaços, pontos separadores de milhar, etc.
        s = valor.lower().replace("r$", "").replace(" ", "").replace(".", "").replace(",", "")
        # Busca por números
        match = re.search(r"\d{4,}", s)
        if match:
            try:
                return int(match.group())
            except Exception:
                return None
    return None

def extrair_ano(anuncio):
    """
    Extrai o ano de um anúncio.
    Procura em campos 'ano', 'titulo', 'descricao'.
    Retorna int ou None.
    """
    # 1. Se já vier como campo numérico
    ano = anuncio.get("ano")
    if isinstance(ano, int) and 1980 <= ano <= 2100:
        return ano
    # 2. Procurar em campos de texto
    for campo in ["titulo", "descricao", "nome", "modelo"]:
        texto = anuncio.get(campo)
        if texto and isinstance(texto, str):
            # Busca por ano entre 1980 e 2100
            match = re.search(r"\b(19[8-9]\d|20\d{2}|2100)\b", texto)
            if match:
                return int(match.group(1))
    return None

def extrair_km(anuncio):
    """
    Extrai a quilometragem de um anúncio.
    Procura em campos 'km', 'descricao', 'titulo', etc.
    Aceita formatos como "21 mil km", "21000 km", "18.500 km".
    Retorna int ou None.
    """
    # 1. Se já vier como campo numérico
    km = anuncio.get("km")
    if isinstance(km, (int, float)):
        return int(km)
    # 2. Procurar em campos de texto
    for campo in ["descricao", "titulo", "nome", "modelo"]:
        texto = anuncio.get(campo)
        if texto and isinstance(texto, str):
            # Busca por "21 mil km", "21000 km", "18500", "18.500 km"
            # 1. "mil" (ex: "21 mil km")
            match_mil = re.search(r"(\d{1,3})\s*mil\s*km", texto.lower())
            if match_mil:
                return int(match_mil.group(1)) * 1000
            # 2. "18500 km", "21000km", "18.500 km"
            match_num = re.search(r"(\d{2,3}\.?\d{3}|\d{4,6})\s*km", texto.lower())
            if match_num:
                s = match_num.group(1).replace(".", "")
                try:
                    return int(s)
                except Exception:
                    continue
            # 3. Só número solto (ex: "km: 18500")
            match_solto = re.search(r"km[:\s]*([\d\.]+)", texto.lower())
            if match_solto:
                s = match_solto.group(1).replace(".", "")
                try:
                    return int(s)
                except Exception:
                    continue
    return None

def calcular_score(anuncio):
    """
    Calcula o score de oportunidade de um anúncio de moto.

    Parâmetros:
        anuncio (dict): Dicionário com informações do anúncio.

    Retorna:
        dict: {
            "score": int,
            "categoria": str ("ALTA", "MEDIA" ou "BAIXA"),
            "preco_detectado": int ou None,
            "ano_detectado": int ou None,
            "km_detectado": int ou None
        }
    """
    score = 50

    # PREÇO
    preco_detectado = extrair_preco(anuncio.get("preco") or anuncio.get("preco_str") or anuncio.get("titulo") or anuncio.get("descricao"))
    if preco_detectado is not None:
        if 5000 <= preco_detectado <= 18000:
            score += 20
        elif 18001 <= preco_detectado <= 30000:
            score += 10
        elif preco_detectado > 40000:
            score -= 10
    else:
        score -= 15

    # ANO
    ano_detectado = extrair_ano(anuncio)
    if ano_detectado is not None:
        if ano_detectado >= 2023:
            score += 20
        elif 2020 <= ano_detectado <= 2022:
            score += 10
        elif ano_detectado < 2015:
            score -= 10
    else:
        score -= 10

    # KM
    km_detectado = extrair_km(anuncio)
    if km_detectado is not None:
        if km_detectado < 10000:
            score += 20
        elif 10000 <= km_detectado <= 30000:
            score += 10
        elif km_detectado > 80000:
            score -= 15
    else:
        score -= 5

    # ORIGEM
    origem = (anuncio.get("origem") or "").strip().lower()
    if "mercado livre" in origem:
        score += 5
    elif "olx" in origem:
        score += 5

    # Limitar score entre 0 e 100
    score = max(0, min(100, score))

    # Categoria
    if score >= 75:
        categoria = "ALTA"
    elif score >= 50:
        categoria = "MEDIA"
    else:
        categoria = "BAIXA"

    return {
        "score": score,
        "categoria": categoria,
        "preco_detectado": preco_detectado,
        "ano_detectado": ano_detectado,
        "km_detectado": km_detectado
    }
