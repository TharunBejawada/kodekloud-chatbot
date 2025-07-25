import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional

# Define the state schema
class ChatState(TypedDict, total=False):
    user_id: str
    topic: str
    user_input: str
    guide: Optional[list]
    response: Optional[str]
    history: Optional[list]
    similarity: Optional[float]

# Import nodes
from chatflow.nodes.start_node import start_node
from chatflow.nodes.validate_topic import validate_topic
from chatflow.nodes.reject_off_topic import reject_off_topic
from chatflow.nodes.generate_guide import generate_guide
from chatflow.nodes.chat import chat_node
from chatflow.nodes.store_message import store_message

builder = StateGraph(ChatState)

builder.add_node("start", start_node)
builder.add_node("validate_topic", validate_topic)
builder.add_node("off_topic", reject_off_topic)
builder.add_node("generate_guide", generate_guide)
builder.add_node("chat", chat_node)
builder.add_node("store_message", store_message)

def route_topic_validation(output: dict) -> str:
    return output.get("branch", "off_topic")

builder.set_entry_point("start")
builder.add_edge("start", "validate_topic")
builder.add_conditional_edges("validate_topic", route_topic_validation)
builder.add_edge("generate_guide", "chat")
builder.add_edge("chat", "store_message")
builder.add_edge("store_message", END)
builder.add_edge("off_topic", END)

chatbot_flow = builder.compile()
