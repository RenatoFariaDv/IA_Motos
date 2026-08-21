"""
Motor de calculo de score de oportunidades (IA Score).

Extraido verbatim de agent_alpha.py (IA_Motos_COMERCIAL) em um modulo
neutro, para separar o motor de pontuacao puro (sem GUI, sem Telegram,
sem AWS, sem memoria/checklist de agente) do conceito mais amplo de
"Agent Alpha", que nao esta integrado nesta branch ainda.

Pesos, thresholds, classificacoes e regras sao EXATAMENTE os mesmos do
COMERCIAL -- nenhuma formula foi alterada nesta extracao. A FIPE nao
participa deste calculo (ver fipe_matching.py para o enriquecimento
independente).
"""

import json
import re
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_FILE = BASE_DIR / "data" / "agent_settings.json"


CONFIGURACOES_PADRAO = {
    "peso_modelo": 30,
    "peso_marca": 15,
    "peso_ano_dentro": 15,
    "peso_ano_um_abaixo": 5,
    "peso_preco_primeira_oferta": 25,
    "peso_preco_limite_final": 18,
    "peso_preco_orcamento": 10,
    "peso_status_novo": 5,
    "penalidade_risco": 20,
    "penalidade_conservadora_risco": 5,
    "bonus_estrategia_agressiva": 5,
    "limite_excelente": 85,
    "limite_boa": 70,
    "limite_regular": 50,
    "palavras_risco": [
        "sinistro",
        "sinistrada",
        "recuperada",
        "recuperado",
        "batida",
        "batido",
        "leilão",
        "leilao",
        "sucata",
    ],
}


def carregar_configuracoes() -> dict[str, Any]:
    """
    Carrega as configurações do Agent Alpha.

    Em caso de arquivo ausente ou inválido, utiliza os valores padrão.
    """
    configuracoes = CONFIGURACOES_PADRAO.copy()
    configuracoes["palavras_risco"] = list(
        CONFIGURACOES_PADRAO["palavras_risco"]
    )

    if not SETTINGS_FILE.exists():
        print(
            "Aviso: agent_settings.json não encontrado. "
            "Usando configurações padrão."
        )
        return configuracoes

    try:
        with SETTINGS_FILE.open(
            "r",
            encoding="utf-8-sig",
        ) as arquivo:
            dados = json.load(arquivo)

    except (OSError, json.JSONDecodeError) as erro:
        print(
            "Aviso: não foi possível carregar agent_settings.json: "
            f"{erro}. Usando configurações padrão."
        )
        return configuracoes

    if not isinstance(dados, dict):
        print(
            "Aviso: agent_settings.json deve conter um objeto JSON. "
            "Usando configurações padrão."
        )
        return configuracoes

    campos_numericos = (
        "peso_modelo",
        "peso_marca",
        "peso_ano_dentro",
        "peso_ano_um_abaixo",
        "peso_preco_primeira_oferta",
        "peso_preco_limite_final",
        "peso_preco_orcamento",
        "peso_status_novo",
        "penalidade_risco",
        "penalidade_conservadora_risco",
        "bonus_estrategia_agressiva",
        "limite_excelente",
        "limite_boa",
        "limite_regular",
    )

    for campo in campos_numericos:
        valor = dados.get(campo)

        if valor is None:
            continue

        try:
            configuracoes[campo] = int(valor)
        except (TypeError, ValueError):
            print(
                f"Aviso: configuração inválida para {campo}. "
                "Mantendo valor padrão."
            )

    palavras_risco = dados.get("palavras_risco")

    if isinstance(palavras_risco, list):
        palavras_validas = [
            str(palavra).strip()
            for palavra in palavras_risco
            if str(palavra).strip()
        ]

        if palavras_validas:
            configuracoes["palavras_risco"] = palavras_validas

    limite_excelente = configuracoes["limite_excelente"]
    limite_boa = configuracoes["limite_boa"]
    limite_regular = configuracoes["limite_regular"]

    if not (
        0 <= limite_regular
        <= limite_boa
        <= limite_excelente
        <= 100
    ):
        print(
            "Aviso: limites de recomendação inválidos. "
            "Usando os limites padrão."
        )

        configuracoes["limite_excelente"] = (
            CONFIGURACOES_PADRAO["limite_excelente"]
        )
        configuracoes["limite_boa"] = (
            CONFIGURACOES_PADRAO["limite_boa"]
        )
        configuracoes["limite_regular"] = (
            CONFIGURACOES_PADRAO["limite_regular"]
        )

    return configuracoes


