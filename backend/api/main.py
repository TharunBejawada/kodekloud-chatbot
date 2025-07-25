from fastapi import FastAPI, Query, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from chatflow.flow import chatbot_flow
from chatflow.nodes.generate_guide import generate_guide
from db.mongo import messages_col
from db import message_db
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))


app = FastAPI()

# Optional: enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to your frontend domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class ChatRequest(BaseModel):
    user_id: str
    topic: str
    user_input: str

# Response schema
class ChatResponse(BaseModel):
    response: str

class GuideRequest(BaseModel):
    topic: str

@app.get("/chat-history")
async def chat_history(user_id: str, topic: str):
    session_id = f"{user_id}_{topic}"
    
    # Try both by session_id and fallback by user_id+topic
    session = message_db.messages_collection.find_one({
        "$or": [
            {"session_id": session_id},
            {"user_id": user_id, "topic": topic}
        ]
    })

    if session and "messages" in session:
        chat_messages = []
        for m in session["messages"]:
            if "user" in m:
                chat_messages.append({"role": "user", "content": m["user"]})
            if "bot" in m:
                chat_messages.append({"role": "assistant", "content": m["bot"]})
        return {"messages": chat_messages}
    return {"messages": []}


@app.get("/guide-history")
async def get_guide_history(user_id: str = Query(...), topic: str = Query(...)):
    try:
        guide = message_db.get_guide_history(user_id, topic)
        return {"guide": guide}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": "Error fetching guide history"})

@app.post("/generate-guide")
async def generate_guide_api(request: GuideRequest):
    try:
        state = {"topic": request.topic}
        result = generate_guide(state)
        return {"guide": result["guide"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    state = chatbot_flow.invoke({
        "user_id": request.user_id,
        "topic": request.topic,
        "user_input": request.user_input
    })
    print("🧾 Final Flow State:", state)
    response = state.get("response", "No response")
    return {"response": response}



# GET old messages (for resuming session)
@app.get("/resume")
async def resume_chat(user_id: str, topic: str):
    session_id = f"{user_id}_{topic.replace(' ', '_').lower()}"
    session = messages_col.find_one({"session_id": session_id})

    if not session or "messages" not in session:
        return {"messages": []}
    
    return {"messages": session["messages"]}
