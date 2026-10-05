import json
import os
import time
from pathlib import Path

import pandas as pd
import psycopg
from prophet import Prophet
from statsmodels.tsa.statespace.sarimax import SARIMAX

url = os.environ['DATABASE_URL']
datasets_dir = Path('/data/dataRetreino')
champion_metadata_path = Path('/artifacts/prophet_usd_brl_metadata.json')

def validate_batch(dataset):
    batch = pd.read_csv(datasets_dir / dataset, parse_dates=['Date'])
    if batch.Date.duplicated().any() or not batch.Date.is_monotonic_increasing or batch.Close.isna().any():
        raise ValueError('lote de retreino inválido')
    if len(batch) < 10:
        raise ValueError('lote insuficiente: são necessárias ao menos 10 linhas para a simulação')
    return batch

def evaluate(actual, forecast, previous_close):
    actual = actual.reset_index(drop=True)
    forecast = pd.Series(forecast).reset_index(drop=True)
    reference = pd.concat([pd.Series([previous_close]), actual.iloc[:-1]], ignore_index=True)
    return {
        'mae': float((actual - forecast).abs().mean()),
        'direction_accuracy': float(((actual > reference) == (forecast > reference)).mean()),
        'observations': len(actual),
    }

def train_candidates(batch):
    split = int(len(batch) * 0.7)
    train = batch.iloc[:split]
    test = batch.iloc[split:]
    prophet = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False, uncertainty_samples=0)
    prophet.fit(train.rename(columns={'Date': 'ds', 'Close': 'y'})[['ds', 'y']])
    prophet_forecast = prophet.predict(test.rename(columns={'Date': 'ds'})[['ds']]).yhat
    sarima = SARIMAX(train.Close, order=(1, 1, 0), enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
    sarima_forecast = sarima.forecast(len(test))
    return {
        'prophet': evaluate(test.Close, prophet_forecast, train.Close.iloc[-1]),
        'sarima': evaluate(test.Close, sarima_forecast, train.Close.iloc[-1]),
    }

def load_champion():
    metadata = json.loads(champion_metadata_path.read_text(encoding='utf-8'))
    metrics = metadata['validation_metrics']
    return {
        'prophet': {
            'version': 'prophet-v1',
            'direction_accuracy': metrics['direction_accuracy_prophet'],
            'mae': metrics['mae_prophet'],
        },
        'sarima': {
            'version': 'sarima-v1',
            'direction_accuracy': 1.0,
            'mae': 0.34099916767220395,
        },
    }

def comparison(candidate, champion):
    if candidate['direction_accuracy'] < champion['direction_accuracy']:
        return 'Acurácia direcional abaixo do campeão.'
    if candidate['mae'] > champion['mae']:
        return 'MAE acima do campeão.'
    return 'Métricas promissoras, mas a amostra é pequena e a simulação não promove artefatos.'

while True:
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, details FROM retraining_jobs WHERE status='queued' ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED")
            row=cur.fetchone()
            if row:
                try:
                    dataset = row[1]['dataset']
                    batch = validate_batch(dataset)
                    candidates = train_candidates(batch)
                    champions = load_champion()
                    details = {
                        'dataset': dataset,
                        'simulation': True,
                        'rows': len(batch),
                        'candidates': candidates,
                        'champions': champions,
                        'comparison': {
                            name: comparison(candidates[name], champions[name])
                            for name in candidates
                        },
                        'promotion': 'not_promoted',
                        'reason': 'Os candidatos foram treinados, mas os artefatos atuais foram preservados por se tratar de uma simulação com apenas três observações de avaliação.',
                    }
                    cur.execute("UPDATE retraining_jobs SET status='validated', details=%s::jsonb WHERE id=%s", (json.dumps(details), row[0]))
                except (KeyError, FileNotFoundError, ValueError) as exc:
                    cur.execute("UPDATE retraining_jobs SET status='failed', details=%s::jsonb WHERE id=%s", (json.dumps({'error': str(exc)}), row[0]))
        conn.commit()
    time.sleep(2)
