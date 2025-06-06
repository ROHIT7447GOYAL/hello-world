import os
import glob
import pandas as pd
from datetime import datetime, timedelta

# Set folder path
folder_path = r'C:\Users\rohit\Documents\stocks'
os.chdir(folder_path)

# Find latest files
tradebook_files = glob.glob('tradebook-NL1305-EQ*.csv')
if tradebook_files:
    latest_tradebook = max(tradebook_files, key=os.path.getctime)
else:
    raise FileNotFoundError("No tradebook files found")

holdings_files = glob.glob('holdings*.csv')
if holdings_files:
    latest_holdings = max(holdings_files, key=os.path.getctime)
else:
    raise FileNotFoundError("No holdings files found")

nifty50_files = glob.glob('Nifty 50 Historical Data*.csv')
if nifty50_files:
    latest_nifty50 = max(nifty50_files, key=os.path.getctime)
else:
    raise FileNotFoundError("No Nifty 50 files found")

nifty500_files = glob.glob('Nifty 500 Historical Data*.csv')
if nifty500_files:
    latest_nifty500 = max(nifty500_files, key=os.path.getctime)
else:
    raise FileNotFoundError("No Nifty 500 files found")

# Print latest file names
print(f"Latest tradebook file: {latest_tradebook}")
print(f"Latest holdings file: {latest_holdings}")
print(f"Latest Nifty 50 file: {latest_nifty50}")
print(f"Latest Nifty 500 file: {latest_nifty500}")

# Print and delete old files
tradebook_files_to_delete = [f for f in tradebook_files if f != latest_tradebook]
for file in tradebook_files_to_delete:
    print(f"Deleted old tradebook file: {file}")
    os.remove(file)
holdings_files_to_delete = [f for f in holdings_files if f != latest_holdings]
for file in holdings_files_to_delete:
    print(f"Deleted old holdings file: {file}")
    os.remove(file)
nifty50_files_to_delete = [f for f in nifty50_files if f != latest_nifty50]
for file in nifty50_files_to_delete:
    print(f"Deleted old Nifty 50 file: {file}")
    os.remove(file)
nifty500_files_to_delete = [f for f in nifty500_files if f != latest_nifty500]
for file in nifty500_files_to_delete:
    print(f"Deleted old Nifty 500 file: {file}")
    os.remove(file)

# Read files with explicit date parsing and numeric conversion
tradebook_df = pd.read_csv(latest_tradebook, parse_dates=['trade_date'])
holdings_df = pd.read_csv(latest_holdings)
# Parse Date column and convert Price to numeric
nifty50_df = pd.read_csv(latest_nifty50, parse_dates=['Date'], date_format='%d-%m-%Y', thousands=',')
nifty500_df = pd.read_csv(latest_nifty500, parse_dates=['Date'], date_format='%d-%m-%Y', thousands=',')

# Convert Price column to numeric, handling non-numeric values
nifty50_df['Price'] = pd.to_numeric(nifty50_df['Price'], errors='coerce')
nifty500_df['Price'] = pd.to_numeric(nifty500_df['Price'], errors='coerce')

# Drop rows with NaT in Date or NaN in Price
nifty50_df = nifty50_df.dropna(subset=['Date', 'Price'])
nifty500_df = nifty500_df.dropna(subset=['Date', 'Price'])

# Log data types and sample values
print(f"Nifty 50 Date dtype: {nifty50_df['Date'].dtype}, Price dtype: {nifty50_df['Price'].dtype}, Sample: {nifty50_df[['Date', 'Price']].head(2).to_dict('records')}")
print(f"Nifty 500 Date dtype: {nifty500_df['Date'].dtype}, Price dtype: {nifty500_df['Price'].dtype}, Sample: {nifty500_df[['Date', 'Price']].head(2).to_dict('records')}")

# Set today's date
today = pd.to_datetime(datetime.today().date())

# Simple annualized return
def simple_annualized_return(profit_loss, invested, days_invested):
    if invested == 0 or days_invested == 0:
        return None
    return (profit_loss / invested) * (365.25 / days_invested) * 100  # Convert to percentage

