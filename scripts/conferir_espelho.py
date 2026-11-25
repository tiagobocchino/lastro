"""Confere o espelho (LST-30) contra o Supabase Storage de verdade: envia, lista, baixa e apaga um arquivo de teste.

Uso (no shell do Render ou em qualquer máquina com as variáveis do Lastro):
    LASTRO_STORAGE_URL=https://<ref>.supabase.co LASTRO_STORAGE_CHAVE=sb_secret_... python scripts/conferir_espelho.py
Sai com 0 se a ida e volta deu certo. Não imprime a chave.
"""

import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lastro.espelho import ErroEspelho, abrir_espelho  # noqa: E402

esp = abrir_espelho()
if esp is None:
    sys.exit("defina LASTRO_STORAGE_URL e LASTRO_STORAGE_CHAVE")
marca = f"teste-{int(time.time())}"
with tempfile.TemporaryDirectory() as d:
    pasta = Path(d) / "_conferencia"
    (pasta / "sub").mkdir(parents=True)
    (pasta / "sub" / f"{marca}.txt").write_text(marca)
    try:
        enviados = esp.sincronizar(pasta, "_conferencia")
        achados = [k for k in esp.listar("_conferencia") if marca in k]
        conteudo = esp.baixar(f"_conferencia/sub/{marca}.txt").decode()
        esp.apagar([f"_conferencia/sub/{marca}.txt"])
    except ErroEspelho as e:
        sys.exit(f"falhou: {e}")
ok = enviados == 1 and achados == [f"_conferencia/sub/{marca}.txt"] and conteudo == marca
print(f"enviados={enviados} listados={len(achados)} conteudo_confere={conteudo == marca} -> {'ok' if ok else 'FALHOU'}")
sys.exit(0 if ok else 1)
