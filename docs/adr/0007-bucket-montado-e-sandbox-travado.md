# ADR 0007: Arquivos das empresas num bucket montado como volume; sandbox travado

**Status:** aceito · 25/11/2026 · card LST-21

## Contexto

O disco do Cloud Run some a cada nova instância, e várias empresas dividem o mesmo servidor. As fontes, o gold, os relatórios, os notebooks e a Caixa de cada empresa precisam sobreviver. Uma consulta de agente também não pode alcançar arquivos de outra empresa, nem quando a trava de SQL (LST-17) for burlada.

## Decisão

- **Armazenamento:** a pasta de tenants é configurável (`LASTRO_TENANTS`). Em produção, ela é um bucket do Cloud Storage montado como volume no Cloud Run, com caminho `gs://<bucket>/tenants/<tenant>/...`. No desenvolvimento, é o disco (`LASTRO_HOME/tenants`). O código não conhece o Cloud Storage: continua lendo e gravando arquivos.
- **O que fica fora do bucket:**
  - o arquivo de trabalho do DuckDB, que vai para uma pasta temporária local e é apagado ao fechar a demanda, porque escrita aleatória em bucket montado é lenta e não tem trava de arquivo;
  - o banco da plataforma, que vai para o Supabase (LST-6);
  - o cache de vetores.
- **Sandbox:**
  1. As fontes são copiadas como tabelas para dentro do DuckDB.
  2. Em seguida o sandbox `travar()`: `allowed_directories` passa a ser só a pasta da própria demanda e `enable_external_access` fica desligado.
  3. Também ficam desligados a instalação e o carregamento automático de extensões, e `lock_configuration` impede mudar a configuração.
  4. O pipeline continua gravando o gold na pasta da demanda.

## Alternativas descartadas

- **Cliente do Cloud Storage no código** (upload e download explícitos): toca todos os pontos de leitura e escrita e duplica a lógica entre local e nuvem. Fica para quando houver volume que justifique.
- **Views sobre os arquivos de origem:** exigem acesso a disco na hora da consulta, o que impede desligar o acesso externo.

## Consequências

- Copiar a fonte custa memória e tempo proporcionais ao tamanho dela. Para os pilotos (até dezenas de MB) isso não pesa.
- Duas instâncias gravando o mesmo arquivo no bucket podem sobrescrever uma à outra (último a gravar vence). As notas de decisão são pequenas e raras. O número de instâncias é limitado a 2 (ADR 0006).
- O deploy (LST-22) precisa montar o volume e definir `LASTRO_TENANTS`, conforme `docs/infra/plano-nuvem-v1.md`.