# Find closest date in index data
def find_closest_date(index_df, target_date, direction='both'):
    dates = index_df['Date']
    if target_date in dates.values:
        return target_date
    if direction == 'before':
        valid_dates = dates[dates <= target_date]
        if not valid_dates.empty:
            return valid_dates.max()
    elif direction == 'after':
        valid_dates = dates[dates >= target_date]
        if not valid_dates.empty:
            return valid_dates.min()
    else:  # both
        if not dates.empty:
            return dates.iloc[(dates - target_date).abs().argmin()]
    return None

# Calculate index return for a given period
def calculate_index_return(index_df, start_date, end_date, symbol=None):
    start_date = find_closest_date(index_df, start_date, 'before')
    end_date = find_closest_date(index_df, end_date, 'after')
    if start_date is None or end_date is None:
        if symbol:
            print(f"Index return N/A for {symbol}: No valid dates found (start: {start_date}, end: {end_date})")
        return None
    start_price = index_df[index_df['Date'] == start_date]['Price'].values
    end_price = index_df[index_df['Date'] == end_date]['Price'].values
    if len(start_price) == 0 or len(end_price) == 0:
        if symbol:
            print(f"Index return N/A for {symbol}: No prices found for dates {start_date}, {end_date}")
        return None
    profit_loss = end_price[0] - start_price[0]
    days = (end_date - start_date).days
    if days == 0:
        if symbol:
            print(f"Index return N/A for {symbol}: Zero days between {start_date} and {end_date}")
        return None
    return simple_annualized_return(profit_loss, start_price[0], days)

# Calculate metrics for a stock
def get_stock_metrics(symbol, tradebook_df, holdings_df, nifty50_df, nifty500_df, today):
    trades = tradebook_df[tradebook_df['symbol'] == symbol]
    total_invested = 0
    qty_buy = 0
    qty_sell = 0
    total_buy_amount = 0
    p_l_sold = 0
    first_date = None
    last_date = None
    # Aggregate same-day transactions
    trades_by_date = trades.groupby(['trade_date', 'trade_type']).agg({
        'quantity': 'sum',
        'price': 'mean'
    }).reset_index()
    for _, trade in trades_by_date.sort_values('trade_date').iterrows():
        if trade['trade_type'] == 'buy':
            cf = -trade['quantity'] * trade['price']
            total_invested += -cf
            total_buy_amount += -cf
            qty_buy += trade['quantity']
        elif trade['trade_type'] == 'sell':
            cf = trade['quantity'] * trade['price']
            p_l_sold += cf
            qty_sell += trade['quantity']
        if first_date is None:
            first_date = trade['trade_date']
        last_date = trade['trade_date']
    holding = holdings_df[holdings_df['Instrument'] == symbol]
    cur_val = holding['Cur. val'].values[0] if not holding.empty else 0
    p_l_unrealized = holding['P&L'].values[0] if not holding.empty else 0
    if cur_val > 0:
        last_date = today
    days_invested = (last_date - first_date).days if first_date and last_date and last_date > first_date else 0
    # Combined Profit/Loss
    profit_loss = p_l_unrealized + (p_l_sold - total_buy_amount if p_l_sold > 0 else 0)
    # Simple annualized return
    return_rate = simple_annualized_return(profit_loss, total_invested, days_invested) if days_invested > 0 else None
    # Calculate index returns for the same period
    nifty50_return = calculate_index_return(nifty50_df, first_date, last_date, symbol) if first_date and last_date else None
    nifty500_return = calculate_index_return(nifty500_df, first_date, last_date, symbol) if first_date and last_date else None
    # Calculate return differences
    return_diff_nifty50 = return_rate - nifty50_return if return_rate is not None and nifty50_return is not None else None
    return_diff_nifty500 = return_rate - nifty500_return if return_rate is not None and nifty500_return is not None else None
    return {
        'Instrument': symbol,
        'Invested': total_invested,
        'Qty Buy': qty_buy,
        'Qty Sell': qty_sell,
        'Current Value': cur_val if cur_val > 0 else p_l_sold,
        'Return (%)': return_rate,
        'Nifty 50 Return (%)': nifty50_return,
        'Nifty 500 Return (%)': nifty500_return,
        'Days Invested': days_invested,
        'Profit/Loss': profit_loss,
        'Return Diff vs Nifty 50 (%)': return_diff_nifty50,
        'Return Diff vs Nifty 500 (%)': return_diff_nifty500
    }

