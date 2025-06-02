import pandas as pd
import subprocess

# Load the option chain data
df = pd.read_csv('option_chain.csv')

records = []
for stock in df['Symbol'].unique():
    sub = df[df['Symbol'] == stock].copy()
    ##underlying = float(sub['CurrentPrice'].iloc[0])
    underlying = 1457.6
    support = float(sub['Support'].iloc[0])
    resistance = float(sub['Resistance'].iloc[0])

    # Split calls & puts, including additional parameters
    calls = sub[sub['OptionType'] == 'Call'][['Strike', 'Last', 'IV', 'OI', 'ChngOI', 'Bid', 'Ask']].dropna()
    puts = sub[sub['OptionType'] == 'Put'][['Strike', 'Last', 'IV', 'OI', 'ChngOI', 'Bid', 'Ask']].dropna()

    # Build all possible collars for this stock
    for _, put in puts.iterrows():
        for _, call in calls.iterrows():
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
            })

# Create DataFrame of all collars
collars = pd.DataFrame(records)

# Apply filter criteria
filtered = collars[
    (collars['Net Prem %'] <= 0.5) &
    (collars['Max Loss %'].between(0, 7)) &
    (collars['Max Profit %'].between(3, 20)) &
    ((collars['Max Profit %'] - collars['Max Loss %']) >= -3) &
    ((collars['Move CE %'] - collars['Move PE %']) >= -3) &
    (collars['Net Prem %'] < collars['Diff %'])
].copy()

if filtered.empty:
    print("No setups meet the criteria.")
else:
    # Compute ranks
    filtered['net_prem_rank'] = filtered['Net Premium'].rank(method='min', ascending=True)
    filtered['liquidity_rank'] = filtered['liquidity'].rank(method='min', ascending=False)
    filtered['iv_diff_rank'] = filtered['iv_diff'].rank(method='min', ascending=False)
    filtered['avg_spread_rank'] = filtered['avg_spread'].rank(method='min', ascending=True)
    filtered['strike_distance_rank'] = filtered['strike_distance'].rank(method='min', ascending=True)

    # Compute weighted total rank
    filtered['weighted_total_rank'] = (
        0.25 * filtered['net_prem_rank'] +
        0.25 * filtered['liquidity_rank'] +
        0.15 * filtered['iv_diff_rank'] +
        0.20 * filtered['avg_spread_rank'] +
        0.15 * filtered['strike_distance_rank']
    )

    # Sort by weighted_total_rank ascending
    filtered = filtered.sort_values(by='weighted_total_rank', ascending=True)

    # Add Rank column
    filtered['Rank'] = range(1, len(filtered) + 1)

    # Create Reason column
    filtered['Reason'] = "Weighted Rank Score: " + filtered['weighted_total_rank'].round(2).astype(str)

    sep = '-' * 120
    # Print grouped by Stock
    for stock, group in filtered.groupby('Stock'):
        print(sep)
        print(f"\nStock: {stock}")
        print(group[['Rank', 'Current Price','Put Strike', 'Call Strike','Put Premium', 'Call Credit', 'Net Premium', 'Net Prem %' ,'Max Loss %', 'Max Profit %',
                     'Move PE %', 'Move CE %', 'Diff %', 'Risk %','Reason' ]].to_string(index=False))
        print(f"\n")


    # Save to CSV
    print(sep)
    csv_path = r'C:\Users\rohit\Documents\csvtohtml\afiltered_collars.csv'
    filtered = filtered[
        ['Rank', 'Put Strike', 'Call Strike', 'Max Loss %', 'Max Profit %', 'Net Prem %', 'net_prem_rank',
         'weighted_total_rank']]

    filtered = filtered[filtered["net_prem_rank"].between(1, 7)]
    filtered = filtered[filtered["Rank"].between(1, 7)]
    filtered.to_csv(csv_path, index=False)
    print(f"Filtered collars saved to {csv_path}")

    # Run csvtohtml.py
    subprocess.run(['python', 'csvtohtml.py'])