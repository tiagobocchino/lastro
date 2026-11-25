"""Confere se o board local (shared-docs/board) espelha o Jira.

Uso: python scripts/conferir_board.py LST-5 LST-6 ...   (chaves de cards do Jira, sem épicos)
O agente pega as chaves com a JQL `project = LST AND issuetype != Epic ORDER BY key` e passa aqui.
Sai com código 1 se faltar ou sobrar card.
"""

import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
locais = {
    re.match(r"(LST-\d+)", p.parent.name).group(1)
    for p in (RAIZ / "shared-docs" / "board").glob("*/LST-*/card.md")
}
jira = set(sys.argv[1:])


def ordem(k: str) -> int:
    return int(k.split("-")[1])


faltam, sobram = sorted(jira - locais, key=ordem), sorted(locais - jira, key=ordem)
print(f"Jira: {len(jira)} · board local: {len(locais)}")
if faltam:
    print("FALTAM no board local:", " ".join(faltam))
if sobram:
    print("SOBRAM no board local (não existem no Jira):", " ".join(sobram))
if not faltam and not sobram:
    print("ok: board local e Jira batem")
sys.exit(1 if faltam or sobram else 0)
