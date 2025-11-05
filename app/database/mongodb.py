from pymongo import MongoClient
from datetime import datetime
import os # <-- Adicione isto

# Substitua a URL hardcoded por esta:
MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)

db = client["ad_logs"]
logs_collection = db["logs"]

def log_event(event_type: str, message: str):
    logs_collection.insert_one({
        "event_type": event_type,
        "message": message,
        "timestamp": datetime.utcnow()
    })