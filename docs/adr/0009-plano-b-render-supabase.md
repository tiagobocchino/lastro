# ADR 0009: Plano B da v1 sem cartão no Google: Render, Supabase Storage e GitHub Actions

**Status:** aceito · 25/11/2026 · substitui a parte "Cloud Run, Cloud Storage, Cloud Scheduler" da ADR 0006 enquanto o faturamento do Google estiver bloqueado

## Contexto

O cadastro do faturamento do Google Cloud falhou com `OR_BACR2_59` ("Não foi possível configurar sua conta"), e o Tiago preferiu seguir sem o Google. O Lastro precisa de quatro coisas: rodar a API, guardar os arquivos de cada empresa, disparar as cargas agendadas e servir o site e o portal.

Fatos conferidos em 25/11/2026 nas páginas oficiais (`docs/infra/fontes/`):

- **Render gratuito:**
  - o disco é efêmero: tudo some ao reiniciar, publicar de novo ou dormir;
  - o serviço dorme após 15 minutos sem tráfego e leva cerca de 1 minuto para acordar;
  - são 750 horas por mês (um serviço no ar o mês todo);
  - sem cartão cadastrado, estourar a banda suspende os serviços até o mês seguinte, sem cobrança;
  - os termos não proíbem uso comercial, mas a documentação diz para não usar instâncias gratuitas em produção.
- **Supabase gratuito:** 1 GB de arquivos, 500 MB de banco, 5 GB de saída de dados; o projeto pausa após 1 semana sem atividade.
- **GitHub Actions agendado:** intervalo mínimo de 5 minutos; atrasa nos horários de pico (o começo de cada hora); é desligado em repositório público após 60 dias sem atividade.
- **Firebase Hosting (Spark):** não pede cartão.

## Decisão

| Peça | ADR 0006 (Google) | Plano B |
| --- | --- | --- |
| API e agentes | Cloud Run | Render (serviço web gratuito, imagem do LST-20) |
| Arquivos das empresas | bucket montado (ADR 0007) | pasta local + espelho no Supabase Storage (LST-30) |
| Banco e cofre | Supabase | Supabase (sem mudança) |
| Cargas agendadas | Cloud Scheduler | **Supabase `pg_cron` + `pg_net`** (migração 0004); GitHub Actions como reserva |
| Site e portal | Firebase Hosting | Firebase Hosting (sem mudança) |

- **Espelho no Storage:** como o disco do Render some, a pasta de cada empresa é espelhada no bucket privado `tenants` do Supabase Storage. Cada gravação vai ao bucket logo depois de acontecer. Quando a pasta não existe no disco, ela é trazida inteira do bucket antes do uso. O código continua lendo e gravando arquivos, como na ADR 0007.
- **Agendamento:** fora do começo da hora (minuto 17), para fugir do pico. O mesmo job mantém o Supabase acordado.

## Consequências

- **Primeiro acesso lento:** quem chega depois de 15 minutos parados espera cerca de 1 minuto. O job de hora em hora não impede isso: o serviço dorme entre um disparo e outro.
- **Limite de arquivos de 1 GB** somando todas as empresas: suficiente para o piloto. O monitoramento (LST-26) precisa medir.
- **Recomendação do Render:** a documentação diz para não usar o plano gratuito em produção. A primeira receita paga o plano pago do Render (persistente, sem dormir) ou a volta ao Google; nos dois casos o espelho continua servindo.
- O Google volta a ser opção quando o faturamento for liberado: o guia `docs/infra/conta-google-cloud.md` e a ADR 0007 continuam válidos.

## Adendo (25/11): agendamento dentro do Supabase

O GitHub Actions recusou o disparo manual (HTTP 500 na API e na interface), e nenhuma execução agendada aconteceu, mesmo com o Actions liberado no repositório. As cargas passaram a ser disparadas pelo próprio Supabase (`supabase/migrations/0004_agendamento.sql`):

- **Agendamento:** dois jobs do `pg_cron`. No minuto 12, `interno.acordar_lastro()` faz GET em `/saude`, porque o Render dorme e leva cerca de 1 minuto para acordar. No minuto 17, `interno.disparar_cargas()` faz POST em `/tarefas/cargas`.
- **Segredos:** o endereço e o segredo da tarefa ficam no Vault (`lastro_url_api`, `lastro_tarefa_segredo`). As funções ficam no schema `interno`, fora da API pública, sem execução para `anon` e `authenticated`.
- **Reserva:** o workflow do GitHub continua no repositório. Se voltar a rodar, a tarefa é chamada duas vezes na hora, mas cada carga só roda uma vez por dia (`devida`).
- **Banco acordado:** a atividade de hora em hora mantém o banco movimentado.
