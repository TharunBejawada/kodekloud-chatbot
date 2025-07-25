from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["roadmap_chatbot"]
messages_collection = db.messages
guides_collection = db.guides

def get_message_history(user_id: str, topic: str):
    results = messages_collection.find({
        "user_id": user_id,
        "topic": topic
    }).sort("timestamp", 1)
    
    return [{"role": r["role"], "content": r["content"]} for r in results]

def get_guide_history(user_id: str, topic: str):
    doc = guides_collection.find_one({"user_id": user_id, "topic": topic})
    return doc.get("guide", []) if doc else []
