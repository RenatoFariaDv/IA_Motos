"""
Motor puro de score financeiro (baseado em FIPE) e composicao com o
score de missao (core/opportunity_scoring.py).

Modulo isolado, sem efeitos colaterais:
- nao faz chamadas HTTP;
- nao le nem escreve arquivos/JSON;
- nao importa opportunity_engine nem qualquer coisa com I/O;
- recebe apenas numeros ja calculados (diferenca_fipe_percentual,
  score_missao, valor_fipe, etc.) e devolve numeros/classificacoes.

Convencao (a mesma de fipe_matching.py, nao redefinida aqui):
    diferenca_fipe_percentual positiva = anuncio ABAIXO da FIPE
                                          (bom negocio)
    diferenca_fipe_percentual negativa = anuncio ACIMA da FIPE
                                          (sobrepreco)

score_missao (core/opportunity_scoring.py) e score_financeiro (aqui)
sao sinais independentes. Este modulo nunca reavalia a missao nem
consulta a FIPE -- so combina numeros ja prontos.

As bandas, pesos e limites abaixo sao a configuracao PADRAO proposta na
auditoria (score financeiro/final) -- nao sao regras definitivas nem
estao espalhadas pelo codigo: toda funcao aceita um dict `configuracoes`
opcional para sobrescrever qualquer valor, com fallback seguro para
CONFIGURACOES_PADRAO quando omitido ou incompleto.

Os limites limite_excelente/limite_boa/limite_regular replicam os
mesmos valores hoje usados por core/opportunity_scoring.py -- mantidos
aqui de forma independente (nao importados) para este modulo nao ter
nenhuma dependencia do motor de score de missao.
"""

from typing import Any, Optional


CONFIGURACOES_PADRAO: dict[str, Any] = {
    # Ancoras de interpolacao linear (diferenca_fipe_percentual, score).
    # Fora do intervalo coberto, o valor satura no extremo mais proximo.
    "ancoras_score_financeiro": [
        (-25.0, 0.0),
        (-15.0, 10.0),
        (-8.0, 25.0),
        (-3.0, 40.0),
        (0.0, 50.0),
        (3.0, 60.0),
        (8.0, 75.0),
        (15.0, 90.0),
        (25.0, 100.0),
    ],
    # Bandas de classificacao textual: (limite_inferior_inclusive, rotulo),
    # da banda mais atrativa para a menos atrativa. O primeiro limite
    # que "diferenca_fipe_percentual >= limite_inferior" satisfizer
    # vence -- ou seja, cada fronteira pertence a banda mais favoravel.
    "bandas_classificacao_financeira": [
        (15.0, "MUITO_ALTA"),
        (8.0, "ALTA"),
        (3.0, "BOA"),
        (-3.0, "NEUTRA"),
        (-8.0, "BAIXA"),
    ],
    "classificacao_financeira_minima": "MUITO_BAIXA",
    "sem_dados_financeiros": "SEM DADOS",
    # Composicao do score final.
    "peso_score_missao": 70,
    "peso_score_financeiro": 30,
    # Classificacao final -- mesmos valores de
    # core/opportunity_scoring.CONFIGURACOES_PADRAO, mantidos
    # independentes aqui de proposito.
    "limite_excelente": 85,
    "limite_boa": 70,
    "limite_regular": 50,
    "classificacao_final_minima": "DESCARTAR",
    # Preco-alvo de negociacao: desconto desejado sobre a FIPE.
    "margem_desejada_negociacao": 0.10,
}


def _config(chave: str, configuracoes: Optional[dict[str, Any]]) -> Any:
    """Le uma chave de `configuracoes`, com fallback para o padrao."""
    if configuracoes and chave in configuracoes:
        return configuracoes[chave]
    return CONFIGURACOES_PADRAO[chave]


