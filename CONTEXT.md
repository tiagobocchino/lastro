# CONTEXT · Lastro

Glossário. Um termo por linha; agentes e código usam estes nomes.

- **Lastro**: o produto. Escreve-se com inicial maiúscula em texto corrido e `lastro` no logotipo.
- **Tenant**: a empresa contratante. Tudo pertence a um tenant; ninguém lê outro.
- **Demandante**: quem faz a pergunta. Papel `demandante` (ou `admin`).
- **Revisor de negócio**: humano da camada 2 da auditoria. Papel `revisor` (ou `admin`).
- **Demanda**: uma pergunta e o ciclo dela: `grill` → `pronta` → `em_revisao` → `aprovada` | `reprovada`.
- **Grill**: as perguntas que o Orquestrador faz antes de construir. Cada pergunta tem uma sugestão padrão.
- **Decisão**: resposta de grill gravada na Caixa do tenant. As da fonte (data, chave, revisor) ficam em `decisoes/` e não voltam ao grill; as da demanda (medida, recorte) ficam em `decisoes/historico/`: a busca acha, mas o grill pergunta de novo.
- **Fonte primária**: dado do cliente conectado à plataforma. Só leitura.
- **Sandbox**: DuckDB da demanda, onde o pipeline escreve. Recebe cópia das fontes e depois é travado: só alcança a pasta da própria demanda (ADR 0007).
- **Staging**: pasta da demanda com o gold em Parquet, o `pipeline.py`, o notebook e o relatório.
- **Caixa de Ferramenta** (ou Caixa): acervo de notas buscado por índice. Escopos: global, tenant, demanda.
- **Nota**: um arquivo Markdown da Caixa, um assunto, com frontmatter. Tipos: playbook, metodo, erro-conhecido, trilha, fonte, decisao.
- **Playbook**: receita de arquitetura (ex.: planilha para star schema; medalhão AWS).
- **Trilha**: conjunto de playbooks de uma nuvem: AWS, Google, Microsoft.
- **Camada 1**: auditoria técnica automática. **Camada 2**: revisão de negócio humana com o notebook do Colab.
- **Plano**: contrato do tenant: `consulta`, `pipeline` ou `operacao`.
- **Liberdade**: ação que a política do tenant libera para um agente (`sandbox_temporario`, `gerar_pipeline`, `pesquisar_fora` …).
- **Bronze, Silver, Gold**: as camadas do pipeline: cópia da fonte, dado limpo e deduplicado, modelo dimensional (fato + dimensões).
