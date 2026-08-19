from agent_decision_history import carregar_decisoes


def converter_numero(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def carregar_metricas_analytics():
    decisoes = [
        item
        for item in carregar_decisoes()
        if isinstance(item, dict)
    ]

    total_analises = len(decisoes)

    scores = [
        converter_numero(item.get("score", 0))
        for item in decisoes
        if converter_numero(item.get("score", 0)) > 0
    ]

    confiancas = [
        converter_numero(item.get("confianca", 0))
        for item in decisoes
        if converter_numero(item.get("confianca", 0)) > 0
    ]

    score_medio = (
        round(sum(scores) / len(scores))
        if scores
        else 0
    )

    confianca_media = (
        round(sum(confiancas) / len(confiancas))
        if confiancas
        else 0
    )

    recomendacoes = [
        str(item.get("recomendacao", "")).strip().upper()
        for item in decisoes
    ]

    total_excelentes = recomendacoes.count("EXCELENTE")
    total_boas = recomendacoes.count("BOA")
    total_regulares = recomendacoes.count("REGULAR")

    total_descartadas = sum(
        1
        for recomendacao in recomendacoes
        if recomendacao in {
            "DESCARTADA",
            "DESCARTAR",
            "DESCARTADO",
        }
    )

    total_oportunidades = total_excelentes + total_boas

    return {
        "decisoes": decisoes,
        "total_analises": total_analises,
        "score_medio": score_medio,
        "confianca_media": confianca_media,
        "total_oportunidades": total_oportunidades,
        "total_excelentes": total_excelentes,
        "total_boas": total_boas,
        "total_regulares": total_regulares,
        "total_descartadas": total_descartadas,
    }
