"""
Consulta de valor FIPE para motos, com resolucao conservadora de modelo.

Problema que este modulo resolve: a API publica da FIPE retorna varios
"modelos" de catalogo que contem o mesmo texto pesquisado como substring
(ex.: procurar "fan" para Honda retorna "CG 125 FAN", "CG 125 FAN ES",
"CG 150 FAN ESDi", "CG 160 FAN Flex", etc.) -- escolher arbitrariamente o
primeiro resultado pode pegar uma variante de catalogo que nem sequer
cobre o ano do anuncio, gerando falso-negativo ("ano nao encontrado")
mesmo quando existe uma variante correta.

Estrategia (conservadora, deterministica, sem LLM):
1. Normaliza texto (minusculas, sem acento, pontuacao vira espaco,
   espacos colapsados) e tokeniza em palavras.
2. Busca todos os modelos da marca na API e filtra os que contem TODOS
   os tokens do modelo procurado como palavras completas -- nunca por
   substring solto sem fronteira de palavra.
3. Para cada candidato que sobrou, consulta os anos disponiveis e
   elimina os que nao tem o ano procurado.
4. Se sobrar exatamente 1 candidato, usa ele.
5. Se sobrar mais de 1 (mesmo ano, nomes de catalogo diferentes),
   aplica um ranking deterministico por especificidade textual
   (correspondencia exata normalizada > menor quantidade de tokens
   "extras" alem dos solicitados). Se ainda empatar, NAO escolhe --
   retorna erro de ambiguidade explicito.
6. Se nenhum candidato tiver o ano procurado, retorna erro explicando
   quais candidatos foram considerados.

Nunca inventa marca, modelo ou ano. Mantem compatibilidade com os
campos ja consumidos no projeto (encontrado, valor_fipe, erro) e
acrescenta campos novos (modelo_solicitado, modelo_fipe_resolvido,
codigo_modelo_fipe, ano_solicitado, confianca_match) sem quebrar quem
so le os campos antigos.
"""

import json
import os
import re
import unicodedata
from datetime import datetime
from typing import Any, Callable, Optional

import requests


CACHE_PATH = os.path.join("interface", "fipe_motos.json")
BASE_URL = "https://parallelum.com.br/fipe/api/v1/motos"


def carregar_cache_fipe():
    try:
        if not os.path.exists(CACHE_PATH):
            return {}
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
        return cache
    except Exception:
        return {}


def salvar_cache_fipe(cache):
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar cache FIPE: {e}")


def gerar_chave_fipe(marca, modelo, ano):
    return f"{str(marca).strip().lower()} {str(modelo).strip().lower()} {str(ano).strip()}"


