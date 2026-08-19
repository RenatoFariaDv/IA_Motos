import json
from datetime import datetime
from typing import Any

from core.paths import agent_decisions_path


def garantir_arquivo_decisoes() -> None:
    """Cria a pasta e o arquivo inicial caso não existam."""
    DECISIONS_FILE = agent_decisions_path()
    DECISIONS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not DECISIONS_FILE.exists():
        DECISIONS_FILE.write_text(
            "[]",
            encoding="utf-8",
        )


def carregar_decisoes() -> list[dict[str, Any]]:
    """Carrega todas as decisões registradas."""
    garantir_arquivo_decisoes()

    try:
        dados = json.loads(
            agent_decisions_path().read_text(
                encoding="utf-8-sig",
            )
        )
    except (OSError, json.JSONDecodeError) as erro:
        print(
            "Erro ao carregar histórico de decisões: "
            f"{erro}"
        )
        return []

    return dados if isinstance(dados, list) else []


def salvar_decisoes(
    decisoes: list[dict[str, Any]],
) -> None:
    """Salva o histórico completo de forma segura."""
    garantir_arquivo_decisoes()

    caminho = agent_decisions_path()
    arquivo_temporario = caminho.with_suffix(
        ".json.tmp"
    )

    arquivo_temporario.write_text(
        json.dumps(
            decisoes,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    arquivo_temporario.replace(
        caminho
    )


def registrar_decisao_oportunidade(
    oportunidade: dict[str, Any],
) -> dict[str, Any]:
    """
    Registra uma decisão real gerada pelo Agent Alpha.
    Evita duplicidade pelo conjunto missão + anúncio.
    """
    decisoes = carregar_decisoes()

    missao_id = oportunidade.get("missao_id")
    anuncio_link = str(
        oportunidade.get(
            "anuncio_link",
            "",
        )
    ).strip()

    for decisao_existente in decisoes:
        mesma_missao = (
            decisao_existente.get("missao_id")
            == missao_id
        )
        mesmo_link = (
            str(
                decisao_existente.get(
                    "anuncio_link",
                    "",
                )
            ).strip()
            == anuncio_link
        )

        if mesma_missao and mesmo_link:
            return decisao_existente

    decisao = {
        "id": (
            max(
                (
                    int(item.get("id", 0))
                    for item in decisoes
                    if isinstance(item, dict)
                ),
                default=0,
            )
            + 1
        ),
        "missao_id": missao_id,
        "data_hora": datetime.now().isoformat(
            sep=" ",
            timespec="seconds",
        ),
        "tipo": "OPORTUNIDADE_ANALISADA",
        "titulo": oportunidade.get(
            "titulo",
            "Anúncio sem título",
        ),
        "anuncio_link": anuncio_link,
        "score": oportunidade.get(
            "score",
            0,
        ),
        "confianca": oportunidade.get(
            "confianca",
            0,
        ),
        "recomendacao": oportunidade.get(
            "recomendacao",
            "",
        ),
        "motivos": oportunidade.get(
            "motivos",
            [],
        ),
        "resumo": oportunidade.get(
            "resumo",
            "",
        ),
        "decisao": oportunidade.get(
            "acao_recomendada",
            "",
        ),
        "alertas": oportunidade.get(
            "alertas",
            [],
        ),
        "checklist": oportunidade.get(
            "checklist",
            [],
        ),
        "preco": oportunidade.get(
            "preco",
            0,
        ),
        "primeira_oferta_sugerida": oportunidade.get(
            "primeira_oferta_sugerida",
            0,
        ),
        "preco_maximo_recomendado": oportunidade.get(
            "preco_maximo_recomendado",
            0,
        ),
    }

    decisoes.append(decisao)
    salvar_decisoes(decisoes)

    return decisao


def listar_decisoes_missao(
    missao_id: int,
    limite: int = 10,
) -> list[dict[str, Any]]:
    """Retorna as decisões mais recentes de uma missão."""
    decisoes = carregar_decisoes()

    filtradas = [
        decisao
        for decisao in decisoes
        if decisao.get("missao_id") == missao_id
    ]

    filtradas.sort(
        key=lambda item: str(
            item.get("data_hora", "")
        ),
        reverse=True,
    )

    return filtradas[:limite]