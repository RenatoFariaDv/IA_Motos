import customtkinter as ctk

from ui import theme
from ui.analytics import theme as analytics_theme


def _numero(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def _limitar_percentual(valor):
    return max(0.0, min(100.0, _numero(valor)))


def _extrair_series(decisoes):
    series = []

    if not isinstance(decisoes, list):
        return series

    for indice, decisao in enumerate(decisoes, start=1):
        if not isinstance(decisao, dict):
            continue

        score = _limitar_percentual(
            decisao.get("score", 0)
        )

        confianca = _limitar_percentual(
            decisao.get("confianca", 0)
        )

        series.append(
            {
                "indice": indice,
                "score": score,
                "confianca": confianca,
            }
        )

    return series


def _criar_legenda(master):
    legenda = ctk.CTkFrame(
        master,
        fg_color="transparent",
    )
    legenda.pack(
        fill="x",
        padx=20,
        pady=(0, 8),
    )

    itens = [
        (
            "Score",
            analytics_theme.COLOR_EXCELENTE,
        ),
        (
            "Confiança",
            analytics_theme.COLOR_BOA,
        ),
    ]

    for texto, cor in itens:
        item = ctk.CTkFrame(
            legenda,
            fg_color="transparent",
        )
        item.pack(
            side="left",
            padx=(0, 24),
        )

        marcador = ctk.CTkFrame(
            item,
            width=12,
            height=12,
            fg_color=cor,
            corner_radius=6,
        )
        marcador.pack(
            side="left",
            padx=(0, 7),
        )
        marcador.pack_propagate(False)

        ctk.CTkLabel(
            item,
            text=texto,
            font=("Arial", 12, "bold"),
            text_color=analytics_theme.COLOR_TEXT_MUTED,
        ).pack(side="left")


def _criar_linha_analise(
    master,
    indice,
    score,
    confianca,
):
    linha = ctk.CTkFrame(
        master,
        fg_color="transparent",
    )
    linha.pack(
        fill="x",
        pady=6,
    )

    ctk.CTkLabel(
        linha,
        text=f"Análise {indice}",
        width=100,
        anchor="w",
        font=("Arial", 12, "bold"),
        text_color=analytics_theme.COLOR_TEXT,
    ).pack(side="left")

    area_score = ctk.CTkFrame(
        linha,
        width=360,
        height=18,
        fg_color=analytics_theme.COLOR_BAR_BACKGROUND,
        corner_radius=9,
    )
    area_score.pack(
        side="left",
        padx=(8, 12),
    )
    area_score.pack_propagate(False)

    if score > 0:
        largura_score = max(
            8,
            int((score / 100) * 360),
        )

        barra_score = ctk.CTkFrame(
            area_score,
            width=largura_score,
            height=18,
            fg_color=analytics_theme.COLOR_EXCELENTE,
            corner_radius=9,
        )
        barra_score.pack(
            side="left",
            fill="y",
        )
        barra_score.pack_propagate(False)

    ctk.CTkLabel(
        linha,
        text=str(round(score)),
        width=40,
        anchor="w",
        font=("Arial", 12),
        text_color=analytics_theme.COLOR_TEXT,
    ).pack(side="left")

    area_confianca = ctk.CTkFrame(
        linha,
        width=360,
        height=18,
        fg_color=analytics_theme.COLOR_BAR_BACKGROUND,
        corner_radius=9,
    )
    area_confianca.pack(
        side="left",
        padx=(18, 12),
    )
    area_confianca.pack_propagate(False)

    if confianca > 0:
        largura_confianca = max(
            8,
            int((confianca / 100) * 360),
        )

        barra_confianca = ctk.CTkFrame(
            area_confianca,
            width=largura_confianca,
            height=18,
            fg_color=analytics_theme.COLOR_BOA,
            corner_radius=9,
        )
        barra_confianca.pack(
            side="left",
            fill="y",
        )
        barra_confianca.pack_propagate(False)

    ctk.CTkLabel(
        linha,
        text=f"{round(confianca)}%",
        width=50,
        anchor="w",
        font=("Arial", 12),
        text_color=analytics_theme.COLOR_TEXT,
    ).pack(side="left")


def criar_grafico_evolucao(master, metricas):
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
        text="Evolução do Agent Alpha",
        font=("Arial", 18, "bold"),
        anchor="w",
        text_color=analytics_theme.COLOR_TEXT,
    ).pack(
        fill="x",
        padx=20,
        pady=(18, 8),
    )

    ctk.CTkLabel(
        painel,
        text="Comparação do score e da confiança em cada análise registrada.",
        font=("Arial", 12),
        anchor="w",
        text_color=analytics_theme.COLOR_TEXT_MUTED,
    ).pack(
        fill="x",
        padx=20,
        pady=(0, 12),
    )

    _criar_legenda(painel)

    corpo = ctk.CTkFrame(
        painel,
        fg_color="transparent",
    )
    corpo.pack(
        fill="x",
        padx=20,
        pady=(0, 18),
    )

    decisoes = metricas.get("decisoes", [])
    series = _extrair_series(decisoes)

    if not series:
        ctk.CTkLabel(
            corpo,
            text="Ainda não existem análises suficientes para exibir a evolução.",
            anchor="w",
            font=("Arial", 13),
            text_color=analytics_theme.COLOR_TEXT_MUTED,
        ).pack(
            fill="x",
            pady=8,
        )

        return painel

    for item in series[-10:]:
        _criar_linha_analise(
            corpo,
            item["indice"],
            item["score"],
            item["confianca"],
        )

    return painel
