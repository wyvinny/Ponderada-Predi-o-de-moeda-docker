# Contratos HTTP

| Método e rota | Uso | Resposta principal |
| --- | --- | --- |
| `GET /health` | saúde agregada | estado dos modelos |
| `GET /v1/help` | comandos suportados | rotas e janela permitida |
| `GET /v1/models/results` | métricas do treino | versão, cutoff, MAE, acurácia e recall |
| `POST /v1/retraining-requests` | solicitar simulação | identificador e estado `queued` |
| `GET /v1/retraining-requests/{id}` | consultar pedido | estado e detalhes |
| `POST /v1/inferences` | inferir | ambos os modelos e métricas |

Os corpos de inferência e retreino são, respectivamente, `{ "dataset": "janela_2026_03_11.csv" }` e `{ "dataset": "lote_2026_01.csv" }`. O nome deve existir na pasta correspondente; outro valor retorna `422`.
