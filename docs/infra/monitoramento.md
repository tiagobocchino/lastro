# Monitoramento de produção (card LST-26)

Tudo roda dentro do Supabase (`lastro-teste`), sem servidor extra e sem custo:

| O quê | Como | Onde |
| --- | --- | --- |
| API no ar | a cada 5 minutos, `interno.monitorar()` chama `/saude` pelo pg_net e colhe a resposta na rodada seguinte | job `lastro-monitor` (migração 0007) |
| Erros 5xx | a API grava requisições, 4xx, 5xx e latência por hora em `interno.metricas_api` | middleware `medir` em `lastro/api.py` |
| Limite gratuito | banco (500 MB) e Storage (1 GB) comparados com 80% | `interno.avaliar_alertas()` |
| E-mail | abrir e fechar um alerta mandam um e-mail pelo Resend | `interno.enviar_alerta()` |
| Keepalive | a verificação a cada 5 minutos passa pelo banco, então o Supabase não pausa | — |

Os alertas e os limites ficam em `interno.alertas` e `interno.limites`. Para mudar um limite, rode no SQL Editor `update interno.limites set valor = ... where nome = ...`. Não precisa de migração.

**Render gratuito:** a verificação a cada 5 minutos mantém o serviço sempre acordado, o que acaba com a espera de 1 minuto no primeiro acesso. Isso gasta cerca de 744 das 750 horas de instância que a conta tem por mês. Se um dia houver um segundo serviço gratuito na mesma conta, troque o job para `*/10` só em horário comercial, ou passe o serviço para o plano pago.

## Ligar o e-mail (uma vez, 5 minutos)

Sem isso, os alertas ficam só na tabela e no painel, com `interno.emails.enviado = false`.

1. Crie a conta gratuita em https://resend.com com o e-mail que vai receber os alertas.
2. Em **API Keys → Create API Key**, dê o nome `lastro-alertas`, permissão **Sending access** e copie o valor (`re_…`).
3. No Supabase, abra o projeto `lastro-teste` → **SQL Editor** e rode, colando os seus valores:
   ```sql
   select vault.create_secret('re_COLE_A_CHAVE', 'lastro_resend_chave');
   select vault.create_secret('SEU_EMAIL_DA_CONTA_RESEND', 'lastro_alerta_email');
   ```
   Os valores ficam cifrados no Vault. Não cole a chave na conversa nem no GitHub.
4. Teste: `select interno.enviar_alerta('[Lastro] teste', 'Se chegou, o alerta funciona.');`. O e-mail chega em menos de 1 minuto.

Sem domínio próprio verificado no Resend, o remetente é `onboarding@resend.dev` e só envia para o e-mail dono da conta. Para alertas, isso basta.

## Painel de operação em Python

O painel é um HTML estático, sem servidor e sem custo. Ele lê as views do schema `painel`.

1. Dê uma senha ao usuário só de leitura, uma vez. No SQL Editor:
   ```sql
   alter role painel_leitor login password 'UMA_SENHA_LONGA';
   ```
2. No seu computador, na pasta do repositório (PowerShell):
   ```powershell
   $env:LASTRO_PAINEL_URL = "postgresql://painel_leitor.dghpdlhztkoyfyqmyjbx:UMA_SENHA_LONGA@HOST_DO_SESSION_POOLER:5432/postgres"
   uv run --extra postgres lastro painel --saida painel-operacao.html
   ```
   O endereço do pooler aparece em **Connect → Session pooler**: troque o usuário `postgres` por `painel_leitor`. Depois abra o `painel-operacao.html` no navegador.

O painel mostra:
- disponibilidade, requisições, taxa de 5xx e latência dos últimos 7 dias;
- requisições e demandas por dia (30 dias);
- uso do plano gratuito;
- cargas agendadas;
- alertas.

## Conectar um BI (Power BI, Looker Studio ou outro)

Use o mesmo usuário `painel_leitor`, que só enxerga as views do schema `painel`:
- `requisicoes_dia`
- `disponibilidade_dia`
- `demandas_dia`
- `cargas`
- `uso_gratuito`
- `alertas`
- `demo_funil_dia`: funil da demonstração do site (subiram, painéis, clicaram, recusas, desistências), sem IP nem dado de visitante (LST-44)

Ele não grava nada e não lê senhas, segredos nem as tabelas internas.

| Campo | Valor |
| --- | --- |
| Servidor | o host do Session pooler (porta 5432) |
| Banco | `postgres` |
| Usuário | `painel_leitor.dghpdlhztkoyfyqmyjbx` |
| SSL | obrigatório |

- **Power BI Desktop** (gratuito): **Obter dados → Banco de dados PostgreSQL**.
- **Looker Studio:** conector **PostgreSQL**, com SSL ativado.

Para cortar o acesso: `alter role painel_leitor nologin;`.

As bases dos clientes ligadas ao BI de cada cliente são outro trabalho, com isolamento por empresa: card LST-33.
