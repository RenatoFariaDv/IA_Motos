"""
Resolução centralizada dos caminhos de dados operacionais do IA_Motos.

Esses arquivos (missões encontradas, decisões do Agent Alpha, anúncios
coletados) são gerados pela execução do robô e da IA — não são
versionados no Git.

Por padrão, cada instalação usa e cria seus próprios arquivos locais,
dentro da raiz do próprio projeto.

Para transição/compatibilidade enquanto o Control Center desta branch
ainda não roda o robô de coleta, é possível apontar para os dados de uma
instalação existente (ex.: a versão comercial) definindo a variável de
ambiente IA_MOTOS_DATA_DIR com o caminho raiz dessa instalação. Nenhum
caminho pessoal é hardcoded aqui — configure em .env (veja .env.example).
"""

import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent


def base_dir() -> Path:
    """Raiz de onde os dados operacionais são lidos/escritos."""
    override = os.environ.get("IA_MOTOS_DATA_DIR", "").strip()
    return Path(override) if override else PROJECT_DIR


def data_dir() -> Path:
    return base_dir() / "data"


def agent_decisions_path() -> Path:
    return data_dir() / "agent_decisions.json"


def missions_path() -> Path:
    return data_dir() / "missions.json"


def mission_matches_path() -> Path:
    return data_dir() / "mission_matches.json"


def anuncios_encontrados_path() -> Path:
    return base_dir() / "interface" / "anuncios_encontrados.json"


def anuncios_vistos_path() -> Path:
    return base_dir() / "anuncios_vistos.json"
