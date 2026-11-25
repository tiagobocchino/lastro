# Criar a conta do Google Cloud para o Lastro (card LST-19)

Tempo: uns 20 minutos. Você precisa de um cartão de crédito e da conta Google que vai administrar o Lastro (sugestão: lixumlabs@gmail.com). Fatos conferidos em 25/11/2026 nas páginas oficiais salvas em `docs/infra/fontes/`.

## O que saber antes

- **A conta começa no "teste gratuito":** US$ 300 de crédito por 90 dias, mais a camada gratuita de cada serviço. Durante o teste, o Google não cobra nada.
- **O teste fecha sozinho em 90 dias, ou quando o crédito acaba.** Se a conta não virar paga, o projeto para e, depois de mais 30 dias, **tudo é apagado**. Por isso o passo 5 existe.
- **Orçamento comum só manda e-mail, não corta gasto.** Quem corta é o "teto de gasto" (spend cap). Hoje ele está disponível para o Cloud Run, que é justamente o serviço que pode escalar sem controle no Lastro. Se o teto for atingido, o Cloud Run pausa até o mês seguinte, sem apagar nada.
- **O que o Lastro usa, dentro do gratuito por mês:**

  | Serviço | Gratuito por mês |
  | --- | --- |
  | Cloud Run | 2 milhões de requisições |
  | Cloud Storage | 5 GB, só nas regiões dos EUA (por isso `us-central1`) |
  | Secret Manager | 6 versões de segredo |
  | Cloud Scheduler | 3 jobs por conta de faturamento |
  | Artifact Registry | 0,5 GB |
  | BigQuery | 1 TiB de consulta |

## Passo 1 · Criar a conta e o faturamento (no navegador)

1. Abra https://console.cloud.google.com com a conta Google escolhida.
2. Clique em **Ativar teste gratuito** (ou "Comece gratuitamente").
3. País: **Brasil**. Assim a moeda fica em reais e o orçamento sai em R$.
4. Tipo de conta: **Empresa**, se a lixum.labs tiver CNPJ; senão, **Pessoa física**.
5. Aceite os termos e cadastre o cartão. O Google faz uma verificação no cartão; o teste gratuito não cobra.

## Passo 2 · Abrir o Cloud Shell

No console, clique no ícone **>_** (Ativar o Cloud Shell), no canto superior direito. Abre um terminal no próprio navegador, já logado e com o `gcloud` instalado. Não precisa instalar nada no Windows.

## Passo 3 · Rodar o script do Lastro

No Cloud Shell, cole estes comandos, um de cada vez:

```bash
git clone https://github.com/tiagobocchino/lastro.git
```

```bash
bash lastro/scripts/gcp/criar_projeto_lastro.sh
```

O script faz quatro coisas:
- cria o projeto `lastro-prod-…` (o número no fim evita conflito de nome, que é único no mundo) e liga ao faturamento;
- habilita as 8 APIs (Cloud Run, Storage, Secret Manager, Scheduler, Artifact Registry e as do deploy pelo GitHub);
- cria o orçamento "Lastro - alerta de custo", de R$ 10, com e-mail em R$ 1, em R$ 10 e quando a previsão do mês passar de R$ 10;
- no fim, mostra o ID do projeto.

Se o Cloud Shell pedir **Autorizar**, autorize: é o próprio console usando a sua conta.

## Passo 4 · Pôr o teto de gasto no Cloud Run (no navegador)

1. Menu ☰ → **Faturamento** → **Orçamentos e alertas** → **Criar orçamento**.
2. Escolha o tipo **teto de gasto** (spend cap). O teto vale para um projeto e um serviço por vez.
3. Projeto: o `lastro-prod-…` do passo 3. Serviço: **Cloud Run**.
4. Valor: **R$ 10 por mês**. Salve.

Ao chegar em 100%, o Cloud Run para de aceitar uso novo até o mês seguinte, ou até você levantar o teto manualmente. Os avisos chegam por e-mail em 50%, 80% e 100%.

## Passo 5 · Antes do dia 90: virar conta paga

Ponha um lembrete na sua agenda para daqui a uns 80 dias. No console: **Faturamento** → **Fazer upgrade** (ou "Ativar conta completa"). O crédito que sobrar continua valendo até o dia 90, e os recursos seguem no ar. Com a conta paga, só se paga o que passar do gratuito, e o teto do passo 4 segura o Cloud Run.

## Passo 6 · Me mandar só o ID do projeto

Cole na conversa o ID mostrado no fim do script (ex.: `lastro-prod-261147`). **Não mande** senha, número do cartão, chave nem arquivo JSON de conta de serviço: o deploy (LST-22) usa a federação de identidade do GitHub, sem chave guardada.

## Se algo der errado

- **"Nenhuma conta de faturamento aberta":** o passo 1 não terminou. Confira em Faturamento.
- **"Billing account … is not open / cannot link":** a verificação do cartão ainda está pendente. Espere o e-mail do Google e rode o script de novo; ele não refaz o que já existe.
- **"Permission denied" no orçamento:** sua conta precisa ser administradora do faturamento, o que já acontece se foi ela que criou. Rode de novo depois de alguns minutos.
