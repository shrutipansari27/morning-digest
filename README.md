# 🌅 Morning Digest

Daily fintech, investing, India markets, MENA, and product management news — auto-published to GitHub Pages every morning at **08:00 UAE time**.

## Quick Setup (first time only) #hello

```bash
cd morning-digest
bash setup.sh
```

This requires the [GitHub CLI](https://cli.github.com) to be installed and logged in.

## What it covers

| Section | Sources |
|---|---|
| 🏦 Fintech & Neobanks | TechCrunch, Finextra, Tearsheet, The Financial Brand |
| 📈 Investing & Wealth | Reuters, CNBC Finance, Seeking Alpha |
| 🇮🇳 India Markets | Economic Times, Moneycontrol, LiveMint |
| 🌍 MENA / UAE | Arabian Business, Zawya, Gulf News, Khaleej Times |
| 🧠 Product Management | Mind the Product, Product Hunt, First Round Review, Lenny's |
| 💡 Tech & Innovation | The Verge, Stratechery, MIT Tech Review |

## Manual trigger

Go to **Actions → Morning Digest — Daily Update → Run workflow** in your GitHub repo to generate a fresh digest on demand.

## How it works

1. GitHub Actions runs `scripts/fetch_news.py` every day at 04:00 UTC (08:00 UAE)
2. The script reads RSS feeds from all sources
3. Generates a dark-mode dashboard at `docs/index.html`
4. Commits and pushes — GitHub Pages serves the update instantly
