"""Base simulada no padrão bruto da GIMI (card LST-36): vendas, orçamentos e RH, para testar os agentes.

Nada aqui é dado real. Copiamos só o **formato** (as entidades e o aninhamento que a API da IApp entrega
para cada empresa) e as **regras** que o ETL da GIMI aplica (repositório engenhadev-iapp-powerbi-etl,
transform `carteira_simulacao`). Nomes, CNPJs, valores e contratos são gerados com semente: a mesma
semente gera sempre a mesma base.

Sujeiras de propósito, as mesmas que as regras tratam:
- registros de teste ("TESTE" no cliente ou no projeto), contrato com valor 0, datas antes do corte;
- vendedor com sufixo " - (id)" ou "_apelido", vendedor ausente; classe entre parênteses no grupo;
- contrato repetido entre páginas, campos nulos, produtos aninhados dentro do contrato.

`gabarito()` aplica as regras com pandas e devolve o resultado esperado de cada pergunta de teste.
"""

from __future__ import annotations

import random
import re
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

# Nomes fictícios (26/11, pedido do Tiago): os códigos reais das empresas não aparecem nos relatórios de demonstração.
# Os ids continuam os mesmos e o nome não entra no sorteio: os totais da base não mudam.
EMPRESAS = {"alfa": 687, "beta": 688, "gama": 689, "delta": 1256}
CORTE = "2024-01-01"
INICIO, FIM = date(2023, 7, 1), date(2026, 10, 31)
STATUS = ["Orçado", "Em negociação", "Aprovado", "Perdido"]
MOTIVOS_PERDA = ["Preço", "Prazo", "Concorrente", "Projeto cancelado", None]
# Time interno (tipo de venda GIMI); o resto é representante. Regra do ETL: nome normalizado contém a palavra.
VENDEDORES_INTERNOS = ["ALINE", "BRUNO", "CARLA", "DIEGO", "ELISA"]
REPRESENTANTES = ["Fabio Rocha", "Gustavo Lima", "Helena Prado", "Igor Matos", "Joana Freitas", "Kleber Nunes", "Lara Duarte"]
INTERNOS = ["Aline Castro", "Bruno Teles", "Carla Moura", "Diego Vaz", "Elisa Ramos"]
GRUPOS = ["Construtoras (A)", "Incorporadoras (A)", "Revendas (B)", "Arquitetos (B)", "Consumidor final (C)", "Governo"]
SEGMENTOS = ["Construtora", "Incorporadora", "Revenda", "Arquitetura", "Pessoa física", "Público"]
UFS = ["DF", "GO", "SP", "MG", "BA", "PR", "SC"]
# Região do IBGE pela UF (fato geográfico, não regra de negócio). O IApp entrega estado e região no contrato.
REGIOES = {"DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste", "SP": "Sudeste", "MG": "Sudeste",
           "RJ": "Sudeste", "ES": "Sudeste", "BA": "Nordeste", "PE": "Nordeste", "CE": "Nordeste", "PR": "Sul", "SC": "Sul",
           "RS": "Sul", "PA": "Norte", "AM": "Norte", "TO": "Norte"}
CIDADES = {"DF": ["Brasília", "Taguatinga", "Ceilândia"], "GO": ["Goiânia", "Anápolis", "Rio Verde"], "MT": ["Cuiabá"], "MS": ["Campo Grande"],
           "SP": ["São Paulo", "Campinas", "Ribeirão Preto", "Santos"], "MG": ["Belo Horizonte", "Uberlândia", "Contagem"],
           "RJ": ["Rio de Janeiro", "Niterói"], "ES": ["Vitória"], "BA": ["Salvador", "Feira de Santana"], "PE": ["Recife"], "CE": ["Fortaleza"],
           "PR": ["Curitiba", "Londrina", "Maringá"], "SC": ["Florianópolis", "Joinville", "Blumenau"], "RS": ["Porto Alegre", "Caxias do Sul"],
           "PA": ["Belém"], "AM": ["Manaus"], "TO": ["Palmas"]}
