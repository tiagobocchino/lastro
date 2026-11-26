# Auditoria de UI/UX · site, portal e dashboards (LST-55)

Data: 26/11/2026. Escopo: `site/index.html` + `site/demo.js`, portal (`lastro/web/index.html`, `app.js`, `marca.css`), painel HTML (`lastro/paineis.py`: `html_painel` e `para_visitante`), tema do Power BI (`lastro/relatorio_powerbi.py`, `TEMA`) e o app Streamlit (`lastro/rapido/app.py`).

Nenhum código de produção foi alterado. A marca (`BRAND.md`) manda: nenhuma proposta troca a paleta (`--chao`, `--sup`, `--tinta`, `--quieta`, `--linha`, `--ouro`) nem as fontes (Bricolage Grotesque, IBM Plex Sans e Mono). A skill `ui-ux-pro-max` entra com regras de acessibilidade, toque, estados e gráficos.

> O card LST-55 ainda não tem pasta em `shared-docs/board/`. Pela regra do AGENTS.md ("card sem espelho no board não está criado"), o curador precisa criar o espelho antes do `/to-spec`.

## 1. Como foi feito

- Servidor local: `LASTRO_HOME=<tmp> uv run lastro demo`, depois `LASTRO_DEMO=1 uv run lastro serve --porta 8765`. A demanda 1 foi aprovada pelo `rui@demo.lastro` e o painel foi montado pela API, para ter todos os estados (grill, aprovada, painel).
- Site em `/site/`, com a demo ligada (`LASTRO_DEMO=1`; sem a variável, `/api/demo/*` responde 404 "demonstração desligada").
- Streamlit: `streamlit run lastro/rapido/app.py` com `secrets.toml` local apontando para uma API falsa (`/bi/v1/tabelas` + um parquet sintético de 3.000 linhas no formato `painel_*`).
- Playwright (Chromium 1243) em 375×812 e 1440×900, tema claro e escuro (`colorScheme`). Em cada tela o script mediu: rolagem horizontal (`scrollWidth` > `clientWidth`), contraste WCAG de todo texto visível contra o fundo efetivo, alvos de toque abaixo de 44 px e campos sem rótulo.
- Estados simulados com `page.route`: lista vazia (`GET /api/demandas` → `[]`) e erro ao abrir demanda (`GET /api/demandas/1` → 500).
- Lighthouse 12 (Chromium do Playwright): site em mobile e desktop, portal em mobile.
- Regras da skill consultadas: `--domain ux` (touch target, horizontal scroll, error messages, loading states, empty states, color contrast, confirmation dialogs, aria labels), `--domain chart` (trend over time, compare categories, part-to-whole), `--domain style` (Data-Dense Dashboard), `--domain typography`.

### Lighthouse

| Página | Desempenho | Acessibilidade | Boas práticas | SEO |
|---|---|---|---|---|
| site, mobile | 99 | 100 | 100 | 100 |
| site, desktop | 100 | 100 | 100 | 100 |
| portal (login), mobile | 100 | 100 | 96 | 90 |

Oportunidades que o Lighthouse aponta: Google Fonts bloqueando a renderização (cerca de 910 ms no mobile, 820 ms no portal), imagens sem `srcset` (192 KiB) e sem WebP/AVIF (90 KiB), cache curto dos estáticos, favicon 404 e falta de `meta description` no portal.

**Atenção:** o Lighthouse mobile emula 412 px e por isso **não pega** a rolagem horizontal de 375 px do site (achado C1). Vale uma nota em `docs/memory/`: "Lighthouse 100 não garante 375 px; medir `scrollWidth` no Playwright".

### Contrastes medidos (tokens da marca)

