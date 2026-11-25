---
type: armadilha
description: Portais de API montados por JavaScript devolvem só a casca HTML no curl; a especificação real está num JSON carregado pela página
---

# Portal de API montado por JavaScript

Regra: antes de dar uma documentação como baixada, abra o arquivo e confira se é a especificação ou só a casca HTML. Quando for casca, abra o portal no Playwright, liste as respostas JSON da página e baixe o arquivo de especificação que ela carrega.

**Why:** o "bling-openapi.json" do repositório era o HTML do portal, e o "ploomes-llms.txt" era uma página 404. Isso só apareceu no LST-10. A especificação real estava em `developer.bling.com.br/build/assets/openapi-<hash>.json`, achada dentro de `reference-<hash>.js`, e em `developers.ploomes.com/json/openapi.json`.

**How to apply:**
- Use `python -c "import json; json.load(open(...))"` para confirmar que uma especificação baixada é JSON de verdade.
- O nome do arquivo do Bling muda a cada publicação do portal: procure de novo pelo `reference-*.js`.
- O Newman dá prioridade a `--env-var` sobre as variáveis da coleção. Não passe `token` em sistemas com login, senão o token do login é ignorado e a chamada volta 401.
- O limitador tem 1% de folga: com 3 requisições por segundo, espaçar 1/3 s somava 0,9999 s e a 4ª chamada caía na mesma janela.
