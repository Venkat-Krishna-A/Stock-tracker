"""
ETF Premium/Discount Tracker
-----------------------------
Compares live market price (LTP via yfinance) against the official
day-end NAV (via AMFI) for international ETFs that trade at a premium
in India (MAFANG, MON100, etc.) due to RBI overseas investment caps.

Run this once a day, ideally after ~11 PM IST when AMFI publishes the
day's NAV file, or any time during market hours to compare LTP against
yesterday's NAV (still a useful signal, just slightly lagged).

Requires: pip install yfinance requests --break-system-packages
"""

import yfinance as yf
import requests
from datetime import datetime
import csv
import os

# Add more ETFs here as (label, NSE ticker, AMFI scheme name substring)
WATCHLIST = [
    ("MAFANG", "MAFANG.NS", "Mirae Asset NYSE FANG+ ETF"),
    ("MON100", "MON100.NS", "Motilal Oswal NASDAQ 100 ETF"),
]

AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"
LOG_FILE = "etf_premium_log.csv"


def get_amfi_navs():
    """Download AMFI's daily NAV file and return {scheme_name: (nav, date)}."""
    resp = requests.get(AMFI_URL, timeout=15)
    resp.raise_for_status()
    navs = {}
    for line in resp.text.splitlines():
        parts = line.split(";")
        if len(parts) < 6:
            continue
        scheme_name = parts[3].strip()
        nav_str = parts[4].strip()
        date_str = parts[5].strip()
        if not scheme_name or not nav_str:
            continue
        try:
            navs[scheme_name] = (float(nav_str), date_str)
        except ValueError:
            continue
    return navs


def find_nav(navs, name_substring):
    """Find the NAV entry whose scheme name contains our target substring.
    Prefers the plain ETF listing over 'Fund of Fund' variants."""
    matches = [
        (name, nav, date) for name, (nav, date) in navs.items()
        if name_substring.lower() in name.lower() and "fund of fund" not in name.lower()
    ]
    if not matches:
        return None
    return matches[0]


def get_ltp(ticker):
    t = yf.Ticker(ticker)
    data = t.history(period="1d")
    if data.empty:
        return None
    return round(float(data["Close"].iloc[-1]), 2)


def main():
    print(f"Fetching AMFI NAV data ({datetime.now().strftime('%Y-%m-%d %H:%M')})...")
    navs = get_amfi_navs()

    rows = []
    for label, ticker, amfi_name in WATCHLIST:
        ltp = get_ltp(ticker)
        match = find_nav(navs, amfi_name)

        if ltp is None or match is None:
            print(f"{label}: could not fetch data (ltp={ltp}, nav_match={match})")
            continue

        scheme_name, nav, nav_date = match
        premium_pct = round((ltp - nav) / nav * 100, 2)

        print(f"\n{label} ({scheme_name})")
        print(f"  LTP: Rs.{ltp}   NAV: Rs.{nav} (as of {nav_date})")
        print(f"  Premium/Discount: {premium_pct:+.2f}%")

        rows.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "etf": label,
            "ltp": ltp,
            "nav": nav,
            "nav_date": nav_date,
            "premium_pct": premium_pct,
        })

    if rows:
        file_exists = os.path.isfile(LOG_FILE)
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            if not file_exists:
                writer.writeheader()
            writer.writerows(rows)
        print(f"\nLogged to {LOG_FILE}")


if __name__ == "__main__":
    main()
