# Painel grátis no site: o visitante sobe uma planilha e sai com um painel (plano · card LST-37)

**Status:** aprovado em 25/11. O Tiago aceitou as 8 recomendações da seção 9. Cards de execução: LST-38 a LST-44.

## 1. Objetivo

Fazer o visitante sentir o Lastro funcionando com os dados dele, em poucos minutos e sem cadastro, e sair com um motivo para contratar.

Medida de sucesso, contada por etapa e sem guardar dado:
- visitantes que **sobem** uma planilha;
- visitantes que **recebem** o painel;
- visitantes que **clicam para conversar** (WhatsApp ou formulário do LST-24).

## 2. A jornada

| # | O visitante | O Lastro | O que já existe |
| --- | --- | --- | --- |
| 1 | Sobe uma planilha (CSV ou Excel) no site, ou usa a de exemplo | Lê numa área temporária isolada, só leitura | conectores e sandbox travado (ADR 0007) |
| 2 | Vê o que o Lastro entendeu: "612 linhas, 9 colunas: 2 valores, 1 data, 5 categorias" | Explorador perfila as colunas | `Explorador` |
| 3 | Responde 3 a 4 perguntas curtas | Grill rápido: o que medir, por o quê quebrar, período, recorte. Sobre o **como mostrar**: número, ranking, evolução ou tabela | `Orquestrador.grill` + escolhas de visual novas |
| 4 | Recebe o painel na tela e pode baixar o HTML | Modelo → gold no sandbox → auditor (camada 1) → designer de painel | `Arquiteto`, `Engenheiro`, `Auditor`, `paineis.py` (LST-34) |
| 5 | Vê o **recibo de apagamento**: "às 15:42 apagamos 1 arquivo, 1 banco de trabalho e 9 tabelas" | Apaga tudo, confere que apagou e mostra | novo |
| 6 | Escolhe: "quero isso com os meus sistemas, atualizando sozinho" | WhatsApp com mensagem pronta ou formulário do LST-24, citando o tipo de painel (nunca os dados) | funil LST-24 |

O gancho comercial está no contraste:
- **no site:** uma planilha, uma vez, sem revisão humana;
- **no Lastro contratado:** os sistemas dele (Sienge, Omie, Bling…), atualizando todo dia, com as duas camadas de conferência e o painel no Power BI ou no Looker.

## 3. Arquitetura

- **Modo visitante** na API (Render), rotas públicas `/api/demo/*`, separado do portal:
  - **não** cria tenant nem usuário;
  - **não** usa o Postgres, nem o espelho do Storage, nem a Caixa da empresa.
- **Sessão de demonstração:**
  - uma pasta temporária `tmp/demo-<id aleatório>` no disco local do container, com tempo de vida máximo de 15 minutos;
  - um `RepoMemoria` (a mesma interface do `Repo`, só em memória) no lugar do banco.
- **Os agentes rodam como hoje,** com três chaves desligadas no modo visitante:
  - o Explorador não grava nota na Caixa;
  - o grill não memoriza decisões;
  - o LLM fica desligado, para que nenhum dado nem nome de coluna saia do servidor.
- **Fila de 1 por vez:** o Render gratuito tem 512 MB. Quem chega com outra análise rodando vê "você é o próximo".
- **Site:** uma seção nova no `site/index.html` ("teste com a sua planilha"), chamando a API. Onde o site fica no ar é a pergunta 5.

## 4. Apagamento: onde o dado pode ficar e como cada lugar é fechado

| Onde um dado do visitante poderia sobrar | Como fica fechado | Como se prova |
| --- | --- | --- |
| arquivo enviado e pasta da sessão | só na pasta `tmp/demo-<id>`, apagada ao entregar | teste varre o disco depois da sessão |
| banco de trabalho do DuckDB (sandbox) | já fica em pasta temporária; fechado e apagado junto | idem |
| notas do Explorador na Caixa | desligado no modo visitante | teste: a Caixa global e as das empresas não mudam |
| decisões do grill (`decisoes_conhecidas`) | desligado no modo visitante | idem |
| espelho no Supabase Storage (LST-30) | o modo visitante não tem espelho | teste com Storage falso: zero envios |
| Postgres (demandas, eventos, rastro) | `RepoMemoria`; nada vai para o banco | teste: contagem das tabelas igual antes e depois |
| logs do servidor | só etapa, tempo, tamanho e número de colunas; nunca valores nem nomes de coluna | teste captura o log e procura um valor da planilha |
| LLM externo | desligado no modo visitante | teste: nenhuma chamada HTTP de saída |
| sessão abandonada no meio | varredura a cada 5 minutos apaga o que passou de 15 minutos; ao reiniciar, o Render já apaga o disco | teste com relógio adiantado |
| painel entregue | gerado e mandado na resposta, depois apagado; só fica no navegador do visitante | — |

