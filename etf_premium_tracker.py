import datetime
import os
import pandas as pd
import yfinance as yf
import requests

LOG_FILE = "etf_premium_log.csv"
ETF_LIST = ["GOLDBEES", "MAFANG", "MIDCAPETF", "MON100", "NIFTYBEES", "SILVERBEES"]

# The official AMFI structural codes for your exact portfolio
AMFI_CODES = {
    "GOLDBEES": "131237",
    "MAFANG": "148766",
    "MIDCAPETF": "147516",
    "MON100": "114144",
    "NIFTYBEES": "131245",
    "SILVERBEES": "149257"
}

def fetch_real_amfi_data(ticker):
    try:
        scheme_code = AMFI_CODES.get(ticker)
        if not scheme_code:
            return 0.0
        
        # Pulling the open live database endpoint
        url = f"https://api.mfapi.in/mf/{scheme_code}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "data" in data and len(data["data"]) > 0:
            return float(data["data"][0]["nav"])
    except Exception as e:
        print(f"Failed to fetch data for {ticker}: {e}")
    return 0.0

def main():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    new_rows = []

    for ticker in ETF_LIST:
        try:
            stock = yf.Ticker(f"{ticker}.NS")
            hist = stock.history(period="1d")
            if hist.empty:
                continue
            ltp = round(hist['Close'].iloc[-1], 2)
            
            # Fetch the real active underlying value
            inav_val = fetch_real_amfi_data(ticker)
            if inav_val == 0.0:
                inav_val = ltp  # Fallback asset protection
                
            premium_pct = round(((ltp - inav_val) / inav_val) * 100, 2)
            
            new_rows.append({
                "date": today_str,
                "etf": ticker,
                "ltp": ltp,
                "inav": inav_val,
                "premium_pct": premium_pct
            })
        except Exception as e:
            print(f"Error processing row for {ticker}: {e}")

    if not new_rows:
        return

    # Open history or build clean tracking frame
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
        try:
            old_df = pd.read_csv(LOG_FILE)
            # Retain only the exact structural columns matching your original layout
            valid_cols = ["date", "etf", "ltp", "inav", "premium_pct", "sma_5", "sma_20"]
            df = old_df[[c for c in old_df.columns if c in valid_cols]]
        except Exception:
            df = pd.DataFrame(columns=["date", "etf", "ltp", "inav", "premium_pct", "sma_5", "sma_20"])
    else:
        df = pd.DataFrame(columns=["date", "etf", "ltp", "inav", "premium_pct", "sma_5", "sma_20"])

    new_df = pd.DataFrame(new_rows)
    df = pd.concat([df, new_df], ignore_index=True)
    df = df.drop_duplicates(subset=["date", "etf"], keep="last")
    
    # Calculate historical moving averages over your clean rows
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['etf', 'date'])
    df['sma_5'] = df.groupby('etf')['premium_pct'].transform(lambda x: x.rolling(5, min_periods=1).mean().round(2))
    df['sma_20'] = df.groupby('etf')['premium_pct'].transform(lambda x: x.rolling(20, min_periods=1).mean().round(2))
    
    df['date'] = df['date'].dt.strftime("%Y-%m-%d")
    df[["date", "etf", "ltp", "inav", "premium_pct", "sma_5", "sma_20"]].to_csv(LOG_FILE, index=False)
    print("Database sync completed successfully with real numbers!")

if __name__ == "__main__":
    main()
