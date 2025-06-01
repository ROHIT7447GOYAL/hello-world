import pandas as pd
import numpy as np

# 1) Load data from the new CSV format
df = pd.read_csv('option_chain.csv')

records = []
for stock in df['Symbol'].unique():
    sub = df[df['Symbol'] == stock]
    underlying = float(sub['CurrentPrice'].iloc[0])

    # 2) Split into calls and puts, using 'Last' as the premium
    calls = sub[sub['OptionType'] == 'Call'][['Strike', 'Last']].dropna()
    puts  = sub[sub['OptionType'] == 'Put'][ ['Strike', 'Last']].dropna()

    # 3) Build all possible collars
    for _, put in puts.iterrows():
        for _, call in calls.iterrows():
            put_strike  = float(put['Strike'])
            call_strike = float(call['Strike'])
            if not (put_strike < underlying < call_strike):
                continue

            put_prem     = float(put['Last'])
            call_credit  = float(call['Last'])
            net_prem     = put_prem - call_credit
            net_prem_pct = net_prem / underlying * 100

            max_loss_pct   = ((underlying - put_strike) + net_prem) / underlying * 100
            max_profit_pct = ((call_strike - underlying) - net_prem) / underlying * 100

            records.append({
                'Stock':         stock,
                'Underlying':    underlying,
                'Put Strike':    put_strike,
                'Call Strike':   call_strike,
                'Put Premium':   round(put_prem,    2),
                'Call Credit':   round(call_credit, 2),
                'Net Premium':   round(net_prem,     2),
                'Net Prem %':    round(net_prem_pct, 3),
                'Max Loss %':    round(max_loss_pct, 3),
                'Max Profit %':  round(max_profit_pct,3)
            })

# 4) Create DataFrame of collars
collars = pd.DataFrame(records)

# 5) Apply your filter criteria
filtered = collars[
    (collars['Net Prem %'] <= 0.5) &
    (collars['Max Loss %'].between(0, 9)) &
    (collars['Max Profit %'].between(3, 15)) &
    ((collars['Max Profit %'] - collars['Max Loss %']) >= -3)
].copy()

# 6) Compute scenario P/L for ±1% to ±8%
##pct_moves = [-0.08, -0.07, -0.06, -0.05, -0.04, -0.03, -0.02, -0.01,0.01,  0.02,  0.03,  0.04,  0.05,  0.06,  0.07,  0.08]
pct_moves = [ -0.04, -0.03, -0.02, -0.01, 0.01,  0.02,  0.03,  0.04]
scenario_cols = []
for pct in pct_moves:
    col = f'PL_{int(pct*100)}%'
    new_price = filtered['Underlying'] * (1 + pct)
    fut_pnl   = new_price - filtered['Underlying']
    put_pnl   = np.maximum(filtered['Put Strike'] - new_price, 0) - filtered['Put Premium']
    call_pnl  = filtered['Call Credit'] - np.maximum(new_price - filtered['Call Strike'], 0)
    filtered[col] = ((fut_pnl + put_pnl + call_pnl) / filtered['Underlying'] * 100).round(3)
    scenario_cols.append(col)

# 7) Calculate 'Complete Total PL %'
pl_total = 0
for n in range(1, 5):
    up = filtered[f'PL_{n}%']
    dn = filtered[f'PL_-{n}%']
    adjusted_dn = np.where(dn >= 0, dn, -np.abs(dn))
    pl_total += up + adjusted_dn
filtered['Complete Total PL %'] = np.round(pl_total, 3)

# 8) Keep only positive 'Complete Total PL %'
#filtered = filtered[filtered['Complete Total PL %'] > 0].copy()

# 9) Global ranking by 'Complete Total PL %'
gfiltered = filtered.copy()
gfiltered.sort_values('Complete Total PL %', ascending=False, inplace=True)
gfiltered['Complete Total Rank'] = (
    gfiltered['Complete Total PL %']
             .rank(method='min', ascending=False)
             .astype(int)
)

gfiltered=gfiltered[gfiltered['Put Strike']==23400]
gfiltered=gfiltered[gfiltered['Call Strike']==25350]

# 10) Prepare columns and print grouped by stock
cols_front = [
    'Stock','Put Strike','Call Strike','Put Premium','Call Credit',
    'Net Premium','Net Prem %','Max Loss %','Max Profit %',
    'Complete Total PL %','Complete Total Rank'
]
cols = cols_front + scenario_cols
sep = '-' * 140

if gfiltered.empty:
    print("No strategies meet the criteria.")
else:
    for stock, grp in gfiltered.groupby('Stock'):
        print(sep)
        print(f"Stock: {stock}")
        print(grp[cols].to_string(index=False))
        print(sep)