def converter_preco_brl(valor: Any) -> float:
    """
    Converte preços brasileiros para float.

    Exemplos:
    R$ 18.600
    R$ 18.600,00
    18600
    18.600
    """
    if valor is None:
        return 0.0

    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()

    if not texto:
        return 0.0

    texto = re.sub(r"[^\d,.-]", "", texto)

    if not texto:
        return 0.0

    try:
        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")

        elif texto.count(".") == 1:
            parte_inteira, parte_decimal = texto.split(".")

            if len(parte_decimal) == 3:
                texto = parte_inteira + parte_decimal

        elif texto.count(".") > 1:
            texto = texto.replace(".", "")

        return float(texto)

    except ValueError:
        return 0.0


def extrair_anos_do_titulo(titulo: str) -> list[int]:
    """Extrai anos entre 2000 e 2099 encontrados no título."""
    return [
        int(ano)
        for ano in re.findall(r"\b20\d{2}\b", titulo)
    ]


def formatar_preco(valor: float) -> str:
    """Formata um valor monetário no padrão brasileiro."""
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def gerar_resumo(
    marca_compativel: bool,
    modelo_compativel: bool,
    ano_situacao: str,
    preco_situacao: str,
    riscos_encontrados: list[str],
) -> str:
    """Gera uma explicação simples da análise."""
    partes: list[str] = []

    if marca_compativel and modelo_compativel:
        partes.append(
            "A marca e o modelo correspondem ao veículo solicitado."
        )
    elif modelo_compativel:
        partes.append(
            "O modelo corresponde ao solicitado, mas a marca não foi "
            "confirmada no título."
        )
    else:
        partes.append(
            "O modelo solicitado não foi confirmado no título."
        )

    if ano_situacao == "DENTRO":
        partes.append(
            "O ano identificado está dentro da faixa da missão."
        )
    elif ano_situacao == "UM_ANO_ABAIXO":
        partes.append(
            "O ano identificado está um ano abaixo da faixa desejada."
        )
    elif ano_situacao == "FORA":
        partes.append(
            "O ano identificado está fora da faixa da missão."
        )
    else:
        partes.append(
            "O ano não foi identificado no título do anúncio."
        )

    if preco_situacao == "PRIMEIRA_OFERTA":
        partes.append(
            "O preço está igual ou abaixo da primeira oferta definida."
        )
    elif preco_situacao == "LIMITE_FINAL":
        partes.append(
            "O preço está acima da primeira oferta, mas dentro do "
            "limite final."
        )
    elif preco_situacao == "ORCAMENTO":
        partes.append(
            "O preço está dentro do orçamento, mas acima do limite "
            "ideal de negociação."
        )
    elif preco_situacao == "ACIMA":
        partes.append(
            "O preço está acima do orçamento máximo."
        )
    else:
        partes.append(
            "O preço não pôde ser validado."
        )

    if riscos_encontrados:
        partes.append(
            "Foram encontrados termos de risco no título: "
            + ", ".join(riscos_encontrados)
            + "."
        )
    else:
        partes.append(
            "Nenhum termo de risco foi identificado no título."
        )

    return " ".join(partes)


def gerar_acao_recomendada(
    recomendacao: str,
    ano_situacao: str,
    riscos_encontrados: list[str],
) -> str:
    """Define a próxima ação recomendada."""
    if riscos_encontrados:
        return (
            "Verificar procedência, documentação, histórico de leilão "
            "e possíveis danos antes de qualquer negociação."
        )

    if recomendacao == "EXCELENTE":
        if ano_situacao == "NAO_IDENTIFICADO":
            return (
                "Abrir o anúncio e confirmar ano, quilometragem, "
                "documentação e estado geral. Se estiver tudo correto, "
                "priorizar o contato com o vendedor."
            )

        return (
            "Priorizar o contato com o vendedor e confirmar "
            "quilometragem, documentação e estado geral da moto."
        )

    if recomendacao == "BOA":
        return (
            "Abrir o anúncio, confirmar as informações ausentes e "
            "avaliar uma abordagem inicial ao vendedor."
        )

    if recomendacao == "REGULAR":
        return (
            "Analisar com cautela e confirmar ano, documentação, "
            "quilometragem e possíveis riscos antes de negociar."
        )

    return (
        "Não priorizar esta oportunidade. Revisar somente se surgirem "
        "novas informações relevantes."
    )


