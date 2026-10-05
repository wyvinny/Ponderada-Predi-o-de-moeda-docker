# Evidências do terminal

Capturas do fluxo interativo executado pelo cliente PowerShell (`client/terminal.ps1`) com a plataforma em execução.

## Status e métricas

O status apresenta as versões ativas, cutoff, MAE, acurácia direcional, recall e os CSVs disponíveis para inferência e retreino.

![Status da plataforma](assets/terminal/01-status.png)

As métricas mostram o protocolo de avaliação informado por cada modelo.

![Métricas dos modelos](assets/terminal/02-metricas.png)

## Predições e inferência

As predições históricas exibem o valor observado e o valor previsto pelo Prophet em cada data de validação.

![Predições passadas](assets/terminal/03-predicoes-passadas.png)

A inferência solicitada para a janela escolhida retorna o valor estimado, a direção e as métricas do Prophet. A direção `ALTA` é destacada em verde.

![Inferência do Prophet](assets/terminal/04-inferencia-prophet.png)

O mesmo pedido retorna a estimativa do SARIMA. A direção `QUEDA` é destacada em vermelho.

![Inferência do SARIMA](assets/terminal/05-inferencia-sarima.png)

## Retreino simulado

O retreino treina candidatos Prophet e SARIMA no lote selecionado, compara-os aos campeões e mantém os artefatos ativos por ser uma simulação com somente três observações de avaliação.

![Resultado do retreino simulado](assets/terminal/06-retreino.png)
