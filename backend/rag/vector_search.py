from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)

def get_topic_embedding_from_neo4j(topic):
    query = """
    MATCH (n:Topic {name: $topic}) RETURN n.embedding AS embedding LIMIT 1
    """
    with driver.session() as session:
        result = session.run(query, topic=topic)
        record = result.single()
        if record:
            return record["embedding"]
        else:
            return [0.0] * 1536  # return zero vector if not found
