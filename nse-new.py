import pandas as pd
from nselib import derivatives, capital_market
import csv
from datetime import datetime

# User configuration
SYMBOLS = ["AXISBANK"]
EXPIRY = "26-Jun-2025"
# Convert expiry date to DD-MM-YYYY format
expiry_dt = datetime.strptime(EXPIRY, "%d-%b-%Y").strftime("%d-%m-%Y")
OUTPUT_CSV = "option_chain.csv"

# CSV Header
CSV_HEADER = [
    "Symbol", "OptionType", "Strike",
    "Open", "High", "Low", "Close", "Last", "Change", "%Change",
    "Volume", "Value", "OI", "ChngOI", "IV", "BidQty", "Bid", "Ask", "AskQty",
    "Expiry", "CurrentPrice", "Support", "Resistance"
]


def main():
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
        for symbol in SYMBOLS:
            try:
                # Fetch option chain data using nselib
                data = derivatives.nse_live_option_chain(symbol=symbol, expiry_date=expiry_dt)

                # Debug: Print columns to confirm structure
                print(f"Columns in data: {data.columns}")

                # Get CurrentPrice using equity_info
                quote = capital_market.equity_info(symbol=symbol)
                current_price = quote['lastPrice']

                # Filter for specific expiry
                filtered = data[data['Expiry_Date'] == EXPIRY]
                if filtered.empty:
                    print(f"No data for {symbol} with expiry {EXPIRY}")
                    continue

                # Calculate Support and Resistance
                support_strike = filtered.loc[filtered['PUTS_OI'].idxmax()]['Strike_Price']
                resistance_strike = filtered.loc[filtered['CALLS_OI'].idxmax()]['Strike_Price']

                # Write to CSV
                for idx, row in filtered.iterrows():
                    strike = row['Strike_Price']
                    # Call row
                    call_row = [
                        symbol,
                        'Call',
                        strike,
                        '',  # Open (not available)
                        '',  # High (not available)
                        '',  # Low (not available)
                        '',  # Close (not available)
                        row.get('CALLS_LTP', ''),
                        row.get('CALLS_Net_Chng', ''),
                        '',  # %Change (not directly available)
                        row.get('CALLS_Volume', ''),
                        '',  # Value (not available)
                        row.get('CALLS_OI', ''),
                        row.get('CALLS_Chng_in_OI', ''),
                        row.get('CALLS_IV', ''),
                        row.get('CALLS_Bid_Qty', ''),
                        row.get('CALLS_Bid_Price', ''),
                        row.get('CALLS_Ask_Price', ''),
                        row.get('CALLS_Ask_Qty', ''),
                        EXPIRY,
                        current_price,
                        support_strike,
                        resistance_strike
                    ]
                    writer.writerow(call_row)
                    # Put row
                    put_row = [
                        symbol,
                        'Put',
                        strike,
                        '',  # Open (not available)
                        '',  # High (not available)
                        '',  # Low (not available)
                        '',  # Close (not available)
                        row.get('PUTS_LTP', ''),
                        row.get('PUTS_Net_Chng', ''),
                        '',  # %Change (not directly available)
                        row.get('PUTS_Volume', ''),
                        '',  # Value (not available)
                        row.get('PUTS_OI', ''),
                        row.get('PUTS_Chng_in_OI', ''),
                        row.get('PUTS_IV', ''),
                        row.get('PUTS_Bid_Qty', ''),
                        row.get('PUTS_Bid_Price', ''),
                        row.get('PUTS_Ask_Price', ''),
                        row.get('PUTS_Ask_Qty', ''),
                        EXPIRY,
                        current_price,
                        support_strike,
                        resistance_strike
                    ]
                    writer.writerow(put_row)
            except Exception as e:
                print(f"Failed to fetch data for {symbol}: {e}")
        print(f"Data saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()