import os
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, HTTPException
from statsmodels.tsa.statespace.sarimax import SARIMAX

series=pd.read_csv(Path(os.getenv("RAW_PATH","/data/raw/usd_brl_daily.csv")),parse_dates=["Date"])[["Date","Close"]].dropna().sort_values("Date").reset_index(drop=True)
validation_end=int(len(series)*.9); validation_start=int(len(series)*.8)
history=series.iloc[:validation_start]; target=series.iloc[validation_start:validation_end]
validation_model=SARIMAX(history.Close,order=(1,1,1),seasonal_order=(1,0,0,5),enforce_stationarity=False,enforce_invertibility=False).fit(disp=False)
predicted=validation_model.forecast(len(target)).to_numpy(); actual=target.Close.to_numpy(); up=actual>float(history.Close.iloc[-1]); pred_up=predicted>float(history.Close.iloc[-1])
metrics={"mae":float(abs(actual-predicted).mean()),"direction_accuracy":float((up==pred_up).mean()),"direction_recall_up":float(pred_up[up].mean()) if up.sum() else None}
active=series.iloc[:validation_end]
model=SARIMAX(active.Close,order=(1,1,1),seasonal_order=(1,0,0,5),enforce_stationarity=False,enforce_invertibility=False).fit(disp=False)
app=FastAPI(title="SARIMA model service",version="v1")
@app.get("/health")
def health(): return {"status":"ok","model":"sarima","version":"sarima-v1"}
@app.get("/v1/results")
def results(): return {"model":"sarima","version":"sarima-v1","model_cutoff":str(active.Date.iloc[-1].date()),"metrics":metrics,"evaluation":"holdout cronológico de 10%; backtesting completo é executado pelo training-worker"}
@app.get("/v1/predictions")
def predictions():
    return {"model":"sarima","version":"sarima-v1","note":"previsões históricas serão publicadas pelo backtesting do worker"}
@app.get("/v1/inference")
def inference(dataset: str):
    if Path(dataset).name != dataset: raise HTTPException(422,"nome de dataset inválido")
    window=pd.read_csv(Path("/data/dataInferencia")/dataset,parse_dates=["Date"])
    if window.empty or window.Close.isna().any(): raise HTTPException(422,"janela inválida")
    last=float(window.Close.iloc[-1]); forecast=float(model.forecast(5).iloc[-1]); direction="alta" if forecast>last else "queda" if forecast<last else "estável"
    return {"model":"sarima","version":"sarima-v1","dataset":dataset,"model_cutoff":str(window.Date.max().date()),"last_close":last,"forecast_close":forecast,"direction":direction,"metrics":metrics,"calendar_note":"cinco dias úteis estimados; feriados não considerados"}
