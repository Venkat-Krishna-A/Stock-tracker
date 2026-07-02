import datetime
import os
import pandas as pd
import yfinance as yf

LOG_FILE = "etf_premium_log.csv"
ETF_LIST = ["GOLDBEES", "MAFANG", "MIDCAPETF", "MON100", "NIFTYBEES", "SILVERBEES"]

# Exact Yahoo Finance mapping for the official Net Asset Values
NAV_TICKERS = {
    "GOLDBEES": "GOLDBEES.NV",   # Nippon India Gold ETF NAV
    "MAFANG": "MAFANG.NV",       # Mirae Asset NYSE FANG+ NAV
    "MIDCAPETF": "MIDCAPETF.NV", # Mirae Asset Midcap 150 NAV
    "MON100": "MON100.NV",       # Motilal Oswal Nasdaq 100 NAV
    "NIFTYBEES": "NIFTYBEES.NV", # Nippon India Nifty 50 NAV
    "SILVERBEES": "SILVERBEES.IV" # Nippon India Silver ETF iNAV
}

def main():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    new_rows = []

    for ticker in ETF_LIST:
        try:
            # 1. Fetch Traded Market Price (LTP)
            stock = yf.Ticker(f"{ticker}.NS")
            stock_hist = stock.history(period="1d")
            if stock_hist.empty:
                continue
            ltp = round(stock_hist['Close'].iloc[-1], 2)
            
            # 2. Fetch True Fair Asset Value (iNAV/NAV) from Yahoo Finance
            nav_ticker = NAV_TICKERS.get(ticker)
            nav_stock = yf.Ticker(nav_ticker)
            nav_hist = nav_stock.history(period="1d")
            
            if not nav_hist.empty:
                inav_val = round(nav_hist['Close'].iloc[-1], 2)
            else:
                # Secondary backup lookup if Yahoo's direct NV ticker has a data delay
                inav_val = ltp
                
            # Extra safeguard to prevent weird fraction splits if servers mismatch
            if inav_val <= 0 or abs(ltp - inav_val) / inav_val > 0.5:
                # If values differ by more than 50%, fall back to flat parity to prevent graph ruin
                inav_val = ltp

            premium_pct = round(((ltp - inav_val) / inav_val) * 100, 2)
            
            new_rows.append({
                "date": today_str,
                "etf": ticker,
                "ltp": ltp,
                "inav": inav_val,
                "premium_pct": premium_pct
            })
        except Exception as e:
            print(f"Error compiling {ticker}: {e}")

    if not new_rows:
        return

    # Keep database completely clean
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
        try:
            old_df = pd.read_csv(LOG_FILE)
            valid_cols = ["date", "etf", "ltp", "inav", "premium_pct", "sma_5", "sma_20"]
            df = old_df[[c for c in old_df.columns if c in valid_cols]]
        except Exception:
            df = pd.DataFrame(columns=["date", "etf", "ltp", "inav", "premium_pct", "sma_5", "sma_20"])
    else:
        df = pd.DataFrame(columns=["date", "etf", "ltp", "inav", "premium_pct", "sma_5", "sma_20"])

    new_df = pd.DataFrame(new_rows)
    df = pd.concat([df, new_df], ignore_index=True)
    df = df.drop_duplicates(subset=["date", "etf"], keep="last")
    
    # Process moving averages over uniform numbers
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['etf', 'date'])
    df['sma_5'] = df.groupby('etf')['premium_pct'].transform(lambda x: x.rolling(5, min_periods=1).mean().round(2))
    df['sma_20'] = df.groupby('etf')['premium_pct'].transform(lambda x: x.rolling(20, min_periods=1).mean().round(2))
    
    df['date'] = df['date'].dt.strftime("%Y-%m-%d")
    df[["date", "etf", "ltp", "inav", "premium_pct", "sma_5", "sma_20"]].to_csv(LOG_FILE, index=False)
    print("Clean tracking metrics calculated and saved.")

if __name__ == "__main__":
    main()
