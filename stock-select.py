import pandas as pd
from thefuzz import process, fuzz
from collections import defaultdict
import datetime
import os
import re
import difflib
import glob
import datetime
import subprocess

# Define the directory path
directory = os.path.join("C:\\", "Users", "rohit", "Documents", "stocks")

# Pattern to match positions.csv or positions(number).csv
pattern = os.path.join(directory, "positions*.csv")

# Get all files matching the pattern
matching_files = glob.glob(pattern)

# Filter files to ensure they match positions.csv or positions(number).csv
valid_files = [
    f for f in matching_files
    if re.match(r'.*positions(\(\d+\))?\.csv$', f)
]

# Find the most recently created file and delete others
if valid_files:
    input_path = max(valid_files, key=os.path.getctime)
    print(f"Keeping latest file: {input_path}")

    # Delete all other matching files
    for file in valid_files:
        if file != input_path:
            try:
                os.remove(file)
                print(f"Deleted file: {file}")
            except OSError as e:
                print(f"Error deleting file {file}: {e}")
else:
    raise FileNotFoundError("No files matching 'positions*.csv' found in the directory.")




# Function to standardize stock names
def standardize_name(name):
    if pd.isna(name):
        return name
    name = name.lower().strip()
    suffixes = ['ltd.', 'limited', 'inc.', 'corporation', 'co.', 'corp.', 'company', 'plc', 'group']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name.replace(suffix, '').strip()
    return name

# Function to extract stock code from instrument name
def extract_stock_code(instrument):
    for i, char in enumerate(instrument):
        if char.isdigit():
            return instrument[:i]
    return instrument

# Set base path and output path
base_path = r"C:\Users\rohit\Documents\stocks"
output_path = r"C:\Users\rohit\Documents\csvtohtml"

# Set today's date dynamically
today = datetime.date.today()
date_str = f"{today.strftime('%B')} {today.day}, {today.year}"

# Define the directory path
folder_path = base_path

# Patterns to match Collar_{date_str}*.csv and ALL PARAMETERS_{date_str}*.csv
collar_pattern = os.path.join(folder_path, f"Collar_{date_str}*.csv")
params_pattern = os.path.join(folder_path, f"ALL PARAMETERS_{date_str}*.csv")

# Get all files matching the patterns
collar_files = glob.glob(collar_pattern)
params_files = glob.glob(params_pattern)

# Filter files to match Collar_{date_str}*.csv or Collar_{date_str}(number).csv
valid_collar_files = [
    f for f in collar_files
    if re.match(rf'.*Collar_{re.escape(date_str)}(\(\d+\))?\.csv$', f)
]

# Filter files to match ALL PARAMETERS_{date_str}*.csv or ALL PARAMETERS_{date_str}(number).csv
valid_params_files = [
    f for f in params_files
    if re.match(rf'.*ALL PARAMETERS_{re.escape(date_str)}(\(\d+\))?\.csv$', f)
]

# Process Collar files: Keep the latest, delete others
if valid_collar_files:
    today_collar = max(valid_collar_files, key=os.path.getctime)
    print(f"Keeping latest Collar file: {today_collar}")
    for file in valid_collar_files:
        if file != today_collar:
            try:
                os.remove(file)
                print(f"Deleted {file}")
            except OSError as e:
                print(f"Error deleting file {file}: {e}")
else:
    print(f"No files matching 'Collar_{date_str}*.csv' found in the directory.")

# Process ALL PARAMETERS files: Keep the latest, delete others
if valid_params_files:
    today_params = max(valid_params_files, key=os.path.getctime)
    print(f"Keeping latest ALL PARAMETERS file: {today_params}")
    for file in valid_params_files:
        if file != today_params:
            try:
                os.remove(file)
                print(f"Deleted {file}")
            except OSError as e:
                print(f"Error deleting file {file}: {e}")
else:
    print(f"No files matching 'ALL PARAMETERS_{date_str}*.csv' found in the directory.")

# Define file names
money_market_file = "money_market_buysstocks.csv"
stock_codes_file = "stock_codes.csv"
collar_file = today_collar
all_params_file = today_params
investing_file = "investing_data.csv"
positions_file = input_path

# Define output files
filtered_output = os.path.join(output_path, "combined_stock_data_filtered.csv")
top7_output = os.path.join(output_path, "top_7_stock_data_filtered.csv")

# Define source priority (lower number = higher priority)
source_priority = {'collar': 0, 'all_params': 1, 'money_market': 2, 'stock_codes': 3}

# Step 1: Read input files and collect stock codes and names
mm_df = pd.read_csv(os.path.join(base_path, money_market_file))
mm_data = mm_df[['Stock Code', 'Stock Name']].rename(columns={'Stock Code': 'stock_code', 'Stock Name': 'stock_name'})
mm_data['source'] = 'money_market'

sc_df = pd.read_csv(os.path.join(base_path, stock_codes_file))
sc_data = sc_df[['m_stock_code', 'm_stock_name']].rename(columns={'m_stock_code': 'stock_code', 'm_stock_name': 'stock_name'})
sc_data['source'] = 'stock_codes'

collar_df = pd.read_csv(os.path.join(collar_file))
collar_data = collar_df[['NSE Code', 'Stock']].rename(columns={'NSE Code': 'stock_code', 'Stock': 'stock_name'})
collar_data['source'] = 'collar'

