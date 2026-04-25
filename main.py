from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from datetime import datetime, timedelta
import httpx
from anthropic import Anthropic

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

async def get_market_data_this_week():
    """Scrape real market data from past 7 days"""
    data = {}
    
    try:
        import yfinance as yf
        spy = yf.download("SPY", period="7d", progress=False)
        qqq = yf.download("QQQ", period="7d", progress=False)
        
        spy_change = ((spy['Close'].iloc[-1] - spy['Close'].iloc[0]) / spy['Close'].iloc[0]) * 100
        qqq_change = ((qqq['Close'].iloc[-1] - qqq['Close'].iloc[0]) / qqq['Close'].iloc[0]) * 100
        
        data["stock_movers"] = {
            "SPY": f"{spy_change:.2f}%",
            "QQQ": f"{qqq_change:.2f}%",
            "summary": f"S&P 500 {spy_change:+.1f}%, Tech {qqq_change:+.1f}%"
        }
    except Exception as e:
        data["stock_movers"] = {"error": str(e)}
    
    try:
        async with httpx.AsyncClient() as client_http:
            news_resp = await client_http.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": "stock market OR cryptocurrency OR federal reserve",
                    "sortBy": "publishedAt",
                    "language": "en",
                    "pageSize": 15,
                    "apiKey": os.getenv("NEWS_API_KEY")
                },
                timeout=10
            )
            if news_resp.status_code == 200:
                articles = news_resp.json().get("articles", [])
                data["news"] = [{"title": a["title"], "description": a["description"]} for a in articles[:10]]
            else:
                data["news"] = {"error": f"Status {news_resp.status_code}"}
    except Exception as e:
        data["news"] = {"error": str(e)}
    
    try:
        async with httpx.AsyncClient() as client_http:
            fed_resp = await client_http.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={
                    "series_id": "DFF",
                    "api_key": os.getenv("FRED_API_KEY"),
                    "limit": 30,
                    "sort_order": "desc"
                },
                timeout=10
            )
            if fed_resp.status_code == 200:
                obs = fed_resp.json().get("observations", [])
                if len(obs) >= 2:
                    latest = float(obs[0]["value"])
                    prev = float(obs[1]["value"])
                    data["fed_rate"] = {
                        "current": latest,
                        "previous": prev,
                        "change": latest - prev,
                        "summary": f"Fed rate {latest}%"
                    }
            else:
                data["fed_rate"] = {"error": f"Status {fed_resp.status_code}"}
    except Exception as e:
        data["fed_rate"] = {"error": str(e)}
    
    try:
        async with httpx.AsyncClient() as client_http:
            crypto_resp = await client_http.get(
                "https://api.coingecko.com/api/v3/global",
                timeout=10
            )
            if crypto_resp.status_code == 200:
                crypto_data = crypto_resp.json()
                btc_dom = crypto_data.get("data", {}).get("btc_market_cap_percentage", {}).get("btc", 0)
                data["crypto"] = {
                    "btc_dominance": f"{btc_dom:.1f}%",
                    "summary": f"Bitcoin dominance {btc_dom:.1f}%"
                }
            else:
                data["crypto"] = {"error": f"Status {crypto_resp.status_code}"}
    except Exception as e:
        data["crypto"] = {"error": str(e)}
    
    return data


def analyze_with_claude(market_data):
    """Send market data to Claude, get briefing back"""
    
    prompt = f"""You are a top VC analyst. Analyze this real market data from the past 7 days.

MARKET DATA:
- Stocks: {json.dumps(market_data.get('stock_movers', {}))}
- News: {json.dumps(market_data.get('news', {})[:5])}
- Fed: {json.dumps(market_data.get('fed_rate', {}))}
- Crypto: {json.dumps(market_data.get('crypto', {}))}

Return ONLY valid JSON (no markdown, no extra text):

{{
  "week_ending": "{(datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d')}",
  "executive_summary": "Brief paragraph on what moved this week and why it matters to VCs",
  "market_signals": [
    {{"signal": "What moved", "why": "Why", "magnitude": "High/Medium/Low"}}
  ],
  "key_trends": [
    {{
      "name": "Trend name",
      "what_moved": "Specific metrics",
      "private_market_impact": "How this affects startups",
      "affected_sectors": ["sector1", "sector2"],
      "direction": "tailwind or headwind",
      "timeline": "When founders feel this"
    }}
  ],
  "portfolio_implications": {{
    "tailwinds": ["Company type that benefits"],
    "headwinds": ["Company type that loses"]
  }},
  "sourcing_angles": [
    {{
      "angle": "Deal angle",
      "opportunity": "Why this is a deal now",
      "which_founders": "Founder profile to target",
      "urgency": "When to move"
    }}
  ]
}}"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = message.content[0].text
    
    try:
        briefing = json.loads(response_text)
    except:
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0]
        else:
            json_str = response_text
        briefing = json.loads(json_str)
    
    return briefing


@app.get("/api/briefing/latest")
async def get_latest_briefing():
    """Main endpoint"""
    try:
        market_data = await get_market_data_this_week()
        briefing = analyze_with_claude(market_data)
        briefing["generated_at"] = datetime.now().isoformat()
        briefing["data_sources"] = list(market_data.keys())
        return briefing
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
