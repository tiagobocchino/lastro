# Marca · Lastro

## Ideia

**Lastro** é o que garante o valor de uma moeda. Aqui, é o que garante uma resposta: o rastro, as auditorias e o dado de origem. Frase-tese: **"Toda resposta com lastro."**

O símbolo é o **Cotejo**: duas camadas que se sobrepõem (a auditoria técnica e a revisão de negócio) e, na interseção, a área conferida em ouro. O logotipo é o símbolo + `lastro` em minúsculas (Bricolage Grotesque ExtraBold, -3%). Arquivos em `site/marca/`; conceitos alternativos (Estratos, Esquadro) no Figma "Lastro · Marca". Nome e símbolo decididos no ADR 0005.

## Cores

| Token | Claro | Escuro | Uso |
| --- | --- | --- | --- |
| `--chao` | #EEF1F3 | #0D1116 | fundo |
| `--sup` | #FFFFFF | #151B22 | superfícies |
| `--tinta` | #111820 | #E7ECF1 | texto |
| `--quieta` | #56606B | #98A3AE | texto secundário |
| `--linha` | #D6DCE2 | #26303A | bordas |
| `--ouro` | #B58324 | #E1B24F | acento único: ações principais, barras, foco |
| `--prata` | #8E98A3 | #AEB7C0 | símbolo |
| `--bronze` | #A4602F | #C98552 | símbolo |

Neutros puxados para o azul-grafite. O ouro é o único acento; verde, vermelho e âmbar são só estado (ok, erro, aviso). Tokens em `lastro/web/marca.css`.

## Tipografia

- **Bricolage Grotesque** (700): títulos e números grandes.
- **IBM Plex Sans**: texto.
- **IBM Plex Mono**: dados, rótulos, SQL, status.
- **Onde moram:** os arquivos `woff2` ficam em `site/fontes/` (licença OFL) e são servidos pelo próprio Lastro no site e no portal, sem Google Fonts.
- **Desvio aceito:** o Power BI usa Segoe UI. O Power BI Service só mostra as fontes da lista dele, e a Bricolage não está nela. A marca entra pelas cores do tema (`relatorio_powerbi.TEMA`).

## Voz

- Português do Brasil, frases curtas, termos que o analista usa (medida, chave, recorte, revisor).
- Prova antes de promessa: mostrar o número, a checagem, o rastro.
- Ações em minúsculas e no infinitivo: "abrir demanda", "rodar agentes", "aprovar entrega".
- Nunca prometer acerto sem auditoria; nunca dizer "IA mágica".

## Assinatura

Um produto lixum.labs (a confirmar no grill: ver pergunta sobre a titularidade do produto).
