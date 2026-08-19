import customtkinter as ctk

from ui import theme
from ui.analytics import theme as analytics_theme


def _numero_inteiro(valor):
    try:
        return max(0, int(float(valor)))
    except (TypeError, ValueError):
        return 0


def criar_barra(
    master,
    titulo,
    valor,
    maior,
    cor,
):
    valor = _numero_inteiro(valor)
    maior = _numero_inteiro(maior)

    linha = ctk.CTkFrame(
        master,
        fg_color="transparent",
    )
    linha.pack(
        fill="x",
        pady=7,
    )

    ctk.CTkLabel(
        linha,
        text=titulo,
        width=130,
        anchor="w",
        font=("Arial", 13, "bold"),
        text_color=analytics_theme.COLOR_TEXT,
    ).pack(side="left")

    area_barra = ctk.CTkFrame(
        linha,
        width=analytics_theme.BAR_MAX_WIDTH,
        height=analytics_theme.BAR_HEIGHT,
        fg_color="transparent",
    )
    area_barra.pack(
        side="left",
        padx=(10, 12),
    )
    area_barra.pack_propagate(False)

    if valor > 0 and maior > 0:
        largura = max(
            14,
            int(
                (valor / maior)
                * analytics_theme.BAR_MAX_WIDTH
            ),
        )

        barra = ctk.CTkFrame(
            area_barra,
            width=largura,
            height=analytics_theme.BAR_HEIGHT,
            fg_color=cor,
            corner_radius=10,
        )
        barra.pack(
            side="left",
            fill="y",
        )
        barra.pack_propagate(False)

    ctk.CTkLabel(
        linha,
        text=str(valor),
        width=45,
        anchor="w",
        font=("Arial", 13),
        text_color=analytics_theme.COLOR_TEXT,
    ).pack(side="left")


def criar_grafico_decisoes(master, metricas):
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
        text="Distribuição das Decisões",
        font=("Arial", 18, "bold"),
        anchor="w",
        text_color=analytics_theme.COLOR_TEXT,
    ).pack(
        fill="x",
        padx=20,
        pady=(18, 10),
    )

    dados = [
        (
            "Excelentes",
            metricas.get("total_excelentes", 0),
            analytics_theme.COLOR_EXCELENTE,
        ),
        (
            "Boas",
            metricas.get("total_boas", 0),
            analytics_theme.COLOR_BOA,
        ),
        (
            "Regulares",
            metricas.get("total_regulares", 0),
            analytics_theme.COLOR_REGULAR,
        ),
        (
            "Descartadas",
            metricas.get("total_descartadas", 0),
            analytics_theme.COLOR_DESCARTADA,
        ),
    ]

    dados = [
        (titulo, _numero_inteiro(valor), cor)
        for titulo, valor, cor in dados
    ]

    maior = max(
        (valor for _, valor, _ in dados),
        default=0,
    )

    corpo = ctk.CTkFrame(
        painel,
        fg_color="transparent",
    )
    corpo.pack(
        fill="x",
        padx=20,
        pady=(0, 20),
    )

    for titulo, valor, cor in dados:
        criar_barra(
            corpo,
            titulo,
            valor,
            maior,
            cor,
        )

    return painel
