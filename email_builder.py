from datetime import datetime


MOOD_EMOJI = {"bullish": "📈", "bearish": "📉", "mixed": "〰️"}
MOOD_COLOR = {"bullish": "#16a34a", "bearish": "#dc2626", "mixed": "#d97706"}
SENTIMENT_BG = {"bullish": "#dcfce7", "bearish": "#fee2e2", "neutral": "#f3f4f6"}
SENTIMENT_FG = {"bullish": "#15803d", "bearish": "#b91c1c", "neutral": "#6b7280"}


def _change_color(pct):
    return "#16a34a" if pct >= 0 else "#dc2626"


def _change_arrow(pct):
    return "▲" if pct >= 0 else "▼"


def _ticker_row(symbol, data):
    price = data["price"]
    pct = data["change_pct"]
    color = _change_color(pct)
    arrow = _change_arrow(pct)
    news = data["news"]
    news_html = ""
    if news:
        n = news[0]
        title = n["title"][:90] + ("…" if len(n["title"]) > 90 else "")
        link = n["url"]
        news_html = f"""
        <p style="margin:6px 0 0 0; font-size:13px; color:#6b7280; line-height:1.5;">
          {title}
          {'<a href="' + link + '" style="color:#6366f1; text-decoration:none; white-space:nowrap;"> Read more →</a>' if link else ''}
        </p>"""
    return f"""
    <tr>
      <td style="padding:14px 0; border-bottom:1px solid #f3f4f6;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="vertical-align:top;">
              <span style="font-size:15px; font-weight:700; color:#111827; font-family:monospace;">${symbol}</span>
              <span style="font-size:13px; color:#6b7280; margin-left:8px; font-family:-apple-system,sans-serif;">${price:.2f}</span>
              <span style="font-size:13px; font-weight:600; color:{color}; margin-left:6px;">{arrow} {abs(pct):.2f}%</span>
              {news_html}
            </td>
          </tr>
        </table>
      </td>
    </tr>"""


def _ticker_mention_row(item, index):
    s = item.get("sentiment", "neutral").lower()
    if s not in SENTIMENT_BG:
        s = "neutral"
    badge_bg = SENTIMENT_BG[s]
    badge_fg = SENTIMENT_FG[s]
    sources_html = " ".join(
        f'<span style="background:#f3f4f6; color:#6b7280; padding:2px 7px; border-radius:10px; font-size:11px;">{src}</span>'
        for src in item.get("sources", [])[:3]
    )
    return f"""
    <tr>
      <td style="padding:12px 0; border-bottom:1px solid #f3f4f6;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="vertical-align:middle; width:60px;">
              <span style="font-size:14px; font-weight:700; color:#111827; font-family:monospace;">${item['ticker']}</span>
            </td>
            <td style="vertical-align:middle; width:80px; text-align:center;">
              <span style="background:{badge_bg}; color:{badge_fg}; padding:2px 10px; border-radius:12px; font-size:11px; font-weight:600; text-transform:uppercase;">{s}</span>
            </td>
            <td style="vertical-align:middle; width:50px; text-align:right;">
              <span style="font-size:12px; color:#9ca3af;">{item.get('mentions', 0)} mentions</span>
            </td>
          </tr>
          <tr>
            <td colspan="3" style="padding-top:4px;">
              <span style="font-size:12px; color:#6b7280;">{item.get('reason', '')}</span>
              <span style="margin-left:8px;">{sources_html}</span>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""


def _news_item(item):
    source = item.get("source", "")
    url = item.get("url", "")
    return f"""
    <tr>
      <td style="padding:14px 0; border-bottom:1px solid #f3f4f6;">
        <p style="margin:0 0 4px 0; font-size:14px; font-weight:600; color:#111827; line-height:1.4;">{item['headline']}</p>
        <p style="margin:0 0 6px 0; font-size:13px; color:#6b7280; line-height:1.5;">{item.get('summary', '')}</p>
        {'<a href="' + url + '" style="font-size:12px; color:#6366f1; text-decoration:none; font-weight:500;">' + source + ' → Read more</a>' if url else f'<span style="font-size:12px; color:#9ca3af;">{source}</span>'}
      </td>
    </tr>"""


VERDICT_COLOR = {
    "strong_buy": "#15803d", "buy": "#16a34a",
    "hold": "#d97706",
    "sell": "#dc2626", "strong_sell": "#b91c1c",
}
VERDICT_BG = {
    "strong_buy": "#dcfce7", "buy": "#f0fdf4",
    "hold": "#fef3c7",
    "sell": "#fee2e2", "strong_sell": "#fecaca",
}
VERDICT_LABEL = {
    "strong_buy": "STRONG BUY", "buy": "BUY",
    "hold": "HOLD",
    "sell": "SELL", "strong_sell": "STRONG SELL",
}
CONVICTION_COLOR = {"high": "#7c3aed", "medium": "#d97706"}
CONVICTION_BG = {"high": "#ede9fe", "medium": "#fef3c7"}
HORIZON_LABEL = {"short-term": "Short-term play", "medium-term": "Medium-term hold"}


def _ticker_analysis_row(symbol, price_data, analysis):
    price = price_data.get("price", 0)
    pct = price_data.get("change_pct", 0)
    price_color = _change_color(pct)
    price_arrow = _change_arrow(pct)

    verdict = analysis.get("verdict", "hold").lower()
    if verdict not in VERDICT_COLOR:
        verdict = "hold"
    v_color = VERDICT_COLOR[verdict]
    v_bg = VERDICT_BG[verdict]
    v_label = VERDICT_LABEL[verdict]

    summary = analysis.get("summary", "")
    street = analysis.get("street_sentiment", "")
    social = analysis.get("social_sentiment", "")
    catalyst = analysis.get("key_catalyst", "")

    news = price_data.get("news", [])
    news_link = ""
    if news:
        n = news[0]
        title = n["title"][:80] + ("…" if len(n["title"]) > 80 else "")
        news_link = f'<a href="{n["url"]}" style="color:#6366f1; text-decoration:none; font-size:12px;">📰 {title}</a>' if n.get("url") else ""

    return f"""
    <tr>
      <td style="padding:16px 0; border-bottom:1px solid #f3f4f6;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="vertical-align:middle; padding-bottom:8px;">
              <span style="font-size:16px; font-weight:700; color:#111827; font-family:monospace;">${symbol}</span>
              <span style="font-size:13px; color:#374151; margin-left:8px;">${price:.2f}</span>
              <span style="font-size:13px; font-weight:600; color:{price_color}; margin-left:4px;">{price_arrow} {abs(pct):.2f}%</span>
              <span style="display:inline-block; margin-left:10px; background:{v_bg}; color:{v_color}; padding:3px 10px; border-radius:10px; font-size:11px; font-weight:700; letter-spacing:0.05em;">{v_label}</span>
            </td>
          </tr>
          <tr>
            <td style="padding-bottom:6px;">
              <p style="margin:0; font-size:13px; color:#374151; line-height:1.6;">{summary}</p>
            </td>
          </tr>
          <tr>
            <td>
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="padding:4px 0; font-size:12px; color:#6b7280; line-height:1.5;">
                    <strong style="color:#374151;">🏦 Street:</strong> {street}
                  </td>
                </tr>
                <tr>
                  <td style="padding:4px 0; font-size:12px; color:#6b7280; line-height:1.5;">
                    <strong style="color:#374151;">💬 Social:</strong> {social}
                  </td>
                </tr>
                <tr>
                  <td style="padding:4px 0; font-size:12px; color:#6b7280; line-height:1.5;">
                    <strong style="color:#374151;">⚡ Catalyst:</strong> {catalyst}
                  </td>
                </tr>
                {'<tr><td style="padding-top:6px;">' + news_link + '</td></tr>' if news_link else ''}
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""


