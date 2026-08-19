import customtkinter as ctk
from ui import theme


def _numero_inteiro(valor):
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return 0


def gerar_texto_insight(metricas):
    total_analises = _numero_inteiro(metricas.get("total_analises", 0))
    score_medio = _numero_inteiro(metricas.get("score_medio", 0))
    confianca_media = _numero_inteiro(metricas.get("confianca_media", 0))
    total_oportunidades = _numero_inteiro(
        metricas.get("total_oportunidades", 0)
    )
    total_excelentes = _numero_inteiro(
        metricas.get("total_excelentes", 0)
    )
    total_boas = _numero_inteiro(metricas.get("total_boas", 0))
    total_descartadas = _numero_inteiro(
        metricas.get("total_descartadas", 0)
    )

    if total_analises == 0:
        return (
            "O Agent Alpha ainda não possui análises registradas. "
            "Execute novas buscas para gerar indicadores e insights."
        )

    if confianca_media >= 80:
        avaliacao_confianca = (
            "O nível de confiança está alto e demonstra boa consistência "
            "nas decisões registradas."
        )
    elif confianca_media >= 60:
        avaliacao_confianca = (
            "O nível de confiança está adequado, mas ainda pode evoluir "
            "com o aumento do histórico de análises."
        )
    else:
        avaliacao_confianca = (
            "O nível de confiança ainda está baixo. É recomendável ampliar "
            "o histórico antes de tomar decisões comerciais importantes."
        )

    if total_oportunidades > total_descartadas:
        avaliacao_cenario = (
            "As oportunidades superam os descartes, indicando um cenário "
            "favorável para prospecção e negociação."
        )
    elif total_oportunidades == total_descartadas:
        avaliacao_cenario = (
            "O cenário está equilibrado entre oportunidades e descartes. "
            "Vale acompanhar novas análises antes de definir uma estratégia."
        )
    else:
        avaliacao_cenario = (
            "Os descartes superam as oportunidades. Convém revisar os "
            "critérios de busca e priorizar anúncios com melhor potencial."
        )

    return (
        f"O Agent Alpha registrou {total_analises} análises, com score médio "
        f"de {score_medio} e confiança média de {confianca_media}%. "
        f"{avaliacao_confianca} Foram identificadas "
        f"{total_oportunidades} oportunidades comerciais, sendo "
        f"{total_excelentes} excelentes e {total_boas} boas. "
        f"{avaliacao_cenario}"
    )


def criar_painel_insight(master, metricas):
    painel = ctk.CTkFrame(
        master,
        fg_color=theme.COLOR_CARD,
        corner_radius=14,
    )
    painel.pack(
        fill="x",
        pady=(0, 20),
    )

    ctk.CTkLabel(
        painel,
        text="💡 Insight do Agent Alpha",
        font=("Arial", 18, "bold"),
        anchor="w",
    ).pack(
        fill="x",
        padx=20,
        pady=(18, 8),
    )

    ctk.CTkLabel(
        painel,
        text=gerar_texto_insight(metricas),
        font=("Arial", 13),
        anchor="w",
        justify="left",
        wraplength=1180,
    ).pack(
        fill="x",
        padx=20,
        pady=(0, 18),
    )

    return painel
