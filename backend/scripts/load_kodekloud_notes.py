import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import requests
from bs4 import BeautifulSoup
from neo4j import GraphDatabase
from dotenv import load_dotenv
import time
from openai import OpenAI
from rag.neo4j_loader import update_topic_embedding


load_dotenv()

# Setup keys
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Setup Neo4j driver
driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)

BASE_URL = "https://notes.kodekloud.com/"

def get_topic_urls():
    res = requests.get(BASE_URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    links = soup.select("a[href^='/']")
    topic_urls = list({BASE_URL + link['href'].lstrip("/") for link in links if "://" not in link['href']})
    return topic_urls

def get_topic_content(topic_url):
    res = requests.get(topic_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    # topic = soup.title.text.strip()
    parts = topic_url.strip("/").split("/")
    topic = parts[4] if len(parts) >= 5 else "Unknown Topic"
    paragraphs = soup.select("article p")
    content_blocks = []

    current_title = "Introduction"
    current_content = ""

    for p in paragraphs:
        text = p.get_text().strip()
        if text.lower().startswith("##") or len(text) > 200:
            if current_content:
                content_blocks.append((current_title, current_content))
            current_title = text.strip("## ").strip()
            current_content = ""
        else:
            current_content += " " + text

    if current_content:
        content_blocks.append((current_title, current_content))

    return topic, content_blocks

def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=[text]
    )
    return response.data[0].embedding

def store_topic_in_neo4j(topic_name, steps):
    with driver.session() as session:
        session.run("MERGE (t:Topic {name: $name})", name=topic_name)

        for idx, (step_title, step_content) in enumerate(steps):
            embedding = get_embedding(step_content)
            session.run("""
                MATCH (t:Topic {name: $topic})
                MERGE (s:Step {title: $title})
                SET s.content = $content,
                    s.order = $order,
                    s.embedding = $embedding
                MERGE (t)-[:HAS_STEP]->(s)
            """, {
                "topic": topic_name,
                "title": step_title,
                "content": step_content,
                "order": idx,
                "embedding": embedding
            })
            time.sleep(1.2)

def run():
    print("Fetching topics from KodeKloud...")
    topic_urls = get_topic_urls()
    print(f"Found {len(topic_urls)} topics.")

    for url in topic_urls:
        print(f"Processing: {url}")
        try:
            topic_name, steps = get_topic_content(url)
            store_topic_in_neo4j(topic_name, steps)
            update_topic_embedding(topic_name)
            print(f"✓ Stored: {topic_name} ({len(steps)} steps)")
        except Exception as e:
            print(f"❌ Failed to process {url}: {e}")

if __name__ == "__main__":
    run()
