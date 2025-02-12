import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from lxml import html
import json
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# ----------------- Telegram Bot Configuration -----------------
# Define an inline keyboard with options (for example, "Send to Notion" and "Summarize using LLMs")
inline_keyboard = {
    "inline_keyboard": [
        [
            {"text": "Send to Notion", "callback_data": "send_to_notion"},
            {"text": "Summarize using LLMs", "callback_data": "summarize_llm"}
        ]
    ]
}
def send_to_telegram(message, keyboard=None):
    """
    Sends a message to Telegram with an optional inline keyboard.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    if keyboard:
        payload["reply_markup"] = json.dumps(keyboard)
    response = requests.post(url, json=payload)
    return response.json()

# URL for the NYT Upshot section
url = "https://www.nytimes.com/section/upshot"

# Headers to mimic a browser request
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/90.0.4430.93 Safari/537.36"
    )
}

# Send a GET request
response = requests.get(url, headers=headers)
if response.status_code != 200:
    print(f"Error: Received status code {response.status_code}")
    exit()

# Parse the HTML content with BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

# Inspect the page structure to identify article containers.
articles = soup.find_all("article")

# Load existing data from CSV if it exists
csv_file = "nyt_upshot_articles.csv"
if os.path.exists(csv_file):
    df_existing = pd.read_csv(csv_file)
    existing_links = set(df_existing['Link'].dropna())
    print(f"Loaded {len(df_existing)} existing articles.")
else:
    df_existing = pd.DataFrame(columns=['Headline', 'Link', 'Summary'])
    existing_links = set()
    print("No existing data found. Starting fresh.")

new_articles = []

for article in articles:
    # Attempt to find the headline. The headline is often in an <h2> tag.
    headline_tag = article.find("h2")
    headline = headline_tag.get_text(strip=True) if headline_tag else "No headline found"

    # Attempt to extract the link. Typically, an <a> tag is used.
    link_tag = article.find("a", href=True)
    if link_tag:
        link = link_tag["href"]
        if link.startswith("/"):
            link = "https://www.nytimes.com" + link
    else:
        link = "No link found"

    # Optionally, extract a summary or snippet, often in a <p> tag.
    summary_tag = article.find("p")
    summary = summary_tag.get_text(strip=True) if summary_tag else "No summary available"

    # Check if the link is already in the existing data
    if link not in existing_links:
        new_articles.append({
            'Headline': headline,
            'Link': link,
            'Summary': summary
        })
    post_message = (
        f"New post found:\n\n"
        f"Title: {headline}\n"
        f"Link: {link}\n\n"
        f"Snippet: {summary}\n\n"
        f"Choose an action below:"
    )
    send_to_telegram(post_message, keyboard=inline_keyboard)

# Append new articles to the existing DataFrame
if new_articles:
    df_new = pd.DataFrame(new_articles)
    df_updated = pd.concat([df_existing, df_new], ignore_index=True)
    df_updated.to_csv(csv_file, index=False)
    print(f"Added {len(new_articles)} new articles. Total articles: {len(df_updated)}")
else:
    print("No new articles found.")