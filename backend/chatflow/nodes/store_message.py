from db.mongo import messages_col
from datetime import datetime

def store_message(state):
    user_id = state["user_id"]
    topic = state["topic"]
    user_input = state["user_input"]
    bot_response = state.get("response", "")
    timestamp = datetime.utcnow()

    session_id = f"{user_id}_{topic.replace(' ', '_').lower()}"

    messages_col.update_one(
        {"session_id": session_id},
        {
            "$push": {
                "messages": {
                    "timestamp": timestamp,
                    "user": user_input,
                    "bot": bot_response
                }
            },
            "$setOnInsert": {
                "user_id": user_id,
                "topic": topic,
                "created_at": timestamp
            }
        },
        upsert=True
    )

    return state
