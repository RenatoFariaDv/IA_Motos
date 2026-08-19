"""
Componente visual do cabeçalho do Dashboard.
"""

import customtkinter as ctk
from datetime import datetime

from ui import theme


class DashboardHeader:
    def render(parent):
        header = ctk.CTkFrame(parent, fg_color='transparent')
        header.pack(fill='x', pady=(0, 24))
        left = ctk.CTkFrame(header, fg_color='transparent')
        left.pack(side='left', fill='x', expand=True)
        hora = datetime.now().hour
        saudacao = 'Bom dia' if hora < 12 else 'Boa tarde' if hora < 18 else 'Boa noite'
        ctk.CTkLabel(left, text=f'{saudacao}, Renato 👋', font=('Arial', 32, 'bold'), text_color=theme.COLOR_TEXT).pack(anchor='w')
        ctk.CTkLabel(left, text='Centro de controle operacional do TH IA MOTOS.', font=('Arial', 16), text_color=theme.COLOR_TEXT_MUTED).pack(anchor='w', pady=(4, 0))
        right = ctk.CTkFrame(header, fg_color=theme.COLOR_CARD, corner_radius=18)
        right.pack(side='right')
        ctk.CTkLabel(right, text='● Sistema Online', font=('Arial', 15, 'bold'), text_color=theme.COLOR_GREEN).pack(padx=22, pady=16)
