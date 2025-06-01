import os
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# Define file paths
money_market_file = r"C:\Users\rohit\Documents\stocks\money_market_buysstocks.csv"
investing_file = r"C:\Users\rohit\Documents\stocks\investing_data.csv"
buy_output_file = r"C:\Users\rohit\Documents\stocks\filtered_combined_data.csv"
sell_output_file = r"C:\Users\rohit\Documents\stocks\sell_records_data.csv"
neutral_output_file = r"C:\Users\rohit\Documents\stocks\neutral_records_data.csv"

try:
    # Load the money market and investing data files
    money_market_data = pd.read_csv(money_market_file)
    investing_data = pd.read_csv(investing_file)

    # Rename columns to lowercase, replace spaces with underscores, and prefix with m_ and i_
    money_market_data.columns = ["m_" + col.lower().replace(" ", "_") for col in money_market_data.columns]
    investing_data.columns = ["i_" + col.lower().replace(" ", "_") for col in investing_data.columns]

    # Perform fuzzy matching for stock names
    investing_names = investing_data['i_name'].dropna().unique()

    def match_names(name, choices, threshold=80):
        match, score = process.extractOne(name, choices, scorer=fuzz.token_sort_ratio)
        return match if score >= threshold else None

    # Apply fuzzy matching to align stock names
    money_market_data['matched_name'] = money_market_data['m_stock_name'].apply(
        lambda x: match_names(x, investing_names)
    )

    # Merge using the matched names
    merged_data = pd.merge(
        money_market_data,
        investing_data,
        left_on="matched_name",
        right_on="i_name",
        how="inner"
    )


    print(merged_data.columns)
    # Further categorize records into Buy, Sell, and Neutral
    buy_records = merged_data[
        merged_data['i_weekly'].str.lower().isin(['buy','strong buy']) &
        merged_data['i_monthly'].str.lower().isin(['buy','strong buy']) &
        merged_data['i_daily_y'].str.lower().isin(['buy','strong buy']) &
        merged_data['i_hourly'].str.lower().isin(['buy','strong buy'])
    ].copy()

    sell_records = merged_data[
        merged_data['i_weekly'].str.lower().isin(['sell', 'strong sell']) |
        merged_data['i_monthly'].str.lower().isin(['sell', 'strong sell'])
    ].copy()

    excluded_stocks = pd.concat([buy_records['m_stock_name'], sell_records['m_stock_name']]).drop_duplicates()
    neutral_records = pd.merge(
        money_market_data[~money_market_data['m_stock_name'].isin(excluded_stocks)],
        investing_data,
        left_on="matched_name",
        right_on="i_name",
        how="left"
    ).copy()

    # Fill blank columns with 'N/A'
    buy_records.fillna("N/A", inplace=True)
    sell_records.fillna("N/A", inplace=True)
    neutral_records.fillna("N/A", inplace=True)

    # Save the filtered data to separate CSV files
    os.makedirs(os.path.dirname(buy_output_file), exist_ok=True)  # Ensure the directory exists
    buy_records.to_csv(buy_output_file, index=False)

    os.makedirs(os.path.dirname(sell_output_file), exist_ok=True)  # Ensure the directory exists
    sell_records.to_csv(sell_output_file, index=False)

    os.makedirs(os.path.dirname(neutral_output_file), exist_ok=True)  # Ensure the directory exists
    neutral_records.to_csv(neutral_output_file, index=False)

    print(f"Buy records successfully saved to {buy_output_file}")
    print(f"Sell records successfully saved to {sell_output_file}")
    print(f"Neutral records successfully saved to {neutral_output_file}")

    import pandas as pd

    # 1. Read the full CSV
    df = pd.read_csv(r"C:\Users\rohit\Documents\stocks\filtered_combined_data.csv")
    codes = df[['m_stock_code','m_stock_name']].copy()
    codes['m_stock_code'] = codes['m_stock_code'].str.upper()
    # 3. Write to a new CSV (no index column)
    codes.to_csv(r"C:\Users\rohit\Documents\stocks\stock_codes.csv", index=False)


except Exception as e:
    print(f"Error during processing: {e}")



quit()
df = pd.read_csv(r"C:\Users\rohit\Documents\stocks\money_market_buysstocks.csv")
print(df)
codes = df[['Stock Code']].copy()
codes['Stock Code'] = codes['Stock Code'].str.upper()
print(codes)








names = df[['m_stock_name']].copy()
names['m_stock_name'] = names['m_stock_name'].str.upper()

    # 3. Write to a new CSV (no index column)



