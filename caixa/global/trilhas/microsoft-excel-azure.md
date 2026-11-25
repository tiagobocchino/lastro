---
name: microsoft-excel-azure
description: "Trilha Microsoft: de Excel e SharePoint ao Azure SQL ou Fabric, com Power BI nativo"
type: trilha
tags: [microsoft, excel, sharepoint, azure, azure sql, fabric, data factory, power bi]
---

# Degraus

1. Excel ou SharePoint como fonte, lidos com permissão somente leitura.
2. Warehouse: Azure SQL (free tier) ou Fabric com camadas bronze, silver e gold.
3. Orquestração: Data Factory ou script Python agendado.
4. Consumo: Power BI nativo; auditoria no Colab.

# Situação

Playbook pronto: `global:playbooks/microsoft-azure-sql-power-bi.md`. O Engenheiro gera o pipeline desta trilha em cada demanda (`trilhas/` da pasta da demanda), conferido por ida e volta contra o sandbox. Falta a primeira execução numa conta real do cliente.