# Obra pode ser em outro estado que o do cliente (construtora de Brasília com obra em Goiânia); peso maior para o Centro-Oeste e o Sudeste.
UFS_OBRA = ["DF"] * 6 + ["GO"] * 5 + ["SP"] * 5 + ["MG"] * 4 + ["MT", "MS", "RJ", "RJ", "ES", "BA", "BA", "PE", "CE", "PR", "PR", "SC", "RS", "PA", "AM", "TO"]
# Classificação por prefixo de SKU (o mesmo tipo de regra do transform_products): fora da lista = material avulso.
CATEGORIAS_SKU = {"ESQ": "Esquadria", "POR": "Porta", "JAN": "Janela", "VID": "Vidro", "PEL": "Pele de vidro", "FAC": "Fachada"}
PREFIXOS_AVULSOS = ["ACE", "PAR", "KIT"]
SETORES = {"Comercial": ["Vendedor interno", "Coordenador comercial", "Orçamentista"], "Engenharia": ["Projetista", "Engenheiro"],
           "Produção": ["Serralheiro", "Vidraceiro", "Ajudante", "Encarregado"], "Administrativo": ["Analista", "Assistente"],
           "Instalação": ["Instalador", "Ajudante de instalação"]}
PRIMEIROS = ["Ana", "Paulo", "Marcos", "Julia", "Rafael", "Beatriz", "Lucas", "Fernanda", "Tiago", "Camila", "Rodrigo", "Patrícia",
             "Gabriel", "Larissa", "Mateus", "Renata", "André", "Sofia", "Vinícius", "Bianca"]
SOBRENOMES = ["Almeida", "Barbosa", "Cardoso", "Dias", "Esteves", "Farias", "Gomes", "Henriques", "Jesus", "Leal", "Macedo", "Nogueira"]
PROJETOS = ["Residencial", "Edifício", "Condomínio", "Galpão", "Escola", "Clínica", "Loja", "Torre", "Casa"]


