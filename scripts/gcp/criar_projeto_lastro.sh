#!/usr/bin/env bash
# Cria o projeto do Lastro no Google Cloud, liga ao faturamento, habilita as APIs e cria o orçamento com alertas.
# Card LST-19 · guia em docs/infra/conta-google-cloud.md
#
# Rode no Cloud Shell (console.cloud.google.com, ícone ">_" no topo), depois de criar a conta de faturamento:
#   bash criar_projeto_lastro.sh
# Pode rodar de novo sem estragar nada: o que já existe é mantido.
set -euo pipefail

PROJETO="${PROJETO:-lastro-prod-$(date +%y%m)$((RANDOM % 90 + 10))}"   # ID de projeto é único no mundo inteiro
REGIAO="us-central1"   # camada gratuita do Cloud Storage só vale em us-east1, us-west1 e us-central1
APIS=(
  run.googleapis.com               # API e agentes (Cloud Run)
  storage.googleapis.com           # arquivos das empresas (ADR 0007)
  secretmanager.googleapis.com     # segredos do Lastro
  cloudscheduler.googleapis.com    # cargas agendadas (LST-7)
  artifactregistry.googleapis.com  # imagem do container (LST-20)
  iamcredentials.googleapis.com    # deploy pelo GitHub sem chave guardada (LST-22)
  sts.googleapis.com
  billingbudgets.googleapis.com    # orçamento por linha de comando
)

passo() { printf '\n== %s\n' "$*"; }

passo "1/5 Conta de faturamento"
CONTA="$(gcloud billing accounts list --filter='open=true' --format='value(name)' | head -n1)"
if [[ -z "$CONTA" ]]; then
  echo "Nenhuma conta de faturamento aberta. Crie em console.cloud.google.com/billing (passo 1 do guia) e rode de novo."
  exit 1
fi
CONTA="${CONTA#billingAccounts/}"
MOEDA="$(gcloud billing accounts describe "$CONTA" --format='value(currencyCode)')"
echo "Conta: $CONTA (moeda $MOEDA)"

passo "2/5 Projeto $PROJETO"
if gcloud projects describe "$PROJETO" >/dev/null 2>&1; then
  echo "Já existe: mantido."
else
  gcloud projects create "$PROJETO" --name="Lastro produção"
fi
gcloud config set project "$PROJETO" >/dev/null
gcloud billing projects link "$PROJETO" --billing-account="$CONTA" >/dev/null
echo "Ligado ao faturamento."

passo "3/5 APIs"
gcloud services enable "${APIS[@]}"
echo "Habilitadas: ${#APIS[@]}"

passo "4/5 Orçamento com alertas (só avisa; o teto do Cloud Run é o passo 4 do guia, no console)"
if [[ "$MOEDA" == "BRL" ]]; then VALOR="10BRL"; else VALOR="2${MOEDA}"; echo "A conta está em $MOEDA: orçamento de 2 $MOEDA (perto de R\$ 10)."; fi
NUMERO="$(gcloud projects describe "$PROJETO" --format='value(projectNumber)')"
if gcloud billing budgets list --billing-account="$CONTA" --format='value(displayName)' | grep -qx "Lastro - alerta de custo"; then
  echo "Orçamento já existe: mantido."
else
  gcloud billing budgets create --billing-account="$CONTA" \
    --display-name="Lastro - alerta de custo" --budget-amount="$VALOR" \
    --filter-projects="projects/$NUMERO" \
    --threshold-rule=percent=0.10 \
    --threshold-rule=percent=1.00 \
    --threshold-rule=percent=1.00,basis=forecasted-spend
  echo "Alertas por e-mail em 10% (R\$ 1), 100% (R\$ 10) e na previsão de passar de 100%."
fi

passo "5/5 Pronto"
cat <<FIM
Projeto: $PROJETO   Região: $REGIAO
Mande para o Claude só o ID do projeto ($PROJETO). Nada de senha, cartão ou chave.
Falta no console: o teto de gasto do Cloud Run (passo 4 do guia) e, antes do dia 90, ativar a conta paga (passo 5).
FIM
