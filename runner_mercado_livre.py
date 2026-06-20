from config_ml import mercado_livre_ativo
from integrador_mercado_livre import obter_anuncios_mercado_livre
import json

def testar_mercado_livre():
    flag = mercado_livre_ativo()
    print("flag atual:", flag)
    if not flag:
        print("Mercado Livre desativado")
        print("Mercado Livre foi chamado: Não")
        print("total retornado: 0")
        return []
    anuncios = obter_anuncios_mercado_livre()
    total = len(anuncios) if hasattr(anuncios, '__len__') else 0
    print("Mercado Livre foi chamado: Sim")
    print("total retornado:", total)
    if total > 0:
        print("primeiro anúncio:")
        print(json.dumps(anuncios[0], ensure_ascii=False, indent=2))
    return anuncios

if __name__ == "__main__":
    testar_mercado_livre()