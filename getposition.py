import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from urllib.parse import urlparse, parse_qs
from kiteconnect import KiteConnect

# Step 1: Set your API key and secret (replace with values from developers.kite.trade)
api_key = "at2abmzvtigjycl8"  # From your login URL
api_secret = "xu58yp87jzqg4sdumkkeqaiu0y4mw531"  # From "My apps" in Kite Connect dashboard

# Step 2: Initialize KiteConnect
kite = KiteConnect(api_key=api_key)

# Step 3: Set up Selenium WebDriver (using Chrome)
# Replace 'path_to_chromedriver' with the path to your ChromeDriver executable if not in PATH
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode (no browser window)
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=options)

# Step 4: Generate login URL and open it in Selenium
login_url = kite.login_url()
print(f"Opening login URL: {login_url}")
driver.get(login_url)

# Step 5: Automate login (replace with your Zerodha credentials)
try:
    # Enter Client ID (Zerodha User ID)
    client_id_field = driver.find_element(By.ID, "userid")
    client_id_field.send_keys("your_zerodha_client_id")  # Replace with your Zerodha Client ID

    # Enter Password
    password_field = driver.find_element(By.ID, "password")
    password_field.send_keys("your_zerodha_password")  # Replace with your Zerodha password

    # Click Login button
    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_button.click()

    # Wait for 2FA (TOTP or PIN)
    time.sleep(2)  # Adjust delay if needed
    totp_field = driver.find_element(By.ID, "totp")
    totp_field.send_keys("your_totp_code")  # Replace with your TOTP/PIN

    # Click Continue button
    continue_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    continue_button.click()

except Exception as e:
    print(f"Error during login: {e}")
    driver.quit()
    exit()

# Step 6: Wait for redirect and extract request token
print("Waiting for redirect...")
timeout = 30  # Wait up to 30 seconds for redirect
start_time = time.time()
request_token = None

while time.time() - start_time < timeout:
    current_url = driver.current_url
    if "request_token" in current_url:
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)
        request_token = query_params.get("request_token", [None])[0]
        if request_token:
            print(f"Request token captured: {request_token}")
            break
    time.sleep(1)

# Close the browser
driver.quit()

if not request_token:
    print("Timeout: Failed to capture request token. Please check your login credentials or Redirect URL.")
    exit()

# Step 7: Generate session and set access token
try:
    data = kite.generate_session(request_token, api_secret=api_secret)
    kite.set_access_token(data["access_token"])
    print("Authentication successful!")
except Exception as e:
    print(f"Authentication failed: {e}")
    exit()

# Step 8: Fetch positions
try:
    positions = kite.positions()
    net_positions = positions["net"]
except Exception as e:
    print(f"Failed to fetch positions: {e}")
    exit()

# Step 9: Define fields and file path for CSV
fields = ["tradingsymbol", "exchange", "product", "quantity", "average_price", "pnl"]
file_path = r"C:\Users\rohit\Documents\csvtohtml\positions.csv"

# Step 10: Write positions to CSV
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