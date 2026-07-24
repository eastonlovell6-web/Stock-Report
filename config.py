import os

PORTFOLIO_TICKERS = ["DRAM", "SOFI", "ZETA", "NBIS", "NOW", "CRWV", "AAOI", "NFLX", "HUT", "INTC"]
WATCHLIST_TICKERS = ["IONQ", "SMCI", "UBER", "OUST", "OKLO"]
RECIPIENT_EMAIL = "eastonlovell6@gmail.com"
SENDER_EMAIL = "eastonlovell6@gmail.com"

REDDIT_SUBREDDITS = ["wallstreetbets", "stocks", "investing", "StockMarket"]

NEWS_URLS = [
    "https://finance.yahoo.com/topic/stock-market-news/",
    "https://www.marketwatch.com/latest-news",
    "https://www.cnbc.com/markets/",
    "https://www.reuters.com/business/finance/",
    "https://www.benzinga.com/markets/",
    "https://stocktwits.com/trending",
]

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
