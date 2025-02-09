import os
import requests
import random
import time
import pandas as pd
from lxml import html
import os
import requests
import random
import time
import pandas as pd
from lxml import html
import json
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# ----------------- Telegram Bot Configuration -----------------

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

# Define an inline keyboard with options (for example, "Send to Notion" and "Summarize using LLMs")
inline_keyboard = {
    "inline_keyboard": [
        [
            {"text": "Send to Notion", "callback_data": "send_to_notion"},
            {"text": "Summarize using LLMs", "callback_data": "summarize_llm"}
        ]
    ]
}

# ----------------- Configuration -----------------
BASE_URL = 'https://flowingdata.com/page/'
LINK_XPATH = '//*[contains(concat(" ", @class, " "), " offset-by-two ")]//a'
# New XPath for text content:
CONTENT_XPATH = '//*[(@id = "entry-content-wrapper")]//p'
# (Optional) XPath for images if needed:
IMG_XPATH = '//*[contains(concat(" ", @class, " "), concat(" ", "wp-post-image", " "))]'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/90.0.4430.93 Safari/537.36'
    )
}

CSV_FILE = "flowingdata_posts.csv"

# ----------------- Load Existing Data -----------------
if os.path.exists(CSV_FILE):
    df_existing = pd.read_csv(CSV_FILE)
    existing_links = set(df_existing['Link'].dropna())
    print(f"Loaded {len(df_existing)} existing posts.")
else:
    df_existing = pd.DataFrame(columns=['Page', 'Text', 'Link', 'Content'])
    existing_links = set()
    print("No existing data found. Starting fresh.")

new_data = []

# ----------------- Scrape the First Page -----------------
page = 1
url = f"{BASE_URL}{page}/"
try:
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
except requests.RequestException as e:
    print(f"Error fetching page {page}: {e}")
    response = None

if response:
    tree = html.fromstring(response.content)
    nodes = tree.xpath(LINK_XPATH)
    if not nodes:
        print(f"No links found on page {page}.")
    else:
        for node in nodes:
            link = node.get('href')
            text = node.text_content().strip()
            # Only add the post if it's not already in our saved data
            if link not in existing_links:
                new_data.append({
                    'Page': page,
                    'Text': text,
                    'Link': link,
                    'Content': None  # To be filled in next step
                })
        print(f"Page {page} scraped. Found {len(new_data)} new posts.")
    time.sleep(random.uniform(1, 3))

# ----------------- Extract Content and Send to Telegram -----------------
for idx, data in enumerate(new_data):
    link = data.get('Link')
    if not link:
        continue
    try:
        response = requests.get(link, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching link {link}: {e}")
        continue

    tree = html.fromstring(response.content)
    # Extract text content using the specified XPath
    content_nodes = tree.xpath(CONTENT_XPATH)
    content_text = " ".join([node.text_content().strip() for node in content_nodes])

    if content_text:
        data['Content'] = content_text
        print(f"Content extracted for link: {link}")
    else:
        print(f"No content found for link: {link}")

    # Create a snippet (first 300 characters) to include in the Telegram message
    snippet = content_text[:300] + ("..." if len(content_text) > 300 else "")
    post_message = (
        f"New post found:\n\n"
        f"Title: {data['Text']}\n"
        f"Link: {link}\n\n"
        f"Snippet: {snippet}\n\n"
        f"Choose an action below:"
    )

    # Send the new post to Telegram
    send_to_telegram(post_message, keyboard=inline_keyboard)
    time.sleep(random.uniform(1, 3))
# ----------------- Update CSV with New Data -----------------
df_new = pd.DataFrame(new_data)
df_updated = pd.concat([df_existing, df_new], ignore_index=True)
print(f"Total posts after update: {len(df_updated)}")
df_updated.to_csv(CSV_FILE, index=False)(df_updated)}"