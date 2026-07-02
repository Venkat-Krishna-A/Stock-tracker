import datetime
import os
import pandas as pd
import yfinance as yf
import requests
import holidays

LOG_FILE = "etf_premium_log.csv"
ETF_LIST = ["MON100", "MAFANG"]

def is_market_open_today():
    today = datetime.date.today()
    if today.weekday() in [5, 6]:
        return False
    indian_holidays = holidays.India(years=today.year)
    if today in indian_holidays:
        return False
    return True

def fetch_inav(ticker):
    # Standard iNAV lookup logic placeholder
    return 0.0

def main():
    # If market was closed today, exit immediately to keep CSV completely clean
    if not is_market_open_today():
        print("Market closed today. No data logged.")
        return

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    new_rows = []

    for ticker in ETF_LIST:
        try:
            stock = yf.Ticker(f"{ticker}.NS")
            hist = stock.history(period="1d")
            if hist.empty:
                continue
            ltp = round(hist['Close'].iloc[-1], 2)
            
            inav = fetch_inav(ticker)
            if inav == 0: 
                inav = ltp 
                
            premium_pct = round(((ltp - inav) / inav) * 100, 2)
            
            new_rows.append({
                "date": today_str,
                "etf": ticker,
                "ltp": ltp,
                "inav": inav,
                "premium_pct": premium_pct
            })
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")

    if not new_rows:
        return

    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
        df = pd.read_csv(LOG_FILE)
    else:
        df = pd.DataFrame(columns=["date", "etf", "ltp", "inav", "premium_pct", "sma_5", "sma_20"])

    new_df = pd.DataFrame(new_rows)
    df = pd.concat([df, new_df], ignore_index=True)
    df = df.drop_duplicates(subset=["date", "etf"], keep="last")
    
    # Calculate Moving Averages over pure historical rows
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['etf', 'date'])
    df['sma_5'] = df.groupby('etf')['premium_pct'].transform(lambda x: x.rolling(5, min_periods=1).mean().round(2))
    df['sma_20'] = df.groupby('etf')['premium_pct'].transform(lambda x: x.rolling(20, min_periods=1).mean().round(2))
    
    df['date'] = df['date'].dt.strftime("%Y-%m-%d")
    df.to_csv(LOG_FILE, index=False)
    print("CSV data updated cleanly.")

if __name__ == "__main__":
    main()
