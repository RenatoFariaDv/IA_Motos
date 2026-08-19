"""
Cards de status exibidos no topo do Dashboard.
"""

import customtkinter as ctk

from ui import theme


class DashboardCards:
    """Renderiza os indicadores operacionais do Dashboard."""

    @staticmethod
    def render(parent, status_robo: str, pid_ativo: bool) -> None:
        grid = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )
        grid.pack(fill="x", pady=(0, 26))

        cards = [
            (
                "\U0001F916",
                "Rob\u00f4 Local",
                status_robo,
                "PID salvo" if pid_ativo else "Aguardando in\u00edcio",
                theme.COLOR_GREEN if pid_ativo else theme.COLOR_YELLOW,
            ),
            (
                "\u2601",
                "AWS",
                "Online",
                "54.233.146.58",
                theme.COLOR_BLUE,
            ),
            (
                "\U0001F4E6",
                "JSON",
                "Sincronizado",
                "Painel atualizado",
                theme.COLOR_PURPLE,
            ),
            (
                "\U0001F4E1",
                "Telegram",
                "Ativo",
                "Canal operacional",
                theme.COLOR_GREEN,
            ),
        ]

        for coluna, dados_card in enumerate(cards):
            DashboardCards._status_card(
                grid,
                *dados_card,
                coluna,
            )

    @staticmethod
    def _status_card(
        parent,
        icon: str,
        title: str,
        value: str,
        desc: str,
        color: str,
        col: int,
    ) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=theme.COLOR_CARD,
            corner_radius=18,
            border_width=1,
            border_color=theme.COLOR_BORDER,
        )
        card.grid(
            row=0,
            column=col,
            padx=8,
            sticky="ew",
        )

        parent.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(
            card,
            text=icon,
            font=("Arial", 30),
        ).pack(
            anchor="w",
            padx=20,
            pady=(18, 4),
        )

        ctk.CTkLabel(
            card,
            text=title.upper(),
            font=("Arial", 12, "bold"),
            text_color=theme.COLOR_TEXT_MUTED,
        ).pack(
            anchor="w",
            padx=20,
        )

        ctk.CTkLabel(
            card,
            text=value,
            font=("Arial", 24, "bold"),
            text_color=color,
        ).pack(
            anchor="w",
            padx=20,
            pady=(4, 0),
        )

        ctk.CTkLabel(
            card,
            text=desc,
            font=("Arial", 12),
            text_color=theme.COLOR_TEXT_MUTED,
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 18),
        )
