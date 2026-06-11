import json
import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _build_context(reddit_posts, news_articles):
    lines = ["=== REDDIT (sorted by score) ==="]
    for p in sorted(reddit_posts, key=lambda x: x["score"], reverse=True)[:35]:
        lines.append(f"[{p['source']}] {p['title']}")
        if p["text"]:
            lines.append(p["text"][:250])
        lines.append(f"URL: {p['url']}\n")

    lines.append("\n=== NEWS SITES ===")
    for a in news_articles:
        lines.append(f"[{a['url']}]")
        lines.append(a["content"][:600])
        lines.append("")

    return "\n".join(lines)


def analyze(reddit_posts, news_articles):
    context = _build_context(reddit_posts, news_articles)

    prompt = f"""You are analyzing today's stock market discussion from Reddit and financial news sites.

CONTENT:
{context}

Return ONLY valid JSON matching this exact schema — no markdown, no explanation:
{{
  "top_tickers": [
    {{
      "ticker": "NVDA",
      "mentions": 47,
      "sentiment": "bullish",
      "reason": "one short sentence why it's trending",
      "sources": ["r/wallstreetbets", "MarketWatch"]
    }}
  ],
  "top_news": [
    {{
      "headline": "Full headline text",
      "summary": "One sentence summary of why this matters",
      "url": "https://...",
      "source": "Reuters"
    }}
  ],
  "trending_topics": "2-3 sentences describing the dominant themes in today's market discussion",
  "market_mood": "bullish"
}}

Rules:
- top_tickers: 8 most-mentioned real stock tickers (not ETFs unless uniquely dominant), ranked by mention count
- top_news: 5 most important market-moving stories
- market_mood: one of: bullish, bearish, mixed
- Use real URLs from the content where possible
"""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2500,
        system="You are a financial data analyst. Return only valid JSON, nothing else.",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    text = msg.content[0].text.strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        print(f"JSON parse failed. Raw response:\n{text}")
        return {
            "top_tickers": [],
            "top_news": [],
            "trending_topics": "Analysis unavailable today.",
            "market_mood": "mixed",
        }


def analyze_personal_tickers(tickers, ticker_data, analyst_ratings, ticker_pages, reddit_posts):
    """
    For each personal portfolio/watchlist ticker, produce a professional analyst-style
    verdict: what people are saying, company health, buy/hold/sell recommendation.
    """
    results = {}

    for symbol in tickers:
        # Filter reddit posts that mention this ticker
        sym_lower = symbol.lower()
        mentions = [
            p for p in reddit_posts
            if sym_lower in p["title"].lower() or sym_lower in p["text"].lower()
            or f"${symbol}" in p["title"] or f"${symbol}" in p["text"]
        ]
        reddit_context = "\n".join(
            f"[{p['source']}] {p['title']}: {p['text'][:150]}"
            for p in mentions[:8]
        ) or "No direct Reddit mentions today."

        price_data = ticker_data.get(symbol, {})
        ratings = analyst_ratings.get(symbol, {})
        web_content = ticker_pages.get(symbol, "")[:2000]

        prompt = f"""You are a professional equity analyst. Write a concise analysis for ${symbol}.

PRICE DATA:
- Current price: ${price_data.get('price', 'N/A')}
- Today's change: {price_data.get('change_pct', 0):+.2f}%

ANALYST CONSENSUS (from Yahoo Finance):
- Recommendation: {ratings.get('recommendation') or 'N/A'}
- Mean price target: ${ratings.get('target_price') or 'N/A'} ({ratings.get('num_analysts', 0)} analysts)
- Sector: {ratings.get('sector', 'N/A')} | Industry: {ratings.get('industry', 'N/A')}

COMPANY DESCRIPTION:
{ratings.get('description') or 'N/A'}

WEB DATA (Yahoo Finance):
{web_content or 'N/A'}

REDDIT SENTIMENT:
{reddit_context}

Return ONLY valid JSON — no markdown, no explanation:
{{
  "verdict": "buy",
  "confidence": "high",
  "street_sentiment": "One sentence on what analysts and institutional investors think",
  "social_sentiment": "One sentence on what Reddit/retail traders are saying",
  "company_health": "2 sentences on the company's current business condition and trajectory",
  "key_catalyst": "The single most important upcoming event or risk that will move this stock",
  "summary": "2-3 sentence punchy analyst-style summary combining all of the above"
}}

verdict must be one of: strong_buy, buy, hold, sell, strong_sell
confidence must be one of: high, medium, low"""

        try:
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                system="You are a professional equity analyst. Return only valid JSON.",
                messages=[{"role": "user", "content": prompt}],
            )
            text = msg.content[0].text.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            results[symbol] = json.loads(text[start:end])
        except Exception as e:
            print(f"  Ticker analysis failed for {symbol}: {e}")
            results[symbol] = {
                "verdict": "hold",
                "confidence": "low",
                "street_sentiment": "N/A",
                "social_sentiment": "N/A",
                "company_health": "N/A",
                "key_catalyst": "N/A",
                "summary": "Analysis unavailable.",
            }

    return results


def find_buy_opportunities(top_tickers, fundamentals):
    """
    Given the day's most-mentioned tickers and their fundamentals,
    identify 3-5 that look like compelling buys from a professional investor POV.
    """
    if not fundamentals:
        return []

    ticker_lines = []
    for item in top_tickers:
        sym = item["ticker"]
        f = fundamentals.get(sym)
        if not f:
            continue
        ticker_lines.append(
            f"{sym}: price=${f['price']} | 52w_high=${f['year_high']} ({f['pct_from_high']}% off high) | "
            f"52w_low=${f['year_low']} ({f['pct_from_low']}% above low) | "
            f"50d_avg=${f['fifty_day_avg']} | 200d_avg=${f['two_hundred_day_avg']} | "
            f"vol_ratio={f['volume_ratio']}x (vs 3mo avg) | "
            f"mentions={item.get('mentions',0)} | sentiment={item.get('sentiment','?')} | "
            f"reason={item.get('reason','')}"
        )

    if not ticker_lines:
        return []

    prompt = f"""You are a professional stock investor and analyst. Evaluate these stocks and identify the 3-5 best buying opportunities for TODAY.

STOCK DATA:
{chr(10).join(ticker_lines)}

Selection criteria (think like a fund manager):
- Meaningful pullback from 52-week high (ideally 20-50% off, not just 2%)
- Price near or above 50-day or 200-day moving average (technical support)
- Elevated volume today (vol_ratio > 1.2 suggests real interest)
- Bullish or neutral sentiment with active discussion
- Strong fundamental reason behind the buzz (not pure meme)
- Avoid: stocks down >70% from high (possible structural problems), pure meme plays

Return ONLY valid JSON — no markdown, no explanation:
[
  {{
    "ticker": "NVDA",
    "price": 118.50,
    "pct_from_high": -22.3,
    "conviction": "high",
    "thesis": "2-3 sentence professional investment thesis explaining WHY this is a buy right now",
    "risk": "One sentence on the main risk to this thesis",
    "target_horizon": "short-term"
  }}
]

conviction must be one of: high, medium
target_horizon must be one of: short-term (days-weeks), medium-term (weeks-months)
Return between 3 and 5 picks. Only include genuinely compelling setups."""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system="You are a professional stock investor. Return only valid JSON arrays, nothing else.",
        messages=[{"role": "user", "content": prompt}],
    )

    text = msg.content[0].text.strip()
    start = text.find("[")
    end = text.rfind("]") + 1
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        print(f"Buy opportunities JSON parse failed:\n{text}")
        return []
