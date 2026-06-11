from config import PORTFOLIO_TICKERS, WATCHLIST_TICKERS
from scraper import (
    scrape_reddit, scrape_news, get_ticker_data,
    get_ticker_fundamentals, scrape_ticker_pages, get_analyst_ratings,
)
from analyzer import analyze, find_buy_opportunities, analyze_personal_tickers
from email_builder import build
from sender import send


def run():
    all_personal = PORTFOLIO_TICKERS + WATCHLIST_TICKERS

    print("1/7 Scraping Reddit...")
    reddit_posts = scrape_reddit()
    print(f"   Got {len(reddit_posts)} posts")

    print("2/7 Scraping news sites...")
    news_articles = scrape_news()
    print(f"   Got {len(news_articles)} articles")

    print("3/7 Fetching portfolio ticker data...")
    ticker_data = get_ticker_data(all_personal)
    print(f"   Got data for {len(ticker_data)} tickers")

    print("4/7 Analyzing market with Claude...")
    analysis = analyze(reddit_posts, news_articles)
    top_tickers = analysis.get("top_tickers", [])
    print(f"   Market mood: {analysis.get('market_mood')}")
    print(f"   Top tickers: {[t['ticker'] for t in top_tickers]}")

    print("5/7 Deep-diving your personal tickers...")
    ticker_pages = scrape_ticker_pages(all_personal)
    analyst_ratings = get_analyst_ratings(all_personal)
    ticker_analysis = analyze_personal_tickers(
        all_personal, ticker_data, analyst_ratings, ticker_pages, reddit_posts
    )
    print(f"   Analyzed: {list(ticker_analysis.keys())}")

    print("6/7 Finding buy opportunities...")
    mentioned_symbols = [t["ticker"] for t in top_tickers]
    fundamentals = get_ticker_fundamentals(mentioned_symbols)
    buy_opps = find_buy_opportunities(top_tickers, fundamentals)
    print(f"   Picks: {[b['ticker'] for b in buy_opps]}")

    print("7/7 Building and sending email...")
    html = build(
        analysis, ticker_data,
        PORTFOLIO_TICKERS, WATCHLIST_TICKERS,
        buy_opps, ticker_analysis,
    )
    send(html)
    print("Done.")


if __name__ == "__main__":
    run()
