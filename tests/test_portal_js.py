"""O portal é um único app.js sem módulos: duas funções com o mesmo nome fazem a segunda apagar a primeira
em silêncio (aconteceu no LST-33: a exportação de fontes derrubou o download de arquivos da demanda)."""

import re
from collections import Counter
from pathlib import Path

APP = Path(__file__).parent.parent / "lastro" / "web" / "app.js"


def test_app_js_sem_nomes_repetidos_no_topo():
    texto = APP.read_text(encoding="utf-8")
    nomes = re.findall(r"^(?:async\s+)?function\s+(\w+)\s*\(", texto, re.M)
    nomes += re.findall(r"^(?:const|let|var)\s+(\w+)\s*=", texto, re.M)
    repetidos = [n for n, c in Counter(nomes).items() if c > 1]
    assert not repetidos, f"nomes declarados mais de uma vez no app.js: {repetidos}"
