"""
Gerenciamento seguro do processo de sincronizacao AWS (sincronizar_aws.ps1).

Diferente do robo (main.py), o sincronizador nao tem um arquivo de PID
proprio -- ele roda em loop infinito e pode ser identificado de forma
confiavel a qualquer momento consultando os processos powershell.exe atuais
cuja linha de comando referencia o script esperado. Nunca encerra um
powershell.exe que nao corresponda com seguranca ao sincronizador do
IA_Motos.
"""

import subprocess
from pathlib import Path
from typing import Callable, NamedTuple, Optional, Tuple


class StatusSync(NamedTuple):
    rodando: bool
    pids: Tuple[int, ...]


class ResultadoIniciar(NamedTuple):
    sucesso: bool
    pid: Optional[int]
    ja_estava_rodando: bool
    erro: str


class ResultadoParar(NamedTuple):
    sucesso: bool
    pids_encerrados: Tuple[int, ...]
    ja_estava_parado: bool
    erro: str


def _listar_processos_sync(
    sync_script: Path,
    executar: Callable[..., "subprocess.CompletedProcess"] = subprocess.run,
) -> Tuple[int, ...]:
    """
    Retorna os PIDs de powershell.exe cuja linha de comando referencia o
    script de sincronizacao esperado. Exclui a propria consulta de
    diagnostico (que sempre contem "Get-CimInstance" no seu comando).
    """
    nome_script = sync_script.name

    try:
        resultado = executar(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                (
                    "Get-CimInstance Win32_Process | "
                    "Where-Object { $_.Name -eq 'powershell.exe' -and "
                    f"$_.CommandLine -match [regex]::Escape('{nome_script}') -and "
                    "$_.CommandLine -notmatch 'Get-CimInstance' } | "
                    "Select-Object -ExpandProperty ProcessId"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=8,
        )
    except (OSError, subprocess.SubprocessError):
        return ()

    saida = (resultado.stdout or "").strip()
    if not saida:
        return ()

    pids = []
    for linha in saida.splitlines():
        linha = linha.strip()
        if linha.isdigit():
            pids.append(int(linha))

    return tuple(pids)


def verificar_status(
    sync_script: Path,
    executar: Callable[..., "subprocess.CompletedProcess"] = subprocess.run,
) -> StatusSync:
    """Determina se o sincronizador esta rodando. Nunca lanca excecao."""
    pids = _listar_processos_sync(sync_script, executar)
    return StatusSync(rodando=len(pids) > 0, pids=pids)


def iniciar(
    sync_script: Path,
    base_dir: Path,
    popen: Callable[..., "subprocess.Popen"] = subprocess.Popen,
    executar: Callable[..., "subprocess.CompletedProcess"] = subprocess.run,
) -> ResultadoIniciar:
    """
    Inicia o sincronizador com seguranca: se ja houver um processo
    confirmado rodando, nao inicia outro (impede duplicidade).
    """
    status = verificar_status(sync_script, executar)

    if status.rodando:
        return ResultadoIniciar(False, status.pids[0], True, "")

    if not sync_script.exists():
        return ResultadoIniciar(False, None, False, f"Script nao encontrado: {sync_script}")

    try:
        processo = popen(
            [
                "powershell",
                "-NoExit",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(sync_script),
            ],
            cwd=str(base_dir),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    except OSError as erro:
        return ResultadoIniciar(False, None, False, str(erro))

    return ResultadoIniciar(True, processo.pid, False, "")


def parar(
    sync_script: Path,
    executar: Callable[..., "subprocess.CompletedProcess"] = subprocess.run,
) -> ResultadoParar:
    """
    Para o sincronizador com seguranca: so encerra PIDs confirmados pelo
    CommandLine como pertencentes ao sincronizador do IA_Motos. Se houver
    mais de um (estado inconsistente de antes desta correcao), encerra
    todos os confirmados.
    """
    pids = _listar_processos_sync(sync_script, executar)

    if not pids:
        return ResultadoParar(True, (), True, "")

    parados = []
    erros = []

    for pid in pids:
        try:
            executar(
                ["taskkill", "/PID", str(pid), "/F"],
                shell=True,
                check=True,
                capture_output=True,
                text=True,
            )
            parados.append(pid)
        except (OSError, subprocess.CalledProcessError) as erro:
            erros.append(f"PID {pid}: {erro}")

    sucesso = len(parados) == len(pids)
    return ResultadoParar(sucesso, tuple(parados), False, "; ".join(erros))
