##https://kite.zerodha.com/connect/login?api_key=at2abmzvtigjycl8&v=3
##iL4FzQscCc3lSahOuL6tkPjqVhL1rjqY
# Step 1: Set your API key and secret (replace with values from developers.kite.trade)
#api_key = "at2abmzvtigjycl8"  # From your login URL
#api_secret = "xu58yp87jzqg4sdumkkeqaiu0y4mw531"  # From "My apps" in Kite Connect dashboard


import csv
from kiteconnect import KiteConnect

# Step 1: Set your API key and access token from the first run
api_key = "at2abmzvtigjycl8"  # Your API key
access_token = "CYAzb42BoMrH9VfSL1e1sdHZlxearyrN"  # Replace with the access token printed in the first run

# Step 2: Initialize KiteConnect and set access token
kite = KiteConnect(api_key=api_key)
try:
    kite.set_access_token(access_token)
    print("Authentication successful!")
except Exception as e:
    print(f"Authentication failed: {e}")
    exit()

# Step 3: Fetch positions
try:
    positions = kite.positions()
    net_positions = positions["net"]
    print("Positions fetched successfully!")
except Exception as e:
    print(f"Failed to fetch positions: {e}")
    exit()

# Step 4: Define fields and file path for CSV
fields = ["tradingsymbol", "exchange", "product", "quantity", "average_price", "pnl"]
file_path = r"C:\Users\rohit\Documents\csvtohtml\positions.csv"

# Step 5: Write positions to CSV
try:
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        for position in net_positions:
            row = {field: position.get(field, '') for field in fields}
            writer.writerow(row)
    print(f"Positions exported to {file_path}")
except Exception as e:
    print(f"Failed to write to CSV: {e}")
    exit()