O **recibo de apagamento** lista o que foi apagado (arquivos, tabelas, bytes) e a hora. É um argumento de venda: "seus dados não ficam com a gente".

**Dado pessoal:** o Explorador passa a marcar colunas com cara de CPF, CNPJ, e-mail ou telefone.
- No modo visitante, essas colunas ficam fora do painel e o visitante é avisado.
- O site pede para não subir dado pessoal, com uma linha de termos e um aceite antes do envio.

## 5. A regra das duas camadas

"Nada sai sem duas camadas" vale para entregas a clientes. No site:
- a camada 1 (auditor automático) roda normalmente e o resultado dela aparece no painel;
- a camada 2 (revisor humano) não existe, porque o próprio visitante é quem confere os números dele.

O painel sai com a marca **"demonstração: conferência automática, sem revisão humana"**. A exceção vira ADR 0010, para não abrir precedente no produto.

## 6. Proteção contra abuso (Render gratuito)

- **Arquivo:** 1 por vez, CSV ou Excel, até 5 MB e 50 mil linhas.
- **Tempo:** a análise tem no máximo 60 segundos.
- **Limite por IP:** 5 análises por hora e 20 por dia, guardado só em memória.
- **Anti-robô** (pergunta 4): Cloudflare Turnstile é gratuito, mas pede uma conta Cloudflare.
- **Hospedagem:** o monitoramento (LST-26) já mantém o serviço acordado, então o visitante não espera o "acordar" de 1 minuto.

## 7. Métricas do funil

Eventos anônimos numa tabela `interno.demo_eventos`, sem IP e sem nada da planilha:
- etapa (`subiu`, `perfil`, `grill`, `painel`, `apagou`, `clicou_contato`);
- duração, tamanho em faixas, número de colunas, tipo de visual escolhido.

Eles entram no painel de operação (`lastro painel`) como um funil.

## 8. Fatias de entrega (cards LST-38 a LST-44, na ordem da tabela)

| Ordem | Card | Seção | Tamanho |
| --- | --- | --- | --- |
| 1 | ADR 0010 (demonstração sem revisão humana) + `RepoMemoria` + as três chaves do modo visitante nos agentes | NUC | M |
| 2 | API `/api/demo`: sessão temporária, perfil, grill rápido, painel, apagamento com recibo, varredura e testes de "nada sobra" | NUC | G |
| 3 | Grill de "como mostrar": as escolhas de visual viram a especificação do painel do LST-34 | NUC | P |
| 4 | Detecção de dado pessoal no Explorador | NUC | P |
| 5 | Limites e anti-abuso (tamanho, tempo, fila, limite por IP; Turnstile se aprovado) | OPS | M |
| 6 | Seção no site: envio, perguntas, painel, recibo e CTA, com copy pela skill `marca-e-copy`, QA em 375 e 1440 px e Lighthouse acima de 90 | MKT | G |
| 7 | Funil de eventos anônimos e integração com o LST-24 (WhatsApp ou formulário) | OPS | P |

O caminho mínimo para ir ao ar é 1 + 2 + 3 + 5 + 6. Os cards 4 e 7 podem entrar logo depois.

## 9. Perguntas para o grill (com a minha recomendação)

1. **Contato antes ou depois do painel?** Recomendo **depois e opcional**. Pedir antes reduz quem chega ao painel, e o painel é o argumento.
2. **Exceção das duas camadas no site** (seção 5)? Recomendo **aceitar**, com a marca de demonstração e a ADR.
3. **Limites:** 5 MB, 50 mil linhas, CSV e Excel, 1 arquivo? Recomendo **sim**. Várias planilhas juntas é argumento para o piloto pago.
4. **Anti-robô:** limite por IP agora e Turnstile só se houver abuso? Recomendo **sim**.
5. **Onde o site vai ao ar:** esperar o domínio (LST-23) ou servir já pelo Render (`/site`)? Recomendo **servir já pelo Render** e mudar quando o domínio existir.
6. **O que o visitante leva:** só o painel na tela e o HTML? Recomendo **sim**. O projeto do Power BI fica como gancho: "quer no seu Power BI, atualizando sozinho? fale com a gente".
7. **LLM no modo visitante:** desligado (nenhum dado sai)? Recomendo **desligado**.
8. **Planilha de exemplo** para quem não quer subir dado? Recomendo **sim**, com a de orçamentos.
