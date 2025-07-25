import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.load_kodekloud_notes import get_topic_content, store_topic_in_neo4j
from rag.neo4j_loader import update_topic_embedding

urls = [
    "https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Introduction/Course-Introduction",
    "https://notes.kodekloud.com/docs/Nginx-For-Beginners/Introduction/Introduction-and-Objectives"
]

for url in urls:
    topic, steps = get_topic_content(url)
    store_topic_in_neo4j(topic, steps)
    update_topic_embedding(topic)
    print(f"✅ Re-stored: {topic} ({len(steps)} steps)")