| Par | Razão | Situação |
|---|---|---|
| `--quieta` sobre `--chao` (claro) | 5,64 | ok |
| `--quieta` sobre `--chao` (escuro) | 7,38 | ok |
| `--ouro-tx` sobre branco | 5,47 | ok para texto |
| `--ouro` (#B58324) sobre branco | 3,37 | ok só para gráfico, barra e texto grande |
| `--linha` como borda de campo (claro, #D6DCE2 sobre #F6F8F9/#FFF) | 1,30 / 1,38 | **falha** WCAG 1.4.11 (pede 3:1) |
| `--linha` como borda de campo (escuro) | 1,20 | **falha** |
| Título do Streamlit (#111820) no tema escuro | 1,01 | **falha crítica** |

No site e no portal, nenhum texto ficou abaixo de 4,5:1 nos dois temas. A paleta da marca está bem resolvida para texto; o problema é a borda de campos e os valores fixos fora dos tokens.

## 2. Estados testados

| Tela | Vazio | Carregando | Erro | Sucesso |
|---|---|---|---|---|
| Site · demo, passo 1 | testado (sem arquivo: "Escolha uma planilha…") | lido no código: o botão vira "lendo a planilha…" e fica desabilitado; fila 503 com contagem | testado: sem aceite ("Marque a caixa…") e arquivo inválido (**aceito**, ver A2) | testado com a planilha de exemplo |
| Site · demo, perguntas → painel | n/a | lido no código: "montando e conferindo…" | lido no código: 404/504 vão para "começar de novo" | testado: painel no iframe, recibo, convite |
| Portal · login | n/a | **sem estado** (botão não muda) | testado: senha errada mostra "Sua sessão expirou" (**bug**, C2) | testado |
| Portal · lista de demandas | testado com rota simulada: "Nenhuma demanda ainda. Comece pela primeira pergunta." (bom) | **sem estado** | testado (500 ao abrir): **nada aparece** (A3) | testado |
| Portal · nova demanda | "Nenhuma fonte conectada." (lido) | "explorador lendo as fontes…" | mensagem abaixo do botão | testado |
| Portal · grill | n/a | **sem estado** | mensagem abaixo do botão | testado |
| Portal · rodar agentes | n/a | "arquiteto, engenheiro, analista e auditor trabalhando…" | mensagem | testado (via demo) |
| Portal · painel da demanda | "montar painel" (lido) | **sem estado** na prévia | `p-msg` | testado |
| Portal · conta/BI | BI indisponível sem Postgres (testado); "Nada publicado ainda" (lido) | "gerando…" só nos downloads | `alert()` nos downloads | testado: senha, exportar, equipe |
| Painel HTML | **sem estado** para visual sem linhas (barras e tabela vazias, linha some) | n/a (estático) | n/a | testado em 375 e 1440, claro e escuro |
| Streamlit | testado: sem chave (`st.info`) e sem tabela (`st.warning`), lidos | spinner do `cache_resource` | `st.error` genérico | testado em 375 e 1440, claro e escuro |

## 3. Achados

Severidade: **crítico** (quebra regra do projeto ou impede o uso), **alto**, **médio**, **baixo**. Esforço: **P** (até 1 h), **M** (meio dia), **G** (1 dia ou mais).

### 3.1 Críticos

**C1 · Site, 375 px: rolagem horizontal de 17 px** (captura 03)
- Problema: em 375 px, `scrollWidth` = 392. O culpado é o `form.envio` (353 px) dentro do `.palco` (299 px úteis). Como é item de grid com `min-width: auto`, ele não encolhe. O texto "A primeira linha precisa ter o nome das colunas" sai cortado. Quebra a regra 2 do card e o QA do AGENTS.md.
- Regra: skill ux "Horizontal Scroll" (High). WCAG 1.4.10 Reflow.
- Correção (verificada no navegador: `scrollWidth` volta a 375):
  ```css
  .envio { min-width: 0 }        /* ou, mais amplo: .palco > * { min-width: 0 } */
  ```
- Esforço: P.

**C2 · Portal, login: senha errada aparece como "Sua sessão expirou. Entre de novo."** (captura 06)
- Problema: `api()` trata qualquer 401 como sessão vencida, inclusive o 401 do `/api/login`. Chama `sair()`, que redesenha o formulário (o e-mail digitado volta para `ana@demo.lastro`), e mostra uma mensagem falsa. Quem errou a senha não descobre que errou.
- Regra: skill ux "Error Messages" (High). WCAG 3.3.1 Identificação do erro.
- Correção em `app.js`:
  ```js
  if (r.status === 401 && sessao) { sair(); throw new Error("Sua sessão expirou. Entre de novo."); }
  if (r.status === 401) throw new Error("E-mail ou senha não conferem.");
  ```
  E dar `role="alert"` ao `#msg` do login.
- Esforço: P.

**C3 · Streamlit, tema escuro: título invisível e subtítulo ilegível** (captura 12)
- Problema: o título usa `color:#111820` fixo no `st.markdown`. Sobre o fundo escuro do Streamlit o contraste é 1,01:1. O subtítulo (#56606B) fica em 2,83:1. O Streamlit segue o tema do sistema, então metade dos usuários vê a tela sem título.
- Regra: skill ux "Color Contrast" (High). WCAG 1.4.3.
- Correção: tirar as cores fixas e usar `st.title("Lastro · relatórios rápidos")` + `st.caption(...)`. As cores passam a vir do tema (ver A8).
- Esforço: P.

### 3.2 Altos

**A1 · Painel HTML, 1440 px: coluna vazia e cartão de KPI esticado** (captura 10)
- Problema: `.grade { grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)) }` cria 3 colunas em 1100 px. O KPI e as barras ocupam duas e a terceira fica vazia. O KPI estica até a altura do ranking (240 px com um único número). Hierarquia fraca e espaço desperdiçado.
- Regra: skill style "Data-Dense Dashboard" (grade de 12 colunas, linha de cartões de KPI).
- Correção: layout explícito (ver a proposta na seção 4). Correção mínima: `.kpi`-bloco com `align-self: start` e `.barras` com `grid-column: span 2`.
- Esforço: M.

**A2 · Site, demo: arquivo inválido é aceito e o painel é oferecido** (captura 05)
- Problema: um CSV de lixo binário passa como "0 linhas e 1 colunas" (sic), mostra o caractere de controle no chip e libera "montar painel". O visitante vai gastar uma rodada para receber um painel vazio. Além disso, "1 colunas" está errado no plural.
- Regra: skill ux "Error Messages" e "Empty States". Voz da marca: prova antes de promessa.
- Correção: no `/api/demo/sessoes` (`lastro/demo.py`), recusar com 400 quando houver 0 linhas ou nenhuma coluna numérica, com a mensagem "A planilha não tem linhas com valor para somar. Confira se a primeira linha tem os nomes das colunas.". No `demo.js`, usar `plural()` como no portal.
- Esforço: P.

**A3 · Portal: erro ao abrir demanda é engolido**
- Problema: `abrirDemanda()` e `carregarLista()` não têm `try/catch`. Com 500 (simulado), o item fica marcado como ativo e a área principal continua mostrando a tela anterior. Nenhuma mensagem aparece e só sobra um erro no console. No Render com cold start ou timeout, a pessoa clica e "nada acontece".
- Regra: skill ux "Error Messages" e "Loading States" (High).
- Correção:
  ```js
  async function abrirDemanda(id) {
    atual = id; marcarLista();
    const p = $("#painel");
    p.setAttribute("aria-busy", "true");
    p.innerHTML = `<p class="rot">demanda ${id}</p><div class="bloco esqueleto" style="height:120px"></div>`;
    let d;
    try { d = await (await api(`/api/demandas/${id}`)).json(); }
    catch (err) { p.innerHTML = `<div class="bloco"><p class="erro-msg" role="alert">${esc(err.message)}</p><div class="linha-btn"><button class="btn sec" id="b-de-novo">tentar de novo</button></div></div>`; $("#b-de-novo").onclick = () => abrirDemanda(id); return; }
    finally { p.removeAttribute("aria-busy"); }
    …
  }
  ```
  CSS do esqueleto: `.esqueleto { background: linear-gradient(90deg, var(--sup) 0, var(--sup-2) 50%, var(--sup) 100%); background-size: 200% 100% } @media (prefers-reduced-motion: no-preference) { .esqueleto { animation: brilho 1.2s linear infinite } @keyframes brilho { to { background-position: -200% 0 } } }`.
- Esforço: M (repetir o padrão em `telaNova`, `telaConectores`, `telaConta`, `telaPainel`).

**A4 · Portal, 375 px: a lista de demandas empurra o conteúdo para fora da tela** (captura 07)
- Problema: abaixo de 760 px o `aside` vira bloco acima do `main`. Ao tocar numa demanda, o conteúdo é desenhado abaixo da lista (y ≈ 480 com 2 demandas). Com 10 demandas, fica fora da tela e o toque parece não fazer nada. O cabeçalho também quebra ("sair" desce para a segunda linha).
- Regra: skill ux "Navigation Patterns" (predictable). Mobile-first.
- Correção:
  1. Em `abrirDemanda`, depois de desenhar: `if (matchMedia("(max-width: 760px)").matches) $("#painel").scrollIntoView({ block: "start", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });`
  2. No mobile, a lista vira `<details>` recolhido com o título da demanda atual no `summary`.
  3. Cabeçalho: `@media (max-width: 480px) { .quem span.papel { display: none } }`, mantendo só o nome e "sair" na mesma linha.
- Esforço: M.

**A5 · Portal, login: credenciais de demonstração pré-preenchidas e visíveis sempre**
- Problema: `telaLogin()` sempre preenche `ana@demo.lastro` / `demo1234` e mostra a caixa "Contas de teste". Em produção (`LASTRO_AMBIENTE=producao`) essas contas não existem, mas a tela continua oferecendo as credenciais. Fica com cara de sistema de teste para o cliente pagante, e o hábito ensina a digitar senha conhecida.
- Regra: confiança é a tese da marca ("Toda resposta com lastro"). Skill ux "Forms".
- Correção: `GET /api/config` devolve `{ demo: true|false }`. O `telaLogin` só pré-preenche e mostra a `.dica` quando `demo`. O botão "entrar" ganha estado de carregamento ("entrando…", `disabled`).
- Esforço: P.

**A6 · Portal, demanda aprovada: o painel fica enterrado no fim de uma página de 4.300 px (6.500 px no mobile)** (captura 08)
- Problema: a ordem atual é total → tabela → auditoria (16 linhas) → camada 2 → SQL → **painel** → conversa → rastro (JSON cru). Para quem pediu, o painel é a entrega. Para quem audita, a auditoria pode ficar recolhida com o resumo à vista. O rastro mostra JSON bruto (`{"pergunta": …}`).
- Regra: skill ux hierarquia e "progressive disclosure". Voz: "mostrar o número, a checagem, o rastro", nessa ordem.
- Correção: reordenar quando `status === "aprovada"` para total + selo da auditoria ("16 checagens · 2 avisos · aprovada por rui") → painel → resposta → `<details>` da auditoria técnica → camada 2 → `<details>` "como chegamos aqui" → `<details>` rastro, com o `detalhe` formatado como chave: valor. Acrescentar uma navegação interna (`.passos` já existe) com âncoras: resposta · painel · auditoria · rastro.
- Esforço: M.

**A7 · Site, painel da demo: o iframe corta os cartões em 375 px e os horários não batem** (captura 04)
- Problema 1: dentro do iframe (≈297 px), `minmax(280px, 1fr)` + 32 px de padding passam da largura, e os cartões saem cortados à direita.
- Problema 2: o painel diz "gerado em 26/11/2026 00:59" e o recibo diz "Apagamos tudo às 03:59". O painel sai no horário de Brasília e o recibo no fuso do navegador. Num produto cuja tese é rastro e conferência, um horário que não bate derruba a confiança.
- Correção 1 (`paineis.py`, `html_painel`): `grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr))`.
- Correção 2: formatar os dois com `timeZone: "America/Sao_Paulo"` e sufixo "(Brasília)", ou mandar `apagado_em` já formatado pelo servidor.
- Esforço: P.

**A8 · Streamlit fora da marca: vermelho do Streamlit, fonte padrão e textos em inglês** (captura 12)
- Problema: sem `.streamlit/config.toml`, a aba ativa e o foco saem em vermelho (#FF4B4B). Pela marca, o ouro é o único acento e o vermelho é só estado de erro. O placeholder do multiselect aparece como "Choose options" (PT e EN misturados), o rótulo fica "Total de valor total", e os eixos do Plotly saem como "valor" e "3.4M" (formato inglês).
- Correção: `lastro/rapido/.streamlit/config.toml` (ou na raiz, onde o Streamlit Cloud roda):
  ```toml
  [theme]
  base = "light"
  primaryColor = "#B58324"
  backgroundColor = "#EEF1F3"
  secondaryBackgroundColor = "#FFFFFF"
  textColor = "#111820"
  font = "sans serif"
  [client]
  toolbarMode = "viewer"
  ```
  O Streamlit 1.67 aceita temas separados para claro e escuro e fontes próprias. Confirmar na documentação da versão instalada antes de usar `[theme.light]`/`[theme.dark]` com os valores escuros de `marca.css` e IBM Plex. No código: `multiselect(..., placeholder="todas")`, `fig.update_layout(separators=",.", font_family="IBM Plex Sans", yaxis_title=None, yaxis_tickformat=",.0f")` e rótulo `f"Total de {n.nome(medida)}"` sem repetir "total".
- Esforço: M.

### 3.3 Médios

**M1 · Bordas de campo com contraste 1,3:1 (portal e site)**. `input`, `select` e `textarea` usam `border: 1px solid var(--linha)` sobre `--sup-2`. WCAG 1.4.11 pede 3:1 para o limite de um componente. Correção sem cor nova, derivada dos tokens: `--borda-campo: color-mix(in srgb, var(--quieta) 60%, var(--linha))` aplicada só aos campos, com o foco continuando em `--ouro`. Esforço P.

**M2 · Cores fora dos tokens.** O site declara a própria cópia dos tokens em vez de importar `lastro/web/marca.css`, e já divergiu: falta `--erro`, e `.alerta` usa `#A3392B` / `#F08A7C` fixos. `.cta.ouro` e `.btn.ouro` usam `color: #1a1408` fixo nos dois arquivos. O `html_painel` copia um subconjunto dos tokens. Regra 1 do card: "cores só por token". Correção: o site faz `<link rel="stylesheet" href="/web/marca.css">` e usa `var(--erro)`. Criar o token `--tinta-sobre-ouro: #1a1408` em `marca.css`. O `html_painel` lê `marca.css` do disco e o incorpora no `<style>` (continua um arquivo só, sem deriva). Esforço M.

**M3 · Google Fonts bloqueando a renderização (≈0,9 s no mobile).** Falta `preconnect` para `fonts.gstatic.com` (só há para `googleapis`). Correção mínima: `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>`. Correção melhor: servir os woff2 de `/web/fontes/` (subconjunto latino, 5 arquivos) com `<link rel="preload" as="font" crossorigin>` e `font-display: swap`. Esforço P / M.

**M4 · Imagens do site: sem `srcset`, sem WebP e claras no tema escuro** (captura 02). As capturas de 1574 px vão para o celular inteiras (192 KiB a mais), e o texto da tabela do hero fica com uns 7 px em 375 px, ilegível. No tema escuro aparecem blocos brancos. Correção:
```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="img/resposta-escuro-800.webp 800w, img/resposta-escuro-1600.webp 1600w" type="image/webp">
  <source srcset="img/resposta-800.webp 800w, img/resposta-1600.webp 1600w" type="image/webp">
  <img src="img/resposta.jpg" sizes="(max-width: 900px) 100vw, 540px" …>
</picture>
```
No mobile, recortar a captura do hero para 4 linhas e 2 colunas (vendedor, total) ou trocá-la por uma mini tabela em HTML com os mesmos números. Esforço M.

**M5 · Site: falta a seção "como funciona" logo depois do hero.** O processo (planilha → perguntas → agentes → auditor → revisor → entrega) está espalhado em 4 seções de perguntas e só fecha em "Como começar", no fim. A prova de confiança também está tardia: "Feito por quem já errou o número antes" aparece depois do preço. Correção: uma faixa de 5 passos logo abaixo do hero, reaproveitando o estilo `.piloto` (último passo em ouro), com âncora `#como-funciona` no menu. Subir "quem está por trás" para antes de "Funciona com o que eu já uso?". A prova deve usar só números que já estão na página e são verificáveis ("15 sistemas mapeados, 3 testados em operação real", "12 contratos duplicados achados na demo"), sem inventar clientes. Esforço M (pede copy aprovada no card antes).

**M6 · Painel HTML: o gráfico de linha não tem eixo, valores, dica nem alternativa em tabela.** Só a polilinha com "máx." no meio do rodapé. O último mês (2027-03) desaba porque está incompleto ou é data futura; o auditor já avisa "1 linha com data no futuro", mas o painel não. Regra: skill chart "Trend Over Time" (fallback: tabela com datas e valores). Correção: linhas de grade com 3 rótulos no eixo Y, um `<circle>` com `<title>` por ponto (dica nativa, sem JS), período incompleto em linha tracejada com a legenda "mês em andamento", e `<details><summary>ver os números</summary><table>…</table></details>`. Esforço M.

**M7 · Nomes crus de coluna na interface.** "total de valor_vendido", cabeçalho "total_valor_vendido", "vendedor" minúsculo ao lado de "Valor vendido" na tabela do painel, "Valor orcado" sem acento (o `_nome` sai do slug). O `relatorio_powerbi.rotulo()` já resolve isso. Correção: expor um `rotulo()` comum (Python) e mandar os rótulos prontos na resposta da API (`colunas_rotulo`). No `para_visitante`, usar o nome original da coluna da planilha, não o slug. Esforço M.

**M8 · Abas do portal sem semântica de abas.** `demandas · conectores · conta` são `<button>` sem `role="tablist"`/`role="tab"`/`aria-selected`, e a ativa só se distingue pelo fundo. Correção: `role="tablist"` no `.abas`, `role="tab" aria-selected="true|false" aria-controls="painel"` em cada aba, `role="tabpanel"` no `main`. Altura mínima de 44 px no mobile (hoje 39 px). Esforço P.

**M9 · Tema do Power BI: paleta categórica com verde de estado e tons sem contraste.** `dataColors` inclui `#4F7A5A` (verde: pela marca, só estado "ok") e três tons abaixo de 3:1 sobre branco: `#C9A15B` 2,4, `#D6B677` 1,94 e `#8E98A3` 2,93 (WCAG 1.4.11). Falta `good`/`bad`/`neutral`, então "Var. vs ano anterior" fica sem cor de sentido. Correção:
```python
"dataColors": ["#B58324", "#2F5D7C", "#A4602F", "#56606B", "#7A5A1A", "#3E4A57", "#7A8D9C", "#8A6214"],
"good": "#2E6B4E", "bad": "#A3392B", "neutral": "#56606B",
"maximum": "#B58324", "center": "#F4EAD3", "minimum": "#FFFFFF",
```
(`#7A5A1A` é o ouro escurecido para a série 5. Medido sobre branco, todos ficam ≥ 3:1: o menor é o próprio `#B58324`, com 3,37, e `#7A8D9C` fica em 3,43. Os tons próximos de ouro (`#B58324`, `#8A6214`, `#7A5A1A`) não devem ficar lado a lado na mesma série.) As fontes Segoe UI ficam: o Power BI Service só renderiza a lista de fontes dele, e a Bricolage não está nela. Isso é um desvio aceito e deve ser registrado no `BRAND.md`. Esforço P.

**M10 · Streamlit: rosca para 5 regiões iguais e KPI sem comparação.** A skill classifica pizza/rosca com acessibilidade grau C e "evitar como gráfico principal". Com fatias de 20%, a comparação some. `st.metric` sem `delta`, enquanto o Power BI de entrega compara com o ano anterior. Correção: trocar a rosca por barras horizontais ordenadas com o valor e o % do total, e passar `delta=` com a variação contra o mesmo período do ano anterior (mesma regra do `relatorio_powerbi`, ADR 0011). Esforço M.

**M11 · Portal: carregamento sem sinal em login, grill, lista e prévia do painel.** O botão "entrar" e o "confirmar respostas" não mudam de texto nem se desabilitam, e um duplo clique manda duas vezes. A prévia do painel aparece em branco até o `srcdoc` chegar. Correção: padrão único `ocupado(botao, "entrando…")`, que desabilita, troca o texto, põe `aria-busy` e restaura no `finally`. Esforço P.

**M12 · Prévia do painel no portal com altura fixa de 520 px.** Corta o painel (o gráfico de linha some pela metade na captura 08). Correção: o iframe é da mesma origem (sem `sandbox`), então `onload = () => (ifr.style.height = ifr.contentDocument.documentElement.scrollHeight + "px")`. No site (iframe com `sandbox`), mandar a altura por `postMessage` a partir do HTML do painel, ou usar `height: min(80vh, 900px)`. Esforço P.

### 3.4 Baixos

| # | Tela | Problema | Correção | Esforço |
|---|---|---|---|---|
| B1 | Portal | Checkbox e rádio no azul padrão do navegador | `input[type=checkbox], input[type=radio] { accent-color: var(--ouro) }` em `marca.css` | P |
| B2 | Portal | `favicon.ico` 404 (Boas práticas 96) e sem `meta description` (SEO 90) | `<link rel="icon" type="image/svg+xml" href="/site/marca/simbolo-cotejo-claro.svg">` + description | P |
| B3 | Portal | "remover" visual sem confirmação (a demanda ganha versão nova) | mesmo padrão de duplo clique do "desligar" do BI: "confirmar: remover v3" | P |
| B4 | Portal | `alert()` nos erros de download | escrever no `#bi-msg`/`#p-msg` mais próximo (`role="status"`) | P |
| B5 | Portal | Status "grill" para quem demanda (jargão interno) | `NOMES.grill = "perguntas pendentes"`; manter "grill" só no rastro | P |
| B6 | Portal, conta | Mensagem do BI começa em minúscula e fala em "Postgres (produção)" | "A conexão direta do BI fica disponível no plano com banco na nuvem. Enquanto isso, exporte em CSV ou Parquet." | P |
| B7 | Portal | CSS morto do logo antigo (`.logo i b`, Estratos) | apagar | P |
| B8 | Site | Abaixo de 560 px o menu some inteiro (só fica "falar com a gente") | manter "testar agora" visível no mobile; os outros vão para o rodapé | P |
| B9 | Site | `.copiar` (25 px de altura) e o link "usar a planilha de exemplo" (19 px) abaixo de 44 px | `min-height: 44px; padding-block: 10px` (o link ganha `padding-block: 12px` sem mudar o visual) | P |
| B10 | Site | `scrollIntoView({behavior:"smooth"})` ignora `prefers-reduced-motion` | checar `matchMedia` como em A4 | P |
| B11 | Site | `<title>Lastro</title>` genérico | "Lastro · análise de dados conferida em duas camadas" | P |
| B12 | Site | Zona de arrastar sem texto que diga que dá para arrastar | "Arraste a planilha aqui ou escolha o arquivo" no `label` | P |
| B13 | Streamlit | `page_icon="📊"` (emoji, fora da marca) | `page_icon="site/marca/simbolo-cotejo-claro.svg"` (aceita caminho de imagem) | P |
| B14 | Painel HTML | Valores sem unidade (o R$ some no painel, mas aparece no site) | quando a medida for de valor (`valor_*`, `preco*`), prefixo "R$" no KPI e no rótulo do eixo | P |
| B15 | Painel HTML | Barras e tabela repetem o mesmo dado; sem "% do total" | ranking com coluna de % do total; a tabela vira o detalhe com todas as colunas (seção 4) | M |

## 4. Proposta de layout dos dashboards

Mesmo padrão do relatório de entrega do Power BI (`relatorio_powerbi.projeto`): **filtros no topo → cartões de KPI com comparação → gráfico principal → ranking → tabela de detalhe**, com as mesmas medidas (total da medida, nº de registros, média por registro, var. vs ano anterior) e a mesma regra: só soma, contagem e média, comparação com o mesmo período do ano anterior (ADR 0011). Assim o cliente vê a mesma tela no HTML, no Streamlit e no Power BI, e o detalhe confere com os cartões.

### 4.1 Estrutura (1440 px)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Título da pergunta                                     [demanda 1 · v1 · ✓]  │
│ origem: gold aprovado · gerado 26/11 00:55 (Brasília) · revisor: rui         │
├──────────────────────────────────────────────────────────────────────────────┤
│ [Empresa ▾ todas]  [Região ▾ todas]  [Ano ▾ 2026]           limpar filtros   │  filtros (sticky)
├───────────────┬───────────────┬───────────────┬──────────────────────────────┤
│ VALOR VENDIDO │ REGISTROS     │ MÉDIA/REG.    │ VS ANO ANTERIOR              │  4 cartões
│ R$ 14,03 mi   │ 197           │ R$ 71,2 mil   │ +8,4 %  ▲ (verde = estado)   │
│ ▲ 8,4 % a.a.  │ ▲ 12          │ ▼ 3,1 %       │ base: R$ 12,94 mi            │
├───────────────┴───────────────┴───────────────┼──────────────────────────────┤
│ Valor vendido por mês                         │ Ranking por vendedor (top 10)│
│ ── 2026 (ouro)   - - 2025 (quieta, tracejada) │ Eva Martins ████████ 18,3 %  │
│ eixo Y com 3 rótulos · último mês tracejado   │ Ana Souza   ███████  15,9 %  │
│ <details> ver os números                      │ …           "outros" no fim  │
│                         (8 colunas)           │                (4 colunas)   │
├───────────────────────────────────────────────┴──────────────────────────────┤
│ Detalhe para conferência   [buscar…]                              baixar CSV │
│ vendedor ▲▼ │ empresa │ região │ valor vendido │ registros │ % do total       │
│ … linhas ordenáveis, cabeçalho fixo, linha de TOTAL = cartões ...            │
└──────────────────────────────────────────────────────────────────────────────┘
```

Em 375 px, tudo vira uma coluna: os filtros ficam num `<details>` "filtros (2 ativos)", os cartões em grade 2×2, o gráfico ocupa a largura toda com altura de 200 px, o ranking mostra o top 5 com "ver todos", e a tabela rola dentro do próprio bloco (`overflow-x: auto`), nunca na página.

### 4.2 HTML do painel (`html_painel`): CSS proposto, só com tokens

```css
main { max-width: 1240px }
.filtros { position: sticky; top: 0; z-index: 1; display: flex; flex-wrap: wrap; gap: 8px; padding: 10px 0;
           background: var(--chao); border-bottom: 1px solid var(--linha) }
.filtros select { min-height: 44px; padding: 0 12px; border-radius: 8px; background: var(--sup); color: var(--tinta);
                  border: 1px solid color-mix(in srgb, var(--quieta) 60%, var(--linha)) }
.grade { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 12px }
.cartao { grid-column: span 3 }  .principal { grid-column: span 8 }  .ranking { grid-column: span 4 }  .detalhe { grid-column: 1 / -1 }
.cartao .rot { font: 500 11px var(--f-dado); text-transform: uppercase; letter-spacing: .08em; color: var(--quieta) }
.cartao b { font: 700 30px var(--f-disp); font-variant-numeric: tabular-nums }
.delta { font: 500 12px var(--f-dado) } .delta.sobe { color: var(--ok) } .delta.desce { color: var(--erro) }  /* sempre com ▲/▼ e o número: nunca só a cor */
.detalhe thead th { position: sticky; top: 0; background: var(--sup) }
.detalhe tfoot td { font-weight: 600; border-top: 2px solid var(--tinta) }
@media (max-width: 900px) { .cartao { grid-column: span 6 } .principal, .ranking { grid-column: 1 / -1 } }
```

Dados e filtros num HTML estático: o `dados()` passa a devolver um cubo pequeno, agregado por (filtros × eixo × ano_mes), embutido como `<script type="application/json" id="cubo">`, com ~40 linhas de JS sem biblioteca para refiltrar. O limite de tamanho é o mesmo `LIMIT 50` por eixo de hoje. Sem filtro aplicado, o HTML mostra os números já desenhados pelo Python, então funciona sem JS e na prévia com `sandbox`.

Mudanças na especificação (`spec`), sem quebrar ids estáveis: `"filtros": ["company", "projeto_regiao", "ano"]` (opcional; o padrão vem do mesmo critério de `relatorio_powerbi.faixa_de_filtros`), o tipo `kpi` ganha `"comparar": "ano_anterior"` quando há `data`, e `barras` passa a ser desenhado como ranking (top 10 + "outros" + % do total). O `para_visitante` segue o mesmo esqueleto, com um selo fixo no topo: "demonstração · conferência automática · sem revisão humana".

### 4.3 Streamlit (`lastro/rapido/app.py`)

```python
st.title("Lastro · relatórios rápidos")
st.caption("KPIs gerais por empresa, setor, região/UF e mês. O detalhe por cliente está nos relatórios do Power BI.")
with st.container(border=True):                       # 1. filtros no topo
    f = st.columns([2] + [1] * len(filtros))
    tabela = f[0].selectbox("Relatório", list(cat), format_func=lambda t: cat[t]["assunto"])
    escolhas = {d: c.multiselect(n.nome(d).capitalize(), valores(d), placeholder="todas") for c, d in zip(f[1:], filtros)}
k = st.columns(4)                                    # 2. KPIs com comparação (mesmas medidas do Power BI)
k[0].metric(f"Total de {n.nome(medida)}", br(atual), delta=f"{var:+.1%}".replace(".", ","), border=True)
k[1].metric("Registros", br(regs, 0), delta=br(regs - regs_ant, 0), border=True)
k[2].metric("Média por registro", br(atual / regs), border=True)
k[3].metric("Mesmo período do ano anterior", br(anterior), border=True)
g, r = st.columns([2, 1])                            # 3. gráfico principal + 4. ranking
g.plotly_chart(linha_ano_atual_vs_anterior(df_mes), use_container_width=True)   # anterior em tracejado
r.plotly_chart(ranking_barras_horizontais(df_dim, top=10), use_container_width=True)  # ordenado, com % do total
st.dataframe(detalhe, use_container_width=True, hide_index=True,                # 5. detalhe para conferência
             column_config={medida: st.column_config.NumberColumn(format="%.2f")})
st.caption(f"Total do detalhe: {br(detalhe[medida].sum())}: confere com o primeiro cartão.")
```

Plotly com a marca, em uma função só:

```python
def marca(fig):
    return fig.update_layout(font_family="IBM Plex Sans", separators=",.", margin=dict(t=40, l=0, r=0, b=0),
                             yaxis_title=None, xaxis_title=None, legend_title=None,
                             hoverlabel=dict(font_family="IBM Plex Mono"))
```

A aba "Pergunte" mantém o fluxo e ganha o mesmo `marca(fig)`, com "Como calculei" aberto por padrão quando o plano veio da LLM (prova antes de promessa).

## 5. Ordem sugerida de correção

1. **Já** (P, sem copy nova): C1, C2, C3, A2, A5, A7, B1, B2, M8, M11, M12.
2. **Próximo ticket** (M): A3 + A4 (estados e mobile do portal), A6 (ordem da demanda aprovada), M1 + M2 (tokens e bordas), A8 + M10 (Streamlit na marca).
3. **Card próprio** (pede grill e copy aprovada): seção 4 (layout dos dashboards, com mudança na `spec`), M5 (como funciona + prova no site), M4 (imagens claras/escuras e WebP), M3 (fontes servidas pelo próprio servidor).

## 6. Capturas (`docs/ux/capturas/`)

| Arquivo | O que mostra |
|---|---|
| `01-site-375-claro-topo.png` | Hero em 375 px, tema claro |
| `02-site-1440-escuro-topo.png` | Hero em 1440 px, tema escuro (captura clara sobre fundo escuro, M4) |
| `03-site-375-demo-erro-aceite-e-rolagem.png` | Erro "marque a caixa de aceite" e o texto cortado pela rolagem horizontal (C1) |
| `04-site-375-demo-sucesso-painel.png` | Sucesso da demo: painel cortado no iframe e horários divergentes (A7) |
| `05-site-375-escuro-arquivo-invalido-aceito.png` | Arquivo inválido aceito, "0 linhas e 1 colunas" (A2) |
| `06-portal-375-login-senha-errada.png` | Senha errada vira "Sua sessão expirou" (C2) e credenciais de demo à vista (A5) |
| `07-portal-375-grill.png` | Grill em 375 px: lista acima do conteúdo e cabeçalho quebrado (A4) |
| `08-portal-1440-demanda-aprovada.png` | Demanda aprovada inteira: painel no meio da página e prévia cortada (A6, M12) |
| `09-portal-375-conta-bi.png` | Conta e BI em 375 px (B6) |
| `10-painel-html-1440-claro.png` | Painel HTML: terceira coluna vazia, KPI esticado, linha sem eixo (A1, M6) |
| `11-painel-html-375-escuro.png` | Painel HTML em 375 px, tema escuro (funciona; base da proposta mobile) |
| `12-streamlit-1440-escuro.png` | Streamlit no escuro: título invisível, vermelho padrão e "Choose options" (C3, A8) |

A subpasta `docs/ux/capturas/atenta/` não faz parte desta auditoria.
