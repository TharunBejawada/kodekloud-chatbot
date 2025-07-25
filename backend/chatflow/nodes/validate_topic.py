def validate_topic(state):
    from utils.embeddings import get_embedding, cosine_similarity
    from rag.neo4j_loader import get_topic_embedding_from_neo4j
    import numpy as np

    message = state["user_input"]
    topic = state["topic"]

    user_vec = get_embedding(message)
    topic_vec = get_topic_embedding_from_neo4j(topic)

    similarity = cosine_similarity(user_vec, topic_vec)

    print(f"🧮 Similarity: {similarity:.4f}")

    if similarity >= 0.85:
        if state.get("guide"):
            return {"branch": "chat", "similarity": similarity}
        else:
            return {"branch": "generate_guide", "similarity": similarity}
    else:
        return {"branch": "off_topic", "similarity": similarity}
