"""
Serviços de leitura e processamento de dados usados pelo Dashboard.

Este módulo não possui dependência da interface CustomTkinter.
"""

import json

from core.paths import anuncios_encontrados_path, mission_matches_path


def obter_ultima_execucao():
    """
    Retorna a data e hora do an?ncio mais recente.
    """
    anuncios = carregar_ultimos_anuncios(limite=1)

    if not anuncios:
        return "Nunca"

    data_hora = str(
        anuncios[0].get(
            "data_hora",
            "",
        )
    ).strip()

    return data_hora or "Nunca"

def carregar_ultimos_anuncios(limite=5):
    """
    Retorna os an?ncios mais recentes do hist?rico local.
    """
    if not anuncios_encontrados_path().exists():
        return []

    try:
        with anuncios_encontrados_path().open(
            "r",
            encoding="utf-8-sig",
        ) as arquivo_json:
            anuncios = json.load(arquivo_json)

    except (OSError, json.JSONDecodeError) as erro:
        print(
            f"Erro ao carregar an?ncios do dashboard: {erro}"
        )
        return []

    if not isinstance(anuncios, list):
        return []

    anuncios_validos = [
        anuncio
        for anuncio in anuncios
        if isinstance(anuncio, dict)
        and anuncio.get("titulo")
    ]

    return anuncios_validos[-limite:][::-1]

def listar_oportunidades_da_missao(missao_id):
    """
    Retorna uma lista de oportunidades da missão especificada, ordenadas do mais recente para o mais antigo.
    """
    if not mission_matches_path().exists():
        return []
    try:
        with mission_matches_path().open("r", encoding="utf-8-sig") as arquivo_json:
            matches = json.load(arquivo_json)
    except Exception as erro:
        print(f"Erro ao carregar oportunidades: {erro}")
        return []
    if not isinstance(matches, list):
        print("Erro: mission_matches.json não contém uma lista.")
        return []
    oportunidades = [
        match for match in matches
        if isinstance(match, dict) and match.get("missao_id") == missao_id
    ]
    try:
        oportunidades.sort(key=lambda x: x.get("encontrado_em", ""), reverse=True)
    except Exception as erro:
        print(f"Erro ao ordenar oportunidades: {erro}")
    return oportunidades

def contar_oportunidades_excelentes():
    """
    Retorna a quantidade de oportunidades classificadas
    como EXCELENTE no arquivo mission_matches.json.
    """
    if not mission_matches_path().exists():
        return 0

    try:
        with mission_matches_path().open(
            "r",
            encoding="utf-8-sig",
        ) as arquivo_json:
            oportunidades = json.load(arquivo_json)

    except (OSError, json.JSONDecodeError) as erro:
        print(
            "Erro ao contar oportunidades excelentes: "
            f"{erro}"
        )
        return 0

    if not isinstance(oportunidades, list):
        return 0

    return sum(
        1
        for oportunidade in oportunidades
        if isinstance(oportunidade, dict)
        and str(
            oportunidade.get("recomendacao", "")
        ).strip().upper() == "EXCELENTE"
    )

def contar_oportunidades_por_missao() -> dict[int, int]:
    """
    Retorna a quantidade de oportunidades vinculadas a cada miss?o.
    """
    if not mission_matches_path().exists():
        return {}

    try:
        with mission_matches_path().open("r", encoding="utf-8-sig") as arquivo_json:
            matches = json.load(arquivo_json)

    except (OSError, json.JSONDecodeError) as erro:
        print(f"Erro ao carregar oportunidades: {erro}")
        return {}

    if not isinstance(matches, list):
        print("Erro: mission_matches.json n?o cont?m uma lista.")
        return {}

    contagem: dict[int, int] = {}

    for match in matches:
        if not isinstance(match, dict):
            continue

        missao_id = match.get("missao_id")

        if missao_id is None:
            continue

        try:
            missao_id = int(missao_id)
        except (TypeError, ValueError):
            continue

        contagem[missao_id] = contagem.get(missao_id, 0) + 1

    return contagem

def gerar_resumo_missao(missao_id):
    """
    Gera estat?sticas das oportunidades vinculadas a uma miss?o.
    """
    if not mission_matches_path().exists():
        return {}

    try:
        with mission_matches_path().open(
            "r",
            encoding="utf-8-sig",
        ) as arquivo_json:
            oportunidades = json.load(arquivo_json)

    except json.JSONDecodeError as erro:
        print(f"Erro ao ler mission_matches.json: {erro}")
        return {}

    except OSError as erro:
        print(f"Erro ao abrir mission_matches.json: {erro}")
        return {}

    if not isinstance(oportunidades, list):
        print("Erro: mission_matches.json n?o cont?m uma lista.")
        return {}

    try:
        missao_id = int(missao_id)
    except (TypeError, ValueError):
        return {}

    oportunidades_missao = []

    for oportunidade in oportunidades:
        if not isinstance(oportunidade, dict):
            continue

        try:
            oportunidade_missao_id = int(
                oportunidade.get("missao_id")
            )
        except (TypeError, ValueError):
            continue

        if oportunidade_missao_id == missao_id:
            oportunidades_missao.append(oportunidade)

    if not oportunidades_missao:
        return {
            "total": 0,
            "excelentes": 0,
            "boas": 0,
            "regulares": 0,
            "descartadas": 0,
            "melhor_score": 0,
            "melhor_preco": 0.0,
            "preco_medio": 0.0,
        }

    excelentes = 0
    boas = 0
    regulares = 0
    descartadas = 0
    scores = []
    precos = []

    for oportunidade in oportunidades_missao:
        recomendacao = str(
            oportunidade.get("recomendacao", "")
        ).strip().upper()

        if recomendacao == "EXCELENTE":
            excelentes += 1
        elif recomendacao == "BOA":
            boas += 1
        elif recomendacao == "REGULAR":
            regulares += 1
        elif recomendacao == "DESCARTAR":
            descartadas += 1

        try:
            score = int(oportunidade.get("score", 0))
            scores.append(score)
        except (TypeError, ValueError):
            pass

        try:
            preco = float(oportunidade.get("preco", 0))

            if preco > 0:
                precos.append(preco)
        except (TypeError, ValueError):
            pass

    melhor_score = max(scores, default=0)
    melhor_preco = min(precos, default=0.0)

    preco_medio = (
        sum(precos) / len(precos)
        if precos
        else 0.0
    )

    return {
        "total": len(oportunidades_missao),
        "excelentes": excelentes,
        "boas": boas,
        "regulares": regulares,
        "descartadas": descartadas,
        "melhor_score": melhor_score,
        "melhor_preco": melhor_preco,
        "preco_medio": preco_medio,
    }
