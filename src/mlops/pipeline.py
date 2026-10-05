from pathlib import Path
import pandas as pd
raw=pd.read_csv(Path('/data/raw/usd_brl_daily.csv'),parse_dates=['Date'])
if raw.Date.duplicated().any() or not raw.Date.is_monotonic_increasing: raise ValueError('snapshot bruto inválido')
print({'status':'validated','raw_rows':len(raw),'missing_close':int(raw.Close.isna().sum())})
