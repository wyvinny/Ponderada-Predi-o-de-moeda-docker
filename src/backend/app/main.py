import json
import os
import uuid
import httpx
import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="USD/BRL Gateway", version="1.0.0")
DATA_ROOT = os.getenv("DATA_ROOT", "/data")
PROPHET_URL = os.getenv("PROPHET_URL", "http://prophet-service:8081")
SARIMA_URL = os.getenv("SARIMA_URL", "http://sarima-service:8082")
DATABASE_URL = os.getenv("DATABASE_URL", "")

class DatasetRequest(BaseModel):
    dataset: str

def call(url, path):
    try:
        response = httpx.get(url + path, timeout=30)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(503, "serviço de modelo indisponível") from exc

def execute(query, params):
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
    except psycopg.Error as exc:
        raise HTTPException(503, "banco de metadados indisponível") from exc

def datasets(kind: str):
    folders={"retraining":"dataRetreino","inference":"dataInferencia"}
    if kind not in folders: raise HTTPException(422,"kind deve ser retraining ou inference")
    folder=os.path.join(DATA_ROOT,folders[kind])
    return sorted(name for name in os.listdir(folder) if name.endswith(".csv"))

def checked_dataset(kind: str, name: str):
    if name not in datasets(kind): raise HTTPException(422,"dataset inexistente ou não permitido")
    return name

@app.get("/health")
def health():
    return {"status":"ok", "services":{"prophet":call(PROPHET_URL,"/health"), "sarima":call(SARIMA_URL,"/health")}}

@app.get("/v1/help")
def help_contract():
    return {"message":"Use client/terminal.ps1 ou curl.exe.","commands":{"status":"GET /v1/status","datasets":"GET /v1/datasets?kind=inference","results":"GET /v1/models/results","predictions":"GET /v1/predictions","retraining":"POST /v1/retraining-requests com {dataset}","inference":"POST /v1/inferences com {dataset}"}}

@app.get("/v1/status")
def status():
    return {"models":[call(PROPHET_URL,"/v1/results"),call(SARIMA_URL,"/v1/results")],"datasets":{"retraining":datasets("retraining"),"inference":datasets("inference")}}

@app.get("/v1/datasets")
def list_datasets(kind: str): return {"kind":kind,"datasets":datasets(kind)}

@app.get("/v1/models/results")
def results():
    return {"models":[call(PROPHET_URL,"/v1/results"),call(SARIMA_URL,"/v1/results")]}

@app.get("/v1/predictions")
def predictions():
    return {"models":[call(PROPHET_URL,"/v1/predictions"),call(SARIMA_URL,"/v1/predictions")]}

@app.post("/v1/retraining-requests", status_code=202)
def retraining(request: DatasetRequest):
    dataset=checked_dataset("retraining",request.dataset)
    job_id=str(uuid.uuid4())
    execute("INSERT INTO retraining_jobs (id, status, details) VALUES (%s, 'queued', %s::jsonb)", (job_id,json.dumps({"dataset":dataset})))
    return {"id":job_id,"status":"queued","dataset":dataset}

@app.get("/v1/retraining-requests/{job_id}")
def retraining_status(job_id: str):
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id,status,details FROM retraining_jobs WHERE id=%s", (job_id,))
                row=cur.fetchone()
    except psycopg.Error as exc:
        raise HTTPException(503,"banco de metadados indisponível") from exc
    if not row: raise HTTPException(404,"pedido não encontrado")
    return {"id":str(row[0]),"status":row[1],"details":row[2]}

@app.post("/v1/inferences")
def inference(request: DatasetRequest):
    dataset=checked_dataset("inference",request.dataset)
    models=[call(PROPHET_URL,f"/v1/inference?dataset={dataset}"),call(SARIMA_URL,f"/v1/inference?dataset={dataset}")]
    return {"dataset":dataset,"models":models,"disclaimer":"Uso educacional; não use esta previsão para decisões financeiras ou apostas."}
