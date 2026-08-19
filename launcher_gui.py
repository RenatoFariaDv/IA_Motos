import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from core import robo_process
from core import aws_sync_process


if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
else:
    APP_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = APP_DIR


BASE_DIR = APP_DIR
CONTROL_CENTER = BASE_DIR / "control_center.py"
ROBO_FILE = BASE_DIR / "main.py"
PID_FILE = BASE_DIR / "robo.pid"
SYNC_SCRIPT = BASE_DIR / "sincronizar_aws.ps1"

LOGO_FILE = (
    RESOURCE_DIR
    / "interface_v2"
    / "static"
    / "img"
    / "th-logo.png"
)

PAINEL_URL = "http://54.233.146.58:5000/?v=launcher"
AWS_KEY = Path.home() / ".ssh" / "IA-Motos-Key.pem"
AWS_HOST = "54.233.146.58"


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class Launcher(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TH IA MOTOS")
        self.geometry("460x960")
        self.resizable(False, False)
        self.configure(fg_color="#0B1220")

        self.criar_interface()

    def criar_interface(self):
        container = ctk.CTkFrame(
            self,
            fg_color="#111827",
            corner_radius=24,
        )
        container.pack(
            fill="both",
            expand=True,
            padx=22,
            pady=22,
        )

        if LOGO_FILE.exists():
            imagem = Image.open(LOGO_FILE)

            self.logo = ctk.CTkImage(
                light_image=imagem,
                dark_image=imagem,
                size=(150, 150),
            )

            ctk.CTkLabel(
                container,
                text="",
                image=self.logo,
            ).pack(pady=(28, 10))

        ctk.CTkLabel(
            container,
            text="TH IA MOTOS",
            font=("Arial", 30, "bold"),
            text_color="#F9FAFB",
        ).pack()

        ctk.CTkLabel(
            container,
            text="Central de Inicialização",
            font=("Arial", 15),
            text_color="#9CA3AF",
        ).pack(pady=(4, 20))

        status = ctk.CTkFrame(
            container,
            fg_color="#1F2937",
            corner_radius=14,
        )
        status.pack(
            fill="x",
            padx=24,
            pady=(0, 18),
        )

        ctk.CTkLabel(
            status,
            text="● Sistema pronto",
            font=("Arial", 14, "bold"),
            text_color="#22C55E",
        ).pack(pady=14)

        self.criar_botao(
            container,
            "Abrir Control Center",
            self.abrir_control_center,
        )

        self.criar_botao(
            container,
            "Iniciar Robô",
            self.iniciar_robo,
        )

        self.criar_botao(
            container,
            "Parar Robô",
            self.parar_robo,
        )

        self.criar_botao(
            container,
            "Status do Robô",
            self.status_robo,
        )

        self.criar_botao(
            container,
            "Iniciar Sync AWS",
            self.iniciar_sync,
        )

        self.criar_botao(
            container,
            "Parar Sync AWS",
            self.parar_sync,
        )

        self.criar_botao(
            container,
            "Status Sync AWS",
            self.status_sync,
        )

        self.criar_botao(
            container,
            "Abrir Painel AWS",
            self.abrir_painel,
        )

        self.criar_botao(
            container,
            "Conectar AWS SSH",
            self.conectar_aws,
        )

        self.criar_botao(
            container,
            "Abrir VS Code",
            self.abrir_vscode,
        )

        ctk.CTkButton(
            container,
            text="Sair",
            height=42,
            corner_radius=12,
            fg_color="#374151",
            hover_color="#4B5563",
            command=self.destroy,
        ).pack(
            fill="x",
            padx=24,
            pady=(10, 20),
        )

        ctk.CTkLabel(
            container,
            text="Versão 1.0 • TH IA MOTOS",
            font=("Arial", 11),
            text_color="#6B7280",
        ).pack(pady=(0, 18))

    def criar_botao(self, parent, texto, comando):
        ctk.CTkButton(
            parent,
            text=texto,
            height=48,
            corner_radius=12,
            fg_color="#22C55E",
            hover_color="#16A34A",
            font=("Arial", 15, "bold"),
            command=comando,
        ).pack(
            fill="x",
            padx=24,
            pady=7,
        )

    def comando_python(self, arquivo):
        python_exe = shutil.which("python")

        if python_exe:
            return [python_exe, str(arquivo)]

        py_launcher = shutil.which("py")

        if py_launcher:
            return [py_launcher, "-3", str(arquivo)]

        return None

    def abrir_control_center(self):
        if not CONTROL_CENTER.exists():
            self.mostrar_erro(
                f"Arquivo não encontrado:\n{CONTROL_CENTER}"
            )
            return

        comando = self.comando_python(CONTROL_CENTER)

        if comando is None:
            self.mostrar_erro(
                "Python não foi encontrado no computador."
            )
            return

        subprocess.Popen(
            comando,
            cwd=str(BASE_DIR),
        )

    def _mostrar_feedback(self, titulo: str, mensagem: str, cor_destaque: str) -> None:
        janela = ctk.CTkToplevel(self)
        janela.title(titulo)
        janela.geometry("420x200")
        janela.resizable(False, False)
        janela.configure(fg_color="#0B1220")
        janela.transient(self)
        janela.grab_set()

        ctk.CTkLabel(
            janela,
            text=titulo,
            font=("Arial", 18, "bold"),
            text_color=cor_destaque,
        ).pack(pady=(24, 8))

        ctk.CTkLabel(
            janela,
            text=mensagem,
            font=("Arial", 13),
            text_color="#9CA3AF",
            justify="center",
            wraplength=360,
        ).pack(padx=20, pady=(0, 16))

        ctk.CTkButton(
            janela,
            text="OK",
            command=janela.destroy,
            height=34,
            corner_radius=9,
            fg_color="#1F2937",
            hover_color="#374151",
            font=("Arial", 12, "bold"),
        ).pack(padx=20, pady=(0, 20))

    def iniciar_robo(self):
        if not ROBO_FILE.exists():
            self.mostrar_erro(
                f"Arquivo não encontrado:\n{ROBO_FILE}"
            )
            return

        resultado = robo_process.iniciar(PID_FILE, ROBO_FILE, BASE_DIR)

        if resultado.ja_estava_rodando:
            self._mostrar_feedback(
                "Robô já em execução",
                f"O robô já está rodando (PID {resultado.pid}).",
                "#FACC15",
            )
            return

        if not resultado.sucesso:
            self._mostrar_feedback(
                "Falha ao iniciar",
                f"Não foi possível iniciar o robô: {resultado.erro}",
                "#EF4444",
            )
            return

        if resultado.pid_orfao_recuperado:
            self._mostrar_feedback(
                "PID antigo recuperado",
                "Um registro antigo do robô (de um processo que já "
                "não existia mais) foi limpo automaticamente. "
                f"Robô iniciado agora (PID {resultado.pid}).",
                "#22C55E",
            )
        else:
            self._mostrar_feedback(
                "Robô iniciado",
                f"Robô iniciado com sucesso (PID {resultado.pid}).",
                "#22C55E",
            )

    def parar_robo(self):
        resultado = robo_process.parar(PID_FILE, ROBO_FILE)

        if resultado.ja_estava_parado:
            self._mostrar_feedback(
                "Robô não está rodando",
                "Não há nenhum robô em execução para parar.",
                "#FACC15",
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

            self._mostrar_feedback(
                "Estado do robô limpo",
                f"O registro do robô estava desatualizado ({motivo_texto}). "
                "Nenhum processo foi encerrado.",
                "#FACC15",
            )
            return

        if not resultado.sucesso:
            self._mostrar_feedback(
                "Falha ao parar",
                f"Não foi possível encerrar o robô "
                f"(PID {resultado.pid}): {resultado.erro}",
                "#EF4444",
            )
            return

        self._mostrar_feedback(
            "Robô parado",
            f"Robô (PID {resultado.pid}) encerrado com sucesso.",
            "#22C55E",
        )

    def status_robo(self):
        status = robo_process.verificar_status(PID_FILE, ROBO_FILE)

        if status.rodando:
            self._mostrar_feedback(
                "Robô rodando",
                f"O robô está em execução (PID {status.pid}).",
                "#22C55E",
            )
        elif status.orfao:
            self._mostrar_feedback(
                "Robô parado (registro desatualizado)",
                "Não há robô em execução. Havia um registro de PID "
                f"desatualizado ({status.motivo_orfao}) que será limpo "
                "automaticamente na próxima vez que o robô for iniciado.",
                "#FACC15",
            )
        else:
            self._mostrar_feedback(
                "Robô parado",
                "Não há robô em execução no momento.",
                "#9CA3AF",
            )

    def iniciar_sync(self):
        resultado = aws_sync_process.iniciar(SYNC_SCRIPT, BASE_DIR)

        if resultado.ja_estava_rodando:
            self._mostrar_feedback(
                "Sincronização já em execução",
                f"A sincronização AWS já está rodando (PID {resultado.pid}).",
                "#FACC15",
            )
            return

        if not resultado.sucesso:
            self._mostrar_feedback(
                "Falha ao iniciar sincronização",
                f"Não foi possível iniciar a sincronização AWS: {resultado.erro}",
                "#EF4444",
            )
            return

        self._mostrar_feedback(
            "Sincronização AWS iniciada",
            f"Sincronização iniciada com sucesso (PID {resultado.pid}).",
            "#22C55E",
        )

    def parar_sync(self):
        resultado = aws_sync_process.parar(SYNC_SCRIPT)

        if resultado.ja_estava_parado:
            self._mostrar_feedback(
                "Sincronização não está rodando",
                "Não há nenhuma sincronização AWS em execução para parar.",
                "#FACC15",
            )
            return

        if not resultado.sucesso:
            self._mostrar_feedback(
                "Falha ao parar sincronização",
                f"Não foi possível encerrar a sincronização AWS: {resultado.erro}",
                "#EF4444",
            )
            return

        self._mostrar_feedback(
            "Sincronização AWS parada",
            f"Sincronização encerrada com sucesso (PID(s) {resultado.pids_encerrados}).",
            "#22C55E",
        )

    def status_sync(self):
        status = aws_sync_process.verificar_status(SYNC_SCRIPT)

        if status.rodando:
            self._mostrar_feedback(
                "Sincronização rodando",
                f"A sincronização AWS está em execução (PID(s) {status.pids}).",
                "#22C55E",
            )
        else:
            self._mostrar_feedback(
                "Sincronização parada",
                "Não há sincronização AWS em execução no momento.",
                "#9CA3AF",
            )

    def abrir_painel(self):
        webbrowser.open(PAINEL_URL)

    def conectar_aws(self):
        if not AWS_KEY.exists():
            self.mostrar_erro(
                f"Chave AWS não encontrada:\n{AWS_KEY}"
            )
            return

        comando = (
            f'ssh -i "{AWS_KEY}" '
            f"ubuntu@{AWS_HOST}"
        )

        subprocess.Popen(
            [
                "powershell",
                "-NoExit",
                "-Command",
                comando,
            ]
        )

    def abrir_vscode(self):
        subprocess.Popen(
            ["code", str(BASE_DIR)],
            cwd=str(BASE_DIR),
            shell=True,
        )

    def mostrar_erro(self, mensagem):
        janela = ctk.CTkToplevel(self)
        janela.title("Erro")
        janela.geometry("420x180")
        janela.resizable(False, False)
        janela.grab_set()

        ctk.CTkLabel(
            janela,
            text=mensagem,
            wraplength=360,
            font=("Arial", 14),
        ).pack(
            expand=True,
            padx=20,
            pady=20,
        )

        ctk.CTkButton(
            janela,
            text="Fechar",
            command=janela.destroy,
        ).pack(pady=(0, 20))


if __name__ == "__main__":
    app = Launcher()
    app.mainloop()