def calcular_score_financeiro(
    diferenca_fipe_percentual: Optional[float],
    configuracoes: Optional[dict[str, Any]] = None,
) -> Optional[float]:
    """
    Converte diferenca_fipe_percentual em um score financeiro 0-100,
    por interpolacao linear entre ancoras configuraveis.

    `diferenca_fipe_percentual is None` (FIPE nao encontrada, ano
    ambiguo, modelo ambiguo, API indisponivel -- qualquer caso em que
    fipe_matching.enriquecer_com_fipe() retornou fipe_encontrada=False)
    -> retorna None. Nunca inventa um numero.
    """
    if diferenca_fipe_percentual is None:
        return None

    ancoras = _config("ancoras_score_financeiro", configuracoes)
    ancoras_ordenadas = sorted(ancoras, key=lambda par: par[0])

    x = float(diferenca_fipe_percentual)
    x_min, y_min = ancoras_ordenadas[0]
    x_max, y_max = ancoras_ordenadas[-1]

    if x <= x_min:
        return float(y_min)

    if x >= x_max:
        return float(y_max)

    for (x0, y0), (x1, y1) in zip(ancoras_ordenadas, ancoras_ordenadas[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return float(y0)

            fracao = (x - x0) / (x1 - x0)
            return round(y0 + fracao * (y1 - y0), 2)

    return float(y_max)  # inatingivel -- ancoras cobrem [x_min, x_max]


def classificar_atratividade_financeira(
    diferenca_fipe_percentual: Optional[float],
    configuracoes: Optional[dict[str, Any]] = None,
) -> str:
    """
    Classifica a atratividade financeira em texto, a partir da mesma
    diferenca_fipe_percentual usada por calcular_score_financeiro().

    `diferenca_fipe_percentual is None` -> "SEM DADOS" (configuravel
    via `sem_dados_financeiros`), nunca uma banda inventada.
    """
    if diferenca_fipe_percentual is None:
        return str(_config("sem_dados_financeiros", configuracoes))

    bandas = _config("bandas_classificacao_financeira", configuracoes)
    bandas_ordenadas = sorted(bandas, key=lambda par: par[0], reverse=True)

    x = float(diferenca_fipe_percentual)

    for limite_inferior, rotulo in bandas_ordenadas:
        if x >= limite_inferior:
            return str(rotulo)

    return str(_config("classificacao_financeira_minima", configuracoes))


def calcular_score_final(
    score_missao: float,
    score_financeiro: Optional[float],
    configuracoes: Optional[dict[str, Any]] = None,
) -> int:
    """
    Combina score_missao (core/opportunity_scoring.py) com
    score_financeiro (calcular_score_financeiro() acima) por media
    ponderada configuravel (`peso_score_missao`/`peso_score_financeiro`).

    `score_financeiro is None` -> score_final = score_missao (sem
    inventar componente financeiro; degrada para o comportamento
    atual do projeto).

    Sempre retorna um inteiro entre 0 e 100 (arredondado e limitado).
    """
    if score_financeiro is None:
        score = float(score_missao)
    else:
        peso_missao = float(_config("peso_score_missao", configuracoes))
        peso_financeiro = float(
            _config("peso_score_financeiro", configuracoes)
        )
        soma_pesos = peso_missao + peso_financeiro

        if soma_pesos <= 0:
            score = float(score_missao)
        else:
            score = (
                peso_missao * float(score_missao)
                + peso_financeiro * float(score_financeiro)
            ) / soma_pesos

    score = max(0.0, min(100.0, score))
    return int(round(score))


def classificar_final(
    score_final: float,
    configuracoes: Optional[dict[str, Any]] = None,
) -> str:
    """
    Classifica score_final em EXCELENTE/BOA/REGULAR/DESCARTAR, usando
    os mesmos limites (limite_excelente/limite_boa/limite_regular) que
    core/opportunity_scoring.py aplica hoje ao score de missao --
    mantidos aqui como configuracao propria deste modulo (nao
    importados), para preservar o isolamento.

    Nao faz parte da lista original de 4 funcoes pedidas, mas e
    necessaria para produzir classificacao_final (usada no caso de
    regressao Honda Fan) sem espalhar os limites soltos pelo codigo
    que for compor o resultado final.
    """
    limite_excelente = float(_config("limite_excelente", configuracoes))
    limite_boa = float(_config("limite_boa", configuracoes))
    limite_regular = float(_config("limite_regular", configuracoes))

    score = float(score_final)

    if score >= limite_excelente:
        return "EXCELENTE"

    if score >= limite_boa:
        return "BOA"

    if score >= limite_regular:
        return "REGULAR"

    return str(_config("classificacao_final_minima", configuracoes))


def calcular_preco_alvo_negociacao(
    preco_anuncio: float,
    limite_final: float,
    primeira_oferta_missao: float,
    valor_fipe: Optional[float] = None,
    configuracoes: Optional[dict[str, Any]] = None,
) -> float:
    """
    Sugere um preco-alvo de abertura de negociacao para esta
    oportunidade especifica.

    Formula:
        alvo_fipe = valor_fipe * (1 - margem_desejada_negociacao)
        base = max(alvo_fipe, primeira_oferta_missao)   # quando ha FIPE
        preco_alvo_negociacao = min(preco_anuncio, limite_final, base)

    Sem FIPE (valor_fipe is None ou <= 0): base = primeira_oferta_missao
    (equivalente ao primeira_oferta_sugerida estatico usado hoje).

    Nunca acima do preco do anuncio nem do limite_final da missao --
    garantido pelo min() final, nao por caso especial.
    """
    preco_anuncio = float(preco_anuncio)
    limite_final = float(limite_final)
    primeira_oferta_missao = float(primeira_oferta_missao)

    if valor_fipe is None or float(valor_fipe) <= 0:
        base = primeira_oferta_missao
    else:
        margem = float(
            _config("margem_desejada_negociacao", configuracoes)
        )
        alvo_fipe = float(valor_fipe) * (1 - margem)
        base = max(alvo_fipe, primeira_oferta_missao)

    return min(preco_anuncio, limite_final, base)
