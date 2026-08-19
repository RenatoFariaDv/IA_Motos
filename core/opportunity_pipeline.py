"""
Orquestracao do Opportunity Engine por rodada de coleta.

Recebe o sinal de que uma rodada OLX terminou (com os anuncios NOVOS
dessa rodada, ja persistidos em disco por main.py), verifica se ha
missao ativa, impede execucoes simultaneas via lock em arquivo, chama
opportunity_engine.buscar_oportunidades() de forma incremental (so os
anuncios novos, nunca o historico completo) e devolve um resumo.

Nunca lanca excecao para quem chamou -- main.py so precisa chamar
processar_rodada() e seguir em frente, mesmo se qualquer etapa falhar.
"""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, NamedTuple, Optional

from mission_manager import listar_missoes
from opportunity_engine import buscar_oportunidades


LOCK_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "opportunity_pipeline.lock"
)


class ResultadoLock(NamedTuple):
    adquirido: bool
    motivo: str


def _ler_pid_lock(lock_path: Path) -> Optional[int]:
    if not lock_path.exists():
        return None

    try:
        conteudo = json.loads(lock_path.read_text(encoding="utf-8"))
        return int(conteudo.get("pid"))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def _pid_vivo_e_python(
    pid: int,
    executar: Callable[..., "subprocess.CompletedProcess"] = subprocess.run,
) -> bool:
    """
    Confirma que o PID gravado no lock ainda pertence a um processo
    Python vivo -- nao basta o numero do PID "existir", porque o
    Windows pode reaproveitar PIDs para processos completamente
    diferentes. Nunca encerra nada, so consulta.
    """
    try:
        resultado = executar(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                (
                    "(Get-CimInstance Win32_Process -Filter "
                    f'"ProcessId={pid}").Name'
                ),
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return False

    nome = (resultado.stdout or "").strip().lower()
    return nome.startswith("python")


def adquirir_lock(
    lock_path: Path = LOCK_PATH,
    executar: Callable[..., "subprocess.CompletedProcess"] = subprocess.run,
) -> ResultadoLock:
    """
    Adquire o lock do pipeline de oportunidades. Se ja houver um PID
    vivo e Python registrado, recusa (ja em execucao). Se o lock for
    ausente, invalido ou orfao (PID morto ou nao-Python), recupera
    automaticamente e grava o lock com o PID atual. Nunca encerra
    nenhum processo.
    """
    pid_existente = _ler_pid_lock(lock_path)

    if pid_existente is not None and _pid_vivo_e_python(
        pid_existente, executar
    ):
        return ResultadoLock(
            False,
            "Já existe uma análise de oportunidades em execução "
            f"(PID {pid_existente}).",
        )

    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text(
            json.dumps(
                {
                    "pid": os.getpid(),
                    "iniciado_em": datetime.now().isoformat(
                        timespec="seconds"
                    ),
                }
            ),
            encoding="utf-8",
        )
    except OSError as erro:
        return ResultadoLock(False, f"Não foi possível criar o lock: {erro}")

    return ResultadoLock(True, "")


def liberar_lock(lock_path: Path = LOCK_PATH) -> None:
    lock_path.unlink(missing_ok=True)


def _resumo_erro(
    motivo: str,
    anuncios_recebidos: int = 0,
    missoes_ativas: int = 0,
    erro: str = "",
) -> dict[str, Any]:
    return {
        "sucesso": False,
        "motivo": motivo,
        "erro": erro,
        "anuncios_recebidos": anuncios_recebidos,
        "missoes_ativas": missoes_ativas,
        "candidatos_compativeis": 0,
        "oportunidades_criadas": 0,
        "descartados": 0,
        "duplicados": 0,
        "erros": 0,
    }


def _executar_analise(
    anuncios_novos: list[dict[str, Any]],
    buscar_oportunidades_fn: Callable[..., dict[str, Any]],
    listar_missoes_fn: Callable[[], list[dict[str, Any]]],
) -> dict[str, Any]:
    try:
        missoes = listar_missoes_fn()
    except Exception as erro:
        print(f"[OPPORTUNITY] Erro ao listar missões: {erro}")
        return _resumo_erro(
            "erro_missoes",
            anuncios_recebidos=len(anuncios_novos),
            erro=str(erro),
        )

    missoes_ativas = [
        m
        for m in missoes
        if isinstance(m, dict) and m.get("status") == "PENDENTE"
    ]
    print(f"[OPPORTUNITY] {len(missoes_ativas)} missão(ões) ativa(s)")

    if not missoes_ativas:
        print("[OPPORTUNITY] Nenhuma missão ativa -- pulando análise.")
        return _resumo_erro(
            "sem_missao_ativa",
            anuncios_recebidos=len(anuncios_novos),
            missoes_ativas=0,
        )

    try:
        resumo = buscar_oportunidades_fn(anuncios=anuncios_novos)
    except Exception as erro:
        print(
            "[OPPORTUNITY] Erro inesperado no Opportunity Engine: "
            f"{erro}"
        )
        return _resumo_erro(
            "excecao_engine",
            anuncios_recebidos=len(anuncios_novos),
            missoes_ativas=len(missoes_ativas),
            erro=str(erro),
        )

    print(
        f"[OPPORTUNITY] {resumo.get('candidatos_compativeis', 0)} "
        "candidatos compatíveis"
    )
    print(
        f"[OPPORTUNITY] {resumo.get('oportunidades_criadas', 0)} "
        "oportunidade(s) criada(s)"
    )
    print(f"[OPPORTUNITY] {resumo.get('descartados', 0)} descartado(s)")
    print(f"[OPPORTUNITY] {resumo.get('duplicados', 0)} duplicado(s)")

    if resumo.get("erros", 0):
        print(
            f"[OPPORTUNITY] {resumo['erros']} erro(s) em "
            "candidatos individuais"
        )

    return {"sucesso": True, "motivo": "", "erro": "", **resumo}


def _finalizar(resultado: dict[str, Any], inicio: float) -> dict[str, Any]:
    duracao = time.time() - inicio
    resultado["duracao_segundos"] = duracao
    print(f"[OPPORTUNITY] Finalizado em {duracao:.2f}s")
    return resultado


def processar_rodada(
    anuncios_novos: Optional[list[dict[str, Any]]],
    buscar_oportunidades_fn: Callable[..., dict[str, Any]] = buscar_oportunidades,
    listar_missoes_fn: Callable[[], list[dict[str, Any]]] = listar_missoes,
    adquirir_lock_fn: Callable[..., ResultadoLock] = adquirir_lock,
    liberar_lock_fn: Callable[[], None] = liberar_lock,
) -> dict[str, Any]:
    """
    Ponto de entrada chamado por main.py depois que uma rodada OLX
    terminou e os anúncios já estão persistidos em disco.

    Nunca lança exceção -- qualquer falha (missões, engine, FIPE, link)
    vira um resumo com sucesso=False e é registrada em log; o lock é
    sempre liberado.
    """
    inicio = time.time()
    print("[OPPORTUNITY] Iniciando análise da rodada")

    anuncios_novos = anuncios_novos or []
    print(f"[OPPORTUNITY] {len(anuncios_novos)} anúncios novos recebidos")

    if not anuncios_novos:
        print(
            "[OPPORTUNITY] Nenhum anúncio novo -- análise não é "
            "necessária."
        )
        return _finalizar(_resumo_erro("sem_anuncios_novos"), inicio)

    # Rede de segurança única cobrindo TUDO daqui pra baixo (aquisição
    # de lock incluída) -- nenhuma falha inesperada, em nenhuma etapa,
    # pode propagar para quem chamou (main.py).
    lock_adquirido = False

    try:
        status_lock = adquirir_lock_fn()

        if not status_lock.adquirido:
            print(f"[OPPORTUNITY] {status_lock.motivo}")
            return _finalizar(
                _resumo_erro(
                    "lock_ativo",
                    anuncios_recebidos=len(anuncios_novos),
                    erro=status_lock.motivo,
                ),
                inicio,
            )

        lock_adquirido = True

        resultado = _executar_analise(
            anuncios_novos,
            buscar_oportunidades_fn,
            listar_missoes_fn,
        )

    except Exception as erro:
        print(f"[OPPORTUNITY] Erro inesperado no pipeline: {erro}")
        resultado = _resumo_erro(
            "excecao_pipeline",
            anuncios_recebidos=len(anuncios_novos),
            erro=str(erro),
        )

    finally:
        if lock_adquirido:
            try:
                liberar_lock_fn()
            except Exception as erro_liberacao:
                print(
                    "[OPPORTUNITY] Aviso: falha ao liberar lock: "
                    f"{erro_liberacao}"
                )

    return _finalizar(resultado, inicio)
