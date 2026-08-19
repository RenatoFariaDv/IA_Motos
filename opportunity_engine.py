import json
import re
from datetime import datetime
from core.opportunity_scoring import analisar_oportunidade
from agent_decision_history import registrar_decisao_oportunidade
from link_validator import validar_link_olx
from pathlib import Path
from typing import Any

from mission_manager import listar_missoes
from core.paths import anuncios_encontrados_path, mission_matches_path
from fipe_matching import enriquecer_com_fipe


ANUNCIOS_PATH = anuncios_encontrados_path()
MATCHES_PATH = mission_matches_path()


def carregar_lista_json(
    caminho: Path,
    descricao: str,
    permitir_inexistente: bool = False,
) -> list[dict[str, Any]] | None:
    """
    Carrega e valida um arquivo JSON que deve conter uma lista.

    Retorna:
    - lista válida;
    - lista vazia quando o arquivo pode não existir;
    - None quando existe erro e a execução deve ser interrompida.
    """
    if not caminho.exists():
        if permitir_inexistente:
            return []

        print(f"Erro: arquivo de {descricao} não encontrado: {caminho}")
        return None

    try:
        with caminho.open("r", encoding="utf-8-sig") as arquivo:
            dados = json.load(arquivo)

    except json.JSONDecodeError as erro:
        print(f"Erro: JSON inválido em {descricao}: {erro}")
        return None

    except OSError as erro:
        print(f"Erro ao carregar {descricao}: {erro}")
        return None

    if not isinstance(dados, list):
        print(f"Erro: o arquivo de {descricao} não contém uma lista.")
        return None

    return [
        item
        for item in dados
        if isinstance(item, dict)
    ]


def carregar_anuncios() -> list[dict[str, Any]] | None:
    return carregar_lista_json(
        ANUNCIOS_PATH,
        "anúncios",
    )


def carregar_matches() -> list[dict[str, Any]] | None:
    return carregar_lista_json(
        MATCHES_PATH,
        "oportunidades",
        permitir_inexistente=True,
    )


def salvar_matches(matches: list[dict[str, Any]]) -> None:
    """
    Salva primeiro em arquivo temporário e só depois substitui o original.
    """
    MATCHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    arquivo_temporario = MATCHES_PATH.with_suffix(".json.tmp")

    try:
        with arquivo_temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(
                matches,
                arquivo,
                ensure_ascii=False,
                indent=2,
            )

        arquivo_temporario.replace(MATCHES_PATH)

    except OSError as erro:
        arquivo_temporario.unlink(missing_ok=True)

        raise OSError(
            f"Não foi possível salvar as oportunidades em: {MATCHES_PATH}"
        ) from erro


def converter_preco(valor: Any) -> float | None:
    """
    Converte formatos como:
    R$ 48.900
    R$ 48.900,00
    48900
    48.900
    """
    if valor is None:
        return None

    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()

    if not texto:
        return None

    texto = re.sub(r"[^\d,.-]", "", texto)

    if not texto:
        return None

    try:
        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")

        elif texto.count(".") == 1:
            parte_inteira, parte_decimal = texto.split(".")

            # Em preços brasileiros, três dígitos depois do ponto
            # normalmente representam separador de milhar.
            if len(parte_decimal) == 3:
                texto = parte_inteira + parte_decimal

        elif texto.count(".") > 1:
            texto = texto.replace(".", "")

        return float(texto)

    except ValueError:
        return None


