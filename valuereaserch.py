import pandas as pd
import xlrd
import os
import glob
import re
from datetime import date, datetime

# Get today's date for matching
today = date.today()
today_str = today.strftime("%d-%b-%Y").lstrip("0")  # e.g., "3-Jun-2025"

# Directory and file pattern
directory = r"C:\Users\rohit\Documents\stocks"
file_pattern = r"bse-500-index-*-*.xls"
output_csv = r"C:\Users\rohit\Documents\stocks\value.csv"

# Find all files matching the pattern
files = glob.glob(os.path.join(directory, file_pattern))

# Filter for today's date and get the latest file
matching_file = None
latest_time = None
for file in files:
    # Extract date from filename using regex
    match = re.search(r"bse-500-index-(\d{1,2}-[A-Za-z]{3}-\d{4})--(\d{4})\.xls", file)
    if match:
        file_date_str = match.group(1)
        file_time_str = match.group(2)
        try:
            file_date = datetime.strptime(file_date_str, "%d-%b-%Y").date()
            if file_date == today:
                # Compare time to get the latest file for today
                if latest_time is None or file_time_str > latest_time:
                    matching_file = file
                    latest_time = file_time_str
        except ValueError:
            continue

if not matching_file:
    print(f"No file found matching today's date: {today_str}")
    exit()

# Read the selected file
try:
    # Use xlrd directly to open the workbook, ignoring corruption
    workbook = xlrd.open_workbook(matching_file, ignore_workbook_corruption=True)
    sheet = workbook.sheet_by_index(0)  # First sheet

    # Extract all data into a list
    data = [sheet.row_values(i) for i in range(sheet.nrows)]

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Print full content to inspect
    print("Full Content of the Excel File:")
    print(df)

    # Remove text rows and set table
    table_df = df.iloc[5:].reset_index(drop=True)  # Table starts at row 5 (index 5)
    table_df.columns = table_df.iloc[0]  # Set row 5 as headers
    table_df = table_df.drop(0).reset_index(drop=True)  # Remove header row from data

    # Save table to CSV (only stock details with headers)
    table_df.to_csv(output_csv, index=False)
    print(f"Stock details saved to {output_csv}")

    # Print table
    print("\nStock Details Table:")
    if not table_df.empty:
        print(table_df)
    else:
        print("No table data found.")
except Exception as e:
    print(f"Error reading file {matching_file}: {e}")
    exit()

# Delete older files with the same pattern
for file in files:
    if file != matching_file and re.match(r".*bse-500-index-\d{1,2}-[A-Za-z]{3}-\d{4}--\d{4}\.xls", file):
        try:
            os.remove(file)
            print(f"Deleted older file: {file}")
        except Exception as e:
            print(f"Error deleting {file}: {e}")