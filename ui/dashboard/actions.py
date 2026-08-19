"""
Componente de ações rápidas do Dashboard.
"""

from collections.abc import Callable

import customtkinter as ctk

from ui import theme


class DashboardActions:
    """Renderiza os atalhos operacionais do Dashboard."""

    @staticmethod
    def render(
        parent,
        iniciar_robo: Callable[[], None],
        parar_robo: Callable[[], None],
        abrir_painel: Callable[[], None],
        conectar_aws: Callable[[], None],
        abrir_vscode: Callable[[], None],
        abrir_agente: Callable[[], None],
    ) -> None:
        frame = ctk.CTkFrame(
            parent,
            fg_color=theme.COLOR_CARD,
            corner_radius=20,
            border_width=1,
            border_color=theme.COLOR_BORDER,
        )
        frame.pack(fill="x", pady=(0, 18))

        ctk.CTkLabel(
            frame,
            text="A\u00e7\u00f5es r\u00e1pidas",
            font=("Arial", 22, "bold"),
            text_color=theme.COLOR_TEXT,
        ).pack(
            anchor="w",
            padx=22,
            pady=(20, 10),
        )

        grid = ctk.CTkFrame(
            frame,
            fg_color="transparent",
        )
        grid.pack(
            fill="x",
            padx=14,
            pady=(0, 18),
        )

        actions = [
            (
                "\U0001F680",
                "Iniciar Rob\u00f4",
                "Come\u00e7ar captura local",
                iniciar_robo,
            ),
            (
                "\u23F9",
                "Parar Rob\u00f4",
                "Encerrar execu\u00e7\u00e3o",
                parar_robo,
            ),
            (
                "\U0001F310",
                "Painel AWS",
                "Abrir painel web",
                abrir_painel,
            ),
            (
                "\u2601",
                "AWS SSH",
                "Conectar servidor",
                conectar_aws,
            ),
            (
                "\U0001F4BB",
                "VS Code",
                "Abrir projeto",
                abrir_vscode,
            ),
            (
                "\U0001F9E0",
                "TH Agent",
                "Miss\u00f5es de IA",
                abrir_agente,
            ),
        ]

        for indice, item in enumerate(actions):
            linha = indice // 3
            coluna = indice % 3

            DashboardActions._action_tile(
                grid,
                *item,
                linha,
                coluna,
            )

    @staticmethod
    def _action_tile(
        parent,
        icon: str,
        title: str,
        desc: str,
        command: Callable[[], None],
        row: int,
        col: int,
    ) -> None:
        tile = ctk.CTkFrame(
            parent,
            fg_color=theme.COLOR_CARD_HOVER,
            corner_radius=16,
        )
        tile.grid(
            row=row,
            column=col,
            padx=8,
            pady=8,
            sticky="nsew",
        )

        parent.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(
            tile,
            text=icon,
            font=("Arial", 28),
        ).pack(
            anchor="w",
            padx=18,
            pady=(16, 2),
        )

        ctk.CTkLabel(
            tile,
            text=title,
            font=("Arial", 16, "bold"),
            text_color=theme.COLOR_TEXT,
        ).pack(
            anchor="w",
            padx=18,
        )

        ctk.CTkLabel(
            tile,
            text=desc,
            font=("Arial", 12),
            text_color=theme.COLOR_TEXT_MUTED,
        ).pack(
            anchor="w",
            padx=18,
            pady=(2, 12),
        )

        ctk.CTkButton(
            tile,
            text="Executar",
            height=30,
            corner_radius=10,
            command=command,
            fg_color=theme.COLOR_GREEN,
            hover_color=theme.COLOR_GREEN_DARK,
        ).pack(
            anchor="w",
            padx=18,
            pady=(0, 16),
        )
