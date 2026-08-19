"""
Componente visual de últimos anúncios do Dashboard.
"""

import customtkinter as ctk

from ui import theme


class DashboardRecentAds:
    """Cria o painel visual de últimos anúncios."""

    @staticmethod
    def render(parent):
        frame = ctk.CTkFrame(
            parent,
            fg_color=theme.COLOR_CARD,
            corner_radius=20,
            border_width=1,
            border_color=theme.COLOR_BORDER,
        )
        frame.pack(
            fill="both",
            expand=True,
        )

        ctk.CTkLabel(
            frame,
            text="\u00daltimos an\u00fancios",
            font=("Arial", 22, "bold"),
            text_color=theme.COLOR_TEXT,
        ).pack(
            anchor="w",
            padx=22,
            pady=(20, 12),
        )

        lista = ctk.CTkFrame(
            frame,
            fg_color="transparent",
        )
        lista.pack(
            fill="both",
            expand=True,
            padx=0,
            pady=(0, 14),
        )

        return lista
