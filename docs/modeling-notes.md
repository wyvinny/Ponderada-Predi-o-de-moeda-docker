# EDA, feature engineering e modelagem

O notebook EDA aplica SCAN somente ao desenvolvimento: verifica ordenação, cobertura, ausências, preços não positivos, retornos e segmentos anuais. O CSV bruto preserva cinco `Close` ausentes; a limpeza remove essas linhas apenas em cópias de preparação.

As features atuais são a série `Close` ordenada, índice temporal e sazonalidade. Prophet usa a data como `ds` e `Close` como `y`; SARIMA usa a série de `Close` e parâmetros sazonais semanais de cinco pregões. Nenhuma transformação é ajustada com dados posteriores ao corte. Os gráficos produzidos pela EDA devem ser exportados para `docs/images/` e referenciados aqui antes da entrega; não existiam imagens externas versionadas no estado inicial.
