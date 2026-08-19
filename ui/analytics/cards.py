import customtkinter as ctk

from ui import theme


def criar_card_kpi(
    master,
    titulo,
    valor,
    descricao,
    icone,
):
    card = ctk.CTkFrame(
        master,
        fg_color=theme.COLOR_CARD,
        corner_radius=14,
        border_width=1,
        border_color=theme.COLOR_DIVIDER,
    )

    topo = ctk.CTkFrame(
        card,
        fg_color="transparent",
    )
    topo.pack(
        fill="x",
        padx=18,
        pady=(16, 4),
    )

    ctk.CTkLabel(
        topo,
        text=icone,
        font=("Arial", 22),
    ).pack(side="left")

    ctk.CTkLabel(
        topo,
        text=titulo,
        font=("Arial", 14, "bold"),
        text_color=theme.COLOR_TEXT_MUTED,
    ).pack(
        side="left",
        padx=(8, 0),
    )

    ctk.CTkLabel(
        card,
        text=valor,
        font=("Arial", 28, "bold"),
        text_color=theme.COLOR_TEXT,
    ).pack(
        anchor="w",
        padx=18,
        pady=(5, 2),
    )

    ctk.CTkLabel(
        card,
        text=descricao,
        font=("Arial", 12),
        text_color=theme.COLOR_TEXT_MUTED,
        wraplength=230,
        justify="left",
    ).pack(
        anchor="w",
        padx=18,
        pady=(0, 16),
    )

    return card


def criar_grade_kpis(
    master,
    cards,
    nome_uniforme,
    pady=(0, 14),
):
    grade = ctk.CTkFrame(
        master,
        fg_color="transparent",
    )
    grade.pack(
        fill="x",
        pady=pady,
    )

    for coluna in range(len(cards)):
        grade.grid_columnconfigure(
            coluna,
            weight=1,
            uniform=nome_uniforme,
        )

    for coluna, dados in enumerate(cards):
        card = criar_card_kpi(
            grade,
            *dados,
        )
        card.grid(
            row=0,
            column=coluna,
            sticky="nsew",
            padx=6,
        )

    return grade
