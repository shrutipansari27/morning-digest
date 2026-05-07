#!/usr/bin/env python3
"""Morning Digest — Daily Finance & Tech News Fetcher"""

import feedparser
import datetime
import html
import re
import os

# ── India Standard Time (UTC+5:30) ────────────────────
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
now = datetime.datetime.now(IST)
today_str = now.strftime("%A, %d %B %Y")
day_of_year = now.timetuple().tm_yday

# ── Daily Vocabulary (rotates each day) ───────────────
VOCABULARY = [
    ("NAV – Net Asset Value", "The per-unit value of a fund's assets minus liabilities, calculated daily. NAV = (Total Assets − Liabilities) ÷ Outstanding Units. Mutual funds and ETFs are priced at NAV; unlike stocks, this is set at end-of-day rather than in real time. For UCITS ETFs, NAV is also the basis for creation and redemption of units by authorised participants."),
    ("UCITS", "Undertakings for Collective Investment in Transferable Securities — an EU regulatory framework enabling open-ended funds to be freely sold across member states. Its strict diversification, liquidity, and disclosure rules make UCITS vehicles popular with global institutional and retail investors seeking a regulated, passport-friendly wrapper. Most cross-border ETFs listed in Europe are UCITS-compliant."),
    ("Alpha", "The excess return of an investment above its benchmark after adjusting for market risk. Alpha > 0 signals outperformance; Alpha < 0 means underperformance. It is considered the purest measure of investment skill, stripping away returns that simply came from riding general market moves. Hedge funds and active managers are judged primarily on alpha generation."),
    ("Beta", "A measure of an asset's price sensitivity to market moves. Beta = 1 tracks the market perfectly; Beta > 1 amplifies swings; Beta < 1 dampens them. A defensive utility stock might carry Beta 0.5, while a high-growth tech stock could exceed Beta 1.8. Beta is a core input in the Capital Asset Pricing Model used to estimate expected returns."),
    ("CFD – Contract for Difference", "A derivative instrument that mirrors an asset's price without requiring ownership. Profit or loss equals the price difference between entry and exit multiplied by contract size. CFDs support leverage and short-selling, making them popular for active traders in equities, FX, commodities, and indices. In most jurisdictions retail leverage limits are capped by the regulator."),
    ("Margin Trading", "Borrowing funds from a broker to control a position larger than your own capital. Leverage amplifies both gains and losses proportionally. If account equity falls below the broker's maintenance margin threshold, a margin call is triggered — requiring an immediate top-up or forced liquidation of positions. Margin rates and requirements vary by asset class and broker."),
    ("ETF – Exchange-Traded Fund", "A basket of securities — equities, bonds, or commodities — that trades on an exchange like a single stock throughout the day. ETFs typically track an index passively at very low cost. UCITS ETFs layer an EU regulatory wrapper, while US-listed ETFs follow SEC rules. Thematic and actively managed ETFs are a fast-growing subset of the universe."),
    ("Yield Curve", "A chart plotting interest rates on government bonds across different maturities at a point in time. A normal curve slopes upward — long rates exceed short rates. An inverted yield curve, where short-term rates are higher than long-term rates, has historically predicted recessions and is closely watched by macro investors and central banks alike."),
    ("AUM – Assets Under Management", "The total market value of all investments a firm manages on behalf of clients. AUM directly drives fee revenue and is the standard measure of a fund manager's scale and market position. Global asset-management AUM exceeds $100 trillion. Rapid AUM growth can paradoxically hurt performance as large funds struggle to deploy capital without moving markets."),
    ("Sharpe Ratio", "A risk-adjusted performance metric calculated as (Portfolio Return − Risk-Free Rate) ÷ Standard Deviation. A ratio above 1 is considered good; above 2 is excellent. It rewards high returns while penalising high volatility, making it the standard tool for comparing strategies that carry different risk profiles. The Sortino Ratio is a variant that penalises only downside volatility."),
    ("DeFi – Decentralised Finance", "Financial services — lending, borrowing, spot trading, yield farming — delivered through smart contracts on public blockchains without traditional intermediaries. Ethereum hosts the majority of DeFi activity. The model is permissionless and non-custodial, meaning no KYC and users retain control of their keys. Smart-contract bugs, liquidity crises, and regulatory uncertainty remain major risks."),
    ("KYC – Know Your Customer", "Mandatory identity-verification process that financial institutions use to confirm client identity and assess financial crime risk before onboarding. Typical steps include government ID verification, proof of address, and a risk questionnaire. Regulators impose heavy fines for KYC failures, making it a core compliance obligation for banks, brokers, and increasingly crypto exchanges."),
    ("Liquidity", "How quickly an asset can be converted to cash at or near its fair market price without materially moving that price. Cash is perfectly liquid; commercial real estate is highly illiquid. Liquidity risk — being unable to exit a position without accepting a steep discount — is a central concern in portfolio construction and institutional risk management, especially during market stress."),
    ("Volatility", "The degree of price variation over time, typically measured as annualised standard deviation of returns. High volatility signals greater uncertainty and implies both higher risk and potential reward. The CBOE VIX Index, tracking implied volatility of S&P 500 options 30 days out, serves as Wall Street's real-time 'fear gauge' and spikes during market stress events."),
    ("P/E Ratio – Price to Earnings", "A valuation metric equal to a company's share price divided by its annual earnings per share. A P/E of 20× means the market pays $20 for each $1 of annual earnings. Useful for comparing similarly structured businesses within one sector. The forward P/E uses next year's expected earnings; both are meaningless for loss-making companies or across very different industries."),
    ("Duration", "A bond's price sensitivity to interest rate changes, expressed in years. A duration of 5 means a 1 percentage-point rise in rates reduces the bond's price by approximately 5%. Longer-dated bonds have higher duration and thus greater interest-rate risk. Portfolio managers actively manage duration — shortening it when they expect rates to rise, lengthening it when they expect cuts."),
    ("IPO – Initial Public Offering", "A private company's first sale of equity shares to public investors on a stock exchange. Companies raise primary capital; early shareholders achieve liquidity. Investment banks underwrite and price the offering through a bookbuilding process. Insiders are typically subject to a lock-up period of 90 to 180 days after listing before they can sell their shares."),
    ("Staking", "Locking cryptocurrency tokens in a Proof-of-Stake blockchain network to help validate transactions and maintain network security, earning newly minted tokens as reward. Conceptually similar to earning interest on a deposit. Ethereum's annualised staking yield currently sits around 3–4%, though rates vary across networks and liquid staking protocols let users remain liquid while staking."),
    ("Open Banking", "A system that enables banks to share customer financial data with authorised third-party providers via secure APIs, with explicit customer consent. It powers account aggregation apps, instant credit scoring, and one-click payment initiation. Mandated by regulation in the UK (Open Banking Standard) and EU (PSD2); expanding through market forces in India, UAE, and the US."),
    ("CAGR – Compound Annual Growth Rate", "The smoothed annual rate at which an investment grows over a multi-year period: CAGR = (End Value ÷ Start Value)^(1/n) − 1, where n is the number of years. Because it eliminates year-to-year fluctuations, CAGR is the preferred metric for communicating long-run fund or business performance. It answers the question: what constant annual rate would produce the same result?"),
    ("Drawdown", "The peak-to-trough decline in portfolio value over a given period. Maximum Drawdown captures the worst historical loss from any peak — a key risk metric for evaluating strategies. Crucially, a 30% drawdown requires a 43% gain just to recover to flat, illustrating the asymmetric mathematics of losses and why limiting downside powerfully compounds into long-run returns."),
    ("Tokenisation", "Converting rights to a real-world asset — real estate, government bonds, private equity, fine art — into digital tokens on a blockchain. Tokenisation enables fractional ownership, near-instant settlement, and 24/7 global trading of assets that are traditionally illiquid or inaccessible to retail investors. Regulators in the UAE, Singapore, and EU are actively developing frameworks for tokenised asset issuance."),
    ("Carry Trade", "Borrowing in a low-interest-rate currency (e.g., Japanese yen) and investing the proceeds in a higher-yielding currency or asset. Profit equals the interest rate differential minus financing and hedging costs. The key risk: adverse currency moves can swiftly erase the accumulated carry income, particularly during risk-off episodes when high-yield currencies depreciate sharply against funding currencies."),
    ("Basis Points (bps)", "A unit of measure equal to 0.01 percentage point, used to express small changes in interest rates, bond yields, and credit spreads without ambiguity. 100 bps equals 1 percentage point. When a central bank hikes by 25 bps it raises its benchmark rate by 0.25%. Using bps avoids confusion between additive and multiplicative percentage changes."),
    ("Robo-Advisor", "A digital platform that automates portfolio construction and ongoing rebalancing using algorithms — typically applying Modern Portfolio Theory with low-cost index ETFs. Annual fees run 0.20–0.50% versus 1%+ for human advisors. Leading platforms include Betterment and Wealthfront in the US, and Groww and Scripbox in India. Hybrid models pair the algorithm with access to a human advisor for complex needs."),
    ("Repo Rate", "The rate at which a central bank lends short-term funds to commercial banks against collateral. Raising the repo rate makes credit costlier across the economy, cooling inflation; cutting it stimulates borrowing and growth. In India, the Reserve Bank of India's repo rate is the primary monetary policy signalling tool; the US equivalent is the Federal Funds Rate."),
    ("AML – Anti-Money Laundering", "Laws, controls, and procedures designed to detect and prevent criminals from disguising illicit proceeds as legitimate income. Obligations include transaction monitoring, filing Suspicious Activity Reports (SARs), and enhanced due diligence for high-risk clients and jurisdictions. Global regulators levy multibillion-dollar fines for AML failures each year, making AML compliance a top priority for any financial institution."),
    ("Market Maker", "A firm or individual that continuously quotes both a buy (bid) and sell (ask) price for a security, profiting from the spread between the two. Market makers provide the liquidity that allows buyers and sellers to transact promptly without waiting for a counterparty. They play critical roles in equities, foreign exchange, bond markets, and increasingly in cryptocurrency trading."),
    ("Impermanent Loss", "A risk specific to liquidity providers in decentralised exchange automated market makers (AMMs). When the relative price of the two pooled tokens changes, the LP ends up holding less value than if the tokens had simply been held in a wallet. The loss is 'impermanent' only if prices fully revert to the original ratio — in practice, it often is not."),
    ("Dark Pool", "A private trading venue where large institutional orders execute away from public exchanges, keeping order details hidden until after execution. This protects big block orders from moving the market against the institution before the trade completes. Dark pools account for roughly 15% of US equity trading volume and are subject to varying post-trade reporting requirements by jurisdiction."),
]

