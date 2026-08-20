"""
Serviços de leitura e processamento de dados usados pelo Dashboard.

Este módulo não possui dependência da interface CustomTkinter.
"""

import json

from datetime import datetime

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


# ==========================================================
# OBSERVABILIDADE DO SHADOW MODE (core/financial_scoring.py)
#
# As funcoes abaixo APENAS leem e agregam campos ja persistidos em
# mission_matches.json pelo Opportunity Engine (score_missao,
# classificacao_missao, score_financeiro, classificacao_financeira,
# score_final_experimental, classificacao_final_experimental,
# preco_alvo_negociacao). Nunca recalculam nada e nunca importam
# core.financial_scoring, core.opportunity_scoring, fipe_matching ou
# opportunity_engine -- essa camada e so leitura/agregacao.
# ==========================================================

_ORDEM_CLASSIFICACAO_SHADOW = {
    "DESCARTAR": 0,
    "REGULAR": 1,
    "BOA": 2,
    "EXCELENTE": 3,
}


def comparar_classificacao_shadow(
    classificacao_missao,
    classificacao_experimental,
):
    """
    Compara duas classificacoes JA PERSISTIDAS (nunca recalculadas)
    usando a mesma ordem EXCELENTE > BOA > REGULAR > DESCARTAR.
    Retorna "SUBIU", "MANTEVE", "CAIU" ou "" quando alguma das duas
    classificacoes nao e reconhecida (ex.: ausente).
    """
    rank_missao = _ORDEM_CLASSIFICACAO_SHADOW.get(
        str(classificacao_missao or "").strip().upper()
    )
    rank_experimental = _ORDEM_CLASSIFICACAO_SHADOW.get(
        str(classificacao_experimental or "").strip().upper()
    )

    if rank_missao is None or rank_experimental is None:
        return ""

    if rank_experimental > rank_missao:
        return "SUBIU"

    if rank_experimental < rank_missao:
        return "CAIU"

    return "MANTEVE"


def _data_ordenacao_oportunidade(oportunidade):
    """
    Extrai uma data para ordenacao a partir dos campos ja persistidos
    (encontrado_em/verificado_em em ISO "AAAA-MM-DD HH:MM:SS",
    data_hora em "DD/MM/AAAA HH:MM:SS"). Nunca lanca excecao nem
    altera o dicionario recebido; datas ausentes ou invalidas viram
    datetime.min, o que as empurra para o final da lista quando
    ordenada com reverse=True (mais recentes primeiro).
    """
    candidatos = (
        (oportunidade.get("encontrado_em"), "%Y-%m-%d %H:%M:%S"),
        (oportunidade.get("verificado_em"), "%Y-%m-%d %H:%M:%S"),
        (oportunidade.get("data_hora"), "%d/%m/%Y %H:%M:%S"),
    )

    for valor, formato in candidatos:
        texto = str(valor or "").strip()

        if not texto:
            continue

        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue

    return datetime.min


def listar_todas_oportunidades():
    """
    Retorna todas as oportunidades de mission_matches.json (de
    qualquer missao), ordenadas da mais recente para a mais antiga.
    Usado pela tela de observabilidade do Shadow Mode -- ao contrario
    de listar_oportunidades_da_missao(), nao filtra por missao_id.
    Nunca altera o arquivo (nao corrige datas antigas nem reordena
    o JSON em disco).
    """
    if not mission_matches_path().exists():
        return []

    try:
        with mission_matches_path().open(
            "r",
            encoding="utf-8-sig",
        ) as arquivo_json:
            matches = json.load(arquivo_json)

    except (OSError, json.JSONDecodeError) as erro:
        print(f"Erro ao carregar oportunidades: {erro}")
        return []

    if not isinstance(matches, list):
        print("Erro: mission_matches.json não contém uma lista.")
        return []

    oportunidades = [
        match for match in matches if isinstance(match, dict)
    ]

    try:
        oportunidades.sort(
            key=_data_ordenacao_oportunidade,
            reverse=True,
        )
    except Exception as erro:
        print(f"Erro ao ordenar oportunidades: {erro}")

    return oportunidades


def _numero_ou_none(valor):
    if valor is None:
        return None

    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _media_ou_none(valores):
    validos = [valor for valor in valores if valor is not None]

    if not validos:
        return None

    return sum(validos) / len(validos)


def gerar_metricas_shadow_mode(oportunidades):
    """
    Agrega metricas de observabilidade do Shadow Mode a partir de
    oportunidades JA PERSISTIDAS -- nunca recalcula score_missao,
    score_financeiro ou score_final_experimental (esses valores ja
    existem em cada oportunidade, gravados pelo Opportunity Engine).

    Registros anteriores ao Shadow Mode (sem "score_missao") entram
    em total_sem_shadow, nunca em total_sem_fipe. A media de
    score_financeiro so considera oportunidades em que a FIPE foi
    encontrada (score_financeiro != None).
    """
    oportunidades_validas = [
        item for item in oportunidades if isinstance(item, dict)
    ]

    total_oportunidades = len(oportunidades_validas)
    total_com_shadow = 0
    total_sem_shadow = 0
    total_sem_fipe = 0
    mesma_classificacao = 0
    subiram_classificacao = 0
    cairam_classificacao = 0

    scores_missao = []
    scores_financeiro = []
    scores_final_experimental = []

    for oportunidade in oportunidades_validas:
        tem_shadow = (
            "score_missao" in oportunidade
            and oportunidade.get("score_missao") is not None
        )

        if not tem_shadow:
            total_sem_shadow += 1
            continue

        total_com_shadow += 1

        score_missao = _numero_ou_none(
            oportunidade.get("score_missao")
        )

        if score_missao is not None:
            scores_missao.append(score_missao)

        score_financeiro = _numero_ou_none(
            oportunidade.get("score_financeiro")
        )

        score_final_experimental = _numero_ou_none(
            oportunidade.get("score_final_experimental")
        )

        if score_final_experimental is not None:
            scores_final_experimental.append(
                score_final_experimental
            )

        if score_financeiro is None:
            total_sem_fipe += 1
            continue

        scores_financeiro.append(score_financeiro)

        resultado_comparacao = comparar_classificacao_shadow(
            oportunidade.get("classificacao_missao"),
            oportunidade.get("classificacao_final_experimental"),
        )

        if resultado_comparacao == "MANTEVE":
            mesma_classificacao += 1
        elif resultado_comparacao == "SUBIU":
            subiram_classificacao += 1
        elif resultado_comparacao == "CAIU":
            cairam_classificacao += 1

    return {
        "total_oportunidades": total_oportunidades,
        "total_com_shadow": total_com_shadow,
        "total_sem_shadow": total_sem_shadow,
        "total_sem_fipe": total_sem_fipe,
        "mesma_classificacao": mesma_classificacao,
        "subiram_classificacao": subiram_classificacao,
        "cairam_classificacao": cairam_classificacao,
        "media_score_missao": _media_ou_none(scores_missao),
        "media_score_financeiro": _media_ou_none(
            scores_financeiro
        ),
        "media_score_final_experimental": _media_ou_none(
            scores_final_experimental
        ),
    }
