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
from core.financial_scoring import (
    calcular_preco_alvo_negociacao,
    calcular_score_final,
    calcular_score_financeiro,
    classificar_atratividade_financeira,
    classificar_final,
)


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


def _resumo_zerado(
    anuncios_recebidos: int = 0,
    missoes_ativas: int = 0,
) -> dict[str, int]:
    return {
        "anuncios_recebidos": anuncios_recebidos,
        "missoes_ativas": missoes_ativas,
        "candidatos_compativeis": 0,
        "oportunidades_criadas": 0,
        "descartados": 0,
        "duplicados": 0,
        "erros": 0,
    }


def buscar_oportunidades(
    anuncios: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    """
    Casa anúncios com missões pendentes, pontua via
    core.opportunity_scoring, enriquece com FIPE e persiste.

    Se `anuncios` for fornecido, usa essa lista diretamente (modo
    incremental -- ex.: só os anúncios novos de uma rodada do robô) em
    vez de carregar o arquivo inteiro. Se `None` (padrão), mantém o
    comportamento histórico de carregar todos os anúncios do arquivo.

    Nunca lança exceção. Retorna um resumo estruturado:
    anuncios_recebidos, missoes_ativas, candidatos_compativeis,
    oportunidades_criadas, descartados, duplicados, erros.
    """
    try:
        missoes = listar_missoes()

    except Exception as erro:
        print(f"Erro ao listar missões: {erro}")
        return _resumo_zerado()

    if not isinstance(missoes, list):
        print("Erro: listar_missoes() não retornou uma lista.")
        return _resumo_zerado()

    missoes_ativas = sum(
        1
        for missao in missoes
        if isinstance(missao, dict) and missao.get("status") == "PENDENTE"
    )

    anuncios_carregados = (
        anuncios if anuncios is not None else carregar_anuncios()
    )
    matches = carregar_matches()

    # Em caso de JSON inválido, não prossegue e não sobrescreve nada.
    if anuncios_carregados is None or matches is None:
        print("Busca cancelada para preservar os dados existentes.")
        return _resumo_zerado(missoes_ativas=missoes_ativas)

    anuncios_recebidos = len(anuncios_carregados)

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
    candidatos_compativeis = 0
    descartados = 0
    duplicados = 0
    erros = 0

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

        for anuncio in anuncios_carregados:
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

            candidatos_compativeis += 1

            chave = (missao_id, link)

            if chave in combinacoes_existentes:
                duplicados += 1
                continue

            try:
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
                    descartados += 1
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

                # Enriquecimento independente com FIPE: roda só depois
                # do score/recomendação já fechados por
                # analisar_oportunidade(). Nunca altera score,
                # recomendacao, motivos, pesos ou thresholds -- só
                # adiciona campos novos.
                fipe = enriquecer_com_fipe(missao, oportunidade)
                oportunidade["valor_fipe"] = fipe["valor_fipe"]
                oportunidade["diferenca_fipe_reais"] = fipe[
                    "diferenca_fipe_reais"
                ]
                oportunidade["diferenca_fipe_percentual"] = fipe[
                    "diferenca_fipe_percentual"
                ]
                oportunidade["fipe_encontrada"] = fipe[
                    "fipe_encontrada"
                ]
                oportunidade["fipe_erro"] = fipe["fipe_erro"]

                # Shadow mode (core/financial_scoring.py): calcula um
                # score financeiro/final EXPERIMENTAL a partir da FIPE,
                # só para calibração -- nunca sobrescreve "score" nem
                # "recomendacao" (que continuam sendo exatamente o
                # score_missao/classificacao_missao de sempre, para
                # compatibilidade com Control Center, Analytics e
                # Memória da IA já existentes).
                dfp_para_financeiro = (
                    oportunidade["diferenca_fipe_percentual"]
                    if oportunidade["fipe_encontrada"]
                    else None
                )

                score_financeiro = calcular_score_financeiro(
                    dfp_para_financeiro
                )
                classificacao_financeira = (
                    classificar_atratividade_financeira(
                        dfp_para_financeiro
                    )
                )
                score_final_experimental = calcular_score_final(
                    oportunidade["score"], score_financeiro
                )
                classificacao_final_experimental = (
                    classificar_final(score_final_experimental)
                    if score_financeiro is not None
                    else oportunidade["recomendacao"]
                )

                oportunidade["score_missao"] = oportunidade["score"]
                oportunidade["classificacao_missao"] = oportunidade[
                    "recomendacao"
                ]
                oportunidade["score_financeiro"] = score_financeiro
                oportunidade["classificacao_financeira"] = (
                    classificacao_financeira
                )
                oportunidade["score_final_experimental"] = (
                    score_final_experimental
                )
                oportunidade["classificacao_final_experimental"] = (
                    classificacao_final_experimental
                )
                oportunidade["preco_alvo_negociacao"] = (
                    calcular_preco_alvo_negociacao(
                        preco_anuncio=oportunidade["preco"],
                        limite_final=oportunidade[
                            "preco_maximo_recomendado"
                        ],
                        primeira_oferta_missao=oportunidade[
                            "primeira_oferta_sugerida"
                        ],
                        valor_fipe=oportunidade["valor_fipe"],
                    )
                )

                registrar_decisao_oportunidade(
                    oportunidade
                )

                matches.append(oportunidade)
                novas_oportunidades.append(oportunidade)
                combinacoes_existentes.add(chave)

            except Exception as erro:
                erros += 1
                print(
                    f"Erro ao processar candidato "
                    f"'{titulo[:60]}': {erro}"
                )
                continue

    if novas_oportunidades:
        salvar_matches(matches)

    print(
        f"{len(novas_oportunidades)} "
        "novas oportunidades encontradas."
    )

    return {
        "anuncios_recebidos": anuncios_recebidos,
        "missoes_ativas": missoes_ativas,
        "candidatos_compativeis": candidatos_compativeis,
        "oportunidades_criadas": len(novas_oportunidades),
        "descartados": descartados,
        "duplicados": duplicados,
        "erros": erros,
    }


if __name__ == "__main__":
    buscar_oportunidades()