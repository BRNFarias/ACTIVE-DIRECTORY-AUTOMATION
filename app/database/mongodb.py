from pymongo import MongoClient
from datetime import datetime
import os # <-- 1. Importe o 'os'

# 2. Pegue a URL do Mongo da variável de ambiente
MONGO_URL = os.getenv("MONGO_URL") 

# 3. Use a variável MONGO_URL para se conectar
client = MongoClient(MONGO_URL) 
db = client["ad_logs"]
logs_collection = db["logs"]

def log_event(event_type: str, message: str):
    logs_collection.insert_one({
        "event_type": event_type,
        "message": message,
        "timestamp": datetime.utcnow()
    })