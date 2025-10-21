from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://172.17.0.3:27017/")
db = client["ad_logs"]
logs_collection = db["logs"]

def log_event(event_type: str, message: str):
    logs_collection.insert_one({
        "event_type": event_type,
        "message": message,
        "timestamp": datetime.utcnow()
    })
