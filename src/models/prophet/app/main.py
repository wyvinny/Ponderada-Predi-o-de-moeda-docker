import json
import os
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, HTTPException
from prophet.serialize import model_from_json

artifacts=Path(os.getenv("ARTIFACT_DIR","/artifacts"))
metadata=json.loads((artifacts/"prophet_usd_brl_metadata.json").read_text(encoding="utf-8"))
model=model_from_json((artifacts/"prophet_usd_brl.json").read_text(encoding="utf-8"))
validation=pd.read_csv(artifacts/"prophet_validation_walk_forward.csv")
positive=validation[validation.actual_direction==1]
metrics={"mae":metadata["validation_metrics"]["mae_prophet"],"direction_accuracy":metadata["validation_metrics"]["direction_accuracy_prophet"],"direction_recall_up":float((positive.prophet_direction==1).mean())}
app=FastAPI(title="Prophet model service",version="v1")
@app.get("/health")
def health(): return {"status":"ok","model":"prophet","version":"prophet-v1"}
@app.get("/v1/results")
def results(): return {"model":"prophet","version":"prophet-v1","model_cutoff":metadata["model_cutoff"],"metrics":metrics,"evaluation":metadata["evaluation_protocol"]}
@app.get("/v1/predictions")
def predictions():
    return {"model":"prophet","version":"prophet-v1","predictions":validation[["cutoff","target_date","actual","prophet_yhat"]].tail(20).to_dict(orient="records")}
@app.get("/v1/inference")
def inference(dataset: str):
    if Path(dataset).name != dataset: raise HTTPException(422,"nome de dataset inválido")
    window=pd.read_csv(Path("/data/dataInferencia")/dataset,parse_dates=["Date"])
    if window.empty or window.Close.isna().any(): raise HTTPException(422,"janela inválida")
    cutoff=window.Date.max(); dates=pd.bdate_range(cutoff+pd.offsets.BDay(1),periods=5)
    last=float(window.Close.iloc[-1]); forecast=float(model.predict(pd.DataFrame({"ds":dates})).yhat.iloc[-1])
    direction="alta" if forecast>last else "queda" if forecast<last else "estável"
    return {"model":"prophet","version":"prophet-v1","dataset":dataset,"model_cutoff":str(cutoff.date()),"last_close":last,"forecast_close":forecast,"direction":direction,"metrics":metrics,"calendar_note":"cinco dias úteis estimados; feriados não considerados"}
