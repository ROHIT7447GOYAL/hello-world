import pandas as pd
import os
import glob
from datetime import datetime

# Define the folder path
folder_path = r'C:\Users\rohit\Documents\stocks'

# Get today's date in non-zero-padded format (e.g., 3_6_2025)
today = datetime.now().strftime('%d_%m_%Y').replace('0', '', 1).replace('0', '', 1)  # Remove leading zeros from day and month

# Find all CSV files matching the pattern
file_pattern = os.path.join(folder_path, f'my_screener_*{today}*.csv')
csv_files = glob.glob(file_pattern)

# If no files found, exit with an error
if not csv_files:
    raise FileNotFoundError(f"No CSV files found matching pattern {file_pattern}")

# Select the latest file based on modification time
latest_file = max(csv_files, key=os.path.getmtime)
print(f"Selected file: {latest_file}")

# Delete older files with the same pattern
for file in csv_files:
    if file != latest_file:
        os.remove(file)
        print(f"Deleted older file: {file}")

# Read the CSV with error handling
try:
    df = pd.read_csv(latest_file, sep=',', encoding='utf-8', on_bad_lines='skip')
except pd.errors.ParserError as e:
    print(f"ParserError: {e}")
    print("Attempting to read with Python engine...")
    df = pd.read_csv(latest_file, sep=',', encoding='utf-8', engine='python', on_bad_lines='skip')

# Define relevant columns
cols = [
    'Name', 'Ticker', 'Close Price', 'Super Trend', 'Fundamental Score',
    'Percentage Upside', 'Total no. of analysts', 'Percentage Buy Reco’s',
    'Value Momentum Rank', 'Price Momentum Rank', 'Earnings Quality Rank',
    'Price to Intrinsic Value Rank'
]

# Select only the relevant columns, handle missing columns
available_cols = [col for col in cols if col in df.columns]
df = df[available_cols]

# Convert to numeric, handling errors
numeric_cols = [col for col in available_cols if col not in ['Name', 'Ticker']]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop rows with NaN in filter columns
filter_cols = ['Total no. of analysts', 'Percentage Upside', 'Percentage Buy Reco’s', 'Close Price', 'Super Trend']
available_filter_cols = [col for col in filter_cols if col in df.columns]
df = df.dropna(subset=available_filter_cols)

# Apply filters
df_filtered = df[
    (df['Total no. of analysts'] > 5) &
    (df['Percentage Upside'] >= 6) &
    (df['Percentage Buy Reco’s'] > 70) &
    (df['Close Price'] > df['Super Trend'])
]

# Compute Super Trend Distance
df_filtered['Super Trend Distance'] = (df_filtered['Close Price'] - df_filtered['Super Trend']) / df_filtered['Super Trend']

# Define metrics for ranking
metrics = [
    'Fundamental Score', 'Super Trend Distance', 'Percentage Upside',
    'Percentage Buy Reco’s', 'Value Momentum Rank', 'Price Momentum Rank',
    'Earnings Quality Rank', 'Price to Intrinsic Value Rank'
]

# Drop rows with NaN in metrics
available_metrics = [m for m in metrics if m in df_filtered.columns]
df_filtered = df_filtered.dropna(subset=available_metrics)

# Compute ranks for each metric (higher value gets lower rank number)
for metric in available_metrics:
    df_filtered[f'rank_{metric}'] = df_filtered[metric].rank(ascending=False, method='min')

# Define weights
weights = {
    'Fundamental Score': 1,
    'Super Trend Distance': 1.5,
    'Percentage Upside': 1,
    'Percentage Buy Reco’s': 1,
    'Value Momentum Rank': 1,
    'Price Momentum Rank': 2,
    'Earnings Quality Rank': 1,
    'Price to Intrinsic Value Rank': 1
}

# Compute composite score
df_filtered['composite_score'] = 0
for metric in available_metrics:
    df_filtered['composite_score'] += weights[metric] * df_filtered[f'rank_{metric}']

# Sort by composite_score ascending (lower is better)
df_sorted = df_filtered.sort_values(by='composite_score')

# Select top 25 or all if less than 25
if len(df_sorted) > 25:
    top_25 = df_sorted.head(25)
else:
    top_25 = df_sorted

# Output the results
print(f"Number of stocks passing filters: {len(df_filtered)}")
print("Top stocks for Collar Options Strategy:")
print(top_25[['Name', 'Ticker']])

top_25.to_csv(r'C:\Users\rohit\Documents\stocks\tickertape.csv', index=False)