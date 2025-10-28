# Interpretador — Projeto **Smell Detect**

Este repositório contém o **interpretador do Projeto Smell Detect** — um microserviço responsável por executar a **smellDSL** (linguagem específica de domínio do projeto) para identificar *smells* definidos pelo próprio time. Ele integra-se a um **barramento de eventos**, promovendo análises assíncronas e baixo acoplamento.

## Propósito

Fornecer um **engine de interpretação** confiável, observável e extensível, capaz de:

- Ler regras escritas na **smellDSL** do projeto  
- Aplicar **limites/parametrizações** definidos pelo time  
- Avaliar **dados operacionais e de engenharia**  
- Produzir **diagnósticos padronizados e auditáveis**

## Visão geral

- **Interpretador da smellDSL do projeto**: compatível com o catálogo de regras versionado pelo time  
- **Execução determinística**: mesma entrada → mesmo diagnóstico  
- **Observabilidade**: geração de logs e metadados de avaliação  
- **Integração por eventos**: ingestão/entrega via tópicos/filas  
- **Microserviço independente**: escalável, *stateless* por padrão

## Contrato da API

### Entrada

- **`script`**: código da smellDSL do **Projeto Smell Detect** (regras a executar)  
- **`limits`**: limiares/parametrizações consumidas pelas regras  
- **`data`**: dados de contexto sobre os quais as regras serão aplicadas

> A combinação **`script + limits + data`** permite versionar critérios, ajustar sensibilidade sem *redeploy* e aplicar a detecção imediatamente.

### Saída

A API responde com um **JSON** contendo:

- **Logs de execução** (parsing, vínculo de variáveis, avaliação de expressões e eventuais erros)  
- **Diagnóstico por métrica/entidade** indicando se **está com smell ou não**

## Integração com o barramento de eventos

- **Entrada**: tópicos/filas de dados relevantes à avaliação  
- **Saída**: tópicos/filas de achados (ex.: *smells detected* / *smells resolved*)  
- **Contratos versionados**: schemas estáveis para interoperabilidade com outros serviços (dashboards, alertas, pipelines)

## Benefícios

- **Alinhado ao projeto**: interpreta exclusivamente a smellDSL do **Smell Detect**  
- **Autonomia do time**: regras como código, revisáveis e rastreáveis  
- **Padronização**: diagnósticos consistentes em múltiplos sistemas  
- **Escalabilidade**: processamento assíncrono e horizontalizável  
- **Transparência**: logs e resultados auditáveis ponta a ponta

---

> **Interpretador — Projeto Smell Detect**: o núcleo que transforma o conhecimento do time, descrito na smellDSL do projeto, em detecção automatizada de *smells* — clara, auditável e orientada a eventos.
