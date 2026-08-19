"""
Gerenciamento seguro do processo do robo (main.py) iniciado pelo Control Center.

Resolve o problema de um robo.pid orfao (processo ja encerrado, ou PID
reaproveitado pelo Windows para outro programa) bloquear silenciosamente o
botao "Iniciar Robo". Nunca lanca excecao para o chamador e nunca encerra um
processo que nao tenha sido confirmado como pertencente ao robo do IA_Motos.
"""

import subprocess
from pathlib import Path
from typing import Callable, NamedTuple, Optional


class StatusRobo(NamedTuple):
    rodando: bool
    pid: Optional[int]
    orfao: bool          # havia PID_FILE, mas nao corresponde a um robo vivo
    motivo_orfao: str    # "" | "arquivo invalido" | "processo morto" | "pid reaproveitado"


class ResultadoIniciar(NamedTuple):
    sucesso: bool
    pid: Optional[int]
    ja_estava_rodando: bool
    pid_orfao_recuperado: bool
    erro: str


class ResultadoParar(NamedTuple):
    sucesso: bool
    pid: Optional[int]
    ja_estava_parado: bool
    estado_limpo_sem_matar: bool
    motivo: str
    erro: str


def ler_pid(pid_file: Path) -> Optional[int]:
    """Le o PID gravado. Retorna None se ausente, vazio ou com conteudo invalido."""
    if not pid_file.exists():
        return None

    try:
        conteudo = pid_file.read_text(encoding="utf-8", errors="ignore").strip()
    except OSError:
        return None

    if not conteudo:
        return None

    try:
        return int(conteudo)
    except ValueError:
        return None


def obter_linha_comando(
    pid: int,
    executar: Callable[..., "subprocess.CompletedProcess"] = subprocess.run,
) -> str:
    """
    Retorna a linha de comando do processo com esse PID, ou "" se o processo
    nao existir (ou se nao for possivel confirmar com seguranca).
    """
    try:
        resultado = executar(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                f'(Get-CimInstance Win32_Process -Filter "ProcessId={pid}").CommandLine',
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return ""

    return (resultado.stdout or "").strip()


def eh_processo_do_robo(
    pid: int,
    robo_file: Path,
    executar: Callable[..., "subprocess.CompletedProcess"] = subprocess.run,
) -> bool:
    """Confirma que o PID vivo corresponde de fato ao robo (main.py) esperado."""
    linha_comando = obter_linha_comando(pid, executar)
    if not linha_comando:
        return False
    return robo_file.name.lower() in linha_comando.lower()


def verificar_status(
    pid_file: Path,
    robo_file: Path,
    executar: Callable[..., "subprocess.CompletedProcess"] = subprocess.run,
) -> StatusRobo:
    """Determina o estado real do robo. Nunca lanca excecao."""
    pid = ler_pid(pid_file)

    if pid is None:
        if pid_file.exists():
            return StatusRobo(False, None, True, "arquivo invalido")
        return StatusRobo(False, None, False, "")

    linha_comando = obter_linha_comando(pid, executar)

    if linha_comando and robo_file.name.lower() in linha_comando.lower():
        return StatusRobo(True, pid, False, "")

    motivo = "pid reaproveitado" if linha_comando else "processo morto"
    return StatusRobo(False, pid, True, motivo)


def limpar_pid_orfao(pid_file: Path) -> None:
    pid_file.unlink(missing_ok=True)


def iniciar(
    pid_file: Path,
    robo_file: Path,
    base_dir: Path,
    popen: Callable[..., "subprocess.Popen"] = subprocess.Popen,
    executar: Callable[..., "subprocess.CompletedProcess"] = subprocess.run,
) -> ResultadoIniciar:
    """
    Inicia o robo com seguranca:
    - se ja estiver rodando (PID confirmado), nao inicia outro;
    - se o PID_FILE for orfao (morto, reaproveitado ou invalido), limpa antes
      de iniciar um novo processo;
    - nunca encerra nada aqui, so limpa o registro local.
    """
    status = verificar_status(pid_file, robo_file, executar)

    if status.rodando:
        return ResultadoIniciar(False, status.pid, True, False, "")

    pid_orfao_recuperado = status.orfao and status.pid is not None
    if pid_orfao_recuperado:
        limpar_pid_orfao(pid_file)

    try:
        processo = popen(
            ["python", str(robo_file)],
            cwd=str(base_dir),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    except OSError as erro:
        return ResultadoIniciar(False, None, False, pid_orfao_recuperado, str(erro))

    pid_file.write_text(str(processo.pid), encoding="utf-8")
    return ResultadoIniciar(True, processo.pid, False, pid_orfao_recuperado, "")


def parar(
    pid_file: Path,
    robo_file: Path,
    executar: Callable[..., "subprocess.CompletedProcess"] = subprocess.run,
) -> ResultadoParar:
    """
    Para o robo com seguranca:
    - se nao houver PID registrado, nao faz nada (informa que ja esta parado);
    - se o PID for orfao (morto ou pertence a outro programa), apenas limpa o
      registro local e NUNCA tenta encerrar processo nenhum;
    - so chama taskkill quando o PID foi confirmado como sendo o robo.
    """
    status = verificar_status(pid_file, robo_file, executar)

    if status.pid is None:
        return ResultadoParar(False, None, True, False, "", "")

    if not status.rodando:
        limpar_pid_orfao(pid_file)
        return ResultadoParar(False, status.pid, False, True, status.motivo_orfao, "")

    try:
        executar(
            ["taskkill", "/PID", str(status.pid), "/F"],
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as erro:
        return ResultadoParar(False, status.pid, False, False, "", str(erro))

    limpar_pid_orfao(pid_file)
    return ResultadoParar(True, status.pid, False, False, "", "")
