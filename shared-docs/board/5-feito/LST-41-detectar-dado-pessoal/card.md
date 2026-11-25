---
chave: LST-41
jira: https://adelecrm.atlassian.net/browse/LST-41
secao: NUC
status: feito
especialista: engenheiro-de-dados
---

# Detectar dado pessoal (CPF, CNPJ, e-mail, telefone) no Explorador

**Plano:** `docs/planos/painel-gratis-no-site.md`, fatia 4.

## Critérios de aceite

- [x] O Explorador marca colunas com cara de CPF, CNPJ, e-mail ou telefone, pelo formato dos valores e não só pelo nome
- [x] No modo visitante essas colunas ficam fora do painel e o visitante é avisado
- [x] No produto, o aviso aparece no perfil da fonte e nada muda no resto
- [x] Testes com valores reais e falsos positivos comuns, como código de produto numérico

## Verificação

`uv run pytest -q` + os critérios acima.

## Evidência (25/11)

**`lastro/pessoal.py`:** detecta CPF, CNPJ, e-mail e telefone pelo **valor**, numa amostra de até 500 valores distintos por coluna.
- CPF e CNPJ só contam com dígitos verificadores válidos.
- Telefone exige DDD válido e o formato de celular (9 na frente) ou de fixo.
- A coluna é marcada só com **80% ou mais** dos valores batendo, e com pelo menos 2 valores.
- CPF lido como número, que perdeu o zero à esquerda, é completado antes da conta.

**Explorador:**
- Marca `coluna["pessoal"]`.
- Registra `dados_pessoais` no rastro da demanda, só com o nome da coluna e o tipo.
- **Troca a amostra da nota da Caixa** por "(dado pessoal: CPF)". Antes, 3 valores reais de cada coluna iam parar na nota da empresa.
- O resto do produto não muda: o teste roda a demanda inteira.

**Modo visitante:**
- As colunas pessoais saem das opções de valor e de categoria, e `para_visitante` recebe `excluir` para não cair nelas no plano B.
- A abertura devolve `avisos`. O site mostra "Dado pessoal. A coluna '…' parece ter CPF: ela ficou fora do painel", e a etiqueta "dado pessoal, fora do painel" aparece no lugar do papel da coluna.

**Testes:** `tests/test_pessoal.py`, 20 testes.
- **Detecta:** CPF formatado, só dígitos e numérico sem o zero; CNPJ; e-mail; telefone formatado e só dígitos.
- **Não acusa:** código de produto de 11 e de 14 dígitos, id sequencial, CEP, valores, datas, categorias, coluna metade CPF e metade código, valor único.
- **Visitante:** colunas `cliente_doc` (CPF, sem "cpf" no nome) e `contato` (e-mail) ficam fora, e nenhum CPF nem e-mail aparece no HTML do painel.
- **Exemplo:** sem falso alarme.
- **Produto:** aviso no rastro sem valor e nota sem CPF.

Suíte completa: **291 passed**.

**QA:** o aviso no site, a 375 px, sem rolagem horizontal e sem erro de JavaScript (`evidencias/aviso-375.png`).
