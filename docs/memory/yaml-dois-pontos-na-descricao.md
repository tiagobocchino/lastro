---
type: armadilha
description: Descrição de nota com dois-pontos quebra o frontmatter YAML
---

Regra: em `description:` de nota da Caixa ou de SKILL.md, texto com ": " vai entre aspas.

**Why:** "Trilha Google: de planilhas…" derrubou a indexação inteira na primeira execução. O leitor agora tem um fallback, mas a nota perde as tags.

**How to apply:** ao criar nota, rode `uv run lastro buscar "<assunto>"` e confira que ela aparece.