def _cnpj(rnd: random.Random) -> str:
    d = [rnd.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
    for pesos in ([5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]):
        r = sum(x * p for x, p in zip(d, pesos, strict=False)) % 11
        d.append(0 if r < 2 else 11 - r)
    s = "".join(map(str, d))
    return f"{s[:2]}.{s[2:5]}.{s[5:8]}/{s[8:12]}-{s[12:]}"


def _pessoa(rnd: random.Random) -> str:
    return f"{rnd.choice(PRIMEIROS)} {rnd.choice(SOBRENOMES)}"


def _data_sazonal(rnd: random.Random) -> datetime:
    """Mais pedidos no 2º semestre, menos no 1º trimestre (obra parada no período de chuvas)."""
    while True:
        d = INICIO + timedelta(days=rnd.randint(0, (FIM - INICIO).days))
        peso = {1: .55, 2: .65, 3: .8, 4: .9, 5: 1, 6: 1, 7: 1.05, 8: 1.15, 9: 1.2, 10: 1.25, 11: 1.15, 12: .8}[d.month]
        if rnd.random() < peso / 1.25:
            return datetime(d.year, d.month, d.day, rnd.randint(7, 19), rnd.randint(0, 59), rnd.randint(0, 59))  # noqa: DTZ001 (o IApp grava hora local, sem fuso)


def _empresa(chave: str, eid: int, rnd: random.Random, contratos_n: int) -> dict[str, list[dict]]:
    base = eid * 100_000
    # ---- vendedores: nome bruto com as sujeiras do sistema ----------------------------------
    vendedores = []
    for i, nome in enumerate(INTERNOS + REPRESENTANTES, start=1):
        bruto = nome
        if i % 3 == 0:
            bruto = f"{nome} - ({base + i})"  # sufixo com id
        elif i % 4 == 0:
            bruto = f"{nome.split()[0].lower()}_{nome.split()[1].lower()}"  # login com sublinhado
        vendedores.append({"id": base + i, "nome": bruto, "email": f"vendedor{i}@empresa-{chave}.exemplo",
                           "ativo": i not in (6, 12), "tipo": None})
    grupos = [{"id": base + 100 + i, "nome": g} for i, g in enumerate(GRUPOS, start=1)]
    clientes = []
    for i in range(1, 260):
        seg = rnd.choice(SEGMENTOS)
        clientes.append({"id": base + 1000 + i, "nome": f"{rnd.choice(['Construtora', 'Obras', 'Grupo', 'Incorporadora', 'Comercial'])} "
                         f"{rnd.choice(SOBRENOMES)} {rnd.choice(['Ltda', 'S.A.', 'EIRELI', 'ME'])}",
                         "documento": _cnpj(rnd), "segmento": seg,
                         "endereco": {"cidade": rnd.choice(["Brasília", "Goiânia", "Anápolis", "Taguatinga", "Uberlândia"]), "uf": rnd.choice(UFS)},
                         "grupo": rnd.choice(grupos) if rnd.random() > .08 else None})
    for cl in clientes:  # cidade coerente com a UF (Random próprio por cliente: a sequência do `rnd` não muda)
        cl["endereco"]["cidade"] = random.Random(cl["id"]).choice(CIDADES[cl["endereco"]["uf"]])
        cl["endereco"]["regiao"] = REGIOES[cl["endereco"]["uf"]]
    clientes.append({"id": base + 1999, "nome": "TESTE CLIENTE SISTEMA", "documento": None, "segmento": None,
                     "endereco": {"cidade": None, "uf": None, "regiao": None}, "grupo": None})
    # ---- contratos (orçamentos) com produtos aninhados ---------------------------------------
    contratos, item_id = [], base * 10
    for i in range(1, contratos_n + 1):
        cli = rnd.choice(clientes[:-1])
        criado = _data_sazonal(rnd)
        status = rnd.choices(STATUS, weights=[.22, .13, .40, .25])[0]
        produtos = []
        for _ in range(rnd.randint(1, 6)):
            item_id += 1
            prefixo = rnd.choice(list(CATEGORIAS_SKU) * 3 + PREFIXOS_AVULSOS)
            qtd = rnd.randint(1, 40)
            unit = round(rnd.lognormvariate(6.4, .7), 2)
            produtos.append({"id": item_id, "produto": {"codigo": f"{prefixo}-{rnd.randint(1000, 9999)}",
                                                        "descricao": f"{CATEGORIAS_SKU.get(prefixo, 'Item')} {rnd.choice(['linha 25', 'linha 30', 'suprema', 'gold'])}"},
                             "quantidade": qtd, "valores": {"unitario": unit, "total": round(qtd * unit, 2)}})
        valor = round(sum(p["valores"]["total"] for p in produtos), 2)
        vend = rnd.choice(vendedores) if rnd.random() > .04 else None
        projeto = f"{rnd.choice(PROJETOS)} {rnd.choice(SOBRENOMES)} {rnd.randint(1, 40)}"
        geo = random.Random(base * 10 + i)  # geografia (LST-51) sem consumir o `rnd`: os totais de antes continuam os mesmos
        uf_cli = cli["endereco"]["uf"]
        uf_obra = uf_cli if geo.random() < .65 else geo.choice(UFS_OBRA)
        obra = {"cidade": geo.choice(CIDADES[uf_obra]), "estado": uf_obra, "regiao": REGIOES[uf_obra]}
        if geo.random() < .03:  # obra sem local cadastrado (acontece no sistema de origem)
            obra = {"cidade": None, "estado": None, "regiao": None}
        c = {"id": base * 10 + i, "numero": f"{chave.upper()}-{criado.year}-{i:05d}", "data_criacao": criado.strftime("%Y-%m-%d %H:%M:%S"),
             "status": {"id": STATUS.index(status) + 1, "nome": status},
             "cliente": {"id": cli["id"], "nome": cli["nome"], "documento": cli["documento"], "cidade": cli["endereco"]["cidade"],
                         "estado": uf_cli, "regiao": REGIOES.get(uf_cli)},
             "projeto": {"nome": projeto, **obra}, "vendedor": {"id": vend["id"], "nome": vend["nome"]} if vend else None,
             "grupo": cli["grupo"], "valores": {"produtos": valor, "desconto": round(valor * rnd.choice([0, 0, .03, .05]), 2)},
             "data_aprovacao": (criado + timedelta(days=rnd.randint(3, 60))).strftime("%Y-%m-%d") if status == "Aprovado" else None,
             "motivo_perda": rnd.choice(MOTIVOS_PERDA) if status == "Perdido" else None, "produtos": produtos}
        r = rnd.random()
        if r < .015:  # registro de teste
            c["cliente"]["nome"] = "TESTE " + c["cliente"]["nome"]
        elif r < .03:
            c["projeto"]["nome"] = "teste de proposta"
        elif r < .05:  # orçamento zerado (rascunho)
            c["valores"] = {"produtos": 0.0, "desconto": 0.0}
            for p in c["produtos"]:
                p["valores"] = {"unitario": 0.0, "total": 0.0}
        contratos.append(c)
    contratos += [dict(c) for c in rnd.sample(contratos, k=max(1, contratos_n // 100))]  # repetidos entre páginas
    # ---- RH: funcionários, usuários e tarefas -----------------------------------------------
    funcionarios = []
    for i in range(1, 75):
        setor = rnd.choice(list(SETORES))
        adm = INICIO - timedelta(days=rnd.randint(0, 1500)) if i <= 45 else INICIO + timedelta(days=rnd.randint(0, (FIM - INICIO).days))
        dem = adm + timedelta(days=rnd.randint(120, 900)) if rnd.random() < .3 else None
        if dem and dem > FIM:
            dem = None
        funcionarios.append({"id": base + 5000 + i, "nome": _pessoa(rnd), "cargo": {"nome": rnd.choice(SETORES[setor])}, "setor": {"nome": setor},
                             "data_admissao": adm.isoformat(), "data_demissao": dem.isoformat() if dem else None, "ativo": dem is None})
    for i, v in enumerate(vendedores[:len(INTERNOS)]):  # vendedores internos também são funcionários do Comercial
        funcionarios.append({"id": base + 5900 + i, "nome": INTERNOS[i], "cargo": {"nome": "Vendedor interno"}, "setor": {"nome": "Comercial"},
                             "data_admissao": (INICIO - timedelta(days=400 + 90 * i)).isoformat(),
                             "data_demissao": None if v["ativo"] else "2025-06-30", "ativo": v["ativo"]})
    usuarios = [{"id": base + 7000 + i, "nome": f["nome"], "email": f"usuario{i}@empresa-{chave}.exemplo", "perfil": rnd.choice(["vendas", "engenharia", "admin"]),
                 "ativo": f["ativo"]} for i, f in enumerate(funcionarios[:30], start=1)]
    tarefas = []
    for i, c in enumerate(rnd.sample(contratos[:contratos_n], k=contratos_n // 3), start=1):
        criada = datetime.strptime(c["data_criacao"], "%Y-%m-%d %H:%M:%S") + timedelta(days=rnd.randint(0, 10))  # noqa: DTZ007
        feita = rnd.random() < .7
        tarefas.append({"id": base * 10 + 500_000 + i, "contrato_id": c["id"], "titulo": rnd.choice(["Visita técnica", "Medição", "Revisar orçamento", "Enviar proposta", "Follow-up"]),
                        "responsavel": {"id": u["id"], "nome": u["nome"]} if (u := rnd.choice(usuarios)) else None,
                        "status": "Concluída" if feita else rnd.choice(["Aberta", "Atrasada"]), "data_criacao": criada.strftime("%Y-%m-%d"),
                        "data_conclusao": (criada + timedelta(days=rnd.randint(1, 20))).strftime("%Y-%m-%d") if feita else None})
    return {"contratos": contratos, "clientes": clientes, "vendedores": vendedores, "grupos": grupos,
            "funcionarios": funcionarios, "usuarios": usuarios, "tarefas": tarefas}


def gerar(semente: int = 36, contratos_por_empresa: int = 3000) -> dict[str, dict[str, list[dict]]]:
    rnd = random.Random(semente)
    return {chave: _empresa(chave, eid, rnd, contratos_por_empresa) for chave, eid in EMPRESAS.items()}


# ---- regras de negócio (as mesmas do ETL da GIMI) e gabarito ----------------------------------

def _normalizar(s: Any) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn").strip().upper()


def tipo_venda(vendedor_bruto: Any) -> str:
    v = _normalizar(vendedor_bruto)
    return "GIMI" if any(k in v for k in VENDEDORES_INTERNOS) else "REPRESENTANTE"


def limpar_vendedor(vendedor_bruto: Any) -> str:
    nome = str(vendedor_bruto).split(" - (")[0].split("_")[0].strip().title()
    return "NAO DEFINIDO" if nome.lower() in ("nao definido", "nan", "none", "") else nome


def classe(grupo_nome: Any) -> str:
    m = re.search(r"\(([^)]+)\)", str(grupo_nome))
    return m.group(1) if m else "-"


def categoria_sku(codigo: Any) -> str:
    return CATEGORIAS_SKU.get(str(codigo).split("-")[0], "MATERIAL AVULSO")


TESTE = re.compile(r"teste", re.IGNORECASE)


def contratos_planos(base: dict) -> pd.DataFrame:
    """Contratos achatados como o conector entrega (json_normalize, separador '_'), com a coluna company."""
    regs = [{k: v for k, v in c.items() if k != "produtos"} | {"company": emp} for emp, ents in base.items() for c in ents["contratos"]]
    return pd.json_normalize(regs, sep="_")


def carteira(base: dict, planos: pd.DataFrame | None = None) -> pd.DataFrame:
    """Regras do transform_carteira_simulacao: sem teste, a partir do corte, sem valor 0, sem repetidos."""
    df = (contratos_planos(base) if planos is None else planos).drop_duplicates(subset=["id"], keep="last")
    df = df[~(df["cliente_nome"].astype(str).str.contains(TESTE) | df["projeto_nome"].astype(str).str.contains(TESTE))]
    df = df[pd.to_datetime(df["data_criacao"]) >= pd.Timestamp(CORTE)]
    df = df[df["valores_produtos"] > 0].copy()
    df["tipo_venda"] = df["vendedor_nome"].apply(tipo_venda)
    df["vendedor"] = df["vendedor_nome"].apply(limpar_vendedor)
    df["classe"] = df["grupo_nome"].apply(classe)
    return df


def gabarito(base: dict) -> dict[str, Any]:
    planos = contratos_planos(base)
    cart = carteira(base, planos)
    aprov = cart[cart["status_nome"] == "Aprovado"]
    fechados = cart[cart["status_nome"].isin(["Aprovado", "Perdido"])]
    itens = []
    for emp, ents in base.items():
        vistos = set()
        for c in ents["contratos"]:
            if c["id"] in vistos:
                continue
            vistos.add(c["id"])
            for p in c["produtos"]:
                itens.append({"contrato_id": c["id"], "company": emp, "codigo": p["produto"]["codigo"], "total": p["valores"]["total"]})
    itens = pd.DataFrame(itens)
    itens = itens[itens["contrato_id"].isin(aprov["id"])].copy()
    itens["categoria"] = itens["codigo"].apply(categoria_sku)
    func = pd.DataFrame([f | {"company": emp} for emp, ents in base.items() for f in ents["funcionarios"]])
    func["setor"] = func["setor"].apply(lambda s: s["nome"])
    r2 = lambda s: {k: round(float(v), 2) for k, v in s.items()}
    return {
        "carteira_linhas": len(cart),
        "vendido_total": round(float(aprov["valores_produtos"].sum()), 2),
        "orcado_total": round(float(cart["valores_produtos"].sum()), 2),
        "vendido_por_tipo_venda": r2(aprov.groupby("tipo_venda")["valores_produtos"].sum()),
        "vendido_por_vendedor": r2(aprov.groupby("vendedor")["valores_produtos"].sum().sort_values(ascending=False)),
        "vendido_por_classe": r2(aprov.groupby("classe")["valores_produtos"].sum()),
        "vendido_por_empresa": r2(aprov.groupby("company")["valores_produtos"].sum()),
        "vendido_por_regiao": r2(aprov.groupby("projeto_regiao")["valores_produtos"].sum().sort_values(ascending=False)),
        "vendido_por_uf": r2(aprov.groupby("projeto_estado")["valores_produtos"].sum().sort_values(ascending=False)),
        "vendido_sem_local": round(float(aprov.loc[aprov["projeto_regiao"].isna(), "valores_produtos"].sum()), 2),
        "orcado_por_regiao": r2(cart.groupby("projeto_regiao")["valores_produtos"].sum().sort_values(ascending=False)),
        "vendido_por_regiao_cliente": r2(aprov.groupby("cliente_regiao")["valores_produtos"].sum().sort_values(ascending=False)),
        "funil": {k: int(v) for k, v in cart["status_nome"].value_counts().items()},
        "taxa_conversao_pct": round(100 * (fechados["status_nome"] == "Aprovado").mean(), 1),
        "vendido_por_categoria": r2(itens.groupby("categoria")["total"].sum()),
        "rh_ativos_por_setor": {k: int(v) for k, v in func[func["ativo"]].groupby("setor").size().items()},
        "rh_admissoes_por_ano": {str(k): int(v) for k, v in pd.to_datetime(func["data_admissao"]).dt.year.value_counts().sort_index().items()},
        "rh_desligamentos_por_ano": {str(int(k)): int(v) for k, v in pd.to_datetime(func["data_demissao"]).dt.year.dropna().value_counts().sort_index().items()},
        "sujeiras": {"testes": int((planos["cliente_nome"].astype(str).str.contains(TESTE) | planos["projeto_nome"].astype(str).str.contains(TESTE)).sum()),
                     "antes_do_corte": int((pd.to_datetime(planos["data_criacao"]) < pd.Timestamp(CORTE)).sum()),
                     "valor_zero": int((planos["valores_produtos"] == 0).sum()),
                     "repetidos": int(planos["id"].duplicated().sum())},
    }


def exportar(base: dict, destino: Path) -> dict[str, int]:
    """Bruto como a API entrega (JSON por empresa e entidade) e o contrato achatado como o conector importa."""
    import json

    destino = Path(destino)
    contagem = {}
    for emp, ents in base.items():
        for ent, regs in ents.items():
            arq = destino / "bruto" / emp / f"{ent}.json"
            arq.parent.mkdir(parents=True, exist_ok=True)
            arq.write_text(json.dumps(regs, ensure_ascii=False, indent=1), encoding="utf-8")
            contagem[f"{emp}/{ent}"] = len(regs)
    contratos_planos(base).to_csv(destino / "contratos.csv", index=False)
    itens = [{"contrato_id": c["id"], "company": emp, "contrato_status": c["status"]["nome"], "contrato_data": c["data_criacao"],
              "cliente_nome": c["cliente"]["nome"], "projeto_nome": c["projeto"]["nome"], "projeto_estado": c["projeto"].get("estado"),
              "projeto_regiao": c["projeto"].get("regiao"), "valor_contrato": c["valores"]["produtos"],
              **pd.json_normalize(p, sep="_").iloc[0].to_dict()} for emp, ents in base.items() for c in ents["contratos"] for p in c["produtos"]]
    pd.DataFrame(itens).to_csv(destino / "itens.csv", index=False)
    func = [f | {"company": emp} for emp, ents in base.items() for f in ents["funcionarios"]]
    pd.json_normalize(func, sep="_").to_csv(destino / "funcionarios.csv", index=False)
    (destino / "gabarito.json").write_text(json.dumps(gabarito(base), ensure_ascii=False, indent=1), encoding="utf-8")
    return contagem
