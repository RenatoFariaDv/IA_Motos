import json
from mercado_livre_playwright_stealth import buscar_mercado_livre

def main():
    # Executa a função
    resultado = buscar_mercado_livre()

    # Salva o retorno em JSON
    with open("teste_integracao_ml.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    # Exibe total de anúncios retornados
    total = len(resultado) if isinstance(resultado, list) else 0
    print(f"total retornado: {total}")

    # Exibe quantidade por filtro_relacionado
    filtro_count = {}
    if isinstance(resultado, list):
        for anuncio in resultado:
            filtro = anuncio.get("filtro_relacionado", "N/A")
            filtro_count[filtro] = filtro_count.get(filtro, 0) + 1
    print("quantidade por filtro:")
    for filtro, count in filtro_count.items():
        print(f"  {filtro}: {count}")

    # Exibe o primeiro anúncio formatado em JSON
    if isinstance(resultado, list) and resultado:
        print("primeiro anúncio:")
        print(json.dumps(resultado[0], ensure_ascii=False, indent=2))
    else:
        print("Nenhum anúncio retornado.")

if __name__ == "__main__":
    main()