import pandas as pd
import plotly.express as px
import os

LOG_FILE = "etf_premium_log.csv"
OUTPUT_FILE = "index.html"

def main():
    if not os.path.isfile(LOG_FILE):
        print(f"Error: {LOG_FILE} not found. Cannot generate chart.")
        return

    # 1. Load data from your clean CSV
    df = pd.read_csv(LOG_FILE)
    
    # Ensure date column is sorted chronologically
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date')

    # 2. Build the interactive Plotly line chart
    fig = px.line(
        df, 
        x="date", 
        y="premium_pct", 
        color="etf",
        title="ETF Premium / Discount Tracker Trend (%)",
        labels={"date": "Date", "premium_pct": "Premium / Discount (%)", "etf": "ETF Ticker"},
        markers=True
    )

    # 3. Enhance the chart features for mobile viewing
    fig.update_layout(
        hovermode="x unified",
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    # Zero baseline guide line
    fig.add_hline(y=0.0, line_dash="dash", line_color="gray", annotation_text="Fair Value (iNAV)")

    # 4. Save as index.html
    fig.write_html(OUTPUT_FILE, include_plotlyjs="cdn")
    print(f"Successfully generated interactive dashboard at {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