def _buy_opportunity_row(item):
    ticker = item.get("ticker", "")
    price = item.get("price", 0)
    pct_off = item.get("pct_from_high", 0)
    conviction = item.get("conviction", "medium").lower()
    if conviction not in CONVICTION_COLOR:
        conviction = "medium"
    thesis = item.get("thesis", "")
    risk = item.get("risk", "")
    horizon = item.get("target_horizon", "short-term")
    horizon_label = HORIZON_LABEL.get(horizon, horizon)
    badge_color = CONVICTION_COLOR[conviction]
    badge_bg = CONVICTION_BG[conviction]

    return f"""
    <tr>
      <td style="padding:14px 0; border-bottom:1px solid #f3f4f6;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="vertical-align:middle;">
              <span style="font-size:15px; font-weight:700; color:#111827; font-family:monospace;">${ticker}</span>
              <span style="font-size:13px; color:#6b7280; margin-left:8px;">${price:.2f}</span>
              <span style="font-size:12px; color:#dc2626; margin-left:6px;">{pct_off:.1f}% off 52w high</span>
              <span style="display:inline-block; margin-left:10px; background:{badge_bg}; color:{badge_color}; padding:2px 8px; border-radius:10px; font-size:10px; font-weight:700; text-transform:uppercase;">{conviction} conviction</span>
              <span style="display:inline-block; margin-left:6px; background:#f0f9ff; color:#0369a1; padding:2px 8px; border-radius:10px; font-size:10px;">{horizon_label}</span>
            </td>
          </tr>
          <tr>
            <td style="padding-top:6px;">
              <p style="margin:0 0 4px 0; font-size:13px; color:#374151; line-height:1.5;">{thesis}</p>
              <p style="margin:0; font-size:12px; color:#9ca3af; line-height:1.4;"><strong style="color:#6b7280;">Risk:</strong> {risk}</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""


def _section(title, emoji, content_html):
    return f"""
  <tr>
    <td style="padding:0 0 20px 0;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:12px; border:1px solid #e5e7eb; overflow:hidden;">
        <tr>
          <td style="padding:18px 24px 0 24px;">
            <p style="margin:0 0 12px 0; font-size:11px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#9ca3af;">{emoji} {title}</p>
          </td>
        </tr>
        <tr>
          <td style="padding:0 24px 18px 24px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              {content_html}
            </table>
          </td>
        </tr>
      </table>
    </td>
  </tr>"""


def build(analysis, ticker_data, portfolio_tickers, watchlist_tickers, buy_opportunities=None, ticker_analysis=None):
    today = datetime.now().strftime("%A, %B %-d, %Y")
    mood = analysis.get("market_mood", "mixed").lower()
    mood_emoji = MOOD_EMOJI.get(mood, "〰️")
    mood_color = MOOD_COLOR.get(mood, "#d97706")

    # Most mentioned tickers
    mentions_rows = "".join(
        _ticker_mention_row(item, i)
        for i, item in enumerate(analysis.get("top_tickers", [])[:8])
    )

    # Top news
    news_rows = "".join(
        _news_item(item) for item in analysis.get("top_news", [])[:5]
    )

    # Trending topics
    trending_text = analysis.get("trending_topics", "")
    trending_row = f'<tr><td style="padding:4px 0;"><p style="margin:0; font-size:14px; color:#374151; line-height:1.6;">{trending_text}</p></td></tr>'

    # Portfolio rows
    portfolio_rows = "".join(
        _ticker_row(s, ticker_data.get(s, {"price": 0, "change_pct": 0, "news": []}))
        for s in portfolio_tickers
    )

    # Watchlist rows
    watchlist_rows = "".join(
        _ticker_row(s, ticker_data.get(s, {"price": 0, "change_pct": 0, "news": []}))
        for s in watchlist_tickers
    )

    # Ticker deep dive (portfolio + watchlist)
    all_personal = portfolio_tickers + watchlist_tickers
    ticker_analysis = ticker_analysis or {}
    deep_dive_rows = "".join(
        _ticker_analysis_row(
            s,
            ticker_data.get(s, {"price": 0, "change_pct": 0, "news": []}),
            ticker_analysis.get(s, {}),
        )
        for s in all_personal
    )
    if not deep_dive_rows:
        deep_dive_rows = '<tr><td style="padding:8px 0; font-size:13px; color:#9ca3af;">Analysis unavailable.</td></tr>'

    # Buy opportunities
    buy_rows = "".join(
        _buy_opportunity_row(item) for item in (buy_opportunities or [])
    )
    if not buy_rows:
        buy_rows = '<tr><td style="padding:8px 0; font-size:13px; color:#9ca3af;">No compelling setups identified today.</td></tr>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Morning Market Brief – {today}</title>
</head>
<body style="margin:0; padding:0; background-color:#f5f4f0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f4f0;">
  <tr>
    <td align="center" style="padding:32px 16px;">
      <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;">

        <!-- HEADER -->
        <tr>
          <td style="padding:0 0 20px 0;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f172a; border-radius:12px; overflow:hidden;">
              <tr>
                <td style="padding:28px 28px 24px 28px;">
                  <p style="margin:0 0 6px 0; font-size:12px; font-weight:600; letter-spacing:0.1em; text-transform:uppercase; color:#94a3b8;">Morning Market Brief</p>
                  <h1 style="margin:0 0 10px 0; font-size:26px; font-weight:700; color:#f8fafc; line-height:1.2;">{today}</h1>
                  <span style="display:inline-block; background:{mood_color}22; border:1px solid {mood_color}44; color:{mood_color}; padding:4px 14px; border-radius:20px; font-size:12px; font-weight:600;">
                    {mood_emoji} Market Mood: {mood.capitalize()}
                  </span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- MOST MENTIONED -->
        {_section("Most Mentioned Tickers", "🔥", mentions_rows)}

        <!-- TOP NEWS -->
        {_section("Top Market News", "📰", news_rows)}

        <!-- TRENDING -->
        {_section("What Everyone's Talking About", "💬", trending_row)}

        <!-- PORTFOLIO PRICES -->
        {_section("Your Portfolio", "📊", portfolio_rows)}

        <!-- WATCHLIST PRICES -->
        {_section("Watchlist", "👀", watchlist_rows)}

        <!-- TICKER DEEP DIVE -->
        {_section("Analyst View — Your Tickers", "🔬", deep_dive_rows)}

        <!-- BUY OPPORTUNITIES -->
        {_section("Potential Buys — AI Picks", "💡", buy_rows)}

        <!-- FOOTER -->
        <tr>
          <td style="padding:8px 0 24px 0; text-align:center;">
            <p style="margin:0; font-size:11px; color:#9ca3af;">
              Delivered daily at 7am MT · Sources: Reddit, Yahoo Finance, MarketWatch, CNBC, Reuters, Benzinga, Stocktwits
            </p>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
</body>
</html>"""

    return html
