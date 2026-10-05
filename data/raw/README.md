# Proveniência do CSV USD/BRL

- Arquivo: `usd_brl_daily.csv`
- Fonte: Yahoo Finance, endpoint de histórico diário `query2.finance.yahoo.com/v8/finance/chart/BRL=X`
- Ticker: `BRL=X` (reais por 1 dólar americano)
- Coleta: 2026-10-05, com exclusão da cotação parcial desse dia
- Intervalo no CSV: 2023-01-02 a 2026-10-02
- Registros: 980
- Fechamentos ausentes: 5, preservados no arquivo bruto para avaliação na EDA
- Reprodução: executar `notebooks/01_aquisicao_usd_brl.ipynb`; o limite final acompanha o dia atual em São Paulo