def buscar_oportunidades() -> int:
    try:
        missoes = listar_missoes()

    except Exception as erro:
        print(f"Erro ao listar missões: {erro}")
        return 0

    if not isinstance(missoes, list):
        print("Erro: listar_missoes() não retornou uma lista.")
        return 0

    anuncios = carregar_anuncios()
    matches = carregar_matches()

    # Em caso de JSON inválido, não prossegue e não sobrescreve nada.
    if anuncios is None or matches is None:
        print("Busca cancelada para preservar os dados existentes.")
        return 0

    combinacoes_existentes = {
        (
            match.get("missao_id"),
            match.get("anuncio_link"),
        )
        for match in matches
        if match.get("missao_id") is not None
        and match.get("anuncio_link")
    }

    novas_oportunidades: list[dict[str, Any]] = []

    for missao in missoes:
        if not isinstance(missao, dict):
            continue

        if missao.get("status") != "PENDENTE":
            continue

        missao_id = missao.get("id")
        marca = str(missao.get("marca", "")).strip()
        modelo = str(missao.get("modelo", "")).strip()
        orcamento = converter_preco(missao.get("orcamento"))

        if missao_id is None or not modelo:
            continue

        if orcamento is None or orcamento <= 0:
            continue

        marca_normalizada = marca.casefold()
        modelo_normalizado = modelo.casefold()

        padrao_modelo = re.compile(
            rf"(?<!\w){re.escape(modelo_normalizado)}(?!\w)",
            flags=re.IGNORECASE,
        )

        for anuncio in anuncios:
            titulo = str(anuncio.get("titulo", "")).strip()
            link = str(anuncio.get("link", "")).strip()
            preco_numerico = converter_preco(anuncio.get("preco"))

            if not titulo or not link:
                continue

            titulo_normalizado = titulo.casefold()

            if not padrao_modelo.search(titulo_normalizado):
                continue

            if (
                marca_normalizada
                and marca_normalizada not in titulo_normalizado
            ):
                continue

            if preco_numerico is None:
                continue

            if preco_numerico > orcamento:
                continue

            chave = (missao_id, link)

            if chave in combinacoes_existentes:
                continue

            print(
                f"Verificando disponibilidade: {titulo[:60]}..."
            )

            validacao_link = validar_link_olx(link)
            status_link = validacao_link.get(
                "status",
                "ERRO_VERIFICACAO",
            )

            if status_link == "REMOVIDO":
                print(
                    f"An?ncio removido ignorado: {titulo[:60]}..."
                )
                continue

            oportunidade = {
                "missao_id": missao_id,
                "anuncio_link": link,
                "titulo": titulo,
                "preco": preco_numerico,
                "status": "NOVO",
                "status_link": status_link,
                "url_final": validacao_link.get(
                    "url_final",
                    link,
                ),
                "verificado_em": datetime.now().isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
                "encontrado_em": datetime.now().isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
                "origem": anuncio.get("origem", ""),
                "cidade": anuncio.get("cidade", ""),
                "imagem": anuncio.get("imagem", ""),
                "data_hora": anuncio.get("data_hora", ""),
            }

            analise = analisar_oportunidade(missao, oportunidade)

            oportunidade["score"] = analise["score"]
            oportunidade["recomendacao"] = analise["recomendacao"]
            oportunidade["motivos"] = analise["motivos"]
            oportunidade["resumo"] = analise["resumo"]
            oportunidade["acao_recomendada"] = analise[
                "acao_recomendada"
            ]
            oportunidade["alertas"] = analise["alertas"]
            oportunidade["confianca"] = analise["confianca"]
            oportunidade["primeira_oferta_sugerida"] = analise[
                "primeira_oferta_sugerida"
            ]
            oportunidade["preco_maximo_recomendado"] = analise[
                "preco_maximo_recomendado"
            ]
            oportunidade["checklist"] = analise["checklist"]

            # Enriquecimento independente com FIPE: roda só depois do
            # score/recomendação já fechados por analisar_oportunidade().
            # Nunca altera score, recomendacao, motivos, pesos ou
            # thresholds -- só adiciona campos novos.
            fipe = enriquecer_com_fipe(missao, oportunidade)
            oportunidade["valor_fipe"] = fipe["valor_fipe"]
            oportunidade["diferenca_fipe_reais"] = fipe[
                "diferenca_fipe_reais"
            ]
            oportunidade["diferenca_fipe_percentual"] = fipe[
                "diferenca_fipe_percentual"
            ]
            oportunidade["fipe_encontrada"] = fipe["fipe_encontrada"]
            oportunidade["fipe_erro"] = fipe["fipe_erro"]

            registrar_decisao_oportunidade(
                oportunidade
            )

            matches.append(oportunidade)
            novas_oportunidades.append(oportunidade)
            combinacoes_existentes.add(chave)

    if novas_oportunidades:
        salvar_matches(matches)

    print(
        f"{len(novas_oportunidades)} "
        "novas oportunidades encontradas."
    )

    return len(novas_oportunidades)


if __name__ == "__main__":
    buscar_oportunidades()