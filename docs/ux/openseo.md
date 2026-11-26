# OpenSEO: o que é e como entra nas tarefas de SEO do Lastro

**Card:** LST-55 · **Fonte:** README e docs do repositório `every-app/open-seo` (lidos em 26/11/2026). As páginas de preço e de MCP em openseo.so não abriram nesta sessão; o que depende delas está marcado como "a confirmar".

## O que é

OpenSEO é uma alternativa de código aberto ao Semrush e ao Ahrefs, com licença MIT. Em vez de assinatura, você paga por uso com a sua própria chave da DataForSEO.

| Módulo | Serve para |
|---|---|
| Keyword research | Volume e dificuldade das palavras-chave (ex.: "dashboard para empresas") |
| Rank tracking | Posição do site no Google para as palavras escolhidas |
| Competitor insights e backlinks | Quem ranqueia e quem aponta para eles |
| Site audit | Rastreia o site (até 10 mil páginas) e aponta erros técnicos |
| AI visibility | Se o Lastro aparece nas respostas de IA |
| MCP + skills | Conecta ao Claude Code para pedir essas análises em conversa |

## Custos e hospedagem

- **Dados:** a DataForSEO é obrigatória para palavras-chave, posições e backlinks.
  - A conta nova ganha US$ 1 de teste e a recarga mínima é US$ 50.
  - O preço por consulta está em openseo.so/pricing, a confirmar.
  - A alternativa "treg" cobra o mesmo preço da DataForSEO, com saldo pré-pago.
- **Rodar por conta própria:**
  - Docker (`ghcr.io/every-app/open-seo-standalone`), com pelo menos 4 GB de memória;
  - ou a conta Cloudflare do cliente pela EveryApp, US$ 5/mês.
- **Versão hospedada:** openseo.so, com teste grátis. A assinatura é US$ 10/mês, e cada chamada à DataForSEO sai 28% mais cara.
- **Português e Brasil:** a documentação não fala do Brasil. A localização da busca vai direto para a DataForSEO, que atende google.com.br. Isso está a confirmar no primeiro uso.

## Como encaixa no Lastro (regra 5: grátis por padrão)

1. **Agora, sem custo:** o Yoast (texto) e o Lighthouse (técnico) já cobrem a auditoria do site. O OpenSEO não é necessário para publicar o site novo.
2. **Quando tiver domínio próprio:** a primeira compra que vale é medir o volume de "dashboard para empresas" e dos sinônimos com a recarga mínima da DataForSEO (US$ 50, paga pela lixum.labs). Esse volume confirma a frase-chave que o redator escolheu.
3. **Depois:** acompanhar a posição das 5 a 10 palavras do site e dos futuros artigos do blog.
   - Caminho mais barato: o OpenSEO em Docker, ligado ao Claude Code pelo MCP.
   - Antes de subir o Docker, a Cloudflare e o MCP, preciso do seu ok, porque são recursos novos.
4. **Não usar** o plano hospedado com 28% a mais enquanto o volume de consultas for pequeno.

O site audit do OpenSEO repete o que o Lighthouse e o teste do Playwright já fazem. Ele só passa a valer a pena quando o site tiver blog e várias páginas.
