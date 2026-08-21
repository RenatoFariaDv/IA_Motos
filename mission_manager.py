import json
from datetime import datetime
from typing import Any

from core.paths import mission_matches_path, missions_path


def garantir_arquivo() -> None:
    """Cria a pasta e o arquivo inicial caso ainda não existam."""
    MISSIONS_FILE = missions_path()
    MISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not MISSIONS_FILE.exists():
        MISSIONS_FILE.write_text("[]", encoding="utf-8")


def carregar_missoes() -> list[dict[str, Any]]:
    """Carrega e valida a lista de missões salva no JSON."""
    garantir_arquivo()
    MISSIONS_FILE = missions_path()

    try:
        with MISSIONS_FILE.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

    except json.JSONDecodeError as erro:
        raise ValueError(
            f"O arquivo de missões está com JSON inválido: {MISSIONS_FILE}"
        ) from erro

    except OSError as erro:
        raise OSError(
            f"Não foi possível ler o arquivo de missões: {MISSIONS_FILE}"
        ) from erro

    if not isinstance(dados, list):
        raise ValueError(
            "Formato inválido: missions.json deve conter uma lista."
        )

    return dados


def salvar_missoes(missoes: list[dict[str, Any]]) -> None:
    """Salva a lista completa de missões no arquivo JSON."""
    garantir_arquivo()
    MISSIONS_FILE = missions_path()

    arquivo_temporario = MISSIONS_FILE.with_suffix(".json.tmp")

    try:
        with arquivo_temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(
                missoes,
                arquivo,
                ensure_ascii=False,
                indent=2,
            )

        arquivo_temporario.replace(MISSIONS_FILE)

    except OSError as erro:
        arquivo_temporario.unlink(missing_ok=True)

        raise OSError(
            f"Não foi possível salvar as missões em: {MISSIONS_FILE}"
        ) from erro


def criar_missao(
    marca: str,
    modelo: str,
    ano_min: str,
    ano_max: str,
    orcamento: str,
    primeira_oferta: str,
    limite_final: str,
    estrategia: str,
    aprovacao_humana: bool,
) -> dict[str, Any]:
    """Valida, evita duplicidade, cria, salva e retorna uma nova missão."""

    marca = marca.strip()
    modelo = modelo.strip()
    estrategia = estrategia.strip()

    if not marca:
        raise ValueError("Informe a marca da moto.")

    if not modelo:
        raise ValueError("Informe o modelo da moto.")

    if not estrategia:
        raise ValueError("Informe a estratégia da missão.")

    try:
        ano_minimo = int(ano_min)
        ano_maximo = int(ano_max)
        valor_orcamento = int(orcamento)
        valor_primeira_oferta = int(primeira_oferta)
        valor_limite_final = int(limite_final)

    except ValueError as erro:
        raise ValueError(
            "Ano e valores financeiros devem conter somente números."
        ) from erro

    if ano_minimo > ano_maximo:
        raise ValueError(
            "O ano mínimo não pode ser maior que o ano máximo."
        )

    if valor_orcamento <= 0:
        raise ValueError(
            "O orçamento máximo deve ser maior que zero."
        )

    if valor_primeira_oferta <= 0:
        raise ValueError(
            "A primeira oferta deve ser maior que zero."
        )

    if valor_limite_final <= 0:
        raise ValueError(
            "O limite final deve ser maior que zero."
        )

    if valor_primeira_oferta > valor_limite_final:
        raise ValueError(
            "A primeira oferta não pode ser maior que o limite final."
        )

    if valor_limite_final > valor_orcamento:
        raise ValueError(
            "O limite final não pode ultrapassar o orçamento máximo."
        )

    missoes = carregar_missoes()

    for missao_existente in missoes:
        if not isinstance(missao_existente, dict):
            continue

        try:
            mesma_missao = (
                str(
                    missao_existente.get("status", "")
                ).strip().upper()
                == "PENDENTE"
                and str(
                    missao_existente.get("marca", "")
                ).strip().upper()
                == marca.upper()
                and str(
                    missao_existente.get("modelo", "")
                ).strip().upper()
                == modelo.upper()
                and int(
                    missao_existente.get("ano_min", 0)
                )
                == ano_minimo
                and int(
                    missao_existente.get("ano_max", 0)
                )
                == ano_maximo
                and int(
                    missao_existente.get("orcamento", 0)
                )
                == valor_orcamento
                and int(
                    missao_existente.get("primeira_oferta", 0)
                )
                == valor_primeira_oferta
                and int(
                    missao_existente.get("limite_final", 0)
                )
                == valor_limite_final
                and str(
                    missao_existente.get("estrategia", "")
                ).strip().casefold()
                == estrategia.casefold()
                and bool(
                    missao_existente.get("aprovacao_humana")
                )
                == bool(aprovacao_humana)
            )

        except (TypeError, ValueError):
            mesma_missao = False

        if mesma_missao:
            raise ValueError(
                "Já existe uma missão PENDENTE idêntica: "
                f"#{missao_existente.get('id')}."
            )

    novo_id = max(
        (
            missao.get("id", 0)
            for missao in missoes
            if isinstance(missao, dict)
        ),
        default=0,
    ) + 1

    missao = {
        "id": novo_id,
        "marca": marca.upper(),
        "modelo": modelo.upper(),
        "ano_min": ano_minimo,
        "ano_max": ano_maximo,
        "orcamento": valor_orcamento,
        "primeira_oferta": valor_primeira_oferta,
        "limite_final": valor_limite_final,
        "estrategia": estrategia,
        "aprovacao_humana": bool(aprovacao_humana),
        "status": "PENDENTE",
        "data_criacao": datetime.now().isoformat(
            timespec="seconds"
        ),
    }

    missoes.append(missao)
    salvar_missoes(missoes)

    return missao

