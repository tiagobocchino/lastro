# Pôr o Lastro no ar no Render, sem cartão (plano B, ADR 0009 · card LST-22)

Tempo: uns 20 minutos, mais 5 a 10 minutos de build. Não pede cartão. O que você vai precisar:
- a conta do GitHub (`tiagobocchino`);
- o painel do Supabase aberto no projeto `lastro-teste`, que vira o banco da v1. Ele já tem as migrações 0001 a 0003 e o bucket privado `tenants`.

## Passo 1 · Conta no Render

Entre em https://render.com, clique em **Get Started** e depois em **GitHub**. Autorize o Render a ler o repositório `tiagobocchino/lastro`.

## Passo 2 · Separar os 4 valores no Supabase

Abra o projeto `lastro-teste` no painel do Supabase.

| Variável | Onde pegar |
| --- | --- |
| `LASTRO_BANCO_URL` | Botão **Connect** (no topo), aba **Transaction pooler** (porta 6543). Copie a URI e troque `[YOUR-PASSWORD]` pela senha do banco. Não lembra a senha? **Database → Settings → Reset database password**. Use o pooler: o Render não alcança o endereço direto do banco, que é só IPv6. |
| `LASTRO_STORAGE_URL` | `https://dghpdlhztkoyfyqmyjbx.supabase.co` |
| `LASTRO_STORAGE_CHAVE` | **Project Settings → API Keys → Secret keys**. Crie uma chave chamada `lastro-render` e copie o valor (`sb_secret_…`). |
| `LASTRO_URL_PUBLICA` | o endereço que o Render der ao serviço. Se o nome `lastro-api` já tiver dono, ele ganha sufixo: o do Lastro é `https://lastro-api-73zx.onrender.com`. Troque em Environment se preciso. |

Esses valores são senhas. Cole só no Render: nada de mandar na conversa, nem no GitHub.

## Passo 3 · Criar o serviço pelo Blueprint

1. No Render: **New +** → **Blueprint** → escolha `tiagobocchino/lastro` (branch `main`).
2. O Render lê o `render.yaml` e mostra o serviço `lastro-api` (Docker, plano Free, Virginia).
3. Ele pede os 4 valores do passo 2. Cole e clique em **Apply**.
4. `LASTRO_SEGREDO` e `LASTRO_TAREFA_SEGREDO`, o Render gera sozinho.
5. Espere o build terminar (o status fica **Live**). Abra `https://lastro-api-73zx.onrender.com/saude`: tem que aparecer `{"estado":"ok", … "banco":"ok"}`.

## Passo 4 · Ligar as cargas agendadas no GitHub

1. No Render: serviço `lastro-api` → **Environment** → copie o valor de `LASTRO_TAREFA_SEGREDO`.
2. No GitHub: repositório `lastro` → **Settings → Secrets and variables → Actions → New repository secret**. Crie dois:
   - `LASTRO_URL_API` = `https://lastro-api-73zx.onrender.com`
   - `LASTRO_TAREFA_SEGREDO` = o valor copiado
3. Aba **Actions** → **cargas agendadas** → **Run workflow**. Tem que terminar verde e mostrar `{"executadas":…}`.

Depois disso, ele roda sozinho no minuto 17 de cada hora.

## Passo 5 · Me avisar

Mande na conversa só o endereço do serviço (ex.: `https://lastro-api-73zx.onrender.com`). Eu confiro a saúde, crio a primeira empresa e o seu usuário admin direto no banco, e confiro que os arquivos chegam ao bucket.

## O que esperar do plano gratuito

- **Primeiro acesso lento:** depois de 15 minutos sem uso, o serviço dorme, e a primeira visita leva cerca de 1 minuto para acordar.
- **Disco:** o do Render some ao dormir. Os arquivos das empresas ficam no Supabase Storage (LST-30) e voltam sozinhos.
- **Plano pago:** a documentação do Render recomenda não usar o plano gratuito em produção. Para o piloto, serve; com o primeiro cliente pagante, vale o plano pago (sem dormir).
