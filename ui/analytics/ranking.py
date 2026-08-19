from collections import Counter
import re

import customtkinter as ctk

from ui import theme
from ui.analytics import theme as analytics_theme


CHAVES_MODELO = (
    "modelo",
    "model",
    "moto",
    "nome_moto",
    "modelo_moto",
    "vehicle_model",
)

CHAVES_TITULO = (
    "titulo",
    "title",
    "anuncio_titulo",
    "vehicle_title",
    "nome",
)

CHAVES_ANINHADAS = (
    "anuncio",
    "veiculo",
    "vehicle",
    "moto",
    "dados",
)


def _texto_valido(valor):
    if valor is None:
        return ""

    if isinstance(valor, (str, int, float)):
        texto = str(valor).strip()

        if texto.lower() not in {
            "",
            "none",
            "null",
            "n/a",
            "na",
        }:
            return texto

    return ""


def _buscar_em_dicionario(dados, chaves):
    if not isinstance(dados, dict):
        return ""

    for chave in chaves:
        texto = _texto_valido(dados.get(chave))

        if texto:
            return texto

    return ""


def _limpar_modelo(texto):
    texto = _texto_valido(texto)

    if not texto:
        return ""

    texto = re.sub(
        r"\b(19|20)\d{2}\b",
        "",
        texto,
    )

    texto = re.sub(
        r"\b(vendo|vende-se|troco|imperdivel|oportunidade)\b",
        "",
        texto,
        flags=re.IGNORECASE,
    )

    texto = re.sub(
        r"[^A-Za-z?-?0-9 .+-]",
        " ",
        texto,
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    ).strip()

    palavras = texto.split()

    if len(palavras) > 4:
        palavras = palavras[:4]

    return " ".join(palavras).title()


def extrair_modelo(decisao):
    if not isinstance(decisao, dict):
        return ""

    modelo = _buscar_em_dicionario(
        decisao,
        CHAVES_MODELO,
    )

    if modelo:
        return _limpar_modelo(modelo)

    for chave in CHAVES_ANINHADAS:
        bloco = decisao.get(chave)

        if isinstance(bloco, dict):
            modelo = _buscar_em_dicionario(
                bloco,
                CHAVES_MODELO,
            )

            if modelo:
                return _limpar_modelo(modelo)

    titulo = _buscar_em_dicionario(
        decisao,
        CHAVES_TITULO,
    )

    if titulo:
        return _limpar_modelo(titulo)

    for chave in CHAVES_ANINHADAS:
        bloco = decisao.get(chave)

        if isinstance(bloco, dict):
            titulo = _buscar_em_dicionario(
                bloco,
                CHAVES_TITULO,
            )

            if titulo:
                return _limpar_modelo(titulo)

    return ""


def calcular_ranking_modelos(decisoes, limite=5):
    contador = Counter()

    if not isinstance(decisoes, list):
        return []

    for decisao in decisoes:
        modelo = extrair_modelo(decisao)

        if modelo:
            contador[modelo] += 1

    return contador.most_common(limite)


def criar_ranking_modelos(master, metricas):
    painel = ctk.CTkFrame(
        master,
        fg_color=theme.COLOR_CARD,
        corner_radius=14,
    )
    painel.pack(
        fill="x",
        pady=(0, 20),
    )

    ctk.CTkLabel(
        painel,
        text="Modelos mais encontrados",
        font=("Arial", 18, "bold"),
        anchor="w",
        text_color=analytics_theme.COLOR_TEXT,
    ).pack(
        fill="x",
        padx=20,
        pady=(18, 10),
    )

    decisoes = metricas.get("decisoes", [])
    ranking = calcular_ranking_modelos(decisoes)

    corpo = ctk.CTkFrame(
        painel,
        fg_color="transparent",
    )
    corpo.pack(
        fill="x",
        padx=20,
        pady=(0, 18),
    )

    if not ranking:
        ctk.CTkLabel(
            corpo,
            text="Nenhum modelo foi identificado no histórico atual.",
            anchor="w",
            font=("Arial", 13),
            text_color=analytics_theme.COLOR_TEXT_MUTED,
        ).pack(
            fill="x",
            pady=(2, 8),
        )

        return painel

    maior = ranking[0][1]

    for posicao, (modelo, quantidade) in enumerate(
        ranking,
        start=1,
    ):
        linha = ctk.CTkFrame(
            corpo,
            fg_color="transparent",
        )
        linha.pack(
            fill="x",
            pady=6,
        )

        ctk.CTkLabel(
            linha,
            text=f"{posicao}.",
            width=32,
            anchor="w",
            font=("Arial", 13, "bold"),
        ).pack(side="left")

        ctk.CTkLabel(
            linha,
            text=modelo,
            width=240,
            anchor="w",
            font=("Arial", 13, "bold"),
        ).pack(side="left")

        area_barra = ctk.CTkFrame(
            linha,
            width=420,
            height=18,
            fg_color="transparent",
        )
        area_barra.pack(
            side="left",
            padx=(8, 12),
        )
        area_barra.pack_propagate(False)

        largura = max(
            14,
            int((quantidade / maior) * 400),
        )

        barra = ctk.CTkFrame(
            area_barra,
            width=largura,
            height=18,
            fg_color=analytics_theme.COLOR_BOA,
            corner_radius=9,
        )
        barra.pack(
            side="left",
            fill="y",
        )
        barra.pack_propagate(False)

        ctk.CTkLabel(
            linha,
            text=str(quantidade),
            width=40,
            anchor="w",
            font=("Arial", 13),
        ).pack(side="left")

    return painel
