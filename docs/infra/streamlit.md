# Publicar os relatórios rápidos no Streamlit Community Cloud (LST-54)

Grátis. São uns 15 minutos, e só o Tiago pode fazer: a conta é pessoal e entra pelo GitHub.

**O que já está pronto no repositório:**

- `lastro/rapido/app.py`: o app.
- `lastro/rapido/requirements.txt`: as dependências. O Streamlit procura primeiro na pasta do app. Testado em 26/11 num ambiente limpo: o app sobe e responde.
- `.streamlit/config.toml`: o tema da marca. Fica na raiz do repositório e não tem segredo nenhum.

> As chaves deste app ficam **só nos Secrets do Streamlit**. O Render (servidor do Lastro) não precisa delas.

## 1. Pegar as duas chaves (antes de abrir o Streamlit)

Nenhuma das duas vai para o chat, para arquivo ou para card. Elas só entram no campo Secrets do passo 3.

1. **Chave de leitura do BI (`lst_…`):**
   - No portal do Lastro, entre como admin da gimi-teste, abra **conta** e vá em **Conectar ao BI**.
   - Use a chave que já está no seu Power BI, ou clique em **gerar chave** para criar outra.
   - Atenção: gerar uma chave nova invalida a anterior, e o Power BI deixa de atualizar até receber a nova.
2. **Chave do Gemini (grátis):**
   - Abra https://aistudio.google.com e entre com a sua conta Google.
   - Clique em **Get API key**, depois em **Create API key**, e escolha o projeto `lastro-515811` (ou crie outro).
   - Copie a chave. Ela começa com `AIza`.
   - No nível gratuito, o Google pode usar o que recebe. Por isso, o app manda ao Gemini só a pergunta e os nomes das colunas, nunca linhas de dados.

## 2. Criar a conta no Streamlit

1. Abra https://share.streamlit.io e clique em **Continue with GitHub**.
2. Entre com a conta do GitHub dona do `tiagobocchino/lastro`.
3. Na tela de autorização do GitHub, clique em **Authorize streamlit**.
   - Se o repositório for privado, o Streamlit pede também acesso aos repositórios privados. Aceite: ele só lê o código para publicar.
4. Complete o cadastro com nome e e-mail, se o Streamlit pedir.

## 3. Publicar o app

1. No painel do Streamlit, clique em **Create app** (canto superior direito) e depois em **Deploy a public app from GitHub**.
2. Preencha:

   | Campo | Valor |
   |---|---|
   | Repository | `tiagobocchino/lastro` |
   | Branch | `main` |
   | Main file path | `lastro/rapido/app.py` |
   | App URL | `lastro-relatorios` (ou outro nome livre) |

3. Abra **Advanced settings**:
   - **Python version:** escolha **3.12**.
   - **Secrets:** cole o bloco abaixo, trocando o que está entre aspas pelas suas chaves:

     ```toml
     LASTRO_API = "https://lastro-api-73zx.onrender.com"
     LASTRO_CHAVE = "lst_cole_aqui_a_chave_de_leitura"
     GOOGLE_API_KEY = "cole_aqui_a_chave_do_gemini"
     ```

   - Clique em **Save**.
4. Clique em **Deploy**. A primeira subida leva de 2 a 5 minutos, enquanto o Streamlit instala as dependências.

## 4. Conferir (os totais da gimi-teste)

- Na aba **Indicadores**, escolha o relatório de vendas e confira o total vendido: **211.290.267,16**.
- No relatório de funil, o total orçado deve ser **532.781.125,76**.
- No relatório de RH, devem aparecer **239** registros.
- Na aba **Pergunte**, escreva "vendas por região da obra por mês".
  - Deve sair um gráfico de linhas. Somando as regiões, Centro-Oeste dá 65.289.780,98.
  - Abra **Como calculei** para ver o SQL que gerou o gráfico.
- Mande o link do app para o Claude. Ele confere os totais e fecha o LST-54.

## Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| "Não consegui ler o BI (HTTPStatusError)" | Chave de leitura errada ou revogada. Confira o `LASTRO_CHAVE` em **Settings → Secrets**; a chave tem que começar com `lst_`. |
| O app fica uns 30 s carregando na primeira vez do dia | O Render (plano grátis) estava dormindo. É normal: a próxima abertura é rápida. |
| "O Gemini não respondeu agora; interpretei o pedido por palavras-chave" | O modelo do Google está fora do ar ou foi desligado. O app usa `gemini-flash-latest`, que sempre aponta para o Flash atual. Para fixar outro modelo, acrescente `GEMINI_MODELO = "nome-do-modelo"` nos Secrets e reinicie o app. |
| "Sem chave do Gemini: interpretação por palavras-chave" | Falta o `GOOGLE_API_KEY` nos Secrets. O app funciona sem ele, só que com uma interpretação mais simples. |
| O app "dorme" depois de alguns dias sem acesso | O Streamlit grátis hiberna apps parados. Basta abrir o link e clicar em **Yes, get this app back up!** |
| Quero que só a empresa veja | Em **Share**, deixe o app privado e convide os e-mails. A chave de leitura já limita o app aos dados de uma empresa. |
