import numpy as np
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from utils.embeddings import get_embedding, cosine_similarity

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)

def fetch_guide_from_neo4j(topic):
    query = """
    MATCH (n:Topic {name: $topic})-[:HAS_STEP]->(s:Step)
    RETURN s.title AS title, s.content AS content
    ORDER BY s.order
    """
    with driver.session() as session:
        result = session.run(query, topic=topic)
        guide_steps = [{"title": row["title"], "content": row["content"]} for row in result]
        return guide_steps if guide_steps else None

def store_topic_and_guide(topic_name, steps):
    with driver.session() as session:
        session.run("MERGE (t:Topic {name: $name})", name=topic_name)

        for idx, step in enumerate(steps):
            title = step.get("title", f"Step {idx+1}")
            content = step.get("content", "")

            embedding = get_embedding(content)

            session.run("""
                MATCH (t:Topic {name: $topic})
                MERGE (s:Step {title: $title})
                SET s.content = $content,
                    s.order = $order,
                    s.embedding = $embedding
                MERGE (t)-[:HAS_STEP]->(s)
            """, {
                "topic": topic_name,
                "title": title,
                "content": content,
                "order": idx,
                "embedding": embedding
            })
        update_topic_embedding(topic_name)
            
def get_topic_embedding_from_neo4j(user_topic):
    print(f"Connecting to Neo4j → {os.getenv('NEO4J_URI')}")
    user_vec = get_embedding(user_topic)
    print(f"\n🔍 User topic = '{user_topic}'")
    print(f"🧠 User vec norm = {np.linalg.norm(user_vec):.4f}")

    query = """
    MATCH (t:Topic)
    WHERE t.embedding IS NOT NULL
    RETURN t.name AS name, t.embedding AS embedding
    """

    with driver.session() as session:
        result = session.run(query)
        records = list(result)
        print(f"🔢 Topics with embeddings in Neo4j: {len(records)}")

        best_match = None
        best_score = -1.0

        for record in records:
            print(f"📦 Raw record from Neo4j → name: {record['name']} | embedding type: {type(record['embedding'])} | length: {len(record['embedding']) if record['embedding'] else 'None'}")
            topic_name = record["name"]
            topic_vec = record["embedding"]

            if not topic_vec:
                print(f"⚠️ No embedding for topic: {topic_name}")
                continue

            norm = np.linalg.norm(topic_vec)
            print(f"🔍 Checking topic: '{topic_name}' | embedding norm: {norm:.4f}")

            if norm == 0 or len(topic_vec) != 1536:
                print(f"⚠️ Skipping invalid vector from topic '{topic_name}'")
                continue

            score = cosine_similarity(user_vec, topic_vec)
            print(f"✅ Cosine similarity: '{user_topic}' vs '{topic_name}' → {score:.4f}")

            if score > best_score:
                best_match = (topic_name, topic_vec)
                best_score = score

        if best_match and best_score >= 0.6:
            print(f"🏁 Selected topic: {best_match[0]} with score {best_score:.4f}")
            return best_match[1]
        else:
            print("❌ No suitable topic match found")
            return [0.0] * 1536

        
def update_topic_embedding(topic_name):
    with driver.session() as session:
        result = session.run("""
            MATCH (:Topic {name: $topic})-[:HAS_STEP]->(s:Step)
            WHERE s.embedding IS NOT NULL
            RETURN s.embedding AS embedding
        """, topic=topic_name)

        embeddings = [record["embedding"] for record in result if record["embedding"]]

        if not embeddings:
            print(f"⚠️ No embeddings found for steps under topic '{topic_name}'")
            return

        avg_vector = np.mean(embeddings, axis=0).tolist()

        session.run("""
            MATCH (t:Topic {name: $topic})
            SET t.embedding = $embedding
        """, topic=topic_name, embedding=avg_vector)

        print(f"✅ Topic embedding updated for '{topic_name}'")