# Process all stocks
all_symbols = tradebook_df['symbol'].unique()
results = [get_stock_metrics(symbol, tradebook_df, holdings_df, nifty50_df, nifty500_df, today) for symbol in all_symbols]
results_df = pd.DataFrame(results)
# Sort by Return (%) in descending order
results_df = results_df.sort_values(by='Return (%)', ascending=False)
results_df['Return (%)'] = results_df['Return (%)'].apply(lambda x: f"{x:.2f}%" if x is not None else 'N/A')
results_df['Nifty 50 Return (%)'] = results_df['Nifty 50 Return (%)'].apply(lambda x: f"{x:.2f}%" if x is not None else 'N/A')
results_df['Nifty 500 Return (%)'] = results_df['Nifty 500 Return (%)'].apply(lambda x: f"{x:.2f}%" if x is not None else 'N/A')
results_df['Return Diff vs Nifty 50 (%)'] = results_df['Return Diff vs Nifty 50 (%)'].apply(lambda x: f"{x:.2f}%" if x is not None else 'N/A')
results_df['Return Diff vs Nifty 500 (%)'] = results_df['Return Diff vs Nifty 500 (%)'].apply(lambda x: f"{x:.2f}%" if x is not None else 'N/A')
results_df['Days Invested'] = results_df['Days Invested'].astype(int)

# Calculate total portfolio return
total_invested = sum([r['Invested'] for r in results if r['Invested'] > 0])
total_current_value = sum([r['Current Value'] for r in results])
total_profit_loss = sum([r['Profit/Loss'] for r in results])
first_dates = [tradebook_df[tradebook_df['symbol'] == r['Instrument']]['trade_date'].min() for r in results if r['Invested'] > 0]
days_total = (today - min(first_dates)).days if first_dates else 0
total_return = simple_annualized_return(total_profit_loss, total_invested, days_total) if days_total > 0 else None
# Calculate total index returns
total_nifty50_return = calculate_index_return(nifty50_df, min(first_dates), today) if first_dates else None
total_nifty500_return = calculate_index_return(nifty500_df, min(first_dates), today) if first_dates else None
total_diff_nifty50 = total_return - total_nifty50_return if total_return is not None and total_nifty50_return is not None else None
total_diff_nifty500 = total_return - total_nifty500_return if total_return is not None and total_nifty500_return is not None else None

# Create second table for stocks with return < 1.5 * Nifty 50 or Nifty 500 return
underperforming_stocks = results_df[
    (results_df['Return (%)'].apply(lambda x: float(x.rstrip('%')) if x != 'N/A' else float('-inf')) <
     results_df['Nifty 50 Return (%)'].apply(lambda x: 1.5 * float(x.rstrip('%')) if x != 'N/A' else float('inf'))) |
    (results_df['Return (%)'].apply(lambda x: float(x.rstrip('%')) if x != 'N/A' else float('-inf')) <
     results_df['Nifty 500 Return (%)'].apply(lambda x: 1.5 * float(x.rstrip('%')) if x != 'N/A' else float('inf')))
]
underperforming_table = underperforming_stocks[['Instrument', 'Return (%)', 'Nifty 50 Return (%)', 'Nifty 500 Return (%)', 'Days Invested', 'Profit/Loss']]

# Print results
print("\nStock-wise data (sorted by Return %):")
print(results_df[['Instrument', 'Invested', 'Qty Buy', 'Qty Sell', 'Current Value', 'Return (%)', 'Days Invested', 'Profit/Loss', 'Return Diff vs Nifty 50 (%)', 'Return Diff vs Nifty 500 (%)']].to_string(index=False))
print(f"\nTotal invested: {total_invested:.2f}")
print(f"Total current value: {total_current_value:.2f}")
print(f"Total profit/loss: {total_profit_loss:.2f}")
print(f"Total portfolio return: {total_return:.2f}%" if total_return is not None else "Cannot calculate total portfolio return")
print(f"Total return diff vs Nifty 50: {total_diff_nifty50:.2f}%" if total_diff_nifty50 is not None else "Cannot calculate total return diff vs Nifty 50")
print(f"Total return diff vs Nifty 500: {total_diff_nifty500:.2f}%" if total_diff_nifty500 is not None else "Cannot calculate total return diff vs Nifty 500")

print("\nStocks with Return < 1.5 * Nifty 50 or Nifty 500 Return:")
print(underperforming_table.to_string(index=False))