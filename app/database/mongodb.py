from pymongo import MongoClient
from datetime import datetime
import os
from prometheus_client import Counter # <-- 1. Importe o Counter

MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client["ad_logs"]
logs_collection = db["logs"]

# 2. Crie uma métrica para contar os logs por tipo
LOG_COUNTER = Counter('app_logs_total', 'Total de logs gerados pela aplicação', ['tipo'])

def log_event(event_type: str, message: str):
    # Insere no MongoDB (como já fazia)
    logs_collection.insert_one({
        "event_type": event_type,
        "message": message,
        "timestamp": datetime.utcnow()
    })

    # 3. Incrementa o contador do Prometheus
    # Se event_type for "Erro", ele incrementa a métrica de erros.
    LOG_COUNTER.labels(tipo=event_type).inc()