def normalizar_texto(texto: Any) -> str:
    """minusculas, sem acento, pontuacao vira espaco, espacos colapsados."""
    texto = str(texto or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^0-9a-z\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def tokenizar(texto: Any) -> list[str]:
    normalizado = normalizar_texto(texto)
    return normalizado.split(" ") if normalizado else []


def _filtrar_candidatos_por_tokens(
    modelo_procurado: str,
    modelos_api: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Mantem somente candidatos cujo nome contem TODOS os tokens do
    modelo procurado como palavras completas (nunca substring solto).
    """
    tokens_procurados = tokenizar(modelo_procurado)

    if not tokens_procurados:
        return []

    candidatos = []

    for item in modelos_api:
        tokens_candidato = set(tokenizar(item.get("nome", "")))

        if all(token in tokens_candidato for token in tokens_procurados):
            candidatos.append(item)

    return candidatos


def _ano_bate(nome_ano: Any, ano_procurado: str) -> bool:
    """
    Confere se o rotulo de ano da FIPE (ex.: '2023-1', '2023 Gasolina')
    corresponde ao ano procurado pelo prefixo numerico de 4 digitos --
    nunca por substring solto.
    """
    match = re.match(r"(\d{4})", str(nome_ano).strip())
    return bool(match) and match.group(1) == str(ano_procurado).strip()


def _calcular_especificidade(modelo_procurado: str, nome_candidato: str) -> int:
    """
    Quanto menor, mais especifico/proximo do que foi pedido. Usado só
    para desempate quando mais de 1 candidato sobra após o filtro de
    ano -- nunca decide sozinho qual candidato "parece certo".
    """
    if normalizar_texto(modelo_procurado) == normalizar_texto(nome_candidato):
        return 0

    tokens_procurados = set(tokenizar(modelo_procurado))
    tokens_candidato = tokenizar(nome_candidato)
    extras = len([t for t in tokens_candidato if t not in tokens_procurados])

    return 1 + extras


def _resolver_modelo(
    marca_id: Any,
    modelo_procurado: str,
    ano_procurado: str,
    obter_modelos: Callable[[Any], list[dict[str, Any]]],
    obter_anos: Callable[[Any, Any], list[dict[str, Any]]],
) -> dict[str, Any]:
    """
    Executa a resolucao conservadora descrita no docstring do modulo.

    Retorna:
      {"resolvido": bool, "modelo": dict|None, "ano_id": Any|None,
       "confianca": "alta"|"media"|"", "motivo": str}
    """
    modelos_api = obter_modelos(marca_id)
    candidatos_por_texto = _filtrar_candidatos_por_tokens(
        modelo_procurado,
        modelos_api,
    )

    if not candidatos_por_texto:
        return {
            "resolvido": False,
            "modelo": None,
            "ano_id": None,
            "confianca": "",
            "motivo": (
                f"Nenhum modelo FIPE contém os termos de "
                f"'{modelo_procurado}'."
            ),
        }

    candidatos_com_ano = []

    for candidato in candidatos_por_texto:
        anos_disponiveis = obter_anos(marca_id, candidato["codigo"])
        ano_info = next(
            (
                a
                for a in anos_disponiveis
                if _ano_bate(a.get("nome", ""), ano_procurado)
            ),
            None,
        )

        if ano_info is not None:
            candidatos_com_ano.append((candidato, ano_info))

    if not candidatos_com_ano:
        nomes = ", ".join(c["nome"] for c in candidatos_por_texto)
        return {
            "resolvido": False,
            "modelo": None,
            "ano_id": None,
            "confianca": "",
            "motivo": (
                f"Ano '{ano_procurado}' não disponível em nenhum "
                f"modelo FIPE compatível com '{modelo_procurado}' "
                f"(candidatos considerados: {nomes})."
            ),
        }

    if len(candidatos_com_ano) == 1:
        candidato, ano_info = candidatos_com_ano[0]
        return {
            "resolvido": True,
            "modelo": candidato,
            "ano_id": ano_info["codigo"],
            "confianca": "alta",
            "motivo": "",
        }

    # Mais de um candidato tem o mesmo ano -> desempate deterministico.
    ranqueados = sorted(
        candidatos_com_ano,
        key=lambda par: _calcular_especificidade(
            modelo_procurado,
            par[0]["nome"],
        ),
    )
    melhor_score = _calcular_especificidade(
        modelo_procurado,
        ranqueados[0][0]["nome"],
    )
    empatados = [
        par
        for par in ranqueados
        if _calcular_especificidade(modelo_procurado, par[0]["nome"])
        == melhor_score
    ]

    if len(empatados) == 1:
        candidato, ano_info = empatados[0]
        return {
            "resolvido": True,
            "modelo": candidato,
            "ano_id": ano_info["codigo"],
            "confianca": "media",
            "motivo": "",
        }

    nomes_empatados = ", ".join(par[0]["nome"] for par in empatados)
    return {
        "resolvido": False,
        "modelo": None,
        "ano_id": None,
        "confianca": "",
        "motivo": (
            f"Modelo FIPE ambíguo para {modelo_procurado} "
            f"{ano_procurado} -- múltiplos candidatos igualmente "
            f"plausíveis: {nomes_empatados}."
        ),
    }


def consultar_fipe_moto(
    marca,
    modelo,
    ano,
    requisitar: Optional[Callable[..., Any]] = None,
):
    """
    Consulta valor FIPE de uma moto usando a API pública da FIPE, com
    cache local e resolução conservadora de modelo (ver docstring do
    módulo).

    Args:
        marca (str): Marca da moto (ex: 'Honda')
        modelo (str): Modelo da moto (ex: 'Fan')
        ano (str/int): Ano da moto (ex: '2022' ou 2022)
        requisitar: função HTTP injetável para testes, assinatura
            `requisitar(url, timeout=10) -> objeto com .status_code
            e .json()`. Usa `requests.get` por padrão.

    Returns:
        dict com pelo menos `encontrado`, `valor_fipe`, `erro`.
        Nunca lança exceção.
    """
    if requisitar is None:
        def requisitar(url, timeout=10):
            return requests.get(url, timeout=timeout)

    chave = gerar_chave_fipe(marca, modelo, ano)
    cache = carregar_cache_fipe()

    if (
        chave in cache
        and isinstance(cache[chave], dict)
        and "valor_fipe" in cache[chave]
    ):
        resultado = dict(cache[chave])
        resultado["fonte"] = "cache local"
        resultado["encontrado"] = True
        return resultado

    def obter_modelos(marca_id):
        resposta = requisitar(
            f"{BASE_URL}/marcas/{marca_id}/modelos",
            timeout=10,
        )
        if resposta.status_code != 200:
            raise RuntimeError("Falha ao consultar modelos FIPE")
        return resposta.json().get("modelos", [])

    def obter_anos(marca_id, modelo_id):
        resposta = requisitar(
            f"{BASE_URL}/marcas/{marca_id}/modelos/{modelo_id}/anos",
            timeout=10,
        )
        if resposta.status_code != 200:
            raise RuntimeError("Falha ao consultar anos FIPE")
        return resposta.json()

    try:
        resp_marcas = requisitar(f"{BASE_URL}/marcas", timeout=10)
        if resp_marcas.status_code != 200:
            return {
                "encontrado": False,
                "erro": "Falha ao consultar marcas FIPE",
            }

        marcas = resp_marcas.json()
        marca_id = None

        for m in marcas:
            if m["nome"].lower() == str(marca).strip().lower():
                marca_id = m["codigo"]
                break

        if not marca_id:
            return {
                "encontrado": False,
                "erro": f"Marca '{marca}' não encontrada na FIPE",
            }

        resolucao = _resolver_modelo(
            marca_id,
            str(modelo),
            str(ano),
            obter_modelos,
            obter_anos,
        )

        if not resolucao["resolvido"]:
            return {
                "encontrado": False,
                "erro": resolucao["motivo"],
            }

        modelo_resolvido = resolucao["modelo"]
        ano_id = resolucao["ano_id"]

        resp_valor = requisitar(
            f"{BASE_URL}/marcas/{marca_id}/modelos/"
            f"{modelo_resolvido['codigo']}/anos/{ano_id}",
            timeout=10,
        )
        if resp_valor.status_code != 200:
            return {
                "encontrado": False,
                "erro": "Falha ao consultar valor FIPE",
            }

        dados = resp_valor.json()
        valor = dados.get("Valor")

        if not valor:
            return {
                "encontrado": False,
                "erro": "Valor FIPE não encontrado",
            }

        def valor_fipe_para_int(valor):
            if not isinstance(valor, str):
                return int(valor)
            valor = (
                valor.replace("R$", "")
                .replace(" ", "")
                .replace(".", "")
                .replace(",00", "")
            )
            return int(valor)

        valor_numerico = valor_fipe_para_int(valor)

        resultado = {
            "encontrado": True,
            "marca": marca,
            "modelo": modelo,
            "ano": ano,
            "valor_fipe": valor_numerico,
            "fonte": "API publica Parallelum/FIPE",
            "ultima_atualizacao": datetime.now().strftime("%Y-%m-%d"),
            "modelo_solicitado": modelo,
            "modelo_fipe_resolvido": modelo_resolvido["nome"],
            "codigo_modelo_fipe": modelo_resolvido["codigo"],
            "ano_solicitado": ano,
            "confianca_match": resolucao["confianca"],
        }

        # Cache guarda o resultado do modelo efetivamente resolvido,
        # nao so o texto pesquisado.
        cache[chave] = {
            k: v for k, v in resultado.items() if k != "encontrado"
        }
        salvar_cache_fipe(cache)

        return resultado

    except RuntimeError as erro:
        return {"encontrado": False, "erro": str(erro)}

    except Exception as e:
        return {"encontrado": False, "erro": f"Erro inesperado: {str(e)}"}


if __name__ == "__main__":
    print("Primeira consulta (deve consultar API ou cache):")
    resultado1 = consultar_fipe_moto("Honda", "PCX", 2022)
    print(resultado1)
    print()
    print("Segunda consulta (deve usar cache):")
    resultado2 = consultar_fipe_moto("Honda", "PCX", 2022)
    print(resultado2)
