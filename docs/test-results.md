# Resultados de testes

Os testes prioritários são de API com o Compose em execução: saúde agregada, ajuda, métricas dos dois modelos, rejeição de janela inválida, pedido de retreino e inferência agregada.

| Check executado | Resultado |
| --- | --- |
| `docker compose config` | PASS |
| Compilação Python dos novos serviços | PASS |
| Build e inicialização dos containers | PASS após fixar a tag do armazenamento e separar a rede `edge` da rede interna |
| `/health`, `/v1/help` e rejeição de janela inválida | PASS |
| Inferência agregada | FAIL na primeira execução: persistência JSON do resultado retornou `503`; correção aplicada, reexecução pendente |

O arquivo não declara a última correção como aprovada até que a suíte seja reexecutada.