all_params_df = pd.read_csv(os.path.join(all_params_file))
all_params_data = all_params_df[['NSE Code', 'Stock']].rename(columns={'NSE Code': 'stock_code', 'Stock': 'stock_name'})
all_params_data['source'] = 'all_params'

# Combine all data
all_data = pd.concat([mm_data, sc_data, collar_data, all_params_data], ignore_index=True)
all_data['priority'] = all_data['source'].map(source_priority)
all_data['standard_name'] = all_data['stock_name'].apply(standardize_name)

# Step 2: Group entries by stock name similarity
groups = []
processed = set()
for i, row in all_data.iterrows():
    if i not in processed and pd.notna(row['standard_name']):
        group = [row]
        processed.add(i)
        for j in range(i + 1, len(all_data)):
            if j not in processed and pd.notna(all_data.iloc[j]['standard_name']):
                other_row = all_data.iloc[j]
                similarity = fuzz.token_set_ratio(row['standard_name'], other_row['standard_name'])
                if similarity >= 80:
                    group.append(other_row)
                    processed.add(j)
        groups.append(group)

# Step 3: Create combined DataFrame from groups
combined_data = []
for group in groups:
    group_df = pd.DataFrame(group)
    representative = group_df.loc[group_df['priority'].idxmin()]
    sources = set(group_df['source'])
    row = {
        'stock_code': representative['stock_code'],
        'stock_name': representative['stock_name'],
        'money_market': 1 if 'money_market' in sources else 0,
        'stock_codes': 1 if 'stock_codes' in sources else 0,
        'collar': 1 if 'collar' in sources else 0,
        'all_params': 1 if 'all_params' in sources else 0,
        'total': len(sources)
    }
    if row['total'] >= 2:
        combined_data.append(row)
combined_df = pd.DataFrame(combined_data)

# Step 4: Read investing_data.csv and preprocess names
investing_df = pd.read_csv(os.path.join(base_path, investing_file))
investing_df['standard_name'] = investing_df['Name'].apply(standardize_name)
names_list = investing_df['standard_name'].tolist()

# Step 5: Use fuzzy matching to add performance columns
for index, row in combined_df.iterrows():
    stock_name = row['stock_name']
    if pd.notna(stock_name):
        standard_name = standardize_name(stock_name)
        best_match = process.extractOne(standard_name, names_list, scorer=fuzz.token_set_ratio)
        if best_match and best_match[1] >= 80:
            match_name = best_match[0]
            match_row = investing_df[investing_df['standard_name'] == match_name].iloc[0]
            combined_df.at[index, 'Daily_x'] = match_row['Daily_x']
            combined_df.at[index, '1 Week'] = match_row['1 Week']
            combined_df.at[index, '1 Month'] = match_row['1 Month']
            combined_df.at[index, '1 Year'] = match_row['1 Year']

# Step 6: Convert performance columns to numerical values
combined_df['Daily_x_num'] = pd.to_numeric(combined_df['Daily_x'].str.replace('%', ''), errors='coerce')
combined_df['1_Week_num'] = pd.to_numeric(combined_df['1 Week'].str.replace('%', ''), errors='coerce')
combined_df['1_Month_num'] = pd.to_numeric(combined_df['1 Month'].str.replace('%', ''), errors='coerce')
combined_df['1_Year_num'] = pd.to_numeric(combined_df['1 Year'].str.replace('%', ''), errors='coerce')

# Step 7: Filter based on performance criteria
filtered_df = combined_df[
    ((combined_df['Daily_x_num'].isna()) | (combined_df['Daily_x_num'] <= 1.5)) &
    ((combined_df['1_Week_num'].isna()) | (combined_df['1_Week_num'] <= 3.5)) &
    ((combined_df['1_Month_num'].isna()) | (combined_df['1_Month_num'] <= 6)) &
    ((combined_df['1_Year_num'].isna()) | (combined_df['1_Year_num'] <= 50))
]

# Step 8: Process positions.csv to add position_value and has_position
positions_df = pd.read_csv(os.path.join(positions_file))
positions_df['stock_code'] = positions_df['Instrument'].apply(extract_stock_code).str.upper()
positions_df['position_value'] = positions_df['Avg.'] * positions_df['Qty.']
position_sum = positions_df.groupby('stock_code')['position_value'].sum()
filtered_df['position_value'] = filtered_df['stock_code'].map(position_sum).fillna(0)
filtered_df['has_position'] = filtered_df['stock_code'].map(lambda x: 1 if x in position_sum else 0)

# Step 9: Save filtered data with specified columns
os.makedirs(output_path, exist_ok=True)
filtered_df[['stock_code', 'stock_name', 'money_market', 'stock_codes', 'collar', 'all_params', 'total', 'position_value', 'has_position', 'Daily_x_num', '1_Week_num', '1_Month_num', '1_Year_num']].to_csv(filtered_output, index=False)

# Step 10: Create top_7_stock_data_filtered.csv
top7_df = filtered_df.sort_values(by='total', ascending=False).head(7)
top7_df[['stock_code', 'total', 'stock_name', 'position_value', 'has_position', 'Daily_x_num', '1_Week_num', '1_Month_num', '1_Year_num']].to_csv(top7_output, index=False)

print("Processing complete. Filtered CSV files have been saved.")

subprocess.run(['python', 'csvtohtml.py'])