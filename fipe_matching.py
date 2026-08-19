"""
Enriquecimento independente de oportunidades com dados da FIPE.

Este modulo NUNCA altera score, recomendacao, motivos, pesos ou thresholds
calculados por core/opportunity_scoring.py. Ele roda depois do score ja
estar fechado, e so adiciona campos novos (valor_fipe, diferenca_fipe_reais,
diferenca_fipe_percentual, fipe_encontrada, fipe_erro) a partir de uma
consulta best-effort a consultar_fipe.py.

Estrategia de identificacao de marca/modelo/ano: deterministica e
conservadora, sem LLM.

- marca/modelo vem da propria missao (ja confirmados contra o titulo do
  anuncio pelo motor de matching do Opportunity Engine antes de chegar
  aqui) -- nunca extraidos de texto livre.
- ano so e usado quando existe exatamente um ano inequivoco no titulo
  (via core.opportunity_scoring.extrair_anos_do_titulo). Ausente ou
  ambiguo -> FIPE nao e consultada.

Quando a confianca nao e suficiente, a FIPE e marcada como nao
consultada/nao encontrada, com o motivo exato -- nunca inventa marca,
modelo ou ano.
"""

from typing import Any, Callable, Optional

from core.opportunity_scoring import extrair_anos_do_titulo
from consultar_fipe import consultar_fipe_moto as _consultar_fipe_moto_padrao


CAMPOS_VAZIOS = {
    "valor_fipe": None,
    "diferenca_fipe_reais": None,
    "diferenca_fipe_percentual": None,
    "fipe_encontrada": False,
    "fipe_erro": "",
}


def identificar_ano_para_fipe(titulo: str) -> tuple[Optional[int], str]:
    """
    Retorna (ano, motivo). `ano` é None quando não há confiança
    suficiente para usar o ano do título (ausente ou ambíguo); nesse
    caso `motivo` explica o porquê.
    """
    anos_distintos = sorted(set(extrair_anos_do_titulo(titulo or "")))

    if not anos_distintos:
        return None, "Ano não identificado no título."

    if len(anos_distintos) > 1:
        return None, "Ano ambíguo no título (mais de um ano encontrado)."

    return anos_distintos[0], ""


def enriquecer_com_fipe(
    missao: dict[str, Any],
    oportunidade: dict[str, Any],
    consultar_fipe: Callable[..., dict[str, Any]] = _consultar_fipe_moto_padrao,
) -> dict[str, Any]:
    """
    Retorna um dict somente com os 5 campos de enriquecimento FIPE.
    Nunca lança exceção. Nunca inventa marca/modelo/ano.
    """
    resultado = dict(CAMPOS_VAZIOS)

    marca = str(missao.get("marca", "")).strip()
    modelo = str(missao.get("modelo", "")).strip()

    if not marca:
        resultado["fipe_erro"] = "Marca não especificada na missão."
        return resultado

    if not modelo:
        resultado["fipe_erro"] = "Modelo não especificado na missão."
        return resultado

    titulo = str(oportunidade.get("titulo", ""))
    ano, motivo_ano = identificar_ano_para_fipe(titulo)

    if ano is None:
        resultado["fipe_erro"] = motivo_ano
        return resultado

    try:
        resultado_fipe = consultar_fipe(marca, modelo, ano)
    except Exception as erro:
        resultado["fipe_erro"] = f"Erro inesperado ao consultar FIPE: {erro}"
        return resultado

    if not isinstance(resultado_fipe, dict) or not resultado_fipe.get("encontrado"):
        erro = ""
        if isinstance(resultado_fipe, dict):
            erro = str(resultado_fipe.get("erro", ""))
        resultado["fipe_erro"] = erro or "FIPE não encontrada."
        return resultado

    valor_fipe = resultado_fipe.get("valor_fipe")

    if not isinstance(valor_fipe, (int, float)) or valor_fipe <= 0:
        resultado["fipe_erro"] = "Valor FIPE retornado é inválido."
        return resultado

    preco = oportunidade.get("preco")

    if not isinstance(preco, (int, float)) or preco <= 0:
        resultado["valor_fipe"] = valor_fipe
        resultado["fipe_encontrada"] = True
        resultado["fipe_erro"] = "Preço do anúncio indisponível para comparação."
        return resultado

    diferenca_reais = valor_fipe - preco
    diferenca_percentual = (diferenca_reais / valor_fipe) * 100

    return {
        "valor_fipe": valor_fipe,
        "diferenca_fipe_reais": diferenca_reais,
        "diferenca_fipe_percentual": diferenca_percentual,
        "fipe_encontrada": True,
        "fipe_erro": "",
    }
