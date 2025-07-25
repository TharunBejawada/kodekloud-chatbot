from rag.neo4j_loader import fetch_guide_from_neo4j
from rag.mcp_fallback import fetch_guide_from_web
from rag.neo4j_loader import store_topic_and_guide

def generate_guide(state):
    topic = state.get("topic")

    # Try Neo4j first
    guide = fetch_guide_from_neo4j(topic)

    if not guide:
        # Fallback to web + OpenAI
        guide = fetch_guide_from_web(topic)

        # Save the web guide into Neo4j for future runs
        store_topic_and_guide(topic, guide)

    state["guide"] = guide
    return state

