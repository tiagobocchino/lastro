"""Gera exemplos/orcamentos.csv: dados sintéticos (fictícios) para testar o Lastro.

Tem armadilhas de propósito: contratos duplicados, valores vazios e uma data no futuro.
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
EMPRESAS = ["alfa", "beta", "gama", "filial"]
VENDEDORES = ["Ana Souza", "Bruno Lima", "Carla Dias", "Diego Rocha", "Eva Martins", "Felipe Nunes", "Gabi Torres"]
ESTADOS = ["SP", "RJ", "MG", "PR", "BA", "SC", "GO"]
SEGMENTOS = ["residencial", "comercial", "industrial"]
STATUS = ["Fechado", "Em Aberto", "Perdido"]


def main() -> None:
    linhas = []
    inicio = date(2025, 1, 1)
    for i in range(1, 601):
        orcado = round(random.lognormvariate(11, 0.8), 2)
        status = random.choices(STATUS, [0.35, 0.4, 0.25])[0]
        vendido = round(orcado * random.uniform(0.85, 1.0), 2) if status == "Fechado" else 0.0
        linhas.append({
            "contrato_id": f"C{i:05d}",
            "empresa": random.choice(EMPRESAS),
            "vendedor": random.choice(VENDEDORES),
            "estado": random.choice(ESTADOS),
            "segmento": random.choice(SEGMENTOS),
            "status": status,
            "data_orcamento": (inicio + timedelta(days=random.randint(0, 540))).isoformat(),
            "valor_orcado": orcado,
            "valor_vendido": vendido,
        })
    for linha in random.sample(linhas, 12):  # duplicados: mesma chave, reenviados
        linhas.append(dict(linha))
    for linha in random.sample(linhas, 5):
        linha["valor_orcado"] = ""
    linhas[7]["data_orcamento"] = "2027-03-01"
    saida = Path(__file__).with_name("orcamentos.csv")
    with saida.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    print(saida, len(linhas), "linhas")


if __name__ == "__main__":
    main()
