import customtkinter as ctk
from ui import theme


class Sidebar(ctk.CTkFrame):

    def __init__(self, master, callbacks):
        super().__init__(
            master,
            width=240,
            fg_color=theme.COLOR_SIDEBAR,
            corner_radius=0
        )
        self.pack_propagate(False)
        self.callbacks = callbacks
        self.criar_interface()

    def criar_interface(self):
        # Área superior para logo
        logo_area = ctk.CTkFrame(
            self,
            height=64,
            fg_color=theme.COLOR_SIDEBAR,
            corner_radius=0
        )
        logo_area.pack(fill="x", pady=(0, 0))
        logo_label = ctk.CTkLabel(
            logo_area,
            text="TH IA MOTOS",
            font=("Arial", 18, "bold"),
            text_color=theme.COLOR_PRIMARY
        )
        logo_label.pack(expand=True, pady=(16, 0))

        # Separador após logo
        ctk.CTkFrame(self, height=1, fg_color=theme.COLOR_DIVIDER).pack(fill="x", pady=(8, 8))

        # Título centralizado
        titulo = ctk.CTkLabel(
            self,
            text=theme.APP_NAME,
            font=("Arial", 20, "bold"),
            text_color=theme.COLOR_TEXT
        )
        titulo.pack(pady=(0, 2))

        versao = ctk.CTkLabel(
            self,
            text=f"Control Center {theme.APP_VERSION}",
            text_color=theme.COLOR_TEXT_MUTED,
            font=theme.FONT_SMALL
        )
        versao.pack(pady=(0, 12))

        # Menu lateral profissional
        menu_items = [
            # (texto, callback, grupo)
            ("🏠 Dashboard", self.callbacks["dashboard"], "main"),
            ("🤖 Robô", self.callbacks["dashboard"], "main"),
            ("🌐 Painel AWS", self.callbacks["painel"], "aws"),
            ("☁ AWS SSH", self.callbacks["aws"], "aws"),
            ("💻 VS Code", self.callbacks["vscode"], "tools"),
            ("🧠 Agente IA", self.callbacks["ia"], "tools"),
            ("\U0001f4da Mem\u00f3ria da IA", self.callbacks["memoria"], "tools"),
            ("\U0001f4ca Agent Analytics", self.callbacks["analytics"], "tools"),
            ("\U0001f9ea Calibração Financeira", self.callbacks["calibracao"], "tools"),
            ("⚙ Configurações", self.callbacks["config"], "config"),
        ]

        grupos = ["main", "aws", "tools", "config"]
        grupo_atual = None

        # Simulação de item ativo (exemplo: Dashboard)
        item_ativo = 0

        for idx, (texto, comando, grupo) in enumerate(menu_items):
            if grupo != grupo_atual:
                if grupo_atual is not None:
                    # Separador entre grupos
                    ctk.CTkFrame(self, height=1, fg_color=theme.COLOR_DIVIDER).pack(fill="x", padx=8, pady=(10, 10))
                grupo_atual = grupo

            # Estilo do item
            is_active = idx == item_ativo
            fg_color = theme.COLOR_PRIMARY if is_active else theme.COLOR_SIDEBAR
            text_color = theme.COLOR_TEXT if is_active else theme.COLOR_TEXT_MUTED
            hover_color = theme.COLOR_PRIMARY_HOVER if not is_active else theme.COLOR_PRIMARY

            item = ctk.CTkButton(
                self,
                text=texto,
                command=comando,
                height=38,
                corner_radius=8,
                fg_color=fg_color,
                hover_color=hover_color,
                text_color=text_color,
                font=theme.FONT_BUTTON,
                anchor="w"
            )
            item.pack(fill="x", padx=12, pady=(2, 2))

        # Espaço para rodapé
        ctk.CTkFrame(self, height=1, fg_color=theme.COLOR_DIVIDER).pack(fill="x", pady=(16, 8))

        rodape = ctk.CTkLabel(
            self,
            text="© TH IA MOTOS",
            text_color=theme.COLOR_TEXT_MUTED,
            font=theme.FONT_SMALL
        )
        rodape.pack(side="bottom", pady=12)