def analisar_oportunidade(
    missao: dict,
    oportunidade: dict,
) -> dict:
    """
    Analisa a oportunidade utilizando as métricas configuráveis.
    """
    if not isinstance(missao, dict):
        raise ValueError("missao deve ser um dicionário")

    if not isinstance(oportunidade, dict):
        raise ValueError("oportunidade deve ser um dicionário")

    configuracoes = carregar_configuracoes()

    peso_modelo = configuracoes["peso_modelo"]
    peso_marca = configuracoes["peso_marca"]
    peso_ano_dentro = configuracoes["peso_ano_dentro"]
    peso_ano_um_abaixo = configuracoes["peso_ano_um_abaixo"]
    peso_preco_primeira = configuracoes[
        "peso_preco_primeira_oferta"
    ]
    peso_preco_limite = configuracoes[
        "peso_preco_limite_final"
    ]
    peso_preco_orcamento = configuracoes[
        "peso_preco_orcamento"
    ]
    peso_status_novo = configuracoes["peso_status_novo"]
    penalidade_risco = configuracoes["penalidade_risco"]
    penalidade_conservadora = configuracoes[
        "penalidade_conservadora_risco"
    ]
    bonus_agressiva = configuracoes[
        "bonus_estrategia_agressiva"
    ]

    palavras_risco = configuracoes["palavras_risco"]

    marca = str(missao.get("marca", "")).strip()
    modelo = str(missao.get("modelo", "")).strip()
    estrategia = str(missao.get("estrategia", "")).strip()

    try:
        ano_min = int(missao.get("ano_min", 0))
    except (TypeError, ValueError):
        ano_min = 0

    try:
        ano_max = int(missao.get("ano_max", 0))
    except (TypeError, ValueError):
        ano_max = 0

    orcamento = converter_preco_brl(
        missao.get("orcamento", 0)
    )
    primeira_oferta = converter_preco_brl(
        missao.get("primeira_oferta", 0)
    )
    limite_final = converter_preco_brl(
        missao.get("limite_final", 0)
    )

    titulo = str(
        oportunidade.get("titulo", "")
    ).strip()

    preco = converter_preco_brl(
        oportunidade.get("preco", 0)
    )

    status = str(
        oportunidade.get("status", "")
    ).strip().upper()

    motivos: list[str] = []
    alertas: list[str] = []
    score = 0

    modelo_compativel = False
    marca_compativel = False
    ano_situacao = "NAO_IDENTIFICADO"
    preco_situacao = "INVALIDO"

    if modelo:
        padrao_modelo = re.compile(
            rf"(?<!\w){re.escape(modelo)}(?!\w)",
            flags=re.IGNORECASE,
        )

        if padrao_modelo.search(titulo):
            modelo_compativel = True
            score += peso_modelo
            motivos.append(
                f"Modelo compatível: +{peso_modelo}"
            )
        else:
            motivos.append(
                "Modelo não encontrado como palavra isolada: +0"
            )
            alertas.append(
                "O modelo solicitado não foi confirmado no título."
            )
    else:
        motivos.append("Modelo não informado: +0")

    if marca:
        padrao_marca = re.compile(
            rf"(?<!\w){re.escape(marca)}(?!\w)",
            flags=re.IGNORECASE,
        )

        if padrao_marca.search(titulo):
            marca_compativel = True
            score += peso_marca
            motivos.append(
                f"Marca compatível: +{peso_marca}"
            )
        else:
            motivos.append(
                "Marca não encontrada no título: +0"
            )
            alertas.append(
                "A marca não foi confirmada no título."
            )
    else:
        motivos.append("Marca não informada: +0")

    anos_titulo = extrair_anos_do_titulo(titulo)

    if ano_min > 0 and ano_max > 0:
        if any(
            ano_min <= ano <= ano_max
            for ano in anos_titulo
        ):
            ano_situacao = "DENTRO"
            score += peso_ano_dentro
            motivos.append(
                "Ano dentro da faixa da missão: "
                f"+{peso_ano_dentro}"
            )

        elif any(
            ano == ano_min - 1
            for ano in anos_titulo
        ):
            ano_situacao = "UM_ANO_ABAIXO"
            score += peso_ano_um_abaixo
            motivos.append(
                "Ano um ano abaixo da faixa da missão: "
                f"+{peso_ano_um_abaixo}"
            )
            alertas.append(
                "O ano está um ano abaixo do solicitado."
            )

        elif anos_titulo:
            ano_situacao = "FORA"
            motivos.append(
                "Ano fora da faixa da missão: +0"
            )
            alertas.append(
                "O ano identificado está fora da faixa da missão."
            )

        else:
            motivos.append(
                "Ano não identificado no título: +0"
            )
            alertas.append(
                "Confirmar o ano diretamente no anúncio ou "
                "com o vendedor."
            )
    else:
        motivos.append(
            "Faixa de ano não informada: +0"
        )

    if preco <= 0:
        motivos.append(
            "Preço inválido ou não informado: +0"
        )
        alertas.append(
            "O preço precisa ser confirmado."
        )

    elif (
        primeira_oferta > 0
        and preco <= primeira_oferta
    ):
        preco_situacao = "PRIMEIRA_OFERTA"
        score += peso_preco_primeira
        motivos.append(
            "Preço igual ou abaixo da primeira oferta: "
            f"+{peso_preco_primeira}"
        )

    elif (
        limite_final > 0
        and preco <= limite_final
    ):
        preco_situacao = "LIMITE_FINAL"
        score += peso_preco_limite
        motivos.append(
            "Preço entre a primeira oferta e o limite final: "
            f"+{peso_preco_limite}"
        )

    elif (
        orcamento > 0
        and preco <= orcamento
    ):
        preco_situacao = "ORCAMENTO"
        score += peso_preco_orcamento
        motivos.append(
            "Preço acima do limite final, mas dentro do orçamento: "
            f"+{peso_preco_orcamento}"
        )
        alertas.append(
            "O valor está acima do limite ideal de negociação."
        )

    else:
        preco_situacao = "ACIMA"
        motivos.append(
            "Preço acima do orçamento: +0"
        )
        alertas.append(
            "O preço anunciado ultrapassa o orçamento máximo."
        )

    if status == "NOVO":
        score += peso_status_novo
        motivos.append(
            f"Status NOVO: +{peso_status_novo}"
        )
    else:
        motivos.append(
            "Status diferente de NOVO: +0"
        )

    titulo_normalizado = titulo.casefold()

    riscos_encontrados = [
        palavra
        for palavra in palavras_risco
        if palavra.casefold() in titulo_normalizado
    ]

    riscos_encontrados = list(
        dict.fromkeys(riscos_encontrados)
    )

    if riscos_encontrados:
        score -= penalidade_risco

        motivos.append(
            "Palavra de risco encontrada "
            f"({', '.join(riscos_encontrados)}): "
            f"-{penalidade_risco}"
        )

        alertas.append(
            "Há indicação de possível risco no histórico do veículo."
        )

    estrategia_normalizada = estrategia.casefold()

    if (
        estrategia_normalizada == "agressiva"
        and primeira_oferta > 0
        and preco <= primeira_oferta
    ):
        score += bonus_agressiva
        motivos.append(
            "Estratégia agressiva e preço na primeira oferta: "
            f"+{bonus_agressiva}"
        )

    elif (
        estrategia_normalizada == "conservadora"
        and riscos_encontrados
    ):
        score -= penalidade_conservadora
        motivos.append(
            "Estratégia conservadora com risco detectado: "
            f"-{penalidade_conservadora}"
        )

    score = max(0, min(100, score))

    if score >= configuracoes["limite_excelente"]:
        recomendacao = "EXCELENTE"

    elif score >= configuracoes["limite_boa"]:
        recomendacao = "BOA"

    elif score >= configuracoes["limite_regular"]:
        recomendacao = "REGULAR"

    else:
        recomendacao = "DESCARTAR"

    resumo = gerar_resumo(
        marca_compativel=marca_compativel,
        modelo_compativel=modelo_compativel,
        ano_situacao=ano_situacao,
        preco_situacao=preco_situacao,
        riscos_encontrados=riscos_encontrados,
    )

    acao_recomendada = gerar_acao_recomendada(
        recomendacao=recomendacao,
        ano_situacao=ano_situacao,
        riscos_encontrados=riscos_encontrados,
    )

    # Novos campos extras
    confianca = int(score)

    # Recomendacao especifica para ESTE anuncio -- nunca pode ultrapassar
    # o preco pedido pelo vendedor (requisito fundamental). `primeira_oferta`
    # e `limite_final` (acima) continuam representando a estrategia GERAL
    # da missao, preservados sem alteracao no retorno como
    # primeira_oferta_missao/limite_final_missao. Nunca inventa um valor
    # quando a entrada esta ausente ou zerada -- nesses casos o campo fica
    # None em vez de um numero fabricado.
    if preco <= 0:
        primeira_oferta_sugerida = None
        preco_maximo_recomendado = None
    else:
        preco_maximo_recomendado = (
            min(limite_final, preco) if limite_final > 0 else None
        )

        if primeira_oferta <= 0:
            primeira_oferta_sugerida = None
        elif preco >= primeira_oferta:
            # Anuncio dentro (ou acima) da abertura planejada da missao --
            # a abertura continua valendo como esta, sem precisar reduzir.
            primeira_oferta_sugerida = primeira_oferta
        elif limite_final > 0:
            # Anuncio mais barato que a propria abertura planejada da
            # missao: em vez de colapsar oferta e teto no mesmo valor
            # (perdendo a nocao de faixa de negociacao), preserva a
            # proporcao que a missao ja definiu entre abertura e limite,
            # aplicada sobre o teto ja calculado para ESTE anuncio. Nao
            # inventa um percentual novo -- reaproveita a propria
            # estrategia configurada pelo usuario. O min() final garante
            # o requisito fundamental mesmo se uma missao antiga tiver
            # abertura > limite (dado inconsistente que a validacao atual
            # de mission_manager.py deveria impedir, mas nao e garantido
            # para missoes ja existentes).
            proporcao = primeira_oferta / limite_final
            primeira_oferta_sugerida = min(
                preco_maximo_recomendado,
                preco_maximo_recomendado * proporcao,
            )
        else:
            # Sem limite_final para calcular uma proporcao -- nao inventa
            # proporcao nenhuma, so garante o teto obrigatorio.
            primeira_oferta_sugerida = min(primeira_oferta, preco)

    # Checklist curto, organizado e sem duplica??es
    checklist: list[str] = []

    def add_check(item: str) -> None:
        item = str(item).strip()

        if item and item not in checklist:
            checklist.append(item)

    if ano_situacao == "NAO_IDENTIFICADO":
        add_check("Confirmar ano")

    elif ano_situacao == "UM_ANO_ABAIXO":
        add_check(
            "Aten\u00e7\u00e3o: ve\u00edculo um ano abaixo da faixa"
        )

    elif ano_situacao == "FORA":
        add_check(
            "Aten\u00e7\u00e3o: ve\u00edculo fora da faixa de ano"
        )

    if (
        "quilometragem" not in oportunidade
        or not oportunidade.get("quilometragem")
    ):
        add_check("Confirmar quilometragem")

    if (
        "documentacao" not in oportunidade
        and "documenta\u00e7\u00e3o" not in oportunidade
    ):
        add_check("Verificar documenta\u00e7\u00e3o")

    add_check("Verificar hist\u00f3rico do ve\u00edculo")

    if preco_situacao == "ORCAMENTO":
        add_check(
            "Aten\u00e7\u00e3o: pre\u00e7o acima do limite ideal"
        )

    elif preco_situacao == "ACIMA":
        add_check(
            "Aten\u00e7\u00e3o: pre\u00e7o acima do or\u00e7amento"
        )

    if riscos_encontrados:
        add_check(
            "Aten\u00e7\u00e3o: poss\u00edvel hist\u00f3rico "
            "de leil\u00e3o ou sinistro"
        )

    return {
        "score": score,
        "recomendacao": recomendacao,
        "motivos": motivos,
        "resumo": resumo,
        "acao_recomendada": acao_recomendada,
        "alertas": alertas,
        "preco": preco,
        "preco_formatado": formatar_preco(preco),
        "orcamento": orcamento,
        "primeira_oferta_missao": primeira_oferta,
        "limite_final_missao": limite_final,
        "configuracoes_aplicadas": configuracoes,
        "confianca": confianca,
        "primeira_oferta_sugerida": primeira_oferta_sugerida,
        "preco_maximo_recomendado": preco_maximo_recomendado,
        "checklist": checklist,
    }
