---
type: armadilha
description: "app.js do portal não tem módulos: duas funções com o mesmo nome fazem a segunda apagar a primeira em silêncio"
---

# Nome repetido no `app.js` quebra outra tela sem erro

**Regra:** antes de criar uma função ou uma constante de topo em `lastro/web/app.js`, procure o nome (`grep -n "function NOME\|const NOME"`). O teste `tests/test_portal_js.py` acusa nome repetido.

**Why:** no LST-33, a exportação de fontes declarou outra `baixar()`. A segunda sobrescreveu a primeira, e os botões de relatório, notebook e pipeline da demanda pararam de funcionar em produção, sem erro no console e com o QA da tela nova passando. Só apareceu no LST-34, ao ler o código da tela de demanda. Corrigido no commit `e459c26`.

**How to apply:**
- Dê nomes específicos (`baixarArquivo`, `quandoBI`).
- No QA de uma tela nova, clique também num botão antigo da tela vizinha.