# ── RSS Sources ────────────────────────────────────────
SOURCES = {
    "wealth": {
        "label": "Wealth",
        "icon": "💰",
        "color": "#10B981",
        "color_bg": "#ECFDF5",
        "has_subsections": True,
        "subsections": {
            "strategy_portfolios": {
                "label": "Strategy & Portfolios",
                "feeds": [
                    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
                    ("LiveMint Markets", "https://www.livemint.com/rss/markets"),
                    ("ET Wealth", "https://economictimes.indiatimes.com/wealth/rssfeeds/837555174.cms"),
                    ("Bloomberg Markets", "https://feeds.bloomberg.com/markets/news.rss"),
                ],
            },
            "bonds": {
                "label": "Bonds",
                "feeds": [
                    ("CNBC Finance", "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
                    ("ET Markets", "https://economictimes.indiatimes.com/markets/bonds/rssfeeds/1652862.cms"),
                    ("Reuters Finance", "https://feeds.reuters.com/reuters/financials"),
                ],
            },
            "ucits_etfs": {
                "label": "UCITS ETFs",
                "feeds": [
                    ("ETF Stream", "https://www.etfstream.com/feed/"),
                    ("Citywire", "https://citywire.com/rss"),
                    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
                ],
            },
        },
    },
    "trade": {
        "label": "Trade",
        "icon": "📊",
        "color": "#3B82F6",
        "color_bg": "#EFF6FF",
        "has_subsections": True,
        "subsections": {
            "stocks_etfs": {
                "label": "Stocks & ETFs",
                "feeds": [
                    ("ET Markets", "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms"),
                    ("LiveMint Markets", "https://www.livemint.com/rss/markets"),
                    ("CNBC Finance", "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
                ],
            },
            "crypto": {
                "label": "Crypto",
                "feeds": [
                    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
                    ("Cointelegraph", "https://cointelegraph.com/rss"),
                    ("ET Crypto", "https://economictimes.indiatimes.com/tech/cryptocurrency/rssfeeds/103567081.cms"),
                ],
            },
            "margin": {
                "label": "Margin",
                "feeds": [
                    ("Finance Magnates", "https://www.financemagnates.com/feed/"),
                    ("Reuters Finance", "https://feeds.reuters.com/reuters/financials"),
                ],
            },
            "cfds": {
                "label": "CFDs",
                "feeds": [
                    ("Finance Magnates", "https://www.financemagnates.com/feed/"),
                    ("FXStreet", "https://www.fxstreet.com/rss/news"),
                    ("LeapRate", "https://www.leaprate.com/feed/"),
                ],
            },
        },
    },
    "ai": {
        "label": "AI",
        "icon": "🤖",
        "color": "#8B5CF6",
        "color_bg": "#F5F3FF",
        "has_subsections": False,
        "feeds": [
            ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
            ("VentureBeat AI", "https://venturebeat.com/ai/feed/"),
            ("MIT Tech Review", "https://www.technologyreview.com/feed/"),
            ("The Verge AI", "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"),
        ],
    },
    "companies": {
        "label": "Companies",
        "icon": "🏢",
        "color": "#F59E0B",
        "color_bg": "#FFFBEB",
        "has_subsections": False,
        "feeds": [
            ("TechCrunch", "https://techcrunch.com/feed/"),
            ("Crunchbase News", "https://news.crunchbase.com/feed/"),
            ("ET Companies", "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms"),
            ("FintechNews UAE", "https://fintechnews.ae/feed/"),
            ("Arabian Business", "https://www.arabianbusiness.com/rss/"),
        ],
    },
    "product": {
        "label": "Product",
        "icon": "🚀",
        "color": "#EC4899",
        "color_bg": "#FDF2F8",
        "has_subsections": False,
        "feeds": [
            ("Mind the Product", "https://www.mindtheproduct.com/feed/"),
            ("TechCrunch Apps", "https://techcrunch.com/category/apps/feed/"),
            ("Product Hunt", "https://www.producthunt.com/feed"),
            ("First Round Review", "https://review.firstround.com/feed"),
        ],
    },
}

ITEMS_PER_SUBSECTION = 3
ITEMS_PER_SECTION = 5


# ── Helpers ───────────────────────────────────────────
def get_entry_summary(entry):
    for field in ("summary", "description"):
        val = entry.get(field, "")
        if val:
            return val
    content = entry.get("content", [])
    if content:
        return content[0].get("value", "")
    return ""


def clean(text, max_words=None):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if max_words:
        words = text.split()
        if len(words) > max_words:
            return " ".join(words[:max_words]) + "…"
    return text


def fetch_feeds(feeds, max_items):
    items = []
    for source_name, url in feeds:
        if len(items) >= max_items:
            break
        try:
            feed = feedparser.parse(
                url,
                request_headers={"User-Agent": "Mozilla/5.0 (compatible; MorningDigest/2.0)"},
            )
            for entry in feed.entries[:3]:
                title = clean(entry.get("title", ""))
                summary = clean(get_entry_summary(entry), max_words=100)
                link = entry.get("link", "#")
                if title:
                    items.append(
                        {"title": title, "summary": summary, "link": link, "source": source_name}
                    )
                if len(items) >= max_items:
                    break
        except Exception as e:
            print(f"  [Error] {source_name}: {e}")
    return items


# ── HTML builders ─────────────────────────────────────
def build_cards(items):
    if not items:
        return '<p class="empty-state">No articles available right now.</p>'
    cards = ""
    for item in items:
        summary_html = (
            f'<p class="card-summary">{html.escape(item["summary"])}</p>'
            if item["summary"]
            else ""
        )
        safe_link = html.escape(item["link"])
        cards += f"""
            <article class="card">
              <span class="card-source">{html.escape(item['source'])}</span>
              <a href="{safe_link}" target="_blank" rel="noopener" class="card-title">{html.escape(item['title'])}</a>
              {summary_html}
              <a href="{safe_link}" target="_blank" rel="noopener" class="card-read-more">Read full article →</a>
            </article>"""
    return f'<div class="cards-grid">{cards}\n          </div>'


def build_section_html(key, section, data):
    color = section["color"]
    color_bg = section["color_bg"]
    style = f'style="--section-color:{color}; --section-color-bg:{color_bg};"'

    if section["has_subsections"]:
        total = sum(len(v) for v in data.values())
        body = ""
        for sub_key, sub_config in section["subsections"].items():
            items = data.get(sub_key, [])
            body += f"""
          <div class="subsection">
            <h3 class="subsection-title">{html.escape(sub_config['label'])}</h3>
            {build_cards(items)}
          </div>"""
    else:
        items = data
        total = len(items)
        body = build_cards(items)

    return f"""
      <section class="section-block" id="{key}" {style}>
        <div class="section-header">
          <span class="section-icon">{section['icon']}</span>
          <h2 class="section-title">{html.escape(section['label'])}</h2>
          <span class="section-count">{total} articles</span>
        </div>
        {body}
      </section>"""


def build_vocab_html(term, definition):
    return f"""
      <section class="section-block" id="vocabulary" style="--section-color:#6366F1; --section-color-bg:#EEF2FF;">
        <div class="section-header">
          <span class="section-icon">📚</span>
          <h2 class="section-title">Vocabulary</h2>
          <span class="section-count">Term of the Day</span>
        </div>
        <div class="vocab-card">
          <p class="vocab-label">Term of the Day</p>
          <h3 class="vocab-term">{html.escape(term)}</h3>
          <p class="vocab-definition">{html.escape(definition)}</p>
        </div>
      </section>"""


def build_full_html(all_data, vocab_term, vocab_definition):
    sections_html = ""
    nav_links = ""

    for key, section in SOURCES.items():
        data = all_data.get(key, {} if section["has_subsections"] else [])
        sections_html += build_section_html(key, section, data)
        nav_links += f'<a href="#{key}">{section["icon"]} {html.escape(section["label"])}</a>\n      '

    nav_links += '<a href="#vocabulary">📚 Vocabulary</a>'
    sections_html += build_vocab_html(vocab_term, vocab_definition)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Morning Digest — {html.escape(today_str)}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #F8FAFC;
      --surface: #FFFFFF;
      --border: #E2E8F0;
      --text-primary: #0F172A;
      --text-secondary: #475569;
      --text-muted: #94A3B8;
      --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
      --shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
      --shadow-hover: 0 6px 20px rgba(0,0,0,0.10), 0 2px 6px rgba(0,0,0,0.06);
      --radius: 12px;
      --section-color: #64748B;
      --section-color-bg: #F8FAFC;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg);
      color: var(--text-primary);
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }}

    /* Header */
    header {{
      background: #FFFFFF;
      border-bottom: 1px solid var(--border);
      padding: 16px 24px;
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: var(--shadow-sm);
    }}
    .header-inner {{
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      gap: 14px;
    }}
    .header-sun {{ font-size: 28px; line-height: 1; }}
    .header-title {{ font-size: 19px; font-weight: 700; color: #0F172A; letter-spacing: -0.4px; }}
    .header-date {{ font-size: 12.5px; color: var(--text-muted); margin-top: 2px; }}

    /* Navigation */
    nav {{
      background: #FFFFFF;
      border-bottom: 1px solid var(--border);
      padding: 0 24px;
      position: sticky;
      top: 65px;
      z-index: 99;
    }}
    .nav-inner {{
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      overflow-x: auto;
      scrollbar-width: none;
    }}
    .nav-inner::-webkit-scrollbar {{ display: none; }}
    .nav-inner a {{
      text-decoration: none;
      color: var(--text-secondary);
      font-size: 13px;
      font-weight: 500;
      padding: 13px 14px;
      white-space: nowrap;
      border-bottom: 2px solid transparent;
      transition: color 0.15s, border-color 0.15s;
      display: flex;
      align-items: center;
      gap: 5px;
    }}
    .nav-inner a:hover {{
      color: #0F172A;
      border-bottom-color: #CBD5E1;
    }}

    /* Main */
    main {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 36px 24px 56px;
    }}

    /* Section */
    .section-block {{
      margin-bottom: 52px;
      scroll-margin-top: 140px;
    }}
    .section-header {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding-bottom: 14px;
      margin-bottom: 24px;
      border-bottom: 2px solid var(--section-color);
    }}
    .section-icon {{ font-size: 24px; }}
    .section-title {{ font-size: 20px; font-weight: 700; color: #0F172A; letter-spacing: -0.3px; }}
    .section-count {{
      margin-left: auto;
      font-size: 11px;
      color: var(--text-muted);
      background: var(--bg);
      border: 1px solid var(--border);
      padding: 3px 10px;
      border-radius: 20px;
      font-weight: 500;
    }}

    /* Subsections */
    .subsection {{ margin-bottom: 28px; }}
    .subsection-title {{
      font-size: 10.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--text-muted);
      margin-bottom: 14px;
    }}

    /* Cards */
    .cards-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 16px;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 18px 20px;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
      gap: 9px;
      transition: box-shadow 0.2s ease, transform 0.2s ease;
    }}
    .card:hover {{
      box-shadow: var(--shadow-hover);
      transform: translateY(-2px);
    }}
    .card-source {{
      display: inline-flex;
      align-items: center;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.7px;
      color: var(--section-color);
      background: var(--section-color-bg);
      padding: 3px 9px;
      border-radius: 20px;
      width: fit-content;
    }}
    .card-title {{
      font-size: 14.5px;
      font-weight: 600;
      color: #0F172A;
      text-decoration: none;
      line-height: 1.45;
      display: block;
    }}
    .card-title:hover {{ color: var(--section-color); }}
    .card-summary {{
      font-size: 13px;
      color: var(--text-secondary);
      line-height: 1.65;
      flex: 1;
    }}
    .card-read-more {{
      font-size: 12px;
      font-weight: 500;
      color: var(--section-color);
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 2px;
      margin-top: 2px;
      opacity: 0.85;
    }}
    .card-read-more:hover {{ opacity: 1; text-decoration: underline; }}
    .empty-state {{ color: var(--text-muted); font-size: 14px; padding: 16px 0; }}

    /* Vocabulary */
    .vocab-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-left: 4px solid var(--section-color);
      border-radius: var(--radius);
      padding: 28px 32px;
      max-width: 840px;
      box-shadow: var(--shadow);
    }}
    .vocab-label {{
      font-size: 10.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--section-color);
      margin-bottom: 8px;
    }}
    .vocab-term {{ font-size: 21px; font-weight: 700; color: #0F172A; margin-bottom: 14px; letter-spacing: -0.4px; }}
    .vocab-definition {{ font-size: 14.5px; color: var(--text-secondary); line-height: 1.75; }}

    /* Footer */
    footer {{
      background: #FFFFFF;
      border-top: 1px solid var(--border);
      text-align: center;
      padding: 22px 24px;
      color: var(--text-muted);
      font-size: 12px;
      line-height: 1.6;
    }}

    /* Responsive */
    @media (max-width: 640px) {{
      header {{ padding: 12px 16px; }}
      nav {{ top: 57px; }}
      main {{ padding: 24px 16px 40px; }}
      .cards-grid {{ grid-template-columns: 1fr; }}
      .vocab-card {{ padding: 20px; }}
      .section-title {{ font-size: 17px; }}
    }}
  </style>
</head>
<body>

  <header>
    <div class="header-inner">
      <span class="header-sun">☀️</span>
      <div>
        <div class="header-title">Morning Digest</div>
        <div class="header-date">{html.escape(today_str)}</div>
      </div>
    </div>
  </header>

  <nav>
    <div class="nav-inner">
      {nav_links}
    </div>
  </nav>

  <main>
    {sections_html}
  </main>

  <footer>
    <p>Auto-generated daily at 8:00 AM IST</p>
    <p style="margin-top:4px;">Sources: Economic Times · LiveMint · Bloomberg · TechCrunch · Crunchbase · FintechNews.ae · Arabian Business · Reuters · CNBC · CoinDesk · Cointelegraph &amp; more</p>
  </footer>

</body>
</html>"""


# ── Main ──────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🚀 Morning Digest — {today_str}")

    vocab_term, vocab_definition = VOCABULARY[day_of_year % len(VOCABULARY)]
    print(f"📚 Vocabulary: {vocab_term}")

    all_data = {}
    for key, section in SOURCES.items():
        print(f"\n📰 [{section['label']}]")
        if section["has_subsections"]:
            all_data[key] = {}
            for sub_key, sub_config in section["subsections"].items():
                items = fetch_feeds(sub_config["feeds"], ITEMS_PER_SUBSECTION)
                all_data[key][sub_key] = items
                print(f"   ↳ {sub_config['label']}: {len(items)} articles")
        else:
            items = fetch_feeds(section["feeds"], ITEMS_PER_SECTION)
            all_data[key] = items
            print(f"   ↳ {len(items)} articles")

    html_content = build_full_html(all_data, vocab_term, vocab_definition)

    os.makedirs("docs", exist_ok=True)

    for path in ["index.html", "docs/index.html", f"docs/{now.strftime('%Y-%m-%d')}.html"]:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"✅ Written: {os.path.abspath(path)}")
