import json
import customtkinter as ctk
import webbrowser
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from agent_decision_history import carregar_decisoes, listar_decisoes_missao
from mission_manager import alterar_status_missao, criar_missao, editar_missao, excluir_missao, listar_missoes

from ui.dashboard.cards import DashboardCards
from ui.dashboard.actions import DashboardActions
from ui.dashboard.recent_ads import DashboardRecentAds
from ui.sidebar import Sidebar
from ui import theme
from ui.analytics.screen import render_agent_analytics

from core.dashboard_service import (
    obter_ultima_execucao,
    carregar_ultimos_anuncios,
    listar_oportunidades_da_missao,
    contar_oportunidades_excelentes,
    contar_oportunidades_por_missao,
    gerar_resumo_missao,
    listar_todas_oportunidades,
    gerar_metricas_shadow_mode,
    comparar_classificacao_shadow,
)
from core.paths import anuncios_encontrados_path, mission_matches_path
from core import robo_process

from ui.dashboard.header import DashboardHeader


BASE_DIR = Path(__file__).resolve().parent
PAINEL_URL = "http://54.233.146.58:5000/?v=1"
ROBO_FILE = BASE_DIR / "main.py"
PID_FILE = BASE_DIR / "robo.pid"
MATCHES_FILE = mission_matches_path()
ANUNCIOS_FILE = anuncios_encontrados_path()


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class THIAMotosApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TH IA MOTOS OS - Control Center")
        self.geometry("1280x760")
        self.minsize(1100, 680)
        self.configure(fg_color=theme.COLOR_BG)

        # Controle do auto refresh do Dashboard
        self.dashboard_after_id = None
        self.dashboard_anuncios_lista = None
        self.dashboard_arquivo_mtime = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(
            self,
            callbacks={
                "dashboard": self.criar_dashboard,
                "painel": self.abrir_painel,
                "aws": self.conectar_aws,
                "vscode": self.abrir_vscode,
                "ia": self.tela_agente_ia,
                "memoria": self.tela_memoria_ia,
                "analytics": self.tela_agent_analytics,
                "calibracao": self.tela_calibracao_financeira,
                "config": self.tela_configuracoes,
            }
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.content = ctk.CTkFrame(
            self,
            fg_color=theme.COLOR_CONTENT,
            corner_radius=0
        )
        self.content.grid(row=0, column=1, sticky="nsew")

        self.criar_dashboard()

    def limpar_content(self):
        self.parar_auto_refresh_dashboard()
        self.dashboard_anuncios_lista = None

        for widget in self.content.winfo_children():
            widget.destroy()

    def criar_dashboard(self):
        self.limpar_content()

        container = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        container.pack(fill="both", expand=True, padx=32, pady=28)

        status_atual = robo_process.verificar_status(PID_FILE, ROBO_FILE)

        DashboardHeader.render(container)
        DashboardCards.render(
            container,
            "Rodando" if status_atual.rodando else "Parado",
            status_atual.rodando,
        )
        self.criar_corpo_dashboard(container)
        self.iniciar_auto_refresh_dashboard()




    def criar_corpo_dashboard(self, parent):
        body = ctk.CTkFrame(parent, fg_color="transparent")
        body.pack(fill="both", expand=True)

        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(body, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(14, 0))

        DashboardActions.render(
            left,
            self.iniciar_robo,
            self.parar_robo,
            self.abrir_painel,
            self.conectar_aws,
            self.abrir_vscode,
            self.tela_agente_ia,
        )
        self.criar_th_agent_preview(left)
        self.dashboard_anuncios_lista = DashboardRecentAds.render(right)
        self.renderizar_ultimos_anuncios()



    def criar_th_agent_preview(self, parent):
        frame = ctk.CTkFrame(
            parent,
            fg_color=theme.COLOR_CARD,
            corner_radius=20,
            border_width=1,
            border_color=theme.COLOR_BORDER
        )
        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            frame,
            text="TH Agent",
            font=("Arial", 22, "bold"),
            text_color=theme.COLOR_TEXT
        ).pack(anchor="w", padx=22, pady=(20, 4))

        ctk.CTkLabel(
            frame,
            text="Área futura para missões, análise de anúncios e negociação assistida por IA.",
            font=("Arial", 14),
            text_color=theme.COLOR_TEXT_MUTED
        ).pack(anchor="w", padx=22, pady=(0, 18))

        missoes_reais = listar_missoes()
        oportunidades_por_missao = (
            contar_oportunidades_por_missao()
        )

        missions = []

        for missao in missoes_reais[:5]:
            missao_id = missao.get("id")
            marca = str(
                missao.get(
                    "marca",
                    "-",
                )
            )
            modelo = str(
                missao.get(
                    "modelo",
                    "-",
                )
            )
            status_missao = str(
                missao.get(
                    "status",
                    "-",
                )
            )

            try:
                total_oportunidades = (
                    oportunidades_por_missao.get(
                        int(missao_id),
                        0,
                    )
                )
            except (TypeError, ValueError):
                total_oportunidades = 0

            nome_missao = f"{marca} {modelo}".strip()
            descricao_missao = (
                f"{status_missao} \u2022 "
                f"{total_oportunidades} oportunidades"
            )

            missions.append(
                (
                    nome_missao,
                    descricao_missao,
                    "",
                )
            )

        if not missions:
            missions = [
                (
                    "Nenhuma miss\u00e3o cadastrada",
                    "Crie uma miss\u00e3o no TH Agent",
                    "",
                )
            ]

        for name, status, progress in missions:
            row = ctk.CTkFrame(frame, fg_color=theme.COLOR_CARD_HOVER, corner_radius=14)
            row.pack(fill="x", padx=18, pady=6)

            ctk.CTkLabel(
                row,
                text=name,
                font=("Arial", 15, "bold"),
                text_color=theme.COLOR_TEXT
            ).pack(anchor="w", padx=16, pady=(10, 0))

            ctk.CTkLabel(
                row,
                text=f"{status} • {progress}",
                font=("Arial", 12),
                text_color=theme.COLOR_TEXT_MUTED
            ).pack(anchor="w", padx=16, pady=(0, 10))


    def renderizar_ultimos_anuncios(self):
        lista = self.dashboard_anuncios_lista

        if lista is None:
            return

        try:
            if not lista.winfo_exists():
                return
        except Exception:
            return

        for widget in lista.winfo_children():
            widget.destroy()

        anuncios = carregar_ultimos_anuncios(limite=5)

        if not anuncios:
            ctk.CTkLabel(
                lista,
                text="Nenhum an?ncio encontrado.",
                font=("Arial", 13),
                text_color=theme.COLOR_TEXT_MUTED,
            ).pack(
                anchor="w",
                padx=22,
                pady=(8, 20),
            )
            return

        for anuncio in anuncios:
            titulo = str(
                anuncio.get(
                    "titulo",
                    "An?ncio sem t?tulo",
                )
            )

            data_hora = str(
                anuncio.get(
                    "data_hora",
                    "Data n?o informada",
                )
            )

            origem = str(
                anuncio.get(
                    "origem",
                    "OLX",
                )
            )

            desc = f"{origem} ? {data_hora}"

            item = ctk.CTkFrame(
                lista,
                fg_color=theme.COLOR_CARD_HOVER,
                corner_radius=14
            )
            item.pack(fill="x", padx=18, pady=6)

            ctk.CTkLabel(
                item,
                text=titulo,
                font=("Arial", 15, "bold"),
                text_color=theme.COLOR_TEXT
            ).pack(anchor="w", padx=16, pady=(10, 0))

            ctk.CTkLabel(
                item,
                text=desc,
                font=("Arial", 12),
                text_color=theme.COLOR_TEXT_MUTED
            ).pack(anchor="w", padx=16, pady=(0, 10))

    def obter_mtime_anuncios(self):
        try:
            return ANUNCIOS_FILE.stat().st_mtime_ns
        except OSError:
            return None

    def iniciar_auto_refresh_dashboard(self):
        self.parar_auto_refresh_dashboard()

        self.dashboard_arquivo_mtime = self.obter_mtime_anuncios()

        self.dashboard_after_id = self.after(
            30000,
            self.verificar_atualizacao_dashboard
        )

    def parar_auto_refresh_dashboard(self):
        if self.dashboard_after_id is None:
            return

        try:
            self.after_cancel(self.dashboard_after_id)
        except Exception:
            pass

        self.dashboard_after_id = None

    def verificar_atualizacao_dashboard(self):
        self.dashboard_after_id = None

        lista = self.dashboard_anuncios_lista

        if lista is None:
            return

        try:
            if not lista.winfo_exists():
                return
        except Exception:
            return

        mtime_atual = self.obter_mtime_anuncios()

        if mtime_atual != self.dashboard_arquivo_mtime:
            self.dashboard_arquivo_mtime = mtime_atual
            self.renderizar_ultimos_anuncios()

        self.dashboard_after_id = self.after(
            30000,
            self.verificar_atualizacao_dashboard
        )

    def status_robo_texto(self):
        status = robo_process.verificar_status(PID_FILE, ROBO_FILE)
        return "Rodando" if status.rodando else "Parado"

    def _mostrar_feedback_robo(self, titulo: str, mensagem: str, cor_destaque: str) -> None:
        janela = ctk.CTkToplevel(self)
        janela.title(titulo)
        janela.geometry("440x210")
        janela.resizable(False, False)
        janela.configure(fg_color=theme.COLOR_BG)
        janela.transient(self)
        janela.grab_set()

        ctk.CTkLabel(
            janela,
            text=titulo,
            font=("Arial", 20, "bold"),
            text_color=cor_destaque,
        ).pack(pady=(26, 8))

        ctk.CTkLabel(
            janela,
            text=mensagem,
            font=("Arial", 13),
            text_color=theme.COLOR_TEXT_MUTED,
            justify="center",
            wraplength=380,
        ).pack(padx=24, pady=(0, 18))

        ctk.CTkButton(
            janela,
            text="OK",
            command=janela.destroy,
            height=36,
            corner_radius=9,
            fg_color=theme.COLOR_CARD_HOVER,
            hover_color=theme.COLOR_BORDER,
            font=("Arial", 12, "bold"),
        ).pack(padx=24, pady=(0, 22))

    def iniciar_robo(self):
        resultado = robo_process.iniciar(PID_FILE, ROBO_FILE, BASE_DIR)

        if resultado.ja_estava_rodando:
            self._mostrar_feedback_robo(
                "Robô já em execução",
                f"O robô já está rodando (PID {resultado.pid}).",
                theme.COLOR_YELLOW,
            )
            return

        if not resultado.sucesso:
            self._mostrar_feedback_robo(
                "Falha ao iniciar",
                f"Não foi possível iniciar o robô: {resultado.erro}",
                theme.COLOR_RED,
            )
            return

        if resultado.pid_orfao_recuperado:
            self._mostrar_feedback_robo(
                "PID antigo recuperado",
                "Um registro antigo do robô (de um processo que já "
                "não existia mais) foi limpo automaticamente. "
                f"Robô iniciado agora (PID {resultado.pid}).",
                theme.COLOR_GREEN,
            )
        else:
            self._mostrar_feedback_robo(
                "Robô iniciado",
                f"Robô iniciado com sucesso (PID {resultado.pid}).",
                theme.COLOR_GREEN,
            )

        self.criar_dashboard()

    def parar_robo(self):
        resultado = robo_process.parar(PID_FILE, ROBO_FILE)

        if resultado.ja_estava_parado:
            self._mostrar_feedback_robo(
                "Robô não está rodando",
                "Não há nenhum robô em execução para parar.",
                theme.COLOR_YELLOW,
            )
            return

        if resultado.estado_limpo_sem_matar:
            if resultado.motivo == "pid reaproveitado":
                motivo_texto = (
                    "o PID registrado agora pertence a outro programa "
                    "— nada foi encerrado por segurança"
                )
            else:
                motivo_texto = "o processo já estava encerrado"

            self._mostrar_feedback_robo(
                "Estado do robô limpo",
                f"O registro do robô estava desatualizado ({motivo_texto}). "
                "Nenhum processo foi encerrado.",
                theme.COLOR_YELLOW,
            )
            self.criar_dashboard()
            return

        if not resultado.sucesso:
            self._mostrar_feedback_robo(
                "Falha ao parar",
                f"Não foi possível encerrar o robô "
                f"(PID {resultado.pid}): {resultado.erro}",
                theme.COLOR_RED,
            )
            return

        self._mostrar_feedback_robo(
            "Robô parado",
            f"Robô (PID {resultado.pid}) encerrado com sucesso.",
            theme.COLOR_GREEN,
        )
        self.criar_dashboard()

    def abrir_painel(self):
        webbrowser.open(PAINEL_URL)

    def abrir_vscode(self):
        subprocess.Popen(["code", str(BASE_DIR)], shell=True)

    def conectar_aws(self):
        key = Path.home() / ".ssh" / "IA-Motos-Key.pem"
        comando = f'ssh -i "{key}" ubuntu@54.233.146.58'
        subprocess.Popen(["powershell", "-NoExit", "-Command", comando])

    def abrir_anuncio_seguro(self, link):
        """
        Abre o an?ncio diretamente no navegador.

        A OLX normalmente responde 403 para verifica??es feitas com
        requests, mesmo quando o an?ncio est? acess?vel no navegador.
        """
        link = str(link).strip()

        if not link:
            return

        webbrowser.open(link)


    def abrir_oportunidades_missao(self, missao):
        """Abre uma janela com as oportunidades vinculadas ? miss?o."""
        missao_id = missao.get("id")
        marca = str(missao.get("marca", "-"))
        modelo = str(missao.get("modelo", "-"))

        oportunidades = listar_oportunidades_da_missao(missao_id)
        resumo_missao = gerar_resumo_missao(missao_id)

        janela = ctk.CTkToplevel(self)
        janela.title(f"Oportunidades - {marca} {modelo}")
        janela.geometry("800x620")
        janela.minsize(680, 500)
        janela.configure(fg_color=theme.COLOR_BG)
        janela.transient(self)
        janela.grab_set()

        cabecalho = ctk.CTkFrame(
            janela,
            fg_color=theme.COLOR_CARD,
            corner_radius=16,
            border_width=1,
            border_color=theme.COLOR_BORDER
        )
        cabecalho.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            cabecalho,
            text=f"Missão #{missao_id} - {marca} {modelo}",
            font=("Arial", 22, "bold"),
            text_color=theme.COLOR_TEXT
        ).pack(anchor="w", padx=20, pady=(16, 4))

        total = resumo_missao.get(
            "total",
            len(oportunidades),
        )
        excelentes = resumo_missao.get("excelentes", 0)
        boas = resumo_missao.get("boas", 0)
        regulares = resumo_missao.get("regulares", 0)
        descartadas = resumo_missao.get("descartadas", 0)
        melhor_score = resumo_missao.get("melhor_score", 0)
        melhor_preco = resumo_missao.get("melhor_preco", 0.0)
        preco_medio = resumo_missao.get("preco_medio", 0.0)

        def formatar_valor_missao(valor):
            try:
                valor = float(valor)
            except (TypeError, ValueError):
                valor = 0.0

            return (
                f"R$ {valor:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

        ctk.CTkLabel(
            cabecalho,
            text=f"Total de oportunidades: {total}",
            font=("Arial", 14, "bold"),
            text_color=theme.COLOR_GREEN
        ).pack(anchor="w", padx=20, pady=(0, 8))

        resumo_frame = ctk.CTkFrame(
            cabecalho,
            fg_color=theme.COLOR_CARD_HOVER,
            corner_radius=12,
        )
        resumo_frame.pack(
            fill="x",
            padx=20,
            pady=(0, 16),
        )

        resumo_frame.grid_columnconfigure(0, weight=1)
        resumo_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            resumo_frame,
            text=f"Excelentes: {excelentes}",
            font=("Arial", 12, "bold"),
            text_color=theme.COLOR_GREEN,
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=14,
            pady=(10, 4),
        )

        ctk.CTkLabel(
            resumo_frame,
            text=f"Boas: {boas}",
            font=("Arial", 12, "bold"),
            text_color=theme.COLOR_TEXT,
        ).grid(
            row=0,
            column=1,
            sticky="w",
            padx=14,
            pady=(10, 4),
        )

        ctk.CTkLabel(
            resumo_frame,
            text=f"Regulares: {regulares}",
            font=("Arial", 12),
            text_color=theme.COLOR_TEXT_MUTED,
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=14,
            pady=4,
        )

        ctk.CTkLabel(
            resumo_frame,
            text=f"Descartadas: {descartadas}",
            font=("Arial", 12),
            text_color=theme.COLOR_TEXT_MUTED,
        ).grid(
            row=1,
            column=1,
            sticky="w",
            padx=14,
            pady=4,
        )

        ctk.CTkLabel(
            resumo_frame,
            text=f"Melhor score: {melhor_score}/100",
            font=("Arial", 12, "bold"),
            text_color=theme.COLOR_TEXT,
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=14,
            pady=4,
        )

        ctk.CTkLabel(
            resumo_frame,
            text=(
                "Melhor pre\u00e7o: "
                f"{formatar_valor_missao(melhor_preco)}"
            ),
            font=("Arial", 12, "bold"),
            text_color=theme.COLOR_GREEN,
        ).grid(
            row=2,
            column=1,
            sticky="w",
            padx=14,
            pady=4,
        )

        ctk.CTkLabel(
            resumo_frame,
            text=(
                "Pre\u00e7o m\u00e9dio: "
                f"{formatar_valor_missao(preco_medio)}"
            ),
            font=("Arial", 12),
            text_color=theme.COLOR_TEXT_MUTED,
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            padx=14,
            pady=(4, 10),
        )

        lista = ctk.CTkScrollableFrame(
            janela,
            fg_color="transparent",
            corner_radius=0
        )
        lista.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        if not oportunidades:
            ctk.CTkLabel(
                lista,
                text="Nenhuma oportunidade encontrada.",
                font=("Arial", 15),
                text_color=theme.COLOR_TEXT_MUTED
            ).pack(pady=40)

            return

        for oportunidade in oportunidades:
            titulo = str(
                oportunidade.get(
                    "titulo",
                    "An?ncio sem t?tulo",
                )
            )

            status = str(
                oportunidade.get(
                    "status",
                    "-",
                )
            )

            link = str(
                oportunidade.get(
                    "anuncio_link",
                    "",
                )
            )

            preco = oportunidade.get("preco")
            score = oportunidade.get("score", 0)
            recomendacao = str(
                oportunidade.get(
                    "recomendacao",
                    "SEM AN?LISE",
                )
            )
            motivos = oportunidade.get("motivos", [])

            try:
                preco_numerico = float(preco)

                preco_formatado = (
                    f"R$ {preco_numerico:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )

            except (TypeError, ValueError):
                preco_formatado = "Pre?o n?o informado"

            try:
                score_numerico = int(score)
            except (TypeError, ValueError):
                score_numerico = 0

            card = ctk.CTkFrame(
                lista,
                fg_color=theme.COLOR_CARD,
                corner_radius=14,
                border_width=1,
                border_color=theme.COLOR_BORDER
            )
            card.pack(fill="x", pady=7)

            ctk.CTkLabel(
                card,
                text=titulo,
                font=("Arial", 15, "bold"),
                text_color=theme.COLOR_TEXT,
                anchor="w",
                justify="left",
                wraplength=650
            ).pack(
                fill="x",
                anchor="w",
                padx=16,
                pady=(14, 5)
            )

            ctk.CTkLabel(
                card,
                text=preco_formatado,
                font=("Arial", 14, "bold"),
                text_color=theme.COLOR_GREEN
            ).pack(
                anchor="w",
                padx=16,
                pady=(0, 3)
            )

            analise_frame = ctk.CTkFrame(
                card,
                fg_color=theme.COLOR_CARD_HOVER,
                corner_radius=10,
            )
            analise_frame.pack(
                fill="x",
                padx=16,
                pady=(6, 8),
            )

            ctk.CTkLabel(
                analise_frame,
                text=f"Score: {score_numerico}/100",
                font=("Arial", 14, "bold"),
                text_color=theme.COLOR_TEXT,
            ).pack(
                anchor="w",
                padx=12,
                pady=(10, 2),
            )

            ctk.CTkLabel(
                analise_frame,
                text=f"Recomenda\u00e7\u00e3o: {recomendacao}",
                font=("Arial", 13, "bold"),
                text_color=theme.COLOR_GREEN,
            ).pack(
                anchor="w",
                padx=12,
                pady=(0, 6),
            )

            if isinstance(motivos, list):
                for motivo in motivos:
                    ctk.CTkLabel(
                        analise_frame,
                        text=f"\u2022 {motivo}",
                        font=("Arial", 11),
                        text_color=theme.COLOR_TEXT_MUTED,
                        anchor="w",
                        justify="left",
                        wraplength=620,
                    ).pack(
                        fill="x",
                        anchor="w",
                        padx=12,
                        pady=1,
                    )

            ctk.CTkLabel(
                analise_frame,
                text=f"Status: {status}",
                font=("Arial", 12),
                text_color=theme.COLOR_TEXT_MUTED
            ).pack(
                anchor="w",
                padx=12,
                pady=(6, 2 if (str(oportunidade.get("origem", "")).strip() or str(oportunidade.get("cidade", "")).strip() or oportunidade.get("fipe_encontrada") is not None) else 10)
            )

            origem_oportunidade = str(
                oportunidade.get("origem", "")
            ).strip()
            cidade_oportunidade = str(
                oportunidade.get("cidade", "")
            ).strip()
            partes_local = [
                parte
                for parte in (origem_oportunidade, cidade_oportunidade)
                if parte
            ]

            if partes_local:
                ctk.CTkLabel(
                    analise_frame,
                    text=" • ".join(partes_local),
                    font=("Arial", 12),
                    text_color=theme.COLOR_TEXT_MUTED
                ).pack(
                    anchor="w",
                    padx=12,
                    pady=(0, 2)
                )

            if oportunidade.get("fipe_encontrada"):
                valor_fipe = oportunidade.get("valor_fipe")
                diferenca_reais = oportunidade.get(
                    "diferenca_fipe_reais"
                )
                diferenca_percentual = oportunidade.get(
                    "diferenca_fipe_percentual"
                )

                try:
                    valor_fipe_formatado = (
                        f"R$ {float(valor_fipe):,.2f}"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                    )
                except (TypeError, ValueError):
                    valor_fipe_formatado = None

                if valor_fipe_formatado:
                    ctk.CTkLabel(
                        analise_frame,
                        text=f"FIPE: {valor_fipe_formatado}",
                        font=("Arial", 12),
                        text_color=theme.COLOR_TEXT_MUTED
                    ).pack(
                        anchor="w",
                        padx=12,
                        pady=(0, 2)
                    )

                try:
                    diferenca_reais_num = float(diferenca_reais)
                    sinal = "+" if diferenca_reais_num >= 0 else "-"
                    diferenca_reais_formatada = (
                        f"R$ {abs(diferenca_reais_num):,.2f}"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                    )

                    ctk.CTkLabel(
                        analise_frame,
                        text=(
                            "Diferença FIPE: "
                            f"{sinal}{diferenca_reais_formatada}"
                        ),
                        font=("Arial", 12),
                        text_color=theme.COLOR_TEXT_MUTED
                    ).pack(
                        anchor="w",
                        padx=12,
                        pady=(0, 2)
                    )
                except (TypeError, ValueError):
                    pass

                try:
                    diferenca_percentual_num = float(
                        diferenca_percentual
                    )
                    sinal_pct = (
                        "+" if diferenca_percentual_num >= 0 else "-"
                    )
                    percentual_formatado = (
                        f"{abs(diferenca_percentual_num):.2f}"
                        .replace(".", ",")
                    )

                    ctk.CTkLabel(
                        analise_frame,
                        text=(
                            "Diferença percentual: "
                            f"{sinal_pct}{percentual_formatado}%"
                        ),
                        font=("Arial", 12),
                        text_color=theme.COLOR_TEXT_MUTED
                    ).pack(
                        anchor="w",
                        padx=12,
                        pady=(0, 10)
                    )
                except (TypeError, ValueError):
                    pass
            else:
                ctk.CTkLabel(
                    analise_frame,
                    text="FIPE não disponível",
                    font=("Arial", 11),
                    text_color=theme.COLOR_TEXT_MUTED
                ).pack(
                    anchor="w",
                    padx=12,
                    pady=(0, 10)
                )

            bloco_financeiro_experimental_op = ctk.CTkFrame(
                card,
                fg_color=theme.COLOR_CARD_HOVER,
                corner_radius=10,
            )
            bloco_financeiro_experimental_op.pack(
                fill="x",
                padx=16,
                pady=(0, 8),
            )

            ctk.CTkLabel(
                bloco_financeiro_experimental_op,
                text="ANÁLISE FINANCEIRA • EXPERIMENTAL",
                font=("Arial", 10, "bold"),
                text_color=theme.COLOR_TEXT_MUTED,
            ).pack(
                anchor="w",
                padx=12,
                pady=(10, 2),
            )

            ctk.CTkLabel(
                bloco_financeiro_experimental_op,
                text=(
                    "Não substitui o Score/Recomendação oficiais "
                    "acima -- somente para calibração."
                ),
                font=("Arial", 9, "italic"),
                text_color=theme.COLOR_TEXT_MUTED,
            ).pack(
                anchor="w",
                padx=12,
                pady=(0, 6),
            )

            score_financeiro_op = oportunidade.get("score_financeiro")

            if score_financeiro_op is None:
                if oportunidade.get("fipe_encontrada"):
                    # A FIPE foi encontrada (ver bloco acima) mas este
                    # registro é anterior ao shadow mode -- nunca
                    # dizer "FIPE não disponível" aqui, seria falso.
                    texto_sem_dados_op = (
                        "Dados experimentais não calculados para "
                        "este registro (anterior ao modo shadow)."
                    )
                else:
                    texto_sem_dados_op = (
                        "Score financeiro: SEM DADOS (FIPE não "
                        "disponível para esta oportunidade)"
                    )

                ctk.CTkLabel(
                    bloco_financeiro_experimental_op,
                    text=texto_sem_dados_op,
                    font=("Arial", 12),
                    text_color=theme.COLOR_TEXT_MUTED,
                ).pack(
                    anchor="w",
                    padx=12,
                    pady=(0, 10),
                )
            else:
                classificacao_financeira_op = oportunidade.get(
                    "classificacao_financeira", "SEM DADOS"
                )
                score_final_experimental_op = oportunidade.get(
                    "score_final_experimental", score_numerico
                )
                classificacao_final_experimental_op = oportunidade.get(
                    "classificacao_final_experimental", recomendacao
                )
                preco_alvo_op = oportunidade.get("preco_alvo_negociacao")

                try:
                    preco_alvo_formatado_op = (
                        f"R$ {float(preco_alvo_op):,.2f}"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                    )
                except (TypeError, ValueError):
                    preco_alvo_formatado_op = "-"

                ctk.CTkLabel(
                    bloco_financeiro_experimental_op,
                    text=(
                        f"Score financeiro: {score_financeiro_op}/100  "
                        f"•  Atratividade: {classificacao_financeira_op}"
                    ),
                    font=("Arial", 12),
                    text_color=theme.COLOR_TEXT_MUTED,
                ).pack(
                    anchor="w",
                    padx=12,
                    pady=(0, 2),
                )

                ctk.CTkLabel(
                    bloco_financeiro_experimental_op,
                    text=(
                        "Score final experimental: "
                        f"{score_final_experimental_op}/100  "
                        "•  Classificação experimental: "
                        f"{classificacao_final_experimental_op}"
                    ),
                    font=("Arial", 12),
                    text_color=theme.COLOR_TEXT_MUTED,
                ).pack(
                    anchor="w",
                    padx=12,
                    pady=(0, 2),
                )

                ctk.CTkLabel(
                    bloco_financeiro_experimental_op,
                    text=f"Preço-alvo: {preco_alvo_formatado_op}",
                    font=("Arial", 12),
                    text_color=theme.COLOR_TEXT_MUTED,
                ).pack(
                    anchor="w",
                    padx=12,
                    pady=(0, 10),
                )

            if link:
                ctk.CTkButton(
                    card,
                    text="Abrir an\u00fancio",
                    command=lambda url=link: (
                        self.abrir_anuncio_seguro(url)
                    ),
                    height=34,
                    corner_radius=10,
                    fg_color=theme.COLOR_GREEN,
                    hover_color=theme.COLOR_GREEN_DARK,
                    font=("Arial", 13, "bold")
                ).pack(
                    anchor="e",
                    padx=16,
                    pady=(0, 14)
                )

    def tela_agente_ia(self):
        self.limpar_content()

        page = ctk.CTkScrollableFrame(
            self.content,
            fg_color="transparent",
            corner_radius=0
        )
        page.pack(fill="both", expand=True, padx=30, pady=24)

        # Cabeçalho
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", pady=(0, 22))

        header_left = ctk.CTkFrame(header, fg_color="transparent")
        header_left.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            header_left,
            text="TH Agent",
            font=("Arial", 32, "bold"),
            text_color=theme.COLOR_TEXT
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_left,
            text="Assistente inteligente para missões de compra e negociação.",
            font=("Arial", 15),
            text_color=theme.COLOR_TEXT_MUTED
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(
            header,
            text="🅘 Modo Copiloto",
            font=("Arial", 14, "bold"),
            text_color=theme.COLOR_GREEN
        ).pack(side="right", padx=12)

        # Cards de status
        status_row = ctk.CTkFrame(page, fg_color="transparent")
        status_row.pack(fill="x", pady=(0, 22))

        status_ativos = {
            "PENDENTE",
            "EM_EXECUCAO",
            "NEGOCIANDO",
        }

        total_missoes_ativas = sum(
            1
            for missao in listar_missoes()
            if str(
                missao.get("status", "")
            ).strip().upper() in status_ativos
        )

        status_items = [
            ("STATUS", "Online", theme.COLOR_GREEN),
            (
                "MISS\u00d5ES ATIVAS",
                str(total_missoes_ativas),
                theme.COLOR_BLUE,
            ),
            ("\u00daLTIMA EXECU\u00c7\u00c3O", obter_ultima_execucao(), theme.COLOR_YELLOW),
            (
                "OPORTUNIDADES EXCELENTES",
                str(contar_oportunidades_excelentes()),
                theme.COLOR_PURPLE,
            ),
        ]

        for column, (title, value, color) in enumerate(status_items):
            card = ctk.CTkFrame(
                status_row,
                fg_color=theme.COLOR_CARD,
                corner_radius=18,
                border_width=1,
                border_color=theme.COLOR_BORDER
            )
            card.grid(
                row=0,
                column=column,
                padx=(0, 10) if column < 3 else 0,
                sticky="ew"
            )
            status_row.grid_columnconfigure(column, weight=1)

            ctk.CTkLabel(
                card,
                text=title,
                font=("Arial", 11, "bold"),
                text_color=theme.COLOR_TEXT_MUTED
            ).pack(anchor="w", padx=18, pady=(16, 4))

            ctk.CTkLabel(
                card,
                text=value,
                font=("Arial", 22, "bold"),
                text_color=color
            ).pack(anchor="w", padx=18, pady=(0, 16))

        # Conte?do em duas colunas
        body = ctk.CTkFrame(page, fg_color="transparent")
        body.pack(fill="both", expand=True)

        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # Nova operação
        mission_card = ctk.CTkFrame(
            body,
            fg_color=theme.COLOR_CARD,
            corner_radius=20,
            border_width=1,
            border_color=theme.COLOR_BORDER
        )
        mission_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 12)
        )

        ctk.CTkLabel(
            mission_card,
            text="🎯 Nova Operação",
            font=("Arial", 21, "bold"),
            text_color=theme.COLOR_TEXT
        ).pack(anchor="w", padx=22, pady=(20, 4))

        ctk.CTkLabel(
            mission_card,
            text="Configure como o TH Agent deverá procurar e negociar este veículo.",
            font=("Arial", 13),
            text_color=theme.COLOR_TEXT_MUTED
        ).pack(anchor="w", padx=22, pady=(0, 8))

        form = ctk.CTkFrame(mission_card, fg_color="transparent")
        form.pack(fill="x", padx=22)

        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        # Grupo VEÍCULO
        ctk.CTkLabel(
            form,
            text="VEÍCULO",
            font=("Arial", 14, "bold"),
            text_color=theme.COLOR_TEXT
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(10, 2))

        def create_field(label, row, column, placeholder):
            wrapper = ctk.CTkFrame(form, fg_color="transparent")
            wrapper.grid(
                row=row,
                column=column,
                sticky="ew",
                padx=(0, 8) if column == 0 else (8, 0),
                pady=7
            )

            ctk.CTkLabel(
                wrapper,
                text=label,
                font=("Arial", 13, "bold"),
                text_color=theme.COLOR_TEXT
            ).pack(anchor="w", pady=(0, 5))

            entry = ctk.CTkEntry(
                wrapper,
                height=38,
                corner_radius=10,
                placeholder_text=placeholder,
                fg_color=theme.COLOR_CARD_HOVER,
                border_color=theme.COLOR_BORDER
            )
            entry.pack(fill="x")
            return entry

        entry_marca = create_field("Marca", 1, 0, "Ex.: BMW")
        entry_modelo = create_field("Modelo", 1, 1, "Ex.: S1000RR")
        entry_ano_min = create_field("Ano mínimo", 2, 0, "Ex.: 2021")
        entry_ano_max = create_field("Ano máximo", 2, 1, "Ex.: 2026")

        # Grupo NEGOCIAÇÃO
        ctk.CTkLabel(
            form,
            text="NEGOCIAÇÃO",
            font=("Arial", 14, "bold"),
            text_color=theme.COLOR_TEXT
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(16, 2))

        entry_valor_max = create_field("Valor máximo", 4, 0, "Ex.: 70000")
        entry_primeira_oferta = create_field("Primeira oferta", 4, 1, "Ex.: 64000")
        entry_oferta_max = create_field("Limite final da oferta", 5, 0, "Ex.: 69000")

        estrategia_wrapper = ctk.CTkFrame(form, fg_color="transparent")
        estrategia_wrapper.grid(
            row=5,
            column=1,
            sticky="ew",
            padx=(8, 0),
            pady=7
        )

        ctk.CTkLabel(
            estrategia_wrapper,
            text="Estratégia",
            font=("Arial", 13, "bold"),
            text_color=theme.COLOR_TEXT
        ).pack(anchor="w", pady=(0, 5))

        combo_estrategia = ctk.CTkComboBox(
            estrategia_wrapper,
            values=["Conservadora", "Equilibrada", "Agressiva"],
            height=38,
            corner_radius=10,
            fg_color=theme.COLOR_CARD_HOVER,
            border_color=theme.COLOR_BORDER,
            button_color=theme.COLOR_GREEN,
            button_hover_color=theme.COLOR_GREEN_DARK,
            state="readonly"
        )
        combo_estrategia.set("Equilibrada")
        combo_estrategia.pack(fill="x")

        # Grupo SEGURANÇA
        ctk.CTkLabel(
            form,
            text="SEGURANÇA",
            font=("Arial", 14, "bold"),
            text_color=theme.COLOR_TEXT
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(16, 2))

        approval_frame = ctk.CTkFrame(
            form,
            fg_color=theme.COLOR_CARD_HOVER,
            corner_radius=14
        )
        approval_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(4, 12))

        approval_switch = ctk.CTkSwitch(
            approval_frame,
            text="Exigir aprovação humana antes de enviar qualquer proposta",
            progress_color=theme.COLOR_GREEN,
            button_hover_color=theme.COLOR_GREEN_DARK,
            text_color=theme.COLOR_TEXT
        )
        approval_switch.pack(anchor="w", padx=16, pady=14)
        approval_switch.select()

        def criar_missao_callback():
            try:
                missao = criar_missao(
                    marca=entry_marca.get(),
                    modelo=entry_modelo.get(),
                    ano_min=entry_ano_min.get(),
                    ano_max=entry_ano_max.get(),
                    orcamento=entry_valor_max.get(),
                    primeira_oferta=entry_primeira_oferta.get(),
                    limite_final=entry_oferta_max.get(),
                    estrategia=combo_estrategia.get(),
                    aprovacao_humana=bool(approval_switch.get()),
                )

                print("Operação criada com sucesso:")
                print(missao)
                self.tela_agente_ia()  # Recarrega a tela após criar missão

            except Exception as erro:
                print(f"Erro ao criar operação: {erro}")

        ctk.CTkButton(
            mission_card,
            text="🚀 Iniciar Operação",
            command=criar_missao_callback,
            height=42,
            corner_radius=12,
            fg_color=theme.COLOR_GREEN,
            hover_color=theme.COLOR_GREEN_DARK,
            font=("Arial", 15, "bold")
        ).pack(anchor="e", padx=22, pady=(4, 22))


        # Coluna lateral
        side_column = ctk.CTkFrame(body, fg_color="transparent")
        side_column.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(12, 0)
        )

        history_card = ctk.CTkFrame(
            side_column,
            fg_color=theme.COLOR_CARD,
            corner_radius=20,
            border_width=1,
            border_color=theme.COLOR_BORDER
        )
        history_card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            history_card,
            text="📋 MISSÕES",
            font=("Arial", 20, "bold"),
            text_color=theme.COLOR_TEXT
        ).pack(anchor="w", padx=20, pady=(20, 5))

        missoes = listar_missoes()
        oportunidades_por_missao = contar_oportunidades_por_missao()

        def abrir_edicao_missao(missao):
            missao_id = missao.get("id")

            janela_edicao = ctk.CTkToplevel(self)
            janela_edicao.title(
                f"Editar miss\u00e3o #{missao_id}"
            )
            janela_edicao.geometry("620x690")
            janela_edicao.minsize(560, 620)
            janela_edicao.configure(
                fg_color=theme.COLOR_BG
            )
            janela_edicao.transient(self)
            janela_edicao.grab_set()

            conteudo_edicao = ctk.CTkScrollableFrame(
                janela_edicao,
                fg_color="transparent",
            )
            conteudo_edicao.pack(
                fill="both",
                expand=True,
                padx=24,
                pady=24,
            )

            ctk.CTkLabel(
                conteudo_edicao,
                text=f"Editar miss\u00e3o #{missao_id}",
                font=("Arial", 24, "bold"),
                text_color=theme.COLOR_TEXT,
            ).pack(
                anchor="w",
                pady=(0, 18),
            )

            def criar_campo(
                titulo,
                valor,
            ):
                ctk.CTkLabel(
                    conteudo_edicao,
                    text=titulo,
                    font=("Arial", 12, "bold"),
                    text_color=theme.COLOR_TEXT,
                ).pack(
                    anchor="w",
                    pady=(8, 4),
                )

                campo = ctk.CTkEntry(
                    conteudo_edicao,
                    height=38,
                    corner_radius=9,
                    fg_color=theme.COLOR_CARD_HOVER,
                    border_color=theme.COLOR_BORDER,
                    text_color=theme.COLOR_TEXT,
                )
                campo.pack(
                    fill="x",
                    pady=(0, 4),
                )
                campo.insert(0, str(valor))

                return campo

            campo_marca = criar_campo(
                "Marca",
                missao.get("marca", ""),
            )

            campo_modelo = criar_campo(
                "Modelo",
                missao.get("modelo", ""),
            )

            campo_ano_min = criar_campo(
                "Ano m\u00ednimo",
                missao.get("ano_min", ""),
            )

            campo_ano_max = criar_campo(
                "Ano m\u00e1ximo",
                missao.get("ano_max", ""),
            )

            campo_orcamento = criar_campo(
                "Or\u00e7amento m\u00e1ximo",
                missao.get("orcamento", ""),
            )

            campo_primeira_oferta = criar_campo(
                "Primeira oferta",
                missao.get("primeira_oferta", ""),
            )

            campo_limite_final = criar_campo(
                "Limite final",
                missao.get("limite_final", ""),
            )

            ctk.CTkLabel(
                conteudo_edicao,
                text="Estrat\u00e9gia",
                font=("Arial", 12, "bold"),
                text_color=theme.COLOR_TEXT,
            ).pack(
                anchor="w",
                pady=(8, 4),
            )

            estrategia_atual = str(
                missao.get(
                    "estrategia",
                    "Conservadora",
                )
            )

            combo_edicao_estrategia = ctk.CTkComboBox(
                conteudo_edicao,
                values=[
                    "Conservadora",
                    "Equilibrada",
                    "Agressiva",
                ],
                height=38,
                corner_radius=9,
                fg_color=theme.COLOR_CARD_HOVER,
                border_color=theme.COLOR_BORDER,
                button_color=theme.COLOR_GREEN,
                button_hover_color=theme.COLOR_GREEN_DARK,
                text_color=theme.COLOR_TEXT,
            )
            combo_edicao_estrategia.pack(
                fill="x",
                pady=(0, 8),
            )
            combo_edicao_estrategia.set(
                estrategia_atual
            )

            ctk.CTkLabel(
                conteudo_edicao,
                text="Status",
                font=("Arial", 12, "bold"),
                text_color=theme.COLOR_TEXT,
            ).pack(
                anchor="w",
                pady=(8, 4),
            )

            status_atual = str(
                missao.get(
                    "status",
                    "PENDENTE",
                )
            ).strip().upper()

            combo_edicao_status = ctk.CTkComboBox(
                conteudo_edicao,
                values=[
                    "PENDENTE",
                    "EM_EXECUCAO",
                    "NEGOCIANDO",
                    "FINALIZADA",
                    "CANCELADA",
                    "COMPRADA",
                ],
                height=38,
                corner_radius=9,
                fg_color=theme.COLOR_CARD_HOVER,
                border_color=theme.COLOR_BORDER,
                button_color=theme.COLOR_GREEN,
                button_hover_color=theme.COLOR_GREEN_DARK,
                text_color=theme.COLOR_TEXT,
            )
            combo_edicao_status.pack(
                fill="x",
                pady=(0, 8),
            )
            combo_edicao_status.set(
                status_atual
            )

            switch_aprovacao = ctk.CTkSwitch(
                conteudo_edicao,
                text=(
                    "Exigir aprova\u00e7\u00e3o humana "
                    "antes de enviar propostas"
                ),
                progress_color=theme.COLOR_GREEN,
                button_hover_color=theme.COLOR_GREEN_DARK,
                text_color=theme.COLOR_TEXT,
            )
            switch_aprovacao.pack(
                anchor="w",
                pady=(12, 18),
            )

            if missao.get("aprovacao_humana", True):
                switch_aprovacao.select()
            else:
                switch_aprovacao.deselect()

            mensagem_edicao = ctk.CTkLabel(
                conteudo_edicao,
                text="",
                font=("Arial", 12, "bold"),
                text_color=theme.COLOR_TEXT_MUTED,
                wraplength=520,
                justify="left",
            )
            mensagem_edicao.pack(
                anchor="w",
                pady=(0, 10),
            )

            def salvar_edicao():
                try:
                    missao_atualizada = editar_missao(
                        missao_id=missao_id,
                        marca=campo_marca.get(),
                        modelo=campo_modelo.get(),
                        ano_min=campo_ano_min.get(),
                        ano_max=campo_ano_max.get(),
                        orcamento=campo_orcamento.get(),
                        primeira_oferta=(
                            campo_primeira_oferta.get()
                        ),
                        limite_final=campo_limite_final.get(),
                        estrategia=(
                            combo_edicao_estrategia.get()
                        ),
                        aprovacao_humana=bool(
                            switch_aprovacao.get()
                        ),
                    )

                    status_atualizado = alterar_status_missao(
                        missao_id=missao_id,
                        novo_status=combo_edicao_status.get(),
                    )

                    print(
                        "Miss\u00e3o editada com sucesso:"
                    )
                    print(status_atualizado)

                    janela_edicao.destroy()
                    self.tela_agente_ia()

                except Exception as erro:
                    mensagem_edicao.configure(
                        text=f"Erro: {erro}",
                        text_color="#FF6B6B",
                    )

            botoes_edicao = ctk.CTkFrame(
                conteudo_edicao,
                fg_color="transparent",
            )
            botoes_edicao.pack(
                fill="x",
                pady=(4, 10),
            )

            ctk.CTkButton(
                botoes_edicao,
                text="Cancelar",
                command=janela_edicao.destroy,
                height=40,
                corner_radius=10,
                fg_color=theme.COLOR_CARD_HOVER,
                hover_color=theme.COLOR_BORDER,
                font=("Arial", 13, "bold"),
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=(0, 6),
            )

            ctk.CTkButton(
                botoes_edicao,
                text="Salvar altera\u00e7\u00f5es",
                command=salvar_edicao,
                height=40,
                corner_radius=10,
                fg_color=theme.COLOR_GREEN,
                hover_color=theme.COLOR_GREEN_DARK,
                font=("Arial", 13, "bold"),
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=(6, 0),
            )

        def confirmar_exclusao_missao(missao):
            missao_id = missao.get("id")
            marca = str(missao.get("marca", "-"))
            modelo = str(missao.get("modelo", "-"))

            janela_confirmacao = ctk.CTkToplevel(self)
            janela_confirmacao.title("Excluir miss\u00e3o")
            janela_confirmacao.geometry("440x230")
            janela_confirmacao.resizable(False, False)
            janela_confirmacao.configure(
                fg_color=theme.COLOR_BG
            )
            janela_confirmacao.transient(self)
            janela_confirmacao.grab_set()

            ctk.CTkLabel(
                janela_confirmacao,
                text="Excluir miss\u00e3o?",
                font=("Arial", 20, "bold"),
                text_color=theme.COLOR_TEXT,
            ).pack(
                pady=(26, 8),
            )

            ctk.CTkLabel(
                janela_confirmacao,
                text=(
                    f"Tem certeza que deseja excluir a miss\u00e3o "
                    f"#{missao_id} - {marca} {modelo}?\n\n"
                    "As oportunidades relacionadas tamb\u00e9m "
                    "ser\u00e3o removidas."
                ),
                font=("Arial", 13),
                text_color=theme.COLOR_TEXT_MUTED,
                justify="center",
                wraplength=380,
            ).pack(
                padx=24,
                pady=(0, 18),
            )

            botoes_confirmacao = ctk.CTkFrame(
                janela_confirmacao,
                fg_color="transparent",
            )
            botoes_confirmacao.pack(
                fill="x",
                padx=24,
                pady=(0, 22),
            )

            def executar_exclusao():
                try:
                    excluir_missao(missao_id)
                    janela_confirmacao.destroy()
                    self.tela_agente_ia()

                except Exception as erro:
                    print(
                        f"Erro ao excluir miss\u00e3o: {erro}"
                    )

            ctk.CTkButton(
                botoes_confirmacao,
                text="Cancelar",
                command=janela_confirmacao.destroy,
                height=36,
                corner_radius=9,
                fg_color=theme.COLOR_CARD_HOVER,
                hover_color=theme.COLOR_BORDER,
                font=("Arial", 12, "bold"),
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=(0, 6),
            )

            ctk.CTkButton(
                botoes_confirmacao,
                text="Excluir",
                command=executar_exclusao,
                height=36,
                corner_radius=9,
                fg_color="#C62828",
                hover_color="#8E0000",
                font=("Arial", 12, "bold"),
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=(6, 0),
            )

        if not missoes:
            ctk.CTkLabel(
                history_card,
                text="Nenhuma missão cadastrada.",
                font=("Arial", 13, "bold"),
                text_color=theme.COLOR_TEXT
            ).pack(anchor="w", padx=20, pady=(0, 2))

        else:
            for missao in missoes:
                missao_id = missao.get("id")
                quantidade_oportunidades = 0

                try:
                    quantidade_oportunidades = oportunidades_por_missao.get(
                        int(missao_id),
                        0,
                    )
                except (TypeError, ValueError):
                    quantidade_oportunidades = 0

                resumo_card_missao = gerar_resumo_missao(
                    missao_id
                )

                total_excelentes = resumo_card_missao.get(
                    "excelentes",
                    0,
                )
                melhor_score_card = resumo_card_missao.get(
                    "melhor_score",
                    0,
                )
                melhor_preco_card = resumo_card_missao.get(
                    "melhor_preco",
                    0,
                )

                try:
                    melhor_preco_numerico = float(
                        melhor_preco_card
                    )
                    melhor_preco_formatado = (
                        f"R$ {melhor_preco_numerico:,.2f}"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                    )
                except (TypeError, ValueError):
                    melhor_preco_formatado = "R$ 0,00"

                try:
                    orcamento_numerico = float(
                        missao.get("orcamento", 0)
                    )
                    orcamento_formatado = (
                        f"R$ {orcamento_numerico:,.2f}"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                    )
                except (TypeError, ValueError):
                    orcamento_formatado = "R$ 0,00"

                estrategia_card = str(
                    missao.get(
                        "estrategia",
                        "-",
                    )
                )

                data_criacao_card = str(
                    missao.get(
                        "data_criacao",
                        "",
                    )
                )

                try:
                    data_criacao_formatada = datetime.fromisoformat(
                        data_criacao_card
                    ).strftime("%d/%m/%Y")
                except (TypeError, ValueError):
                    data_criacao_formatada = "N\u00e3o informada"

                missao_frame = ctk.CTkFrame(
                    history_card,
                    fg_color=theme.COLOR_CARD_HOVER,
                    corner_radius=12
                )
                missao_frame.pack(fill="x", padx=16, pady=6)

                ctk.CTkLabel(
                    missao_frame,
                    text=f"ID: {missao_id if missao_id is not None else '-'}",
                    font=("Arial", 12, "bold"),
                    text_color=theme.COLOR_TEXT
                ).pack(anchor="w", padx=12, pady=(8, 0))

                ctk.CTkLabel(
                    missao_frame,
                    text=(
                        f"{missao.get('marca', '-')} "
                        f"{missao.get('modelo', '-')}"
                    ),
                    font=("Arial", 13),
                    text_color=theme.COLOR_TEXT
                ).pack(anchor="w", padx=12)

                indicadores_missao = [
                    (
                        "OPORTUNIDADES",
                        str(quantidade_oportunidades),
                        theme.COLOR_GREEN,
                    ),
                    (
                        "EXCELENTES",
                        str(total_excelentes),
                        theme.COLOR_PURPLE,
                    ),
                    (
                        "MELHOR SCORE",
                        f"{melhor_score_card}/100",
                        theme.COLOR_TEXT,
                    ),
                    (
                        "MELHOR PRE\u00c7O",
                        melhor_preco_formatado,
                        theme.COLOR_GREEN,
                    ),
                ]

                indicadores_frame = ctk.CTkFrame(
                    missao_frame,
                    fg_color="transparent",
                )
                indicadores_frame.pack(
                    fill="x",
                    padx=12,
                    pady=(8, 5),
                )

                indicadores_frame.grid_columnconfigure(
                    0,
                    weight=1,
                )
                indicadores_frame.grid_columnconfigure(
                    1,
                    weight=1,
                )

                for indice_indicador, (
                    titulo_indicador,
                    valor_indicador,
                    cor_indicador,
                ) in enumerate(indicadores_missao):
                    linha_indicador = indice_indicador // 2
                    coluna_indicador = indice_indicador % 2

                    mini_card = ctk.CTkFrame(
                        indicadores_frame,
                        fg_color=theme.COLOR_CARD,
                        corner_radius=9,
                        border_width=1,
                        border_color=theme.COLOR_BORDER,
                    )
                    mini_card.grid(
                        row=linha_indicador,
                        column=coluna_indicador,
                        sticky="nsew",
                        padx=(
                            (0, 4)
                            if coluna_indicador == 0
                            else (4, 0)
                        ),
                        pady=4,
                    )

                    ctk.CTkLabel(
                        mini_card,
                        text=titulo_indicador,
                        font=("Arial", 9, "bold"),
                        text_color=theme.COLOR_TEXT_MUTED,
                    ).pack(
                        anchor="w",
                        padx=10,
                        pady=(8, 1),
                    )

                    ctk.CTkLabel(
                        mini_card,
                        text=valor_indicador,
                        font=("Arial", 13, "bold"),
                        text_color=cor_indicador,
                    ).pack(
                        anchor="w",
                        padx=10,
                        pady=(0, 8),
                    )

                informacoes_missao = ctk.CTkFrame(
                    missao_frame,
                    fg_color="transparent",
                )
                informacoes_missao.pack(
                    fill="x",
                    padx=12,
                    pady=(4, 8),
                )

                ctk.CTkLabel(
                    informacoes_missao,
                    text=(
                        "Or\u00e7amento: "
                        f"{orcamento_formatado}"
                    ),
                    font=("Arial", 11),
                    text_color=theme.COLOR_TEXT_MUTED,
                ).pack(
                    anchor="w",
                    pady=1,
                )

                ctk.CTkLabel(
                    informacoes_missao,
                    text=(
                        "Estrat\u00e9gia: "
                        f"{estrategia_card}"
                    ),
                    font=("Arial", 11),
                    text_color=theme.COLOR_TEXT_MUTED,
                ).pack(
                    anchor="w",
                    pady=1,
                )

                ctk.CTkLabel(
                    informacoes_missao,
                    text=(
                        "Criada em: "
                        f"{data_criacao_formatada}"
                    ),
                    font=("Arial", 11),
                    text_color=theme.COLOR_TEXT_MUTED,
                ).pack(
                    anchor="w",
                    pady=1,
                )

                status_missao = str(
                    missao.get(
                        "status",
                        "-",
                    )
                ).strip().upper()

                cores_status = {
                    "PENDENTE": theme.COLOR_GREEN,
                    "EM_EXECUCAO": theme.COLOR_BLUE,
                    "NEGOCIANDO": theme.COLOR_YELLOW,
                    "CANCELADA": "#FF5C5C",
                    "FINALIZADA": theme.COLOR_TEXT_MUTED,
                    "COMPRADA": theme.COLOR_PURPLE,
                }

                cor_status = cores_status.get(
                    status_missao,
                    theme.COLOR_TEXT_MUTED,
                )

                icones_status = {
                    "PENDENTE": "\u23f3",
                    "EM_EXECUCAO": "\U0001f50e",
                    "NEGOCIANDO": "\U0001f91d",
                    "COMPRADA": "\U0001f3c6",
                    "FINALIZADA": "\u2714",
                    "CANCELADA": "\u2716",
                }

                icone_status = icones_status.get(
                    status_missao,
                    "\u2022",
                )

                ctk.CTkLabel(
                    missao_frame,
                    text=(
                        f"{icone_status} "
                        f"{status_missao}"
                    ),
                    font=("Arial", 12, "bold"),
                    text_color=cor_status,
                ).pack(
                    anchor="w",
                    padx=12,
                    pady=(0, 4),
                )

                etapas_timeline = [
                    "CAPTURA",
                    "AN\u00c1LISE",
                    "IA",
                    "NEGOCIA\u00c7\u00c3O",
                    "COMPRA",
                ]

                etapas_concluidas_por_status = {
                    "PENDENTE": 0,
                    "EM_EXECUCAO": 2,
                    "NEGOCIANDO": 3,
                    "COMPRADA": 5,
                    "FINALIZADA": 5,
                    "CANCELADA": 0,
                }

                total_etapas_concluidas = (
                    etapas_concluidas_por_status.get(
                        status_missao,
                        0,
                    )
                )

                timeline_missao = ctk.CTkFrame(
                    missao_frame,
                    fg_color="transparent",
                )
                timeline_missao.pack(
                    fill="x",
                    padx=12,
                    pady=(3, 8),
                )

                for coluna_etapa, nome_etapa in enumerate(
                    etapas_timeline
                ):
                    timeline_missao.grid_columnconfigure(
                        coluna_etapa,
                        weight=1,
                    )

                    etapa_concluida = (
                        coluna_etapa
                        < total_etapas_concluidas
                    )

                    etapa_atual = (
                        coluna_etapa
                        == total_etapas_concluidas
                        and status_missao not in {
                            "COMPRADA",
                            "FINALIZADA",
                            "CANCELADA",
                        }
                    )

                    if status_missao == "CANCELADA":
                        simbolo_etapa = "\u2716"
                        cor_etapa = "#FF5C5C"

                    elif etapa_concluida:
                        simbolo_etapa = "\u2714"
                        cor_etapa = theme.COLOR_GREEN

                    elif etapa_atual:
                        simbolo_etapa = "\u25cf"
                        cor_etapa = cor_status

                    else:
                        simbolo_etapa = "\u25cb"
                        cor_etapa = theme.COLOR_TEXT_MUTED

                    etapa_frame = ctk.CTkFrame(
                        timeline_missao,
                        fg_color="transparent",
                    )
                    etapa_frame.grid(
                        row=0,
                        column=coluna_etapa,
                        sticky="nsew",
                    )

                    ctk.CTkLabel(
                        etapa_frame,
                        text=simbolo_etapa,
                        font=("Arial", 13, "bold"),
                        text_color=cor_etapa,
                    ).pack(
                        pady=(0, 1),
                    )

                    ctk.CTkLabel(
                        etapa_frame,
                        text=nome_etapa,
                        font=("Arial", 7, "bold"),
                        text_color=cor_etapa,
                    ).pack()

                progresso_por_status = {
                    "PENDENTE": 0.20,
                    "EM_EXECUCAO": 0.45,
                    "NEGOCIANDO": 0.70,
                    "COMPRADA": 1.00,
                    "FINALIZADA": 1.00,
                    "CANCELADA": 0.00,
                }

                valor_progresso = progresso_por_status.get(
                    status_missao,
                    0.0,
                )

                percentual_progresso = int(
                    valor_progresso * 100
                )

                ctk.CTkLabel(
                    missao_frame,
                    text=(
                        "Progresso da miss\u00e3o: "
                        f"{percentual_progresso}%"
                    ),
                    font=("Arial", 11, "bold"),
                    text_color=theme.COLOR_TEXT_MUTED,
                ).pack(
                    anchor="w",
                    padx=12,
                    pady=(0, 4),
                )

                progresso_missao = ctk.CTkProgressBar(
                    missao_frame,
                    height=10,
                    corner_radius=6,
                    fg_color=theme.COLOR_BORDER,
                    progress_color=cor_status,
                )
                progresso_missao.pack(
                    fill="x",
                    padx=12,
                    pady=(0, 10),
                )
                progresso_missao.set(
                    valor_progresso
                )

                decisoes_missao = listar_decisoes_missao(
                    missao_id,
                    limite=1,
                )

                ultima_decisao_frame = ctk.CTkFrame(
                    missao_frame,
                    fg_color=theme.COLOR_CARD,
                    corner_radius=10,
                    border_width=1,
                    border_color=theme.COLOR_BORDER,
                )
                ultima_decisao_frame.pack(
                    fill="x",
                    padx=12,
                    pady=(0, 10),
                )

                ctk.CTkLabel(
                    ultima_decisao_frame,
                    text="\u00daltima decis\u00e3o da IA",
                    font=("Arial", 11, "bold"),
                    text_color=theme.COLOR_BLUE,
                ).pack(
                    anchor="w",
                    padx=10,
                    pady=(8, 3),
                )

                if decisoes_missao:
                    ultima_decisao = decisoes_missao[0]

                    titulo_decisao = str(
                        ultima_decisao.get(
                            "titulo",
                            "An?ncio sem t?tulo",
                        )
                    )

                    recomendacao_decisao = str(
                        ultima_decisao.get(
                            "recomendacao",
                            "-",
                        )
                    )

                    score_decisao = ultima_decisao.get(
                        "score",
                        0,
                    )

                    texto_decisao = str(
                        ultima_decisao.get(
                            "decisao",
                            "Sem a??o recomendada.",
                        )
                    )

                    ctk.CTkLabel(
                        ultima_decisao_frame,
                        text=titulo_decisao,
                        font=("Arial", 11, "bold"),
                        text_color=theme.COLOR_TEXT,
                        anchor="w",
                        justify="left",
                        wraplength=300,
                    ).pack(
                        fill="x",
                        padx=10,
                        pady=(0, 2),
                    )

                    ctk.CTkLabel(
                        ultima_decisao_frame,
                        text=(
                            f"Score {score_decisao} ? "
                            f"{recomendacao_decisao}"
                        ),
                        font=("Arial", 10, "bold"),
                        text_color=theme.COLOR_GREEN,
                    ).pack(
                        anchor="w",
                        padx=10,
                        pady=(0, 3),
                    )

                    ctk.CTkLabel(
                        ultima_decisao_frame,
                        text=texto_decisao,
                        font=("Arial", 10),
                        text_color=theme.COLOR_TEXT_MUTED,
                        anchor="w",
                        justify="left",
                        wraplength=300,
                    ).pack(
                        fill="x",
                        padx=10,
                        pady=(0, 8),
                    )

                else:
                    ctk.CTkLabel(
                        ultima_decisao_frame,
                        text=(
                            "Aguardando nova decis\u00e3o "
                            "do Agent Alpha."
                        ),
                        font=("Arial", 10),
                        text_color=theme.COLOR_TEXT_MUTED,
                    ).pack(
                        anchor="w",
                        padx=10,
                        pady=(0, 8),
                    )

                botoes_missao = ctk.CTkFrame(
                    missao_frame,
                    fg_color="transparent",
                )
                botoes_missao.pack(
                    fill="x",
                    padx=12,
                    pady=(0, 10),
                )

                if quantidade_oportunidades > 0:
                    ctk.CTkButton(
                        botoes_missao,
                        text="Ver",
                        command=lambda m=missao: (
                            self.abrir_oportunidades_missao(m)
                        ),
                        height=32,
                        corner_radius=9,
                        fg_color=theme.COLOR_GREEN,
                        hover_color=theme.COLOR_GREEN_DARK,
                        font=("Arial", 11, "bold"),
                    ).pack(
                        side="left",
                        fill="x",
                        expand=True,
                        padx=(0, 4),
                    )

                ctk.CTkButton(
                    botoes_missao,
                    text="Editar",
                    command=lambda m=missao: (
                        abrir_edicao_missao(m)
                    ),
                    height=32,
                    corner_radius=9,
                    fg_color="#1565C0",
                    hover_color="#0D47A1",
                    font=("Arial", 11, "bold"),
                ).pack(
                    side="left",
                    fill="x",
                    expand=True,
                    padx=(
                        4 if quantidade_oportunidades > 0 else 0,
                        4,
                    ),
                )

                ctk.CTkButton(
                    botoes_missao,
                    text="Excluir",
                    command=lambda m=missao: (
                        confirmar_exclusao_missao(m)
                    ),
                    height=32,
                    corner_radius=9,
                    fg_color="#C62828",
                    hover_color="#8E0000",
                    font=("Arial", 11, "bold"),
                ).pack(
                    side="left",
                    fill="x",
                    expand=True,
                    padx=(4, 0),
                )

        # Card inferior
        bottom_card = ctk.CTkFrame(
            side_column,
            fg_color=theme.COLOR_CARD_HOVER,
            corner_radius=14
        )
        bottom_card.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            bottom_card,
            text="TH Agent Alpha",
            font=("Arial", 13, "bold"),
            text_color=theme.COLOR_TEXT
        ).pack(anchor="w", padx=12, pady=(10, 0))

        ctk.CTkLabel(
            bottom_card,
            text="Modo Copiloto",
            font=("Arial", 12),
            text_color=theme.COLOR_TEXT_MUTED
        ).pack(anchor="w", padx=12)

        ctk.CTkLabel(
            bottom_card,
            text="IA ainda não habilitada.",
            font=("Arial", 12),
            text_color=theme.COLOR_TEXT_MUTED
        ).pack(anchor="w", padx=12, pady=(0, 10))

    def tela_memoria_ia(self):
        self.limpar_content()

        frame = ctk.CTkFrame(
            self.content,
            fg_color="transparent",
        )
        frame.pack(
            fill="both",
            expand=True,
            padx=32,
            pady=28,
        )

        ctk.CTkLabel(
            frame,
            text="\U0001f9e0 Mem\u00f3ria do Agent Alpha",
            font=("Arial", 32, "bold"),
            text_color=theme.COLOR_TEXT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            frame,
            text=(
                "Hist\u00f3rico completo das decis\u00f5es "
                "tomadas pela IA."
            ),
            font=("Arial", 16),
            text_color=theme.COLOR_TEXT_MUTED,
        ).pack(
            anchor="w",
            pady=(4, 20),
        )

        decisoes = carregar_decisoes()


        total_excelentes_memoria = sum(
            1
            for item in decisoes
            if str(
                item.get("recomendacao", "")
            ).strip().upper() == "EXCELENTE"
        )

        total_boas_memoria = sum(
            1
            for item in decisoes
            if str(
                item.get("recomendacao", "")
            ).strip().upper() == "BOA"
        )

        total_regulares_memoria = sum(
            1
            for item in decisoes
            if str(
                item.get("recomendacao", "")
            ).strip().upper() == "REGULAR"
        )

        total_descartadas_memoria = sum(
            1
            for item in decisoes
            if str(
                item.get("recomendacao", "")
            ).strip().upper() == "DESCARTADA"
        )

        estatisticas_memoria = ctk.CTkFrame(
            frame,
            fg_color="transparent",
        )
        estatisticas_memoria.pack(
            fill="x",
            pady=(12, 18),
        )

        for coluna in range(5):
            estatisticas_memoria.grid_columnconfigure(
                coluna,
                weight=1,
            )

        dados_estatisticas = [
            (
                "TOTAL",
                len(decisoes),
                theme.COLOR_BLUE,
            ),
            (
                "EXCELENTES",
                total_excelentes_memoria,
                theme.COLOR_GREEN,
            ),
            (
                "BOAS",
                total_boas_memoria,
                theme.COLOR_BLUE,
            ),
            (
                "REGULARES",
                total_regulares_memoria,
                theme.COLOR_YELLOW,
            ),
            (
                "DESCARTADAS",
                total_descartadas_memoria,
                "#FF5C5C",
            ),
        ]

        for coluna, (
            titulo_estatistica,
            valor_estatistica,
            cor_estatistica,
        ) in enumerate(dados_estatisticas):
            card_estatistica = ctk.CTkFrame(
                estatisticas_memoria,
                fg_color=theme.COLOR_CARD_HOVER,
                corner_radius=14,
                border_width=1,
                border_color=theme.COLOR_BORDER,
            )
            card_estatistica.grid(
                row=0,
                column=coluna,
                sticky="nsew",
                padx=5,
            )

            ctk.CTkLabel(
                card_estatistica,
                text=titulo_estatistica,
                font=("Arial", 10, "bold"),
                text_color=theme.COLOR_TEXT_MUTED,
            ).pack(
                anchor="w",
                padx=12,
                pady=(12, 3),
            )

            ctk.CTkLabel(
                card_estatistica,
                text=str(valor_estatistica),
                font=("Arial", 22, "bold"),
                text_color=cor_estatistica,
            ).pack(
                anchor="w",
                padx=12,
                pady=(0, 12),
            )


        decisoes_ordenadas = sorted(
            decisoes,
            key=lambda item: str(
                item.get(
                    "data_hora",
                    "",
                )
            ),
            reverse=True,
        )

        missoes_memoria = listar_missoes()

        opcoes_missao = [
            "Todas as miss\u00f5es"
        ]

        mapa_missoes_memoria = {
            "Todas as miss\u00f5es": None
        }

        for missao_memoria in missoes_memoria:
            id_missao_memoria = missao_memoria.get(
                "id",
                "-",
            )

            marca_missao_memoria = str(
                missao_memoria.get(
                    "marca",
                    "-",
                )
            )

            modelo_missao_memoria = str(
                missao_memoria.get(
                    "modelo",
                    "-",
                )
            )

            nome_opcao_missao = (
                f"Miss\u00e3o #{id_missao_memoria} - "
                f"{marca_missao_memoria} "
                f"{modelo_missao_memoria}"
            )

            opcoes_missao.append(
                nome_opcao_missao
            )

            try:
                mapa_missoes_memoria[
                    nome_opcao_missao
                ] = int(id_missao_memoria)

            except (TypeError, ValueError):
                mapa_missoes_memoria[
                    nome_opcao_missao
                ] = id_missao_memoria

        seletor_missao_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent",
        )
        seletor_missao_frame.pack(
            fill="x",
            pady=(0, 10),
        )

        ctk.CTkLabel(
            seletor_missao_frame,
            text="Filtrar por miss\u00e3o:",
            font=("Arial", 12, "bold"),
            text_color=theme.COLOR_TEXT,
        ).pack(
            side="left",
            padx=(0, 10),
        )

        combo_filtro_missao = ctk.CTkComboBox(
            seletor_missao_frame,
            values=opcoes_missao,
            height=34,
            corner_radius=9,
            fg_color=theme.COLOR_CARD_HOVER,
            border_color=theme.COLOR_BORDER,
            button_color=theme.COLOR_BLUE,
            button_hover_color="#0D47A1",
            text_color=theme.COLOR_TEXT,
            state="readonly",
            width=340,
        )
        combo_filtro_missao.pack(
            side="left",
        )
        combo_filtro_missao.set(
            "Todas as miss\u00f5es"
        )

        estado_filtro_memoria = {
            "recomendacao": "TODAS",
        }

        estado_paginacao_memoria = {
            "pagina_atual": 0,
            "itens_por_pagina": 25,
            "total_paginas": 1,
        }

        busca_memoria_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent",
        )
        busca_memoria_frame.pack(
            fill="x",
            pady=(0, 10),
        )

        ctk.CTkLabel(
            busca_memoria_frame,
            text="Pesquisar na mem\u00f3ria:",
            font=("Arial", 12, "bold"),
            text_color=theme.COLOR_TEXT,
        ).pack(
            side="left",
            padx=(0, 10),
        )

        campo_busca_memoria = ctk.CTkEntry(
            busca_memoria_frame,
            height=34,
            corner_radius=9,
            fg_color=theme.COLOR_CARD_HOVER,
            border_color=theme.COLOR_BORDER,
            text_color=theme.COLOR_TEXT,
            placeholder_text=(
                "Digite modelo, resumo ou a\u00e7\u00e3o..."
            ),
        )
        campo_busca_memoria.pack(
            side="left",
            fill="x",
            expand=True,
        )

        filtros_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent",
        )
        filtros_frame.pack(
            fill="x",
            pady=(0, 10),
        )

        paginacao_memoria_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent",
        )
        paginacao_memoria_frame.pack(
            fill="x",
            pady=(0, 8),
        )

        botao_pagina_anterior = ctk.CTkButton(
            paginacao_memoria_frame,
            text="← Anterior",
            width=110,
            height=32,
            corner_radius=9,
            fg_color=theme.COLOR_CARD_HOVER,
            hover_color=theme.COLOR_BORDER,
            font=("Arial", 11, "bold"),
            state="disabled",
        )
        botao_pagina_anterior.pack(
            side="left",
        )

        label_paginacao_memoria = ctk.CTkLabel(
            paginacao_memoria_frame,
            text="Página 1 de 1",
            font=("Arial", 11, "bold"),
            text_color=theme.COLOR_TEXT_MUTED,
        )
        label_paginacao_memoria.pack(
            side="left",
            expand=True,
        )

        botao_proxima_pagina = ctk.CTkButton(
            paginacao_memoria_frame,
            text="Próxima →",
            width=110,
            height=32,
            corner_radius=9,
            fg_color=theme.COLOR_CARD_HOVER,
            hover_color=theme.COLOR_BORDER,
            font=("Arial", 11, "bold"),
            state="disabled",
        )
        botao_proxima_pagina.pack(
            side="right",
        )

        lista_decisoes = ctk.CTkScrollableFrame(
            frame,
            fg_color="transparent",
        )
        lista_decisoes.pack(
            fill="both",
            expand=True,
            pady=(4, 0),
        )

        botoes_filtro = {}

        cores_recomendacao = {
            "EXCELENTE": theme.COLOR_GREEN,
            "BOA": theme.COLOR_BLUE,
            "REGULAR": theme.COLOR_YELLOW,
            "DESCARTADA": "#FF5C5C",
        }

        def abrir_raciocinio_ia(decisao):
            janela_raciocinio = ctk.CTkToplevel(self)
            janela_raciocinio.title(
                "Racioc\u00ednio do Agent Alpha"
            )
            janela_raciocinio.geometry("760x650")
            janela_raciocinio.minsize(650, 520)
            janela_raciocinio.configure(
                fg_color=theme.COLOR_BG
            )
            janela_raciocinio.transient(self)
            janela_raciocinio.grab_set()

            conteudo = ctk.CTkScrollableFrame(
                janela_raciocinio,
                fg_color="transparent",
            )
            conteudo.pack(
                fill="both",
                expand=True,
                padx=24,
                pady=24,
            )

            titulo = str(
                decisao.get(
                    "titulo",
                    "An\u00fancio sem t\u00edtulo",
                )
            )

            ctk.CTkLabel(
                conteudo,
                text=titulo,
                font=("Arial", 24, "bold"),
                text_color=theme.COLOR_TEXT,
                anchor="w",
                justify="left",
                wraplength=660,
            ).pack(
                fill="x",
                anchor="w",
                pady=(0, 10),
            )

            ctk.CTkLabel(
                conteudo,
                text=(
                    f"Miss\u00e3o #{decisao.get('missao_id', '-')}  "
                    f"\u2022  Score {decisao.get('score', 0)}  "
                    f"\u2022  {decisao.get('recomendacao', '-')}"
                ),
                font=("Arial", 13, "bold"),
                text_color=theme.COLOR_BLUE,
            ).pack(
                anchor="w",
                pady=(0, 16),
            )

            def adicionar_secao(
                titulo_secao,
                conteudo_secao,
                cor_titulo,
            ):
                card_secao = ctk.CTkFrame(
                    conteudo,
                    fg_color=theme.COLOR_CARD_HOVER,
                    corner_radius=12,
                    border_width=1,
                    border_color=theme.COLOR_BORDER,
                )
                card_secao.pack(
                    fill="x",
                    pady=7,
                )

                ctk.CTkLabel(
                    card_secao,
                    text=titulo_secao,
                    font=("Arial", 14, "bold"),
                    text_color=cor_titulo,
                ).pack(
                    anchor="w",
                    padx=14,
                    pady=(12, 6),
                )

                ctk.CTkLabel(
                    card_secao,
                    text=conteudo_secao,
                    font=("Arial", 12),
                    text_color=theme.COLOR_TEXT,
                    anchor="w",
                    justify="left",
                    wraplength=650,
                ).pack(
                    fill="x",
                    padx=14,
                    pady=(0, 12),
                )

            motivos = decisao.get(
                "motivos",
                [],
            )

            if isinstance(motivos, list) and motivos:
                texto_motivos = "\n".join(
                    f"\u2714 {item}"
                    for item in motivos
                )
            else:
                texto_motivos = (
                    "Nenhum motivo detalhado registrado."
                )

            adicionar_secao(
                "Por que a IA chegou a essa conclus\u00e3o?",
                texto_motivos,
                theme.COLOR_GREEN,
            )

            alertas = decisao.get(
                "alertas",
                [],
            )

            if isinstance(alertas, list) and alertas:
                texto_alertas = "\n".join(
                    f"\u26a0 {item}"
                    for item in alertas
                )
            else:
                texto_alertas = (
                    "Nenhum alerta identificado."
                )

            adicionar_secao(
                "Alertas",
                texto_alertas,
                theme.COLOR_YELLOW,
            )

            checklist = decisao.get(
                "checklist",
                [],
            )

            if isinstance(checklist, list) and checklist:
                texto_checklist = "\n".join(
                    f"\u2022 {item}"
                    for item in checklist
                )
            else:
                texto_checklist = (
                    "Nenhum checklist registrado."
                )

            adicionar_secao(
                "Checklist de verifica\u00e7\u00e3o",
                texto_checklist,
                theme.COLOR_BLUE,
            )

            preco = decisao.get(
                "preco",
                0,
            )
            primeira_oferta = decisao.get(
                "primeira_oferta_sugerida"
            )
            preco_maximo = decisao.get(
                "preco_maximo_recomendado"
            )

            def formatar_moeda(valor):
                if valor is None:
                    return "N\u00e3o dispon\u00edvel"

                try:
                    valor = float(valor)
                except (TypeError, ValueError):
                    return "N\u00e3o dispon\u00edvel"

                return (
                    f"R$ {valor:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )

            texto_financeiro = (
                "Pre\u00e7o do an\u00fancio: "
                f"{formatar_moeda(preco)}\n\n"
                "Recomenda\u00e7\u00e3o para este an\u00fancio:\n"
                "Primeira oferta sugerida: "
                f"{formatar_moeda(primeira_oferta)}\n"
                "Pre\u00e7o m\u00e1ximo recomendado: "
                f"{formatar_moeda(preco_maximo)}"
            )

            # Estrategia GERAL da missao (nao especifica deste anuncio) --
            # buscada ao vivo em missions.json pelo missao_id da decisao,
            # para funcionar tanto em registros novos quanto antigos (que
            # nao guardam primeira_oferta_missao/limite_final_missao).
            # Se a missao nao existir mais, a secao e omitida -- nunca
            # inventa um valor.
            try:
                missoes_atuais = listar_missoes()
            except Exception:
                missoes_atuais = []

            missao_relacionada = next(
                (
                    m
                    for m in missoes_atuais
                    if isinstance(m, dict)
                    and m.get("id") == decisao.get("missao_id")
                ),
                None,
            )

            if missao_relacionada:
                texto_financeiro += (
                    "\n\nEstrat\u00e9gia da miss\u00e3o:\n"
                    "Primeira oferta da miss\u00e3o: "
                    f"{formatar_moeda(missao_relacionada.get('primeira_oferta'))}\n"
                    "Limite da miss\u00e3o: "
                    f"{formatar_moeda(missao_relacionada.get('limite_final'))}"
                )

            adicionar_secao(
                "Dados financeiros",
                texto_financeiro,
                theme.COLOR_PURPLE,
            )

            resumo = str(
                decisao.get(
                    "resumo",
                    "Sem resumo registrado.",
                )
            )

            adicionar_secao(
                "Resumo da an\u00e1lise",
                resumo,
                theme.COLOR_TEXT,
            )

            acao = str(
                decisao.get(
                    "decisao",
                    "Sem a\u00e7\u00e3o recomendada.",
                )
            )

            adicionar_secao(
                "Pr\u00f3xima a\u00e7\u00e3o",
                acao,
                theme.COLOR_GREEN,
            )


        def renderizar_decisoes_memoria(
            filtro="TODAS",
            resetar_pagina=False,
        ):
            estado_filtro_memoria[
                "recomendacao"
            ] = filtro

            if resetar_pagina:
                estado_paginacao_memoria[
                    "pagina_atual"
                ] = 0

            for widget in lista_decisoes.winfo_children():
                widget.destroy()

            for nome_filtro, botao_filtro in (
                botoes_filtro.items()
            ):
                ativo = nome_filtro == filtro

                botao_filtro.configure(
                    fg_color=(
                        theme.COLOR_GREEN
                        if ativo
                        else theme.COLOR_CARD_HOVER
                    ),
                    hover_color=(
                        theme.COLOR_GREEN_DARK
                        if ativo
                        else theme.COLOR_BORDER
                    ),
                )

            if filtro == "TODAS":
                decisoes_filtradas = decisoes_ordenadas
            else:
                recomendacao_filtro = {
                    "EXCELENTES": "EXCELENTE",
                    "BOAS": "BOA",
                    "REGULARES": "REGULAR",
                    "DESCARTADAS": "DESCARTADA",
                }.get(
                    filtro,
                    "",
                )

                decisoes_filtradas = [
                    decisao
                    for decisao in decisoes_ordenadas
                    if str(
                        decisao.get(
                            "recomendacao",
                            "",
                        )
                    ).strip().upper()
                    == recomendacao_filtro
                ]

            opcao_missao_selecionada = (
                combo_filtro_missao.get()
            )

            missao_id_selecionada = (
                mapa_missoes_memoria.get(
                    opcao_missao_selecionada
                )
            )

            if missao_id_selecionada is not None:
                decisoes_filtradas = [
                    decisao
                    for decisao in decisoes_filtradas
                    if str(
                        decisao.get(
                            "missao_id",
                            "",
                        )
                    )
                    == str(missao_id_selecionada)
                ]

            termo_busca_memoria = (
                campo_busca_memoria.get()
                .strip()
                .casefold()
            )

            if termo_busca_memoria:
                decisoes_filtradas = [
                    decisao
                    for decisao in decisoes_filtradas
                    if termo_busca_memoria
                    in " ".join(
                        [
                            str(
                                decisao.get(
                                    "titulo",
                                    "",
                                )
                            ),
                            str(
                                decisao.get(
                                    "resumo",
                                    "",
                                )
                            ),
                            str(
                                decisao.get(
                                    "decisao",
                                    "",
                                )
                            ),
                            str(
                                decisao.get(
                                    "recomendacao",
                                    "",
                                )
                            ),
                        ]
                    ).casefold()
                ]

            total_decisoes_filtradas = len(
                decisoes_filtradas
            )

            itens_por_pagina = (
                estado_paginacao_memoria[
                    "itens_por_pagina"
                ]
            )

            total_paginas = max(
                1,
                (
                    total_decisoes_filtradas
                    + itens_por_pagina
                    - 1
                )
                // itens_por_pagina,
            )

            estado_paginacao_memoria[
                "total_paginas"
            ] = total_paginas

            pagina_atual = (
                estado_paginacao_memoria[
                    "pagina_atual"
                ]
            )

            pagina_atual = max(
                0,
                min(
                    pagina_atual,
                    total_paginas - 1,
                ),
            )

            estado_paginacao_memoria[
                "pagina_atual"
            ] = pagina_atual

            label_paginacao_memoria.configure(
                text=(
                    f"Página {pagina_atual + 1} "
                    f"de {total_paginas}  •  "
                    f"{total_decisoes_filtradas} decisões"
                )
            )

            botao_pagina_anterior.configure(
                state=(
                    "normal"
                    if pagina_atual > 0
                    else "disabled"
                )
            )

            botao_proxima_pagina.configure(
                state=(
                    "normal"
                    if pagina_atual < total_paginas - 1
                    else "disabled"
                )
            )

            if not decisoes_filtradas:
                ctk.CTkLabel(
                    lista_decisoes,
                    text=(
                        "Nenhuma decis\u00e3o encontrada "
                        "para este filtro."
                    ),
                    font=("Arial", 14),
                    text_color=theme.COLOR_TEXT_MUTED,
                ).pack(
                    anchor="w",
                    padx=4,
                    pady=24,
                )
                return

            indice_inicial = (
                pagina_atual
                * itens_por_pagina
            )
            indice_final = (
                indice_inicial
                + itens_por_pagina
            )

            decisoes_da_pagina = (
                decisoes_filtradas[
                    indice_inicial:indice_final
                ]
            )

            for decisao in decisoes_da_pagina:
                recomendacao = str(
                    decisao.get(
                        "recomendacao",
                        "-",
                    )
                ).strip().upper()

                cor_recomendacao = (
                    cores_recomendacao.get(
                        recomendacao,
                        theme.COLOR_TEXT_MUTED,
                    )
                )

                card_decisao = ctk.CTkFrame(
                    lista_decisoes,
                    fg_color=theme.COLOR_CARD_HOVER,
                    corner_radius=14,
                    border_width=1,
                    border_color=theme.COLOR_BORDER,
                )
                card_decisao.pack(
                    fill="x",
                    padx=4,
                    pady=7,
                )

                titulo_card_decisao = str(
                    decisao.get(
                        "titulo",
                        "An\u00fancio sem t\u00edtulo",
                    )
                ).strip()

                data_card_decisao = str(
                    decisao.get(
                        "data_hora",
                        "-",
                    )
                ).strip()

                link_card_decisao = str(
                    decisao.get(
                        "anuncio_link",
                        "",
                    )
                ).strip().casefold()

                if "olx" in link_card_decisao:
                    fonte_decisao = "OLX"
                elif "mercadolivre" in link_card_decisao:
                    fonte_decisao = "Mercado Livre"
                else:
                    fonte_decisao = "An\u00fancio"

                cabecalho_decisao = ctk.CTkFrame(
                    card_decisao,
                    fg_color="transparent",
                )
                cabecalho_decisao.pack(
                    fill="x",
                    padx=14,
                    pady=(14, 4),
                )

                area_titulo_decisao = ctk.CTkFrame(
                    cabecalho_decisao,
                    fg_color="transparent",
                )
                area_titulo_decisao.pack(
                    side="left",
                    fill="x",
                    expand=True,
                )

                ctk.CTkLabel(
                    area_titulo_decisao,
                    text=titulo_card_decisao,
                    font=("Arial", 17, "bold"),
                    text_color=theme.COLOR_TEXT,
                    anchor="w",
                    justify="left",
                    wraplength=760,
                ).pack(
                    fill="x",
                    anchor="w",
                )

                ctk.CTkLabel(
                    area_titulo_decisao,
                    text=f"Fonte: {fonte_decisao}",
                    font=("Arial", 10, "bold"),
                    text_color=theme.COLOR_TEXT_MUTED,
                ).pack(
                    anchor="w",
                    pady=(3, 0),
                )

                missao_id_decisao = decisao.get(
                    "missao_id",
                    "-",
                )
                score_decisao = decisao.get(
                    "score",
                    0,
                )

                confianca_decisao = decisao.get(
                    "confianca",
                    0,
                )

                try:
                    confianca_decisao = int(
                        float(confianca_decisao)
                    )
                except (TypeError, ValueError):
                    confianca_decisao = 0

                confianca_decisao = max(
                    0,
                    min(
                        confianca_decisao,
                        100,
                    ),
                )

                if confianca_decisao >= 85:
                    nivel_confianca = (
                        "CONFIAN\u00c7A MUITO ALTA"
                    )
                    cor_confianca = theme.COLOR_GREEN

                elif confianca_decisao >= 70:
                    nivel_confianca = (
                        "ALTA CONFIAN\u00c7A"
                    )
                    cor_confianca = theme.COLOR_BLUE

                elif confianca_decisao >= 40:
                    nivel_confianca = (
                        "CONFIAN\u00c7A MODERADA"
                    )
                    cor_confianca = theme.COLOR_YELLOW

                else:
                    nivel_confianca = (
                        "BAIXA CONFIAN\u00c7A"
                    )
                    cor_confianca = "#FF5C5C"

                indicadores_decisao = ctk.CTkFrame(
                    card_decisao,
                    fg_color="transparent",
                )
                indicadores_decisao.pack(
                    fill="x",
                    padx=14,
                    pady=(3, 8),
                )

                badge_missao = ctk.CTkFrame(
                    indicadores_decisao,
                    fg_color=theme.COLOR_CARD,
                    corner_radius=8,
                    border_width=1,
                    border_color=theme.COLOR_BORDER,
                )
                badge_missao.pack(
                    side="left",
                    padx=(0, 6),
                )

                ctk.CTkLabel(
                    badge_missao,
                    text=(
                        f"MISS\u00c3O #{missao_id_decisao}"
                    ),
                    font=("Arial", 10, "bold"),
                    text_color=theme.COLOR_PURPLE,
                ).pack(
                    padx=10,
                    pady=5,
                )

                badge_score = ctk.CTkFrame(
                    indicadores_decisao,
                    fg_color=theme.COLOR_CARD,
                    corner_radius=8,
                    border_width=1,
                    border_color=theme.COLOR_BORDER,
                )
                badge_score.pack(
                    side="left",
                    padx=6,
                )

                ctk.CTkLabel(
                    badge_score,
                    text=f"SCORE {score_decisao}",
                    font=("Arial", 10, "bold"),
                    text_color=theme.COLOR_BLUE,
                ).pack(
                    padx=10,
                    pady=5,
                )

                badge_recomendacao = ctk.CTkFrame(
                    indicadores_decisao,
                    fg_color=theme.COLOR_CARD,
                    corner_radius=8,
                    border_width=1,
                    border_color=cor_recomendacao,
                )
                badge_recomendacao.pack(
                    side="left",
                    padx=6,
                )

                ctk.CTkLabel(
                    badge_recomendacao,
                    text=recomendacao,
                    font=("Arial", 10, "bold"),
                    text_color=cor_recomendacao,
                ).pack(
                    padx=10,
                    pady=5,
                )

                badge_confianca = ctk.CTkFrame(
                    indicadores_decisao,
                    fg_color=theme.COLOR_CARD,
                    corner_radius=8,
                    border_width=1,
                    border_color=cor_confianca,
                )
                badge_confianca.pack(
                    side="left",
                    padx=6,
                )

                ctk.CTkLabel(
                    badge_confianca,
                    text=(
                        f"{nivel_confianca} "
                        f"{confianca_decisao}%"
                    ),
                    font=("Arial", 10, "bold"),
                    text_color=cor_confianca,
                ).pack(
                    padx=10,
                    pady=5,
                )

                motivos_indicadores = decisao.get(
                    "motivos",
                    [],
                )

                if not isinstance(
                    motivos_indicadores,
                    list,
                ):
                    motivos_indicadores = []

                texto_motivos_indicadores = " ".join(
                    str(item)
                    for item in motivos_indicadores
                ).casefold()

                compatibilidade_indicador = 0

                if "modelo compat" in texto_motivos_indicadores:
                    compatibilidade_indicador += 60

                if "marca compat" in texto_motivos_indicadores:
                    compatibilidade_indicador += 40

                compatibilidade_indicador = min(
                    compatibilidade_indicador,
                    100,
                )

                preco_indicador = 50

                if (
                    "abaixo da primeira oferta"
                    in texto_motivos_indicadores
                ):
                    preco_indicador = 95

                elif (
                    "dentro do orcamento"
                    in texto_motivos_indicadores
                    or "dentro do or?amento"
                    in texto_motivos_indicadores
                ):
                    preco_indicador = 80

                alertas_indicadores = decisao.get(
                    "alertas",
                    [],
                )

                if not isinstance(
                    alertas_indicadores,
                    list,
                ):
                    alertas_indicadores = []

                total_alertas_indicadores = len(
                    alertas_indicadores
                )

                seguranca_indicador = max(
                    20,
                    100
                    - (
                        total_alertas_indicadores
                        * 20
                    ),
                )

                try:
                    score_indicador = int(
                        float(score_decisao)
                    )
                except (TypeError, ValueError):
                    score_indicador = 0

                negociacao_indicador = max(
                    0,
                    min(
                        score_indicador,
                        100,
                    ),
                )

                indicadores_ia_frame = ctk.CTkFrame(
                    card_decisao,
                    fg_color=theme.COLOR_CARD,
                    corner_radius=10,
                    border_width=1,
                    border_color=theme.COLOR_BORDER,
                )
                indicadores_ia_frame.pack(
                    fill="x",
                    padx=14,
                    pady=(0, 9),
                )

                ctk.CTkLabel(
                    indicadores_ia_frame,
                    text="Diagn\u00f3stico da IA",
                    font=("Arial", 11, "bold"),
                    text_color=theme.COLOR_TEXT,
                ).pack(
                    anchor="w",
                    padx=12,
                    pady=(10, 6),
                )

                dados_indicadores_ia = [
                    (
                        "Compatibilidade",
                        compatibilidade_indicador,
                        theme.COLOR_GREEN,
                    ),
                    (
                        "Preco",
                        preco_indicador,
                        theme.COLOR_BLUE,
                    ),
                    (
                        "Seguranca",
                        seguranca_indicador,
                        theme.COLOR_YELLOW,
                    ),
                    (
                        "Negociacao",
                        negociacao_indicador,
                        theme.COLOR_PURPLE,
                    ),
                ]

                for (
                    nome_indicador,
                    valor_indicador,
                    cor_indicador,
                ) in dados_indicadores_ia:
                    linha_indicador = ctk.CTkFrame(
                        indicadores_ia_frame,
                        fg_color="transparent",
                    )
                    linha_indicador.pack(
                        fill="x",
                        padx=12,
                        pady=3,
                    )

                    ctk.CTkLabel(
                        linha_indicador,
                        text=nome_indicador,
                        width=115,
                        font=("Arial", 9, "bold"),
                        text_color=theme.COLOR_TEXT_MUTED,
                        anchor="w",
                    ).pack(
                        side="left",
                    )

                    barra_indicador = ctk.CTkProgressBar(
                        linha_indicador,
                        height=8,
                        corner_radius=5,
                        progress_color=cor_indicador,
                        fg_color=theme.COLOR_BORDER,
                    )
                    barra_indicador.pack(
                        side="left",
                        fill="x",
                        expand=True,
                        padx=(8, 10),
                    )
                    barra_indicador.set(
                        valor_indicador / 100
                    )

                    ctk.CTkLabel(
                        linha_indicador,
                        text=f"{valor_indicador}%",
                        width=42,
                        font=("Arial", 9, "bold"),
                        text_color=cor_indicador,
                        anchor="e",
                    ).pack(
                        side="right",
                    )

                ctk.CTkFrame(
                    indicadores_ia_frame,
                    fg_color="transparent",
                    height=5,
                ).pack()

                recomendacoes_finais = {
                    "EXCELENTE": (
                        "Prioridade alta. Validar os dados "
                        "do an\u00fancio e iniciar contato."
                    ),
                    "BOA": (
                        "Boa oportunidade. Confirmar os "
                        "alertas antes de negociar."
                    ),
                    "REGULAR": (
                        "Avaliar com cautela e conferir "
                        "todas as informa\u00e7\u00f5es."
                    ),
                    "DESCARTADA": (
                        "N\u00e3o priorizar esta oportunidade "
                        "sem uma nova avalia\u00e7\u00e3o."
                    ),
                }

                texto_recomendacao_final = (
                    recomendacoes_finais.get(
                        recomendacao,
                        "Revisar os dados antes de decidir.",
                    )
                )

                card_recomendacao_final = ctk.CTkFrame(
                    card_decisao,
                    fg_color=theme.COLOR_CARD,
                    corner_radius=10,
                    border_width=1,
                    border_color=cor_recomendacao,
                )
                card_recomendacao_final.pack(
                    fill="x",
                    padx=14,
                    pady=(0, 9),
                )

                ctk.CTkLabel(
                    card_recomendacao_final,
                    text="RECOMENDA\u00c7\u00c3O FINAL",
                    font=("Arial", 9, "bold"),
                    text_color=cor_recomendacao,
                ).pack(
                    anchor="w",
                    padx=12,
                    pady=(9, 3),
                )

                ctk.CTkLabel(
                    card_recomendacao_final,
                    text=texto_recomendacao_final,
                    font=("Arial", 11, "bold"),
                    text_color=theme.COLOR_TEXT,
                    anchor="w",
                    justify="left",
                    wraplength=950,
                ).pack(
                    fill="x",
                    padx=12,
                    pady=(0, 10),
                )

                resumo_decisao = str(
                    decisao.get(
                        "resumo",
                        "Sem resumo registrado.",
                    )
                ).strip()

                bloco_resumo_decisao = ctk.CTkFrame(
                    card_decisao,
                    fg_color=theme.COLOR_CARD,
                    corner_radius=10,
                    border_width=1,
                    border_color=theme.COLOR_BORDER,
                )
                bloco_resumo_decisao.pack(
                    fill="x",
                    padx=14,
                    pady=(0, 9),
                )

                ctk.CTkLabel(
                    bloco_resumo_decisao,
                    text="RESUMO DA AN\u00c1LISE",
                    font=("Arial", 9, "bold"),
                    text_color=theme.COLOR_BLUE,
                ).pack(
                    anchor="w",
                    padx=12,
                    pady=(9, 4),
                )

                ctk.CTkLabel(
                    bloco_resumo_decisao,
                    text=resumo_decisao,
                    font=("Arial", 11),
                    text_color=theme.COLOR_TEXT_MUTED,
                    anchor="w",
                    justify="left",
                    wraplength=950,
                ).pack(
                    fill="x",
                    padx=12,
                    pady=(0, 10),
                )

                acao_decisao = str(
                    decisao.get(
                        "decisao",
                        "Sem a\u00e7\u00e3o recomendada.",
                    )
                ).strip()

                bloco_acao_decisao = ctk.CTkFrame(
                    card_decisao,
                    fg_color=theme.COLOR_CARD,
                    corner_radius=10,
                    border_width=1,
                    border_color=theme.COLOR_BORDER,
                )
                bloco_acao_decisao.pack(
                    fill="x",
                    padx=14,
                    pady=(0, 9),
                )

                ctk.CTkLabel(
                    bloco_acao_decisao,
                    text="PR\u00d3XIMA A\u00c7\u00c3O",
                    font=("Arial", 9, "bold"),
                    text_color=theme.COLOR_GREEN,
                ).pack(
                    anchor="w",
                    padx=12,
                    pady=(9, 4),
                )

                ctk.CTkLabel(
                    bloco_acao_decisao,
                    text=f"\u2714 {acao_decisao}",
                    font=("Arial", 11, "bold"),
                    text_color=theme.COLOR_TEXT,
                    anchor="w",
                    justify="left",
                    wraplength=950,
                ).pack(
                    fill="x",
                    padx=12,
                    pady=(0, 10),
                )

                score_financeiro_decisao = decisao.get(
                    "score_financeiro"
                )
                classificacao_financeira_decisao = decisao.get(
                    "classificacao_financeira",
                    "SEM DADOS",
                )
                score_final_experimental_decisao = decisao.get(
                    "score_final_experimental",
                    score_decisao,
                )
                classificacao_final_experimental_decisao = decisao.get(
                    "classificacao_final_experimental",
                    recomendacao,
                )
                preco_alvo_negociacao_decisao = decisao.get(
                    "preco_alvo_negociacao"
                )

                bloco_financeiro_experimental = ctk.CTkFrame(
                    card_decisao,
                    fg_color=theme.COLOR_CARD,
                    corner_radius=10,
                    border_width=1,
                    border_color=theme.COLOR_TEXT_MUTED,
                )
                bloco_financeiro_experimental.pack(
                    fill="x",
                    padx=14,
                    pady=(0, 9),
                )

                ctk.CTkLabel(
                    bloco_financeiro_experimental,
                    text=(
                        "ANÁLISE FINANCEIRA • EXPERIMENTAL"
                    ),
                    font=("Arial", 9, "bold"),
                    text_color=theme.COLOR_TEXT_MUTED,
                ).pack(
                    anchor="w",
                    padx=12,
                    pady=(9, 2),
                )

                ctk.CTkLabel(
                    bloco_financeiro_experimental,
                    text=(
                        "Não substitui a classificação "
                        "oficial acima -- somente para "
                        "calibração."
                    ),
                    font=("Arial", 9, "italic"),
                    text_color=theme.COLOR_TEXT_MUTED,
                ).pack(
                    anchor="w",
                    padx=12,
                    pady=(0, 6),
                )

                if score_financeiro_decisao is None:
                    # Pode ser FIPE genuinamente indisponível ou um
                    # registro anterior ao shadow mode -- este dict
                    # (agent_decisions.json) não guarda fipe_encontrada,
                    # então o texto fica neutro para não afirmar uma
                    # causa que não dá para confirmar aqui.
                    texto_financeiro_experimental = (
                        "Dados financeiros experimentais "
                        "indisponíveis para este registro (SEM "
                        "DADOS)."
                    )
                else:
                    if isinstance(
                        preco_alvo_negociacao_decisao,
                        (int, float),
                    ):
                        texto_preco_alvo_experimental = (
                            f"R$ {preco_alvo_negociacao_decisao:,.2f}"
                        )
                    else:
                        texto_preco_alvo_experimental = "-"

                    texto_financeiro_experimental = (
                        f"Score financeiro: "
                        f"{score_financeiro_decisao}/100  "
                        f"•  Atratividade: "
                        f"{classificacao_financeira_decisao}\n"
                        f"Score final experimental: "
                        f"{score_final_experimental_decisao}/100  "
                        f"•  Classificação "
                        f"experimental: "
                        f"{classificacao_final_experimental_decisao}\n"
                        f"Preço-alvo: "
                        f"{texto_preco_alvo_experimental}"
                    )

                ctk.CTkLabel(
                    bloco_financeiro_experimental,
                    text=texto_financeiro_experimental,
                    font=("Arial", 11),
                    text_color=theme.COLOR_TEXT,
                    anchor="w",
                    justify="left",
                    wraplength=950,
                ).pack(
                    fill="x",
                    padx=12,
                    pady=(0, 10),
                )

                link_decisao = str(
                    decisao.get(
                        "anuncio_link",
                        "",
                    )
                ).strip()

                botoes_decisao = ctk.CTkFrame(
                    card_decisao,
                    fg_color="transparent",
                )
                botoes_decisao.pack(
                    fill="x",
                    padx=14,
                    pady=(0, 12),
                )

                ctk.CTkButton(
                    botoes_decisao,
                    text="Ver racioc\u00ednio da IA",
                    command=lambda item=decisao: (
                        abrir_raciocinio_ia(item)
                    ),
                    height=32,
                    corner_radius=9,
                    fg_color=theme.COLOR_BLUE,
                    hover_color="#0D47A1",
                    font=("Arial", 11, "bold"),
                ).pack(
                    side="right",
                    padx=(8, 0),
                )

                if link_decisao:
                    ctk.CTkButton(
                        botoes_decisao,
                        text="Abrir an\u00fancio",
                        command=lambda url=link_decisao: (
                            self.abrir_anuncio_seguro(url)
                        ),
                        height=32,
                        corner_radius=9,
                        fg_color=theme.COLOR_GREEN,
                        hover_color=theme.COLOR_GREEN_DARK,
                        font=("Arial", 11, "bold"),
                    ).pack(
                        side="right",
                    )

                id_decisao_tecnico = decisao.get(
                    "id",
                    "-",
                )

                tipo_decisao_tecnico = str(
                    decisao.get(
                        "tipo",
                        "OPORTUNIDADE_ANALISADA",
                    )
                ).strip().replace(
                    "_",
                    " ",
                ).title()

                rodape_tecnico_decisao = ctk.CTkFrame(
                    card_decisao,
                    fg_color="transparent",
                )
                rodape_tecnico_decisao.pack(
                    fill="x",
                    padx=14,
                    pady=(0, 10),
                )

                ctk.CTkLabel(
                    rodape_tecnico_decisao,
                    text=(
                        "Agent Alpha"
                        f"  \u2022  Decis\u00e3o #{id_decisao_tecnico}"
                        f"  \u2022  {tipo_decisao_tecnico}"
                        f"  \u2022  {fonte_decisao}"
                        f"  \u2022  {data_card_decisao}"
                    ),
                    font=("Arial", 9),
                    text_color=theme.COLOR_TEXT_MUTED,
                    anchor="w",
                    justify="left",
                ).pack(
                    fill="x",
                    anchor="w",
                )

        def mudar_pagina_memoria(direcao):
            nova_pagina = (
                estado_paginacao_memoria[
                    "pagina_atual"
                ]
                + direcao
            )

            total_paginas = (
                estado_paginacao_memoria[
                    "total_paginas"
                ]
            )

            nova_pagina = max(
                0,
                min(
                    nova_pagina,
                    total_paginas - 1,
                ),
            )

            if (
                nova_pagina
                == estado_paginacao_memoria[
                    "pagina_atual"
                ]
            ):
                return

            estado_paginacao_memoria[
                "pagina_atual"
            ] = nova_pagina

            renderizar_decisoes_memoria(
                estado_filtro_memoria[
                    "recomendacao"
                ],
                resetar_pagina=False,
            )

        botao_pagina_anterior.configure(
            command=lambda: mudar_pagina_memoria(-1)
        )

        botao_proxima_pagina.configure(
            command=lambda: mudar_pagina_memoria(1)
        )

        combo_filtro_missao.configure(
            command=lambda escolha: (
                renderizar_decisoes_memoria(
                    estado_filtro_memoria[
                        "recomendacao"
                    ],
                    resetar_pagina=True,
                )
            )
        )

        campo_busca_memoria.bind(
            "<KeyRelease>",
            lambda evento: (
                renderizar_decisoes_memoria(
                    estado_filtro_memoria[
                        "recomendacao"
                    ],
                    resetar_pagina=True,
                )
            ),
        )

        nomes_filtros = [
            "TODAS",
            "EXCELENTES",
            "BOAS",
            "REGULARES",
            "DESCARTADAS",
        ]

        for nome_filtro in nomes_filtros:
            botao_filtro = ctk.CTkButton(
                filtros_frame,
                text=nome_filtro,
                command=lambda filtro=nome_filtro: (
                    renderizar_decisoes_memoria(
                        filtro,
                        resetar_pagina=True,
                    )
                ),
                height=34,
                corner_radius=9,
                fg_color=theme.COLOR_CARD_HOVER,
                hover_color=theme.COLOR_BORDER,
                font=("Arial", 11, "bold"),
            )
            botao_filtro.pack(
                side="left",
                fill="x",
                expand=True,
                padx=4,
            )

            botoes_filtro[nome_filtro] = (
                botao_filtro
            )

        renderizar_decisoes_memoria(
            "TODAS",
            resetar_pagina=True,
        )


    def tela_agent_analytics(self):
        self.limpar_content()
        render_agent_analytics(self.content)


    def tela_calibracao_financeira(self):
        """
        Observabilidade do Shadow Mode (core/financial_scoring.py).

        So le/exibe campos ja persistidos em mission_matches.json.
        Nunca recalcula score, nunca filtra oportunidades oficiais,
        nunca altera badges/contadores oficiais e nunca dispara
        Telegram/AWS -- e uma tela passiva de leitura.
        """
        self.limpar_content()

        def _fmt_preco(valor):
            try:
                return (
                    f"R$ {float(valor):,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )
            except (TypeError, ValueError):
                return "-"

        def _fmt_percentual(valor):
            try:
                numero = float(valor)
            except (TypeError, ValueError):
                return "-"

            sinal = "+" if numero >= 0 else "-"
            texto = f"{abs(numero):.2f}".replace(".", ",")
            return f"{sinal}{texto}%"

        def _fmt_score(valor):
            try:
                return f"{float(valor):.0f}/100"
            except (TypeError, ValueError):
                return "-"

        def _fmt_media(valor):
            if valor is None:
                return "--"

            try:
                return f"{float(valor):.1f}"
            except (TypeError, ValueError):
                return "--"

        frame = ctk.CTkFrame(
            self.content,
            fg_color="transparent",
        )
        frame.pack(
            fill="both",
            expand=True,
            padx=32,
            pady=28,
        )

        ctk.CTkLabel(
            frame,
            text="\U0001f9ea Calibração Financeira",
            font=("Arial", 32, "bold"),
            text_color=theme.COLOR_TEXT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            frame,
            text=(
                "Shadow Mode — observabilidade apenas. Não altera a "
                "classificação oficial."
            ),
            font=("Arial", 16),
            text_color=theme.COLOR_TEXT_MUTED,
        ).pack(
            anchor="w",
            pady=(4, 20),
        )

        oportunidades_shadow = listar_todas_oportunidades()
        metricas_shadow = gerar_metricas_shadow_mode(
            oportunidades_shadow
        )

        dados_kpis_shadow = [
            (
                "COM SHADOW",
                str(metricas_shadow["total_com_shadow"]),
                theme.COLOR_BLUE,
            ),
            (
                "SEM SHADOW (ANTIGO)",
                str(metricas_shadow["total_sem_shadow"]),
                theme.COLOR_TEXT_MUTED,
            ),
            (
                "SEM FIPE",
                str(metricas_shadow["total_sem_fipe"]),
                theme.COLOR_YELLOW,
            ),
            (
                "MESMA CLASSIFICAÇÃO",
                str(metricas_shadow["mesma_classificacao"]),
                theme.COLOR_BLUE,
            ),
            (
                "CAÍRAM",
                str(metricas_shadow["cairam_classificacao"]),
                "#FF5C5C",
            ),
            (
                "SUBIRAM",
                str(metricas_shadow["subiram_classificacao"]),
                theme.COLOR_GREEN,
            ),
            (
                "MÉDIA MISSÃO",
                _fmt_media(metricas_shadow["media_score_missao"]),
                theme.COLOR_BLUE,
            ),
            (
                "MÉDIA FINANCEIRA",
                _fmt_media(
                    metricas_shadow["media_score_financeiro"]
                ),
                theme.COLOR_PURPLE,
            ),
            (
                "MÉDIA EXPERIMENTAL",
                _fmt_media(
                    metricas_shadow[
                        "media_score_final_experimental"
                    ]
                ),
                theme.COLOR_GREEN,
            ),
        ]

        grade_kpis_shadow = ctk.CTkFrame(
            frame,
            fg_color="transparent",
        )
        grade_kpis_shadow.pack(
            fill="x",
            pady=(0, 18),
        )

        colunas_kpis_shadow = 3

        for coluna in range(colunas_kpis_shadow):
            grade_kpis_shadow.grid_columnconfigure(
                coluna,
                weight=1,
            )

        for indice, (
            titulo_kpi,
            valor_kpi,
            cor_kpi,
        ) in enumerate(dados_kpis_shadow):
            linha_kpi, coluna_kpi = divmod(
                indice, colunas_kpis_shadow
            )

            card_kpi = ctk.CTkFrame(
                grade_kpis_shadow,
                fg_color=theme.COLOR_CARD_HOVER,
                corner_radius=14,
                border_width=1,
                border_color=theme.COLOR_BORDER,
            )
            card_kpi.grid(
                row=linha_kpi,
                column=coluna_kpi,
                sticky="nsew",
                padx=5,
                pady=5,
            )

            ctk.CTkLabel(
                card_kpi,
                text=titulo_kpi,
                font=("Arial", 10, "bold"),
                text_color=theme.COLOR_TEXT_MUTED,
            ).pack(
                anchor="w",
                padx=12,
                pady=(12, 3),
            )

            ctk.CTkLabel(
                card_kpi,
                text=valor_kpi,
                font=("Arial", 22, "bold"),
                text_color=cor_kpi,
            ).pack(
                anchor="w",
                padx=12,
                pady=(0, 12),
            )

        lista_shadow = ctk.CTkScrollableFrame(
            frame,
            fg_color="transparent",
        )
        lista_shadow.pack(
            fill="both",
            expand=True,
            pady=(4, 0),
        )

        if not oportunidades_shadow:
            ctk.CTkLabel(
                lista_shadow,
                text="Nenhuma oportunidade encontrada.",
                font=("Arial", 15),
                text_color=theme.COLOR_TEXT_MUTED,
            ).pack(pady=40)

            return

        for oportunidade in oportunidades_shadow:
            titulo = str(
                oportunidade.get(
                    "titulo", "Anúncio sem título"
                )
            )
            origem = str(oportunidade.get("origem", "-")) or "-"
            data_hora = (
                str(oportunidade.get("data_hora", "-")) or "-"
            )

            card = ctk.CTkFrame(
                lista_shadow,
                fg_color=theme.COLOR_CARD,
                corner_radius=14,
                border_width=1,
                border_color=theme.COLOR_BORDER,
            )
            card.pack(fill="x", pady=7)

            ctk.CTkLabel(
                card,
                text=titulo,
                font=("Arial", 15, "bold"),
                text_color=theme.COLOR_TEXT,
                anchor="w",
                justify="left",
                wraplength=650,
            ).pack(
                fill="x",
                anchor="w",
                padx=16,
                pady=(14, 2),
            )

            ctk.CTkLabel(
                card,
                text=f"{origem} • {data_hora}",
                font=("Arial", 11),
                text_color=theme.COLOR_TEXT_MUTED,
            ).pack(
                anchor="w",
                padx=16,
                pady=(0, 8),
            )

            corpo = ctk.CTkFrame(
                card,
                fg_color=theme.COLOR_CARD_HOVER,
                corner_radius=10,
            )
            corpo.pack(
                fill="x",
                padx=16,
                pady=(0, 8),
            )

            ctk.CTkLabel(
                corpo,
                text=(
                    f"Preço: {_fmt_preco(oportunidade.get('preco'))}"
                    "   •   FIPE: "
                    f"{_fmt_preco(oportunidade.get('valor_fipe'))}"
                    "   •   Diferença: "
                    f"{_fmt_percentual(oportunidade.get('diferenca_fipe_percentual'))}"
                ),
                font=("Arial", 12),
                text_color=theme.COLOR_TEXT,
                anchor="w",
                justify="left",
                wraplength=900,
            ).pack(
                anchor="w",
                padx=12,
                pady=(10, 4),
            )

            classificacao_missao = oportunidade.get(
                "classificacao_missao", "-"
            )

            ctk.CTkLabel(
                corpo,
                text=(
                    "Missão (oficial): "
                    f"{_fmt_score(oportunidade.get('score_missao'))}"
                    f"  •  {classificacao_missao}"
                ),
                font=("Arial", 12, "bold"),
                text_color=theme.COLOR_TEXT,
                anchor="w",
            ).pack(
                anchor="w",
                padx=12,
                pady=(0, 10),
            )

            tem_shadow = (
                "score_missao" in oportunidade
                and oportunidade.get("score_missao") is not None
            )

            bloco_experimental = ctk.CTkFrame(
                card,
                fg_color=theme.COLOR_CARD,
                corner_radius=10,
                border_width=1,
                border_color=theme.COLOR_TEXT_MUTED,
            )
            bloco_experimental.pack(
                fill="x",
                padx=16,
                pady=(0, 14),
            )

            ctk.CTkLabel(
                bloco_experimental,
                text="SHADOW MODE • EXPERIMENTAL",
                font=("Arial", 9, "bold"),
                text_color=theme.COLOR_TEXT_MUTED,
            ).pack(
                anchor="w",
                padx=12,
                pady=(9, 2),
            )

            if not tem_shadow:
                ctk.CTkLabel(
                    bloco_experimental,
                    text=(
                        "Experimental: Não calculado (registro "
                        "anterior ao shadow mode)"
                    ),
                    font=("Arial", 12),
                    text_color=theme.COLOR_TEXT_MUTED,
                ).pack(
                    anchor="w",
                    padx=12,
                    pady=(0, 10),
                )

                continue

            score_financeiro = oportunidade.get("score_financeiro")
            classificacao_financeira = oportunidade.get(
                "classificacao_financeira", "SEM DADOS"
            )

            if score_financeiro is None:
                if str(classificacao_financeira).strip().upper() == "SEM DADOS":
                    texto_financeiro = "Financeiro: SEM DADOS"
                else:
                    texto_financeiro = (
                        f"Financeiro: SEM DADOS ({classificacao_financeira})"
                    )
            else:
                texto_financeiro = (
                    f"Financeiro: {_fmt_score(score_financeiro)}"
                    f"  •  {classificacao_financeira}"
                )

            ctk.CTkLabel(
                bloco_experimental,
                text=texto_financeiro,
                font=("Arial", 12),
                text_color=theme.COLOR_TEXT_MUTED,
            ).pack(
                anchor="w",
                padx=12,
                pady=(0, 2),
            )

            classificacao_final_experimental = oportunidade.get(
                "classificacao_final_experimental", "-"
            )

            resultado_comparacao = comparar_classificacao_shadow(
                classificacao_missao,
                classificacao_final_experimental,
            )

            indicadores_direcao = {
                "SUBIU": ("↑ SUBIU", theme.COLOR_GREEN),
                "MANTEVE": ("= MANTEVE", theme.COLOR_TEXT_MUTED),
                "CAIU": ("↓ CAIU", "#FF5C5C"),
            }
            texto_indicador, cor_indicador = indicadores_direcao.get(
                resultado_comparacao,
                ("", theme.COLOR_TEXT_MUTED),
            )

            linha_experimental = ctk.CTkFrame(
                bloco_experimental,
                fg_color="transparent",
            )
            linha_experimental.pack(
                fill="x",
                padx=12,
                pady=(0, 2),
            )

            ctk.CTkLabel(
                linha_experimental,
                text=(
                    "Experimental: "
                    f"{_fmt_score(oportunidade.get('score_final_experimental'))}"
                    f"  •  {classificacao_final_experimental}"
                ),
                font=("Arial", 12, "bold"),
                text_color=theme.COLOR_TEXT,
                anchor="w",
            ).pack(
                side="left",
            )

            if texto_indicador:
                ctk.CTkLabel(
                    linha_experimental,
                    text=texto_indicador,
                    font=("Arial", 11, "bold"),
                    text_color=cor_indicador,
                ).pack(
                    side="left",
                    padx=(10, 0),
                )

            ctk.CTkLabel(
                bloco_experimental,
                text=(
                    "Preço-alvo: "
                    f"{_fmt_preco(oportunidade.get('preco_alvo_negociacao'))}"
                ),
                font=("Arial", 12),
                text_color=theme.COLOR_TEXT_MUTED,
            ).pack(
                anchor="w",
                padx=12,
                pady=(2, 10),
            )


    def tela_configuracoes(self):
        self.limpar_content()

        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=32, pady=28)

        ctk.CTkLabel(
            frame,
            text="Configurações",
            font=("Arial", 32, "bold"),
            text_color=theme.COLOR_TEXT
        ).pack(anchor="w")

        ctk.CTkLabel(
            frame,
            text="Configurações futuras do robô, AWS, painel, GitHub e TH Agent.",
            font=("Arial", 16),
            text_color=theme.COLOR_TEXT_MUTED
        ).pack(anchor="w", pady=(4, 0))


if __name__ == "__main__":
    app = THIAMotosApp()
    app.mainloop()
