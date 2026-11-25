# ADR 0006: Infra da v1 em planos gratuitos do Google e do Supabase; Vercel fora da produção

**Status:** proposto · 25/11/2026 · aguarda aprovação do Tiago

## Contexto

Pedido: conectar à Vercel e usar ferramentas gratuitas do Google para sustentar a primeira versão e o atendimento. A política da Vercel restringe o plano Hobby a uso pessoal e não comercial; uso comercial exige Pro ou Enterprise ([fair use guidelines](https://vercel.com/docs/limits/fair-use-guidelines)). O site e o portal do Lastro são uso comercial.

## Decisão

- Site e portal: Firebase Hosting (Spark), com rewrite de `/api` para o Cloud Run.
- API e agentes: Cloud Run, escala a zero, máximo de 2 instâncias.
- Banco e login: Supabase Free (ADR 0004), com keepalive diário.
- Arquivos: Cloud Storage; segredos: Secret Manager; deploy: GitHub Actions com Workload Identity.
- Vercel: não usada em produção. Reavaliar com o plano Pro se surgir necessidade concreta (por exemplo, previews de PR do site com o time).

## Consequências

- Custo zero dentro dos limites, mas o Google exige conta de faturamento: orçamento com alerta é a primeira tarefa.
- Dados de clientes ficam em região dos EUA enquanto estivermos na camada gratuita (registrar na política de privacidade).
- Detalhes, limites com fontes e fases em `docs/infra/plano-nuvem-v1.md`.
