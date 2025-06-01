##https://grok.com/chat/da744871-060d-4bff-9f65-722e34029b0a
#!/usr/bin/env python3
import requests
import csv
import time

##SYMBOLS    = ["MGL", "SBIN", "ICICIBANK", "AXISBANK ", "OIL" ,"VEDL", "FEDERALBNK", "NIFTY","UNIONBANK" ,"HDFCBANK","INDIANB" ,"SHRIRAMFIN" ,"PNBHOUSING"]  # equity vs index


# ——— USER CONFIGURATION ———
SYMBOLS = ["AXISBANK"]
EXPIRY = "26-Jun-2025"
OUTPUT_CSV = "option_chain.csv"

# ——— Constants & URLs ———
BASE_URL = "https://www.nseindia.com"
EQUITY_HTML = BASE_URL + "/option-chain-equities?symbol={}"
EQUITY_API = BASE_URL + "/api/option-chain-equities?symbol={}"
INDEX_HTML = BASE_URL + "/option-chain-indices?symbol={}"
INDEX_API = BASE_URL + "/api/option-chain-indices?symbol={}"

# ——— CSV Header ———
CSV_HEADER = [
    "Symbol", "OptionType", "Strike",
    "Open", "High", "Low", "Close", "Last", "Change", "%Change",
    "Volume", "Value", "Expiry", "CurrentPrice", "Support", "Resistance"
]

# ——— Headers Sets ———
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Origin": BASE_URL,
    "Cache-Control": "no-cache",
}

SEC_HEADERS = {
    "sec-ch-ua": "\"Not/A)Brand\";v=\"99\", \"Google Chrome\";v=\"126\", \"Chromium\";v=\"126\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin"
}

HTML_HEADERS = {
    **COMMON_HEADERS,
    **SEC_HEADERS,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": BASE_URL + "/",
}

API_HEADERS = {
    **COMMON_HEADERS,
    **SEC_HEADERS,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Encoding": "gzip, deflate, br",
}

def fetch_chain(session, symbol):
    """Fetch the option chain JSON for either equity or index."""
    # Choose endpoints based on symbol
    if symbol.upper() in ("NIFTY", "BANKNIFTY"):
        html_url = INDEX_HTML.format(symbol)
        api_url = INDEX_API.format(symbol)
    else:
        html_url = EQUITY_HTML.format(symbol)
        api_url = EQUITY_API.format(symbol)

    # 1) Seed cookies via base page
    session.get(BASE_URL, headers=HTML_HEADERS, timeout=10)
    time.sleep(3)  # Increased delay to ensure cookies are set

    # 2) Load symbol HTML to get cookies
    session.get(html_url, headers=HTML_HEADERS, timeout=10)
    time.sleep(3)  # Increased delay

    # Print cookies for debugging
    print(f"Cookies after loading HTML for {symbol}: {session.cookies}")

    # 3) Request JSON API with proper headers
    hdrs = {**API_HEADERS, "Referer": html_url}
    resp = session.get(api_url, headers=hdrs, timeout=10)

    # Print headers for debugging
    print(f"Headers sent with API request: {hdrs}")

    # 4) Retry up to 5 times if unauthorized
    attempts = 0
    while resp.status_code == 401 and attempts < 5:
        print(f"Retry {attempts+1} for {symbol}: Unauthorized (401)")
        session.get(BASE_URL, headers=HTML_HEADERS, timeout=10)
        time.sleep(3)
        session.get(html_url, headers=HTML_HEADERS, timeout=10)
        time.sleep(3)
        resp = session.get(api_url, headers=hdrs, timeout=10)
        attempts += 1

    resp.raise_for_status()
    return resp.json()

def main():
    sess = requests.Session()

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)

        for sym in SYMBOLS:
            try:
                data = fetch_chain(sess, sym)
            except Exception as e:
                print(f"⚠️  Failed to fetch {sym}: {e}")
                continue

            recs = data.get("records", {})
            current_price = recs.get("underlyingValue", "")
            all_strikes = recs.get("data", [])
            # Filter by expiry
            filt = [r for r in all_strikes if r.get("expiryDate") == EXPIRY]
            if not filt:
                print(f"⚠️  {sym}: no data for expiry {EXPIRY}")
                continue

            # Calculate support/resistance
            max_pe = max((r.get("PE", {}).get("openInterest", 0) for r in filt), default=0)
            max_ce = max((r.get("CE", {}).get("openInterest", 0) for r in filt), default=0)
            support = next((r["strikePrice"] for r in filt if r.get("PE", {}).get("openInterest", 0) == max_pe), "")
            resistance = next((r["strikePrice"] for r in filt if r.get("CE", {}).get("openInterest", 0) == max_ce), "")

            # Write rows to CSV
            for r in filt:
                for side, label in (("CE", "Call"), ("PE", "Put")):
                    opt = r.get(side)
                    if not opt or opt.get("expiryDate") != EXPIRY:
                        continue
                    writer.writerow([
                        sym,
                        label,
                        r.get("strikePrice", ""),
                        opt.get("openPrice", ""),
                        opt.get("highPrice", ""),
                        opt.get("lowPrice", ""),
                        opt.get("closePrice", ""),
                        opt.get("lastPrice", ""),
                        opt.get("change", ""),
                        opt.get("pChange", ""),
                        opt.get("totalTradedVolume", ""),
                        opt.get("totalTradedValue", ""),
                        EXPIRY,
                        current_price,
                        support,
                        resistance
                    ])

            # Polite pause between symbols
            time.sleep(3)

    print(f"\n✅ CSV saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()