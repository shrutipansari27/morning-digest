# Morning Digest

A daily intelligence briefing focused on fintech, global markets, trading, and AI — auto-published to GitHub Pages every morning at **08:00 IST (06:30 UAE / 02:30 UTC)**.

Live site: [shrutipansari27.github.io/morning-digest](https://shrutipansari27.github.io/morning-digest)

---

## Content Structure

The digest is divided into six sections. Each section has a deliberate editorial scope — articles outside that scope are filtered out automatically.

### Wealth
Personal finance, investment strategy, and asset management news with a specific focus on the UAE and broader MENA fintech ecosystem.

| Subsection | What it covers |
|---|---|
| Wealth Management | Investment strategy, portfolio construction, fund performance, macro outlook, retail investor trends |
| Fintech & UAE Market | UAE fintech funding, DIFC/ADGM ecosystem, neobanks, payments, open banking, digital lending in the Gulf |
| Funds & ETFs | ETF launches and flows, mutual fund performance, passive vs active debate, fund manager moves |

### Trade
Global markets and instruments — structured around asset class, not geography.

| Subsection | What it covers |
|---|---|
| Global Indices | Nifty, Sensex, S&P 500, Dow, Nasdaq, FTSE 100, HKEX, Hang Seng — index moves, sector rotations, earnings season |
| Commodities & Precious Metals | Spot Gold (XAU/USD), Spot Silver (XAG/USD) via LBMA, crude oil (Brent/WTI), base metals |
| Crypto | Bitcoin, Ethereum, altcoins, DeFi, stablecoins, regulatory developments, on-chain data |
| CFDs & Margin | Retail and institutional brokerage, leverage products, FX, prop trading, platform news |

### AI
Artificial intelligence research, product launches, enterprise adoption, and policy — sourced from TechCrunch AI, VentureBeat, MIT Technology Review, and The Verge.

### Companies
Startup funding rounds, M&A, IPOs, and corporate strategy news — with emphasis on fintech, MENA, and India-based companies via Crunchbase, TechCrunch, FintechNews UAE, and Arabian Business.

### Product
Product management craft, consumer app launches, and growth strategy — from Mind the Product, Product Hunt, TechCrunch Apps, and First Round Review.

### Vocabulary
Five advanced fintech and markets terms every day, rotating through a 45-term library. Terms are pitched at practitioners — covering instruments, regulation, risk, and market structure (e.g., Delta Hedging, MiCA, MEV, Dispersion Trading, ISO 20022, Prime of Prime).

---

## Content Quality Rules

The following rules govern what gets published:

**Relevance filtering** — every article must contain at least one keyword relevant to its subsection. Articles that pass keyword matching but cover off-topic subjects (career advice, legal/personal matters, entertainment) are blocked by a secondary blocklist.

**Summary quality** — card previews and modal summaries always end at a sentence boundary. No trailing ellipsis. For paywalled articles where the full text cannot be retrieved, a "Read Full Article" redirect is shown instead.

**No nav contamination** — article bodies fetched from external pages are checked for navigation/boilerplate text (no sentence punctuation → discarded). Only genuine prose paragraphs of 20+ words are used.

---

## How it works

1. GitHub Actions runs `scripts/fetch_news.py` daily at 02:30 UTC (08:00 IST)
2. The script fetches RSS feeds for each subsection, filters by relevance keywords, and enriches short summaries by fetching article body text in parallel
3. Generates a static HTML digest at `docs/index.html` and `docs/YYYY-MM-DD.html`
4. Commits and pushes — GitHub Pages serves the update immediately

```
scripts/fetch_news.py   # fetch, filter, generate
docs/index.html         # today's digest (served by GitHub Pages)
docs/YYYY-MM-DD.html    # daily archive
```

---

## RSS Sources

| Section | Sources |
|---|---|
| Wealth Management | ET Wealth, Reuters Business, LiveMint Markets, Bloomberg Markets |
| Fintech & UAE | FintechNews UAE, Arabian Business, Gulf Business, Khaleej Times |
| Funds & ETFs | CNBC Investing, MarketWatch, CNBC Finance, Reuters Business |
| Global Indices | ET Markets, LiveMint Markets, CNBC Markets, Reuters Finance |
| Commodities | Metals Focus, Investing.com Gold, MarketWatch |
| Crypto | Finance Magnates Crypto, Decrypt, ET Crypto |
| CFDs & Margin | Finance Magnates, FXStreet, LeapRate |
| AI | TechCrunch AI, VentureBeat AI, MIT Tech Review, The Verge AI |
| Companies | TechCrunch, Crunchbase News, ET Companies, FintechNews UAE, Arabian Business |
| Product | Mind the Product, TechCrunch Apps, Product Hunt, First Round Review |

---

## Manual trigger

Go to **Actions → Morning Digest — Daily Update → Run workflow** in the GitHub repo to generate a fresh digest on demand.

## Local run

```bash
pip install feedparser
python scripts/fetch_news.py
open docs/index.html
```
