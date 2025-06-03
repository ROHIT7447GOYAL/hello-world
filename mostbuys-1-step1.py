import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Set up Selenium
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Navigate to Moneycontrol list page
url = "https://www.moneycontrol.com/markets/stock-ideas/analysts-choice/#most-buys"
driver.get(url)
time.sleep(3)  # Allow initial page load

# Wait for stock cards to load
wait = WebDriverWait(driver, 30)
stock_cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".AnylyticCardsSec_web_anylyticsCard__K0OB7")))

stocks_data = []

for card in stock_cards:
    try:
        # Extract stock name and link
        stock_link_element = card.find_element(By.CSS_SELECTOR, "h3 a")
        stock_name = stock_link_element.text.strip()
        stock_link = stock_link_element.get_attribute("href")

        # Extract stock code from the link
        stock_code = stock_link.split('/')[-2]

        # Extract current price and change
        price_element = card.find_element(By.CSS_SELECTOR, ".AnylyticCardsSec_web_rgtNumber__g_x3n")
        price_text = price_element.text.strip()
        current_price = price_text.split()[0]
        price_change = ' '.join(price_text.split()[1:])

        # Extract buy ratings
        buy_element = card.find_element(By.CSS_SELECTOR, ".AnylyticCardsSec_web_buyCol__o9t6I span")
        buy_ratings_text = buy_element.text.split('(')[0]
        buy_ratings = int(buy_ratings_text)

        # Extract targets
        targets_div = card.find_element(By.CSS_SELECTOR, ".AnylyticCardsSec_web_tarDetails__DuOo2")
        target_divs = targets_div.find_elements(By.CSS_SELECTOR, ".AnylyticCardsSec_web_algnCen__Yz5lB.AnylyticCardsSec_web_lftTxt__IVbsT")
        low_target = average_target = high_target = 'N/A'
        for div in target_divs:
            p = div.find_element(By.TAG_NAME, "p")
            text = p.text
            if "Low" in text:
                low_target = p.find_element(By.CSS_SELECTOR, "span").text.split()[0]
            elif "Average" in text:
                average_target = p.find_element(By.CSS_SELECTOR, "span").text.split()[0]
            elif "High" in text:
                high_target = p.find_element(By.CSS_SELECTOR, "span").text.split()[0]

        # Collect data
        stock_data = [stock_name, stock_link, stock_code, current_price, price_change, buy_ratings, low_target, average_target, high_target]
        stocks_data.append(stock_data)

    except Exception as e:
        print(f"Error processing stock: {e}")
        continue

# Close Selenium driver
driver.quit()

# Filter stocks with buy ratings >= 7
filtered_stocks = [stock for stock in stocks_data if stock[5] >= 5]

# Write to CSV at specified path
output_path = r'C:\Users\rohit\Documents\stocks\money_market_buysstocks.csv'
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Stock Name', 'Stock Link', 'Stock Code', 'Current Price', 'Price Change', 'Buy Ratings', 'Low Target', 'Average Target', 'High Target'])
    writer.writerows(filtered_stocks)

print(f"Filtered stocks data has been saved to {output_path}")