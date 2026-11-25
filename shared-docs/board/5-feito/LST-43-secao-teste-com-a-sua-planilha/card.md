---
chave: LST-43
jira: https://adelecrm.atlassian.net/browse/LST-43
secao: MKT
status: feito
especialista: engenheiro-frontend
---

# Seção "teste com a sua planilha" no site, servido pelo Render

**Plano:** `docs/planos/painel-gratis-no-site.md`, fatia 6. **Depende de:** LST-39, LST-40, LST-42.

## Critérios de aceite

- [x] O site passa a ser servido pelo Render até existir domínio (LST-23)
- [x] Seção nova com: envio ou planilha de exemplo, aceite dos termos e aviso de não subir dado pessoal; perguntas, painel na tela, download do HTML e recibo de apagamento; chamada para conversar (WhatsApp ou formulário do LST-24), com o Power BI como gancho
- [x] Contato depois do painel e opcional
- [x] Copy pela skill `marca-e-copy`
- [x] QA em 375 px e 1440 px e Lighthouse acima de 90

## Verificação

`uv run pytest -q` + os critérios acima.

## Evidência (25/11)

**No ar:** https://lastro-api-73zx.onrender.com/site/ (seção "teste com a sua planilha", também em `#teste`).
- O botão "testar com os meus dados" do topo e o link "testar agora" levam até ela.
- `LASTRO_DEMO=1` veio pelo `render.yaml`.

**O que o visitante vê:**
1. Envio de CSV ou Excel (ou arrastar o arquivo), ou "usar a planilha de exemplo", com aceite obrigatório: não enviar dado pessoal e ciência de que é uma demonstração apagada ao final.
2. "O que o Lastro entendeu": linhas, colunas e o papel de cada uma (valor, data, categoria), com as 4 perguntas já preenchidas com a sugestão.
3. O painel numa moldura isolada (`sandbox`, sem script):
   - selo "demonstração · conferência automática aprovada · sem revisão humana";
   - botão para baixar o HTML;
   - **recibo** ("Apagamos tudo às …: N arquivos · N tabelas · KB · conferido");
   - convite: o painel no Lastro contratado liga nos sistemas, atualiza todo dia, tem revisão humana e abre no Power BI ou no Looker. Botão de WhatsApp com o tipo de painel na mensagem, nunca os dados.

O contato só aparece **depois** do painel e é opcional.

**Robustez:**
- Fila cheia: espera o `Retry-After` e tenta de novo sozinho, com contagem.
- "Desistir e apagar" e sair da página no meio (`sendBeacon`) apagam na hora.
- No modo demonstração, o painel diz "conferência automática, sem revisão humana", e não "gold aprovado".

**Copy:** segue a voz do `BRAND.md` do Lastro (frases curtas, prova antes de promessa, ações em minúsculas no infinitivo, sem "IA mágica"). A skill `marca-e-copy` citada no card é da lixum.labs.

**Verificação:**
- **QA local (Playwright):**
  - recusa sem aceite;
  - exemplo em 1440 e 375 (tema claro) dá 14.030.477,92, com recibo conferido;
  - CSV próprio em 375 (tema escuro) dá receita 730;
  - desistir gera recibo;
  - sem rolagem horizontal e sem erro de JavaScript.
- **Lighthouse** (local): celular 99/100/100/100 e desktop 100/100/100/100 (desempenho, acessibilidade, boas práticas, SEO), depois de GZip, meta description e favicon.
- **Produção** (Render + exemplo):
  - perfil com 612 linhas e 9 colunas, 4 perguntas;
  - painel com 14.030.477,92 e "sem revisão humana";
  - auditoria aprovada com 15 checagens;
  - recibo de 22 arquivos, 8 tabelas e 105 KB, `conferido: true`;
  - fila zerada depois.
- **Testes:** 270 passed, mais o teste do contexto do Docker.

**Incidente no deploy (resolvido):** o primeiro deploy falhou no Render ("failed to compute cache key: not found"), porque `site/` estava no `.dockerignore`.
- Correção: commit `48b7cc8`.
- Teste novo: `test_dockerfile_so_copia_o_que_esta_no_contexto`.
- Nota: `docs/memory/dockerignore-e-copy.md`.
- A versão anterior ficou no ar durante a falha.

**Conhecimento durável:** `docs/memory/dockerignore-e-copy.md`.