def listar_missoes() -> list[dict[str, Any]]:
    """Retorna todas as missões cadastradas."""
    return carregar_missoes()


def excluir_missao(missao_id: int) -> None:
    """
    Remove a missão pelo id do missions.json e todas as oportunidades relacionadas do mission_matches.json.
    """
    # Remover missão do missions.json
    missoes = carregar_missoes()
    novas_missoes = [m for m in missoes if m.get("id") != missao_id]
    salvar_missoes(novas_missoes)

    # Remover oportunidades do mission_matches.json
    matches_path = mission_matches_path()
    if matches_path.exists():
        try:
            with matches_path.open("r", encoding="utf-8") as f:
                matches = json.load(f)
        except Exception:
            matches = []

        if isinstance(matches, list):
            novos_matches = [m for m in matches if m.get("missao_id") != missao_id]
            with matches_path.open("w", encoding="utf-8") as f:
                json.dump(novos_matches, f, ensure_ascii=False, indent=2)



def editar_missao(
    missao_id: int,
    marca: str,
    modelo: str,
    ano_min: str,
    ano_max: str,
    orcamento: str,
    primeira_oferta: str,
    limite_final: str,
    estrategia: str,
    aprovacao_humana: bool,
) -> dict[str, Any]:
    """
    Atualiza uma missao existente, preservando id,
    status e data de criacao.
    """
    try:
        missao_id_numerico = int(missao_id)
    except (TypeError, ValueError) as erro:
        raise ValueError(
            "O ID da missao deve ser numerico."
        ) from erro

    marca = str(marca).strip()
    modelo = str(modelo).strip()
    estrategia = str(estrategia).strip()

    if not marca:
        raise ValueError("Informe a marca da moto.")

    if not modelo:
        raise ValueError("Informe o modelo da moto.")

    if not estrategia:
        raise ValueError(
            "Informe a estrategia da missao."
        )

    try:
        ano_minimo = int(ano_min)
        ano_maximo = int(ano_max)
        valor_orcamento = int(orcamento)
        valor_primeira_oferta = int(primeira_oferta)
        valor_limite_final = int(limite_final)

    except (TypeError, ValueError) as erro:
        raise ValueError(
            "Ano e valores financeiros devem conter "
            "somente numeros."
        ) from erro

    if ano_minimo > ano_maximo:
        raise ValueError(
            "O ano minimo nao pode ser maior "
            "que o ano maximo."
        )

    if valor_orcamento <= 0:
        raise ValueError(
            "O orcamento maximo deve ser maior que zero."
        )

    if valor_primeira_oferta <= 0:
        raise ValueError(
            "A primeira oferta deve ser maior que zero."
        )

    if valor_limite_final <= 0:
        raise ValueError(
            "O limite final deve ser maior que zero."
        )

    if valor_primeira_oferta > valor_limite_final:
        raise ValueError(
            "A primeira oferta nao pode ser maior "
            "que o limite final."
        )

    if valor_limite_final > valor_orcamento:
        raise ValueError(
            "O limite final nao pode ultrapassar "
            "o orcamento maximo."
        )

    missoes = carregar_missoes()
    missao_atualizada = None

    for indice, missao in enumerate(missoes):
        try:
            id_atual = int(missao.get("id"))
        except (TypeError, ValueError):
            continue

        if id_atual != missao_id_numerico:
            continue

        missao_atualizada = dict(missao)

        missao_atualizada.update(
            {
                "marca": marca.upper(),
                "modelo": modelo.upper(),
                "ano_min": ano_minimo,
                "ano_max": ano_maximo,
                "orcamento": valor_orcamento,
                "primeira_oferta": valor_primeira_oferta,
                "limite_final": valor_limite_final,
                "estrategia": estrategia,
                "aprovacao_humana": bool(
                    aprovacao_humana
                ),
                "data_atualizacao": datetime.now().isoformat(
                    timespec="seconds"
                ),
            }
        )

        missoes[indice] = missao_atualizada
        break

    if missao_atualizada is None:
        raise ValueError(
            f"Missao #{missao_id_numerico} "
            "nao encontrada."
        )

    salvar_missoes(missoes)

    return missao_atualizada



def alterar_status_missao(
    missao_id: int,
    novo_status: str,
) -> dict[str, Any]:
    """
    Altera somente o status de uma miss?o existente.
    """
    status_validos = {
        "PENDENTE",
        "EM_EXECUCAO",
        "NEGOCIANDO",
        "FINALIZADA",
        "CANCELADA",
        "COMPRADA",
    }

    try:
        missao_id_numerico = int(missao_id)
    except (TypeError, ValueError) as erro:
        raise ValueError(
            "O ID da miss?o deve ser num?rico."
        ) from erro

    status_normalizado = str(
        novo_status
    ).strip().upper()

    if status_normalizado not in status_validos:
        raise ValueError(
            "Status inv?lido. Use: "
            + ", ".join(sorted(status_validos))
        )

    missoes = carregar_missoes()
    missao_atualizada = None

    for indice, missao in enumerate(missoes):
        try:
            id_atual = int(
                missao.get("id")
            )
        except (TypeError, ValueError):
            continue

        if id_atual != missao_id_numerico:
            continue

        missao_atualizada = dict(missao)

        missao_atualizada.update(
            {
                "status": status_normalizado,
                "data_atualizacao": datetime.now().isoformat(
                    timespec="seconds"
                ),
            }
        )

        missoes[indice] = missao_atualizada
        break

    if missao_atualizada is None:
        raise ValueError(
            f"Miss?o #{missao_id_numerico} "
            "n?o encontrada."
        )

    salvar_missoes(missoes)

    return missao_atualizada
