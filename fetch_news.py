#!/usr/bin/env python3
"""
Morning Digest — Daily Fintech & PM News Fetcher
Fetches RSS feeds, generates a dashboard HTML page, and saves it for GitHub Pages.
"""

import feedparser
import datetime
import json
import os
import html
import re
import sys

# ── Timezone: UAE is UTC+4 ──────────────────────────────────────────────────
UAE_OFFSET = datetime.timezone(datetime.timedelta(hours=4))
now = datetime.datetime.now(UAE_OFFSET)
today_str = now.strftime("%A, %d %B %Y")
date_slug = now.strftime("%Y-%m-%d")

# ── RSS Source List ─────────────────────────────────────────────────────────
SOURCES = {
    "fintech": {
        "label": "Fintech & Neobanks",
        "icon": "🏦",
        "color": "#4F46E5",
        "feeds": [
            ("TechCrunch Fintech",  "https://techcrunch.com/category/fintech/feed/"),
            ("Finextra",            "https://www.finextra.com/rss/headlines.aspx"),
            ("Tearsheet",          "https://tearsheet.co/feed/"),
            ("The Financial Brand", "https://thefinancialbrand.com/feed/"),
        ]
    },
    "investing": {
        "label": "Investing & Wealth",
        "icon": "📈",
        "color": "#059669",
        "feeds": [
            ("Reuters Business",   "https://feeds.reuters.com/reuters/businessNews"),
            ("CNBC Finance",       "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
            ("Seeking Alpha",      "https://seekingalpha.com/feed.xml"),
        ]
    },
    "india": {
        "label": "India Markets",
        "icon": "🇮🇳",
        "color": "#D97706",
        "feeds": [
            ("Economic Times Markets", "https://economictimes.indiatimes.com/markets/rss.cms"),
            ("Moneycontrol",           "https://www.moneycontrol.com/rss/business.xml"),
            ("LiveMint Markets",       "https://www.livemint.com/rss/markets"),
            ("BSE India News",         "https://www.bseindia.com/investor_relations/ann_pub.html"),
        ]
    },
    "mena": {
        "label": "MENA / UAE Market",
        "icon": "🌍",
        "color": "#7C3AED",
        "feeds": [
            ("Arabian Business",   "https://www.arabianbusiness.com/rss.xml"),
            ("Zawya Economy",      "https://www.zawya.com/en/rss"),
            ("Gulf News Business", "https://gulfnews.com/rss/business"),
            ("Khaleej Times Biz",  "https://www.khaleejtimes.com/business/rss.xml"),
        ]
    },
    "product": {
        "label": "Product Management",
        "icon": "🧠",
        "color": "#DB2777",
        "feeds": [
            ("Mind the Product",   "https://www.mindtheproduct.com/feed/"),
            ("Product Hunt",       "https://www.producthunt.com/feed"),
            ("First Round Review", "https://review.firstround.com/feed.xml"),
            ("Lenny's Newsletter", "https://www.lennysnewsletter.com/feed"),
        ]
    },
    "innovation": {
        "label": "Tech & Innovation",
        "icon": "💡",
        "color": "#0891B2",
        "feeds": [
            ("The Verge",          "https://www.theverge.com/rss/index.xml"),
            ("Stratechery",        "https://stratechery.com/feed/"),
            ("MIT Tech Review",    "https://www.technologyreview.com/feed/"),
        ]
    },
}

ITEMS_PER_SECTION = 4  # articles per category

# ── Fetch & Parse ───────────────────────────────────────────────────────────
def clean(text):
    """Strip HTML tags and excess whitespace."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:280] + ("…" if len(text) > 280 else "")

def fetch_section(section_key, section_data):
    items = []
    for source_name, feed_url in section_data["feeds"]:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:2]:
                title = clean(entry.get("title", ""))
                summary = clean(entry.get("summary", entry.get("description", "")))
                link = entry.get("link", "#")
                pub_date = ""
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        pd = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
                        hours_ago = int((datetime.datetime.now(datetime.timezone.utc) - pd).total_seconds() / 3600)
                        pub_date = f"{hours_ago}h ago" if hours_ago < 48 else pd.strftime("%d %b")
                    except Exception:
                        pass
                if title:
                    items.append({
                        "title": title,
                        "summary": summary,
                        "link": link,
                        "source": source_name,
                        "time": pub_date,
                    })
                if len(items) >= ITEMS_PER_SECTION:
                    break
        except Exception as e:
            print(f"  ⚠ Skipped {source_name}: {e}", file=sys.stderr)
        if len(items) >= ITEMS_PER_SECTION:
            break
    return items

# ── Build HTML ──────────────────────────────────────────────────────────────
def render_card(item, color):
    return f"""
        <div class="card">
          <div class="card-header">
            <span class="source-tag" style="background:{color}20;color:{color}">{html.escape(item['source'])}</span>
            {"<span class='time-tag'>" + html.escape(item['time']) + "</span>" if item['time'] else ""}
          </div>
          <a class="card-title" href="{html.escape(item['link'])}" target="_blank" rel="noopener">{html.escape(item['title'])}</a>
          <p class="card-summary">{html.escape(item['summary'])}</p>
        </div>"""

def render_section(key, section_data, items):
    cards_html = "".join(render_card(i, section_data["color"]) for i in items) if items else \
        '<p class="empty">No articles fetched — sources may be temporarily unavailable.</p>'
    return f"""
      <section class="section" id="{key}">
        <div class="section-header">
          <span class="section-icon">{section_data['icon']}</span>
          <h2 style="color:{section_data['color']}">{section_data['label']}</h2>
          <span class="count-badge" style="background:{section_data['color']}20;color:{section_data['color']}">{len(items)} articles</span>
        </div>
        <div class="cards-grid">{"".join(render_card(i, section_data['color']) for i in items) if items else '<p class="empty">No articles available right now.</p>'}</div>
      </section>"""

def build_html(all_sections):
    nav_links = "".join(
        f'<a href="#{k}" class="nav-link" style="--accent:{v["color"]}">{v["icon"]} {v["label"]}</a>'
        for k, v in SOURCES.items()
    )
    sections_html = "".join(
        render_section(k, SOURCES[k], all_sections.get(k, []))
        for k in SOURCES
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Morning Digest — {today_str}</title>
  <style>
    :root {{
      --bg: #0f1117;
      --surface: #1a1d27;
      --border: #2a2d3a;
      --text: #e2e8f0;
      --muted: #8892a4;
      --radius: 12px;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; min-height: 100vh; }}

    /* Top bar */
    .topbar {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 100; }}
    .logo {{ font-size: 1.1rem; font-weight: 700; letter-spacing: -0.3px; }}
    .logo span {{ color: #60a5fa; }}
    .date-badge {{ background: #1e3a5f; color: #60a5fa; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 500; }}
    .refresh-time {{ color: var(--muted); font-size: 0.75rem; }}

    /* Nav */
    .nav {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 0 24px; display: flex; gap: 4px; overflow-x: auto; scrollbar-width: none; }}
    .nav::-webkit-scrollbar {{ display: none; }}
    .nav-link {{ padding: 12px 16px; text-decoration: none; color: var(--muted); font-size: 0.85rem; white-space: nowrap; border-bottom: 2px solid transparent; transition: all 0.2s; }}
    .nav-link:hover {{ color: var(--text); border-bottom-color: var(--accent); }}

    /* Main */
    .main {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}

    /* Hero */
    .hero {{ text-align: center; padding: 32px 0 40px; }}
    .hero h1 {{ font-size: 2rem; font-weight: 800; letter-spacing: -0.5px; margin-bottom: 8px; }}
    .hero p {{ color: var(--muted); font-size: 0.95rem; }}

    /* Section */
    .section {{ margin-bottom: 48px; }}
    .section-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }}
    .section-icon {{ font-size: 1.4rem; }}
    .section-header h2 {{ font-size: 1.15rem; font-weight: 700; }}
    .count-badge {{ padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; margin-left: auto; }}

    /* Cards */
    .cards-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }}
    .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; transition: border-color 0.2s, transform 0.2s; }}
    .card:hover {{ border-color: #3a3d4a; transform: translateY(-2px); }}
    .card-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
    .source-tag {{ padding: 2px 8px; border-radius: 6px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; }}
    .time-tag {{ color: var(--muted); font-size: 0.72rem; margin-left: auto; }}
    .card-title {{ display: block; color: var(--text); text-decoration: none; font-size: 0.92rem; font-weight: 600; line-height: 1.4; margin-bottom: 8px; }}
    .card-title:hover {{ color: #60a5fa; }}
    .card-summary {{ color: var(--muted); font-size: 0.8rem; line-height: 1.5; }}
    .empty {{ color: var(--muted); font-style: italic; font-size: 0.85rem; }}

    /* Footer */
    .footer {{ text-align: center; padding: 32px 24px; color: var(--muted); font-size: 0.8rem; border-top: 1px solid var(--border); }}
    .footer a {{ color: #60a5fa; text-decoration: none; }}

    @media (max-width: 640px) {{
      .hero h1 {{ font-size: 1.4rem; }}
      .cards-grid {{ grid-template-columns: 1fr; }}
      .topbar {{ flex-wrap: wrap; gap: 8px; }}
    }}
  </style>
</head>
<body>

<div class="topbar">
  <div class="logo">🌅 Morning <span>Digest</span></div>
  <span class="date-badge">{today_str}</span>
  <span class="refresh-time">Updated {now.strftime("%H:%M")} UAE</span>
</div>

<nav class="nav">{nav_links}</nav>

<main class="main">
  <div class="hero">
    <h1>Your Daily Briefing</h1>
    <p>Fintech · Investing · India Markets · MENA · Product · Innovation</p>
  </div>
  {sections_html}
</main>

<footer class="footer">
  Auto-updated daily at 08:00 UAE time via GitHub Actions &nbsp;·&nbsp;
  <a href="https://github.com" target="_blank">View on GitHub</a> &nbsp;·&nbsp;
  Built for Shruti @ Wio Securities
</footer>

</body>
</html>"""

# ── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"📰 Fetching news for {today_str}…")
    all_sections = {}
    for key, data in SOURCES.items():
        print(f"  → {data['label']}")
        all_sections[key] = fetch_section(key, data)

    html_content = build_html(all_sections)

    # Save to docs/index.html (GitHub Pages source)
    out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "index.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Also save a dated archive copy
    archive_path = os.path.join(os.path.dirname(__file__), "..", "docs", f"{date_slug}.html")
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Saved to docs/index.html and docs/{date_slug}.html")
