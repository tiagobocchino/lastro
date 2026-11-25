---
chave: LST-42
jira: https://adelecrm.atlassian.net/browse/LST-42
secao: OPS
status: feito
especialista: engenheiro-backend
---

# Limites e anti-abuso da demonstração (tamanho, tempo, fila e limite por IP)

**Plano:** `docs/planos/painel-gratis-no-site.md`, fatia 5. **Depende de:** LST-39.

## Critérios de aceite

- [x] Um arquivo, CSV ou Excel, de até 5 MB e 50 mil linhas; recusa com mensagem clara
- [x] Análise com no máximo 60 segundos
- [x] Fila de 1 por vez (Render gratuito, 512 MB); quem chega vê "você é o próximo"
- [x] Limite por IP: 5 análises por hora e 20 por dia, guardado só em memória
- [x] Turnstile fica fora por ora: só entra se houver abuso (decisão do grill do LST-37)

## Verificação

`uv run pytest -q` + os critérios acima.

## Evidência (25/11)

**`lastro/demo.py`:**
- **Tamanho:** até 5 MB e CSV ou Excel (já vinham do LST-39), e agora até **50 mil linhas**, conferido logo depois do perfil. A recusa apaga tudo na hora.
- **Prazo de 60 s:** a análise roda numa thread com prazo. Ao estourar, o visitante recebe 504 com a explicação. A sessão é apagada assim que a análise termina, inclusive a que nasce depois do prazo na leitura.
- **Fila de 1 por vez:** semáforo único. Quem chega espera até 20 s; se não abrir vaga, recebe 503 com `Retry-After: 10` e "tem gente analisando agora e você é o próximo". A vaga só volta quando a análise termina de verdade, então o servidor nunca roda duas ao mesmo tempo, nem depois de um prazo estourado. `GET /api/demo/fila` mostra quantos estão esperando.
- **Por IP:** 5 por hora e 20 por dia, com 429 e mensagem clara.
  - O IP vem do primeiro `X-Forwarded-For` (Render) e é guardado só como hash SHA-256 com sal aleatório do processo; o endereço nunca fica em memória.
  - Reiniciar o servidor zera a contagem, e entradas com mais de 24 h somem.
- **Turnstile:** fora, conforme o grill do LST-37.

**Testes** (`tests/test_demo.py`, mais 7):
- 50.001 linhas são recusadas sem deixar pasta;
- 5 análises por IP passam e a 6ª recebe 429, enquanto outro IP continua passando; o IP não aparece na memória;
- 20 por dia com relógio simulado, voltando no dia seguinte;
- fila ocupada dá "você é o próximo" e, liberada, entra; na API vira 503 com `Retry-After`;
- prazo estourado na análise e na leitura: a vaga só volta ao fim e nada sobra.

Suíte completa: **268 passed**.

**Em produção:** a demonstração continua desligada (`LASTRO_DEMO`) até a tela do site (LST-43) ficar pronta.
