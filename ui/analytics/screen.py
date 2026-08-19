import customtkinter as ctk

from ui import theme
from ui.analytics.cards import criar_grade_kpis
from ui.analytics.insights import criar_painel_insight
from ui.analytics.loader import carregar_metricas_analytics
from ui.analytics.charts import criar_grafico_decisoes
from ui.analytics.ranking import criar_ranking_modelos
from ui.analytics.evolution import criar_grafico_evolucao


def render_agent_analytics(master):
    metricas = carregar_metricas_analytics()

    total_analises = metricas["total_analises"]
    score_medio = metricas["score_medio"]
    confianca_media = metricas["confianca_media"]
    total_oportunidades = metricas["total_oportunidades"]
    total_excelentes = metricas["total_excelentes"]
    total_boas = metricas["total_boas"]
    total_regulares = metricas["total_regulares"]
    total_descartadas = metricas["total_descartadas"]

    container = ctk.CTkScrollableFrame(
        master,
        fg_color="transparent",
        corner_radius=0,
    )
    container.pack(
        fill="both",
        expand=True,
        padx=28,
        pady=24,
    )

    cabecalho = ctk.CTkFrame(
        container,
        fg_color="transparent",
    )
    cabecalho.pack(fill="x", pady=(0, 22))

    ctk.CTkLabel(
        cabecalho,
        text="\U0001f4ca Agent Analytics",
        font=("Arial", 30, "bold"),
        text_color=theme.COLOR_TEXT,
    ).pack(anchor="w")

    ctk.CTkLabel(
        cabecalho,
        text=(
            "Vis\u00e3o estrat\u00e9gica do desempenho do Agent Alpha "
            "e das oportunidades analisadas."
        ),
        font=("Arial", 14),
        text_color=theme.COLOR_TEXT_MUTED,
    ).pack(anchor="w", pady=(5, 0))

    cards_1 = [
        (
            "AN\u00c1LISES",
            str(total_analises),
            "Total de decis\u00f5es registradas pelo Agent Alpha.",
            "\U0001f50d",
        ),
        (
            "SCORE M\u00c9DIO",
            str(score_medio),
            "M\u00e9dia geral dos scores calculados pela intelig\u00eancia.",
            "\U0001f3af",
        ),
        (
            "CONFIAN\u00c7A M\u00c9DIA",
            f"{confianca_media}%",
            (
                "N\u00edvel m\u00e9dio de confian\u00e7a "
                "das decis\u00f5es registradas."
            ),
            "\U0001f9e0",
        ),
        (
            "OPORTUNIDADES",
            str(total_oportunidades),
            "An\u00fancios classificados como boas oportunidades.",
            "\u2705",
        ),
    ]

    criar_grade_kpis(
        container,
        cards_1,
        nome_uniforme="analytics_linha_1",
        pady=(0, 14),
    )

    cards_2 = [
        (
            "EXCELENTES",
            str(total_excelentes),
            "Oportunidades com maior potencial de compra.",
            "\U0001f31f",
        ),
        (
            "BOAS",
            str(total_boas),
            (
                "Oportunidades recomendadas para "
                "negocia\u00e7\u00e3o."
            ),
            "\U0001f44d",
        ),
        (
            "REGULARES",
            str(total_regulares),
            (
                "An\u00fancios que exigem an\u00e1lise "
                "mais cuidadosa."
            ),
            "\U0001f7e1",
        ),
        (
            "DESCARTADAS",
            str(total_descartadas),
            "An\u00fancios sem vantagem comercial suficiente.",
            "\u274c",
        ),
    ]

    criar_grade_kpis(
        container,
        cards_2,
        nome_uniforme="analytics_linha_2",
        pady=(0, 22),
    )

    criar_painel_insight(
        container,
        metricas,
    )

    criar_grafico_decisoes(
        container,
        metricas,
    )

    criar_ranking_modelos(
        container,
        metricas,
    )

    criar_grafico_evolucao(
        container,
        metricas,
    )
