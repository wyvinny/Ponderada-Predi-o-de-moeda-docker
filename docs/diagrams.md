# Diagramas

## Arquitetura

```mermaid
flowchart LR
  T[terminal.ps1 / curl.exe] --> B[backend-api]
  B --> P[prophet-service]
  B --> S[sarima-service]
  B --> D[(PostgreSQL)]
  W[training-worker] --> D
  W --> R[data/dataRetreino]
  I[data/dataInferencia] --> P
  I --> S
  M[mlops-worker] --> L[Bronze / MinIO]
```

## Inferência

```mermaid
sequenceDiagram
  participant U as Terminal
  participant B as Backend
  participant P as Prophet
  participant S as SARIMA
  U->>B: lista CSVs de dataInferencia
  U->>B: POST inferência(dataset)
  B->>P: previsão 5 dias
  B->>S: previsão 5 dias
  P-->>B: versão, métricas, direção
  S-->>B: versão, métricas, direção
  B-->>U: resposta agregada
```

## Prophet

O serviço Prophet carrega o artefato versionado treinado no histórico cronológico. Para cada CSV escolhido, usa o último `Close` como referência e prevê o fechamento no fim dos cinco dias úteis seguintes. A direção é `alta`, `queda` ou `estável` comparando esse fechamento previsto à referência. As métricas retornadas vêm do backtesting do artefato, nunca do CSV de inferência.
