#!/usr/bin/env python3
import requests
import csv
import time

# ——— USER CONFIGURATION ———
##SYMBOLS    = ["MGL", "SBIN", "ICICIBANK", "FEDERALBNK", "NIFTY","UNIONBANK" ,"HDFCBANK","INDIANB" ,"SHRIRAMFIN" ,"PNBHOUSING"]  # equity vs index
SYMBOLS = ["OIL"]
EXPIRY     = "26-Jun-2025"
OUTPUT_CSV = "option_chain.csv"

# ——— Constants & URLs ———
BASE_URL    = "https://www.nseindia.com"
EQUITY_HTML = BASE_URL + "/option-chain-equities?symbol={}"
EQUITY_API  = BASE_URL + "/api/option-chain-equities?symbol={}"
INDEX_HTML  = BASE_URL + "/option-chain-indices?symbol={}"
INDEX_API   = BASE_URL + "/api/option-chain-indices?symbol={}"

# ——— CSV Header ———
CSV_HEADER = [
    "Symbol", "OptionType", "Strike",
    "Open", "High", "Low", "Close", "Last", "Change", "%Change",
    "Volume", "Value", "Expiry", "CurrentPrice", "Support", "Resistance"
]

# ——— Headers Sets ———
COMMON_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/114.0.5735.198 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection":      "keep-alive",
    "Origin":          BASE_URL,
    "Cache-Control":   "no-cache",
}

SEC_HEADERS = {
    "sec-ch-ua":          "\"Chromium\";v=\"114\", \" Not A;Brand\";v=\"99\"",
    "sec-ch-ua-mobile":   "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest":     "empty",
    "sec-fetch-mode":     "cors",
    "sec-fetch-site":     "same-origin"
}

HTML_HEADERS = {
    **COMMON_HEADERS,
    **SEC_HEADERS,
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer":         BASE_URL + "/",
}

API_HEADERS = {
    **COMMON_HEADERS,
    **SEC_HEADERS,
    "Accept":           "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}


def fetch_chain(session, symbol):
    """Fetch the option chain JSON for either equity or index."""
    # choose endpoints based on symbol
    if symbol.upper() in ("NIFTY", "BANKNIFTY"):
        html_url = INDEX_HTML.format(symbol)
        api_url  = INDEX_API.format(symbol)
    else:
        html_url = EQUITY_HTML.format(symbol)
        api_url  = EQUITY_API.format(symbol)

    # 1) seed cookies via base page
    session.get(BASE_URL, headers=HTML_HEADERS, timeout=5)
    time.sleep(1)

    # 2) load symbol HTML to get cookies
    session.get(html_url, headers=HTML_HEADERS, timeout=5)
    time.sleep(1)

    # 3) request JSON API with proper headers
    hdrs = {**API_HEADERS, "Referer": html_url}
    resp = session.get(api_url, headers=hdrs, timeout=5)

    # 4) retry once if unauthorized
    if resp.status_code == 401:
        session.get(BASE_URL, headers=HTML_HEADERS, timeout=5)
        time.sleep(1)
        session.get(html_url, headers=HTML_HEADERS, timeout=5)
        time.sleep(1)
        resp = session.get(api_url, headers=hdrs, timeout=5)

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

            recs          = data.get("records", {})
            ##current_price = 816.88
            current_price = recs.get("underlyingValue", "")
            all_strikes   = recs.get("data", [])
            # filter by expiry
            filt = [r for r in all_strikes if r.get("expiryDate") == EXPIRY]
            if not filt:
                print(f"⚠️  {sym}: no data for expiry {EXPIRY}")
                continue

            # calculate support/resistance
            max_pe = max((r.get("PE", {}).get("openInterest", 0) for r in filt), default=0)
            max_ce = max((r.get("CE", {}).get("openInterest", 0) for r in filt), default=0)
            support    = next((r["strikePrice"] for r in filt if r.get("PE", {}).get("openInterest", 0) == max_pe), "")
            resistance = next((r["strikePrice"] for r in filt if r.get("CE", {}).get("openInterest", 0) == max_ce), "")

            # write rows to CSV
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

            # polite pause between symbols
            time.sleep(1)

    print(f"\n✅ CSV saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
