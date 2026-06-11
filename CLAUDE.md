# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Python script that runs every weekday at 7am MT (via GitHub Actions) to scrape financial news and Reddit, analyze it with Claude, then email an HTML market brief to the owner.

## Running Locally

```bash
# Install dependencies (use .venv)
pip install -r requirements.txt

# Required env vars
export FIRECRAWL_API_KEY=...
export ANTHROPIC_API_KEY=...
export GMAIL_APP_PASSWORD=...

# Run the full pipeline
python main.py
```

There are no tests and no lint configuration.

## Architecture

The pipeline in `main.py` runs 7 steps in sequence:

1. **`scraper.py`** — Data collection
   - `scrape_reddit()`: Fetches RSS feeds from 4 subreddits (wallstreetbets, stocks, investing, StockMarket), up to 25 posts each
   - `scrape_news()`: Uses Firecrawl to scrape 6 financial news URLs
   - `get_ticker_data()`: Pulls price/change/news for portfolio+watchlist tickers via yfinance
   - `scrape_ticker_pages()`: Firecrawl scrapes Yahoo Finance quote + news pages per ticker
   - `get_analyst_ratings()`: Pulls analyst consensus data via yfinance
   - `get_ticker_fundamentals()`: Pulls 52w range, moving averages, volume for trending tickers

2. **`analyzer.py`** — Claude Haiku (`claude-haiku-4-5-20251001`) analysis
   - `analyze()`: Takes all Reddit posts + news, returns JSON with `top_tickers`, `top_news`, `trending_topics`, `market_mood`
   - `analyze_personal_tickers()`: One API call per portfolio/watchlist ticker — returns verdict (strong_buy → strong_sell), sentiment, catalyst, summary
   - `find_buy_opportunities()`: Given top trending tickers + their fundamentals, picks 3-5 best setups with thesis and risk

3. **`email_builder.py`** — Pure HTML string construction, no external dependencies. Returns a full HTML document with 7 sections: most-mentioned tickers, top news, trending topics, portfolio prices, watchlist prices, analyst deep-dive, buy opportunities.

4. **`sender.py`** — Sends via Gmail SMTP using an App Password.

5. **`config.py`** — Portfolio tickers, watchlist tickers, subreddits, news URLs, and env-var API keys. Edit tickers here.

## Deployment

Automated via `.github/workflows/daily_report.yml`. Runs Mon–Fri at 13:00 UTC (7am MDT). Requires three GitHub Actions secrets: `FIRECRAWL_API_KEY`, `ANTHROPIC_API_KEY`, `GMAIL_APP_PASSWORD`. Can be manually triggered via `workflow_dispatch`.

## Key Design Decisions

- All Claude calls use `claude-haiku-4-5-20251001` for cost efficiency — responses are pure JSON (no markdown wrapper).
- JSON is extracted from Claude responses using `text.find("{")` / `text.rfind("}")` rather than strict parsing, to tolerate minor formatting variation.
- Each failure in scraping/analysis is caught and logged individually — the pipeline continues even if individual tickers or sources fail.
- Reddit is fetched via RSS (no API key needed); Firecrawl handles the paywalled/JS-heavy news sites.
