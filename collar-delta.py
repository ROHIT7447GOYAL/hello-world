import pandas as pd
import subprocess
from datetime import datetime
import mibian
import logging

# Set up logging
logging.basicConfig(filename='collar_strategy.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load the option chain data
try:
    df = pd.read_csv('option_chain.csv')
except Exception as e:
    logging.error(f"Failed to load option_chain.csv: {e}")
    print(f"Error: Could not load option_chain.csv - {e}")
    exit()

# Get expiry date and calculate days to expiration
try:
    expiry_str = df['Expiry'].iloc[0]
    expiry_date = datetime.strptime(expiry_str, "%d-%b-%Y")
    current_date = datetime.now()
    days_to_expiration = (expiry_date - current_date).days
    if days_to_expiration <= 0:
        logging.error("Expiry date has passed. Cannot calculate Greeks.")
        print("Error: Expiry date has passed. Cannot calculate Greeks.")
        exit()
except Exception as e:
    logging.error(f"Failed to parse expiry date: {e}")
    print(f"Error: Invalid expiry date format - {e}")
    exit()

# Set risk-free interest rate (India 10-year bond yield, June 2025)
interest_rate = 6.75  # Consider fetching dynamically from Trading Economics

records = []
for stock in df['Symbol'].unique():
    sub = df[df['Symbol'] == stock].copy()
    try:
        underlying = float(sub['CurrentPrice'].iloc[0])
        support = float(sub['Support'].iloc[0])
        resistance = float(sub['Resistance'].iloc[0])
    except Exception as e:
        logging.error(f"Failed to parse underlying, support, or resistance for {stock}: {e}")
        continue

    # Split calls & puts, including additional parameters
    calls = sub[sub['OptionType'] == 'Call'][['Strike', 'Last', 'IV', 'OI', 'ChngOI', 'Bid', 'Ask']].dropna()
    puts = sub[sub['OptionType'] == 'Put'][['Strike', 'Last', 'IV', 'OI', 'ChngOI', 'Bid', 'Ask']].dropna()

    # Build all possible collars for this stock
    for _, put in puts.iterrows():
        for _, call in calls.iterrows():
            try:
                put_strike = float(put['Strike'])
                call_strike = float(call['Strike'])
                # Only valid if put < underlying < call
                if not (put_strike < underlying < call_strike):
                    continue

                put_prem = float(put['Last'])
                call_credit = float(call['Last'])
                net_prem = put_prem - call_credit
                net_prem_pct = (net_prem / underlying) * 100

                max_loss = (underlying - put_strike) + net_prem
                max_loss_pct = (max_loss / underlying) * 100

                max_profit = (call_strike - underlying) - net_prem
                max_profit_pct = (max_profit / underlying) * 100

                # New calculations
                move_pe_pct = ((underlying - put_strike) / underlying) * 100
                move_ce_pct = ((call_strike - underlying) / underlying) * 100
                diff_pct = move_ce_pct - move_pe_pct

                # Calculate risk
                if diff_pct > 0 and net_prem_pct < 0:
                    risk_pct = diff_pct + abs(net_prem_pct)
                elif diff_pct > 0 and net_prem_pct > 0:
                    risk_pct = diff_pct - net_prem_pct
                elif diff_pct < 0 and net_prem_pct < 0:
                    risk_pct = diff_pct + abs(net_prem_pct)
                elif diff_pct < 0 and net_prem_pct > 0:
                    risk_pct = diff_pct - net_prem_pct
                else:
                    risk_pct = diff_pct

                # Calculate additional metrics
                put_bid = float(put['Bid'])
                put_ask = float(put['Ask'])
                call_bid = float(call['Bid'])
                call_ask = float(call['Ask'])
                put_last = float(put['Last'])
                call_last = float(call['Last'])

                put_spread = (put_ask - put_bid) / put_last if put_last != 0 else float('inf')
                call_spread = (call_ask - call_bid) / call_last if call_last != 0 else float('inf')
                avg_spread = (put_spread + call_spread) / 2 if put_spread != float('inf') and call_spread != float('inf') else float('inf')

                liquidity = float(put['OI']) + float(call['OI'])
                iv_diff = float(call['IV']) - float(put['IV'])  # call IV - put IV
                strike_distance = abs(put_strike - support) + abs(call_strike - resistance)

                # Calculate Greeks using mibian
                try:
                    put_greeks = mibian.BS([underlying, put_strike, interest_rate, days_to_expiration], volatility=put['IV'])
                    call_greeks = mibian.BS([underlying, call_strike, interest_rate, days_to_expiration], volatility=call['IV'])
                    put_delta = put_greeks.putDelta
                    call_delta = call_greeks.callDelta
                    net_delta = put_delta - call_delta
                    net_delta_abs = abs(net_delta)
                    put_gamma = put_greeks.putGamma
                    call_gamma = call_greeks.callGamma
                    net_gamma = put_gamma - call_gamma
                    put_theta = put_greeks.putTheta
                    call_theta = call_greeks.callTheta
                    net_theta = put_theta - call_theta
                    put_vega = put_greeks.vega
                    call_vega = call_greeks.vega
                    net_vega = put_vega - call_vega
                except Exception as e:
                    logging.warning(f"Error calculating Greeks for {stock} (Put Strike: {put_strike}, Call Strike: {call_strike}): {e}")
                    net_delta_abs = float('inf')
                    net_gamma = float('inf')
                    net_theta = float('inf')
                    net_vega = float('inf')

                records.append({
                    'Stock': stock,
                    'Current Price': underlying,
                    'Put Strike': put_strike,
                    'Call Strike': call_strike,
                    'Put Premium': round(put_prem, 2),
                    'Call Credit': round(call_credit, 2),
                    'Net Premium': round(net_prem, 2),
                    'Net Prem %': round(net_prem_pct, 3),
                    'Max Loss %': round(max_loss_pct, 3),
                    'Max Profit %': round(max_profit_pct, 3),
                    'Move PE %': round(move_pe_pct, 3),
                    'Move CE %': round(move_ce_pct, 3),
                    'Diff %': round(diff_pct, 3),
                    'Risk %': round(risk_pct, 3),
                    'Put IV': put['IV'],
                    'Call IV': call['IV'],
                    'liquidity': liquidity,
                    'iv_diff': iv_diff,
                    'avg_spread': avg_spread,
                    'strike_distance': strike_distance,
                    'net_delta_abs': net_delta_abs,
                    'net_gamma': net_gamma,
                    'net_theta': net_theta,
                    'net_vega': net_vega,
                })
            except Exception as e:
                logging.warning(f"Error processing strategy for {stock} (Put Strike: {put_strike}, Call Strike: {call_strike}): {e}")
                continue

# Create DataFrame of all collars
collars = pd.DataFrame(records)

# Apply filter criteria with max profit and loss of 4%
filtered = collars[
    (collars['Net Prem %'] <= 0) &
    (collars['Max Loss %'].between(0, 4)) &
    (collars['Max Profit %'].between(0, 4)) &
    ((collars['Max Profit %'] - collars['Max Loss %']) >= -3) &
    ((collars['Move CE %'] - collars['Move PE %']) >= -3) &
    (collars['Net Prem %'] < collars['Diff %'])
].copy()

if filtered.empty:
    print("No setups meet the criteria.")
    logging.info("No collar strategies met the filter criteria.")
else:
    # Compute ranks
    filtered['net_prem_rank'] = filtered['Net Premium'].rank(method='min', ascending=True)
    filtered['liquidity_rank'] = filtered['liquidity'].rank(method='min', ascending=False)
    filtered['iv_diff_rank'] = filtered['iv_diff'].rank(method='min', ascending=False)
    filtered['avg_spread_rank'] = filtered['avg_spread'].rank(method='min', ascending=True)
    filtered['strike_distance_rank'] = filtered['strike_distance'].rank(method='min', ascending=True)
    filtered['net_delta_abs_rank'] = filtered['net_delta_abs'].rank(method='min', ascending=True)
    filtered['net_gamma_rank'] = filtered['net_gamma'].rank(method='min', ascending=True)
    filtered['net_theta_rank'] = filtered['net_theta'].rank(method='min', ascending=True)
    filtered['net_vega_rank'] = filtered['net_vega'].rank(method='min', ascending=True)

    # Compute weighted total rank
    filtered['weighted_total_rank'] = (
        0.20 * filtered['net_prem_rank'] +
        0.20 * filtered['liquidity_rank'] +
        0.15 * filtered['iv_diff_rank'] +
        0.15 * filtered['avg_spread_rank'] +
        0.15 * filtered['strike_distance_rank'] +
        0.15 * filtered['net_delta_abs_rank'] +
        0.05 * filtered['net_gamma_rank'] +
        0.05 * filtered['net_theta_rank'] +
        0.05 * filtered['net_vega_rank']
    )

    # Sort by weighted_total_rank ascending
    filtered = filtered.sort_values(by='weighted_total_rank', ascending=True)

    # Add Rank column
    filtered['Rank'] = range(1, len(filtered) + 1)

    # Create Reason column
    filtered['Reason'] = (
        "Weighted Rank Score: " + filtered['weighted_total_rank'].round(2).astype(str) +
        " (NetPrem:" + filtered['net_prem_rank'].astype(str) +
        ", Liquidity:" + filtered['liquidity_rank'].astype(str) +
        ", IVDiff:" + filtered['iv_diff_rank'].astype(str) +
        ", Spread:" + filtered['avg_spread_rank'].astype(str) +
        ", StrikeDist:" + filtered['strike_distance_rank'].astype(str) +
        ", NetDeltaAbs:" + filtered['net_delta_abs_rank'].astype(str) +
        ", NetGamma:" + filtered['net_gamma_rank'].astype(str) +
        ", NetTheta:" + filtered['net_theta_rank'].astype(str) +
        ", NetVega:" + filtered['net_vega_rank'].astype(str) + ")"
    )

    # Print grouped by Stock
    for stock, group in filtered.groupby('Stock'):
        print(f"\nStock: {stock}")
        print(group[['Rank', 'Put Strike', 'Call Strike', 'Net Premium', 'Max Loss %', 'Max Profit %', 'Reason']].to_string(index=False))
        logging.info(f"Processed strategies for {stock}: {len(group)} strategies")

    # Save to CSV
    csv_path = r'C:\Users\rohit\Documents\csvtohtml\filtered_collars.csv'
    filtered.to_csv(csv_path, index=False)
    print(f"Filtered collars saved to {csv_path}")
    logging.info(f"Filtered collars saved to {csv_path}")

    # Run csvtohtml.py
    try:
        subprocess.run(['python', 'csvtohtml.py'])
        logging.info("Successfully ran csvtohtml.py")
    except Exception as e:
        logging.error(f"Failed to run csvtohtml.py: {e}")
        print(f"Error: Failed to run csvtohtml.py - {e}")