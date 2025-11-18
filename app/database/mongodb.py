from pymongo import MongoClient
from datetime import datetime
import os
# (Removido: Importação do Prometheus)

MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client["ad_logs"]
logs_collection = db["logs"]

# (Removido: Definição do LOG_COUNTER)

def log_event(event_type: str, message: str):
    # Insere no MongoDB
    logs_collection.insert_one({
        "event_type": event_type,
        "message": message,
        "timestamp": datetime.utcnow()
    })

    # (Removido: Incremento do contador do Prometheus)