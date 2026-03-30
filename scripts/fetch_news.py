#!/usr/bin/env python3
"""
Morning Digest — Daily Fintech & PM News Fetcher
"""

import feedparser
import datetime
import os
import html
import re
import sys

# ── Timezone: UAE (UTC+4) ─────────────────────────────
UAE_OFFSET = datetime.timezone(datetime.timedelta(hours=4))
now = datetime.datetime.now(UAE_OFFSET)
today_str = now.strftime("%A, %d %B %Y")

# ── RSS Sources ───────────────────────────────────────
SOURCES = {
    "fintech": {
        "label": "Fintech & Neobanks",
        "icon": "🏦",
        "color": "#4F46E5",
        "feeds": [
            ("TechCrunch Fintech", "https://techcrunch.com/category/fintech/feed/"),
            ("Finextra", "https://www.finextra.com/rss/headlines.aspx"),
            ("Tearsheet", "https://tearsheet.co/feed/"),
        ]
    },
    "investing": {
        "label": "Investing & Wealth",
        "icon": "📈",
        "color": "#059669",
        "feeds": [
            ("Reuters", "https://feeds.reuters.com/reuters/businessNews"),
            ("CNBC", "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
        ]
    }
}

ITEMS_PER_SECTION = 4

# ── Helpers ───────────────────────────────────────────
def clean(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()[:200]

# ── Fetch ─────────────────────────────────────────────
def fetch_section(section):
    items = []

    for source_name, url in section["feeds"]:
        try:
            feed = feedparser.parse(
                url,
                request_headers={'User-Agent': 'Mozilla/5.0'}
            )

            for entry in feed.entries[:2]:
                title = clean(entry.get("title", ""))
                summary = clean(entry.get("summary", ""))
                link = entry.get("link", "#")

                if title:
                    items.append({
                        "title": title,
                        "summary": summary,
                        "link": link,
                        "source": source_name
                    })

                if len(items) >= ITEMS_PER_SECTION:
                    break

        except Exception as e:
            print(f"Error in {source_name}: {e}")

        if len(items) >= ITEMS_PER_SECTION:
            break

    return items

# ── HTML Builder ──────────────────────────────────────
def build_html(all_data):
    sections_html = ""

    for key, section in SOURCES.items():
        items = all_data.get(key, [])

        cards = ""
        for item in items:
            cards += f"""
            <div class="card">
              <a href="{item['link']}" target="_blank">
                <h3>{html.escape(item['title'])}</h3>
              </a>
              <p>{html.escape(item['summary'])}</p>
              <span>{item['source']}</span>
            </div>
            """

        if not cards:
            cards = "<p>No articles available right now.</p>"

        sections_html += f"""
        <section>
          <h2>{section['icon']} {section['label']}</h2>
          {cards}
        </section>
        """

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Morning Digest</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #0f1117;
            color: white;
            padding: 20px;
        }}
        h1 {{ color: #60a5fa; }}
        section {{ margin-bottom: 30px; }}
        .card {{
            background: #1a1d27;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
        }}
        a {{ color: #60a5fa; text-decoration: none; }}
        p {{ color: #aaa; }}
        span {{ font-size: 12px; color: #888; }}
    </style>
</head>
<body>

<h1>🌅 Morning Digest</h1>
<p>{today_str}</p>

{sections_html}

</body>
</html>
"""

# ── Main ──────────────────────────────────────────────
if __name__ == "__main__":
    print("Fetching news...")

    all_data = {}
    for key, section in SOURCES.items():
        all_data[key] = fetch_section(section)
        print(f"{key}: {len(all_data[key])} articles")

    html_content = build_html(all_data)

    # ✅ Save to ROOT index.html
    base_dir = os.path.dirname(__file__)
    output_path = os.path.join(base_dir, "..", "index.html")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print("✅ Updated index.html")
