import re
import requests
import xml.etree.ElementTree as ET
import yfinance as yf
from firecrawl.v1 import V1FirecrawlApp as FirecrawlApp
from config import FIRECRAWL_API_KEY, REDDIT_SUBREDDITS, NEWS_URLS

BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
ATOM_NS = "http://www.w3.org/2005/Atom"


def scrape_reddit():
    posts = []
    for sub in REDDIT_SUBREDDITS:
        try:
            url = f"https://www.reddit.com/r/{sub}/.rss"
            r = requests.get(url, headers={"User-Agent": BROWSER_UA}, timeout=10)
            r.raise_for_status()
            root = ET.fromstring(r.text)
            for entry in root.findall(f"{{{ATOM_NS}}}entry")[:25]:
                title_el = entry.find(f"{{{ATOM_NS}}}title")
                link_el = entry.find(f"{{{ATOM_NS}}}link")
                content_el = entry.find(f"{{{ATOM_NS}}}content")
                title = title_el.text if title_el is not None else ""
                link = link_el.get("href", "") if link_el is not None else ""
                raw = content_el.text or "" if content_el is not None else ""
                text = re.sub(r"<[^>]+>", " ", raw)[:400].strip()
                posts.append({
                    "source": f"r/{sub}",
                    "title": title,
                    "text": text,
                    "score": 0,
                    "url": link,
                })
            print(f"Reddit r/{sub}: {len(root.findall(f'{{{ATOM_NS}}}entry'))} posts")
        except Exception as e:
            print(f"Reddit r/{sub} failed: {e}")
    return posts


def scrape_news():
    app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
    articles = []
    for url in NEWS_URLS:
        try:
            result = app.scrape_url(url, formats=["markdown"])
            content = (result.markdown or "")[:4000]
            articles.append({"url": url, "content": content})
            print(f"Scraped: {url}")
        except Exception as e:
            print(f"Firecrawl failed for {url}: {e}")
    return articles


def get_ticker_data(tickers):
    data = {}
    for symbol in tickers:
        try:
            t = yf.Ticker(symbol)
            fi = t.fast_info

            curr = getattr(fi, "last_price", None) or getattr(fi, "regularMarketPrice", None)
            prev = getattr(fi, "previous_close", None) or getattr(fi, "regularMarketPreviousClose", None)

            if curr and prev and prev > 0:
                change_pct = round(((curr - prev) / prev) * 100, 2)
            else:
                change_pct = 0.0

            curr = round(float(curr), 2) if curr else 0.0

            raw_news = getattr(t, "news", []) or []
            news = [
                {"title": n.get("title", ""), "url": n.get("link", n.get("url", ""))}
                for n in raw_news[:4]
                if n.get("title")
            ]

            data[symbol] = {"price": curr, "change_pct": change_pct, "news": news}
            print(f"{symbol}: ${curr} ({change_pct:+.2f}%)")
        except Exception as e:
            print(f"yfinance failed for {symbol}: {e}")
            data[symbol] = {"price": 0.0, "change_pct": 0.0, "news": []}
    return data


def scrape_ticker_pages(tickers):
    """Scrape Yahoo Finance quote + news page for each personal ticker."""
    app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
    data = {}
    for symbol in tickers:
        pages = []
        for url in [
            f"https://finance.yahoo.com/quote/{symbol}/",
            f"https://finance.yahoo.com/quote/{symbol}/news/",
        ]:
            try:
                result = app.scrape_url(url, formats=["markdown"])
                content = (result.markdown or "")[:3000]
                if content:
                    pages.append(content)
            except Exception as e:
                print(f"  Firecrawl {symbol} ({url}): {e}")
        data[symbol] = "\n\n".join(pages)
        print(f"  Scraped ticker page: {symbol} ({sum(len(p) for p in pages)} chars)")
    return data


def get_analyst_ratings(tickers):
    """Pull analyst consensus and recommendations from yfinance."""
    ratings = {}
    for symbol in tickers:
        try:
            t = yf.Ticker(symbol)
            info = t.info or {}
            rec = info.get("recommendationKey", "")        # strongBuy / buy / hold / sell
            mean_target = info.get("targetMeanPrice")
            num_analysts = info.get("numberOfAnalystOpinions", 0)
            description = info.get("longBusinessSummary", "")[:600]
            sector = info.get("sector", "")
            industry = info.get("industry", "")
            ratings[symbol] = {
                "recommendation": rec,
                "target_price": round(float(mean_target), 2) if mean_target else None,
                "num_analysts": num_analysts,
                "description": description,
                "sector": sector,
                "industry": industry,
            }
        except Exception as e:
            print(f"  Analyst ratings failed for {symbol}: {e}")
            ratings[symbol] = {
                "recommendation": "",
                "target_price": None,
                "num_analysts": 0,
                "description": "",
                "sector": "",
                "industry": "",
            }
    return ratings


def get_ticker_fundamentals(tickers):
    """Extended data for buy-opportunity analysis: 52w range, moving averages, volume."""
    data = {}
    for symbol in tickers:
        try:
            t = yf.Ticker(symbol)
            fi = t.fast_info

            curr = float(getattr(fi, "last_price", 0) or 0)
            year_high = float(getattr(fi, "year_high", 0) or 0)
            year_low = float(getattr(fi, "year_low", 0) or 0)
            fifty_day_avg = float(getattr(fi, "fifty_day_average", 0) or 0)
            two_hundred_day_avg = float(getattr(fi, "two_hundred_day_average", 0) or 0)
            three_month_vol = float(getattr(fi, "three_month_average_volume", 0) or 0)
            last_vol = float(getattr(fi, "last_volume", 0) or 0)

            pct_from_high = round(((curr - year_high) / year_high) * 100, 1) if year_high > 0 else 0
            pct_from_low = round(((curr - year_low) / year_low) * 100, 1) if year_low > 0 else 0
            vol_ratio = round(last_vol / three_month_vol, 2) if three_month_vol > 0 else 1.0

            data[symbol] = {
                "price": round(curr, 2),
                "year_high": round(year_high, 2),
                "year_low": round(year_low, 2),
                "pct_from_high": pct_from_high,
                "pct_from_low": pct_from_low,
                "fifty_day_avg": round(fifty_day_avg, 2),
                "two_hundred_day_avg": round(two_hundred_day_avg, 2),
                "volume_ratio": vol_ratio,
            }
        except Exception as e:
            print(f"Fundamentals failed for {symbol}: {e}")
    return data
