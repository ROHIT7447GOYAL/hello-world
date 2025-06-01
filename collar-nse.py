import pandas as pd

# Load the option chain data
df = pd.read_csv('option_chain.csv')

records = []
for stock in df['Symbol'].unique():
    sub = df[df['Symbol'] == stock].copy()
    underlying = float(sub['CurrentPrice'].iloc[0])

    # Split calls & puts, using 'Last' as the premium
    calls = sub[sub['OptionType'] == 'Call'][['Strike', 'Last', 'IV']].dropna()
    puts = sub[sub['OptionType'] == 'Put'][['Strike', 'Last', 'IV']].dropna()

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
                'Call IV': call['IV']
            })

# Create DataFrame of all collars
collars = pd.DataFrame(records)

# Apply filter criteria
filtered = collars[
    (collars['Net Prem %'] <= 0) &
    (collars['Max Loss %'].between(0, 7)) &
    (collars['Max Profit %'].between(3, 20)) &
    ((collars['Max Profit %'] - collars['Max Loss %']) >= -3) &
    ((collars['Move CE %'] - collars['Move PE %']) >= -3) &
    ((collars['Net Prem %'] < collars['Diff %']))
].copy()

# Sort by smallest net premium and add rank
filtered.sort_values(by='Net Premium', inplace=True)
filtered['Rank'] = range(1, len(filtered) + 1)

# Save to CSV
filtered.to_csv('filtered_collars.csv', index=False)
print("Filtered collars saved to filtered_collars.csv")