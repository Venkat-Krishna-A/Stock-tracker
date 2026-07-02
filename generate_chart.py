import pandas as pd
import plotly.express as px
import os
import datetime
import holidays

LOG_FILE = "etf_premium_log.csv"
OUTPUT_FILE = "index.html"

def get_market_status_tomorrow():
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    if tomorrow.weekday() in [5, 6]: 
        return "🔴 Closed (Weekend)"
    indian_holidays = holidays.India(years=tomorrow.year)
    if tomorrow in indian_holidays:
        return f"🔴 Closed (NSE Holiday: {indian_holidays.get(tomorrow)})"
    return "🟢 Open for Trading"

def main():
    if not os.path.isfile(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
        with open(OUTPUT_FILE, "w") as f:
            f.write("<html><body style='background:#111;color:#fff;text-align:center;'><h1>Awaiting Data...</h1></body></html>")
        return

    df = pd.read_csv(LOG_FILE)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date')

    fig = px.line(
        df, 
        x="date", 
        y="premium_pct", 
        color="etf",
        title="ETF Premium / Discount Historical Trends",
        labels={"date": "Date", "premium_pct": "Premium / Discount (%)", "etf": "ETF Ticker"},
        markers=True
    )

    fig.update_layout(
        hovermode="x unified",
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=80, b=20)
    )
    fig.add_hline(y=0.0, line_dash="dash", line_color="gray")

    graph_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
    tomorrow_status = get_market_status_tomorrow()

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ETF Analytics Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background-color: #111116; color: #eee; margin: 0; padding: 20px; }}
            .banner {{ background: #1e1e24; border-left: 5px solid #3b82f6; padding: 15px; margin-bottom: 20px; border-radius: 4px; }}
            .banner h3 {{ margin: 0 0 5px 0; color: #9ab4e9; font-size: 14px; text-transform: uppercase; }}
            .banner p {{ margin: 0; font-size: 18px; font-weight: bold; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="banner">
                <h3>Market Status Tomorrow</h3>
                <p>{tomorrow_status}</p>
            </div>
            {graph_html}
        </div>
    </body>
    </html>
    """

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Dashboard created successfully.")

if __name__ == "__main__":
    main()
