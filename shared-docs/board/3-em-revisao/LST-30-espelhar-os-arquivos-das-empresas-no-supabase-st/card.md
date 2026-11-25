---
chave: LST-30
jira: https://adelecrm.atlassian.net/browse/LST-30
secao: OPS
status: em-qa
especialista: engenheiro-de-dados
---

# Espelhar os arquivos das empresas no Supabase Storage (disco do Render é efêmero)

**Por quê:** plano B (ADR 0009). No Render gratuito, o disco é apagado quando o serviço reinicia, publica de novo ou dorme. As fontes, o gold, os relatórios e a Caixa de cada empresa precisam sobreviver.

## Critérios de aceite

- [ ] Cada gravação na pasta da empresa vai para o bucket privado `tenants/<empresa>/...` do Supabase Storage
- [ ] Pasta ausente no disco é restaurada inteira do bucket antes do uso
- [ ] Teste: apagar o disco local e o ciclo da demanda continua com os mesmos dados
- [ ] Sem `LASTRO_STORAGE_URL`, nada muda (modo local e bucket montado da ADR 0007)
- [ ] Chave do Storage só em variável de ambiente; nunca no repositório, no rastro ou no laudo

## Verificação

`uv run pytest -q` + teste contra o Storage do projeto lastro-teste.

## Entrega (25/11, aguardando a ida e volta com a chave secreta no LST-22)

**Código:**
- `lastro/espelho.py` traz a pasta da empresa do bucket quando ela não está no disco e envia só o que mudou, comparando com o manifesto.
- Ele é ligado na `Plataforma` (restaura ao abrir), na API (sincroniza ao fim de cada requisição) e nas cargas (restaura e sincroniza).
- Sem `LASTRO_STORAGE_URL`, nada muda.

**Testes** (`tests/test_espelho.py`, Storage falso que imita a API):
- Só os arquivos alterados sobem; temporários e `.duckdb` ficam fora.
- Com o disco apagado, a demanda e o relatório voltam iguais, as decisões do grill voltam (a segunda demanda pergunta só 2 coisas) e uma nova demanda roda.
- Upload pela API vai para o bucket.
- A chave não aparece na resposta nem no banco.
- Rede fora vira aviso na carga, sem derrubar o laço das outras empresas.

**Achados:**
- A chave secreta nova vai só no `apikey` (`docs/memory/supabase-chave-secreta-no-apikey.md`).
- Erro de rede crua derrubaria o laço das cargas; corrigido.

**Supabase real (`lastro-teste`):**
- Bucket `tenants` privado, com limite de 50 MB por arquivo.
- Com a chave pública: gravar = 400, listar = `[]`. Com chave secreta falsa: 400.

**Suíte:** 201 passed com Postgres.

**Falta:** `python scripts/conferir_espelho.py` com a chave secreta real, no shell do Render (LST-22).
