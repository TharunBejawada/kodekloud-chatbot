import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
import json
import re

load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def search_web(topic):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": topic}

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    results = response.json().get("organic", [])[:5]  # Top 5 results
    sources = []

    for item in results:
        snippet = item.get("snippet") or ""
        title = item.get("title") or ""
        link = item.get("link") or ""
        sources.append(f"Title: {title}\nSnippet: {snippet}\nURL: {link}\n")

    return "\n".join(sources)

def format_guide_from_web(topic, sources_text):
    prompt = f"""
You are an expert technical tutor. You are given search results about the topic: "{topic}".

Create a structured beginner-friendly guide based on it, broken into 3–5 sections.
Respond ONLY with a JSON list, where each element is:
  {{
    "title": "...",
    "content": "..."
  }}

Sources:
{sources_text}
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates study guides."},
            {"role": "user", "content": prompt}
        ]
    )

    try:
        content = response.choices[0].message.content.strip()

        # Extract JSON block from messy output
        match = re.search(r"\[.*\]", content, re.DOTALL)
        json_str = match.group(0) if match else content

        guide = json.loads(json_str)
        return guide
    except Exception as e:
        print("❌ JSON Parsing failed:", e)
        return [{
            "title": f"Overview of {topic}",
            "content": sources_text[:1500]
        }]

def fetch_guide_from_web(topic):
    print(f"🔎 MCP fallback triggered for topic: {topic}")
    sources = search_web(topic)
    guide = format_guide_from_web(topic, sources)
    return guide

if __name__ == "__main__":
    guide = fetch_guide_from_web("Docker")
    for step in guide:
        print(step["title"])
        print(step["content"][:100])
        print()
