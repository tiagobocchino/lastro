---
type: armadilha
description: "Lighthouse 100 no mobile não garante 375 px: ele emula 412 px; a rolagem horizontal só aparece medindo scrollWidth no Playwright"
---

# Lighthouse não mede 375 px

**Regra:** o QA de página mede `document.documentElement.scrollWidth` no Playwright, de 320 a 1440 px (320, 375, 414, 768, 900, 1024, 1440). Nota do Lighthouse não substitui essa medida.

**Why:**
- Em 26/11 (LST-55), o site tinha nota 99–100 no Lighthouse mobile e mesmo assim rolava para o lado em 375 px. O formulário da demo ficava com 392 px. O Lighthouse emula 412 px e não pegou.
- No redesenho, o menu com `white-space: nowrap` passou de 768 px e só a varredura por largura achou.

**How to apply:**
- Faça um laço por largura, comparando `scrollWidth` com `innerWidth`. Quando passar, liste os elementos cujo `getBoundingClientRect().right` excede a largura da tela.
- Filho de grid ou flex com texto, formulário ou tabela leva `min-width: 0`. Grade com `minmax(Npx, 1fr)` usa `minmax(min(Npx, 100%), 1fr)`.
