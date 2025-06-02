#!/usr/bin/env python3
import os
import time
import glob
import pandas as pd
from datetime import datetime
import subprocess

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────
URL = "https://www.investing.com/indices/s-p-cnx-500-components"
DOWNLOAD_DIR = r"C:\Users\rohit\Documents\investing"
OUTPUT_DIR  = r"C:\Users\rohit\Documents\stocks"
CSV_PREFIX  = "investing_data"
HTML_PREFIX = "investing_diff"

# ─── HEADLESS CHROME SETUP ─────────────────────────────────────────────────────
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1920,1080")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 20)

# ─── SCRAPE & PARSE TABLE ──────────────────────────────────────────────────────
def load_and_parse(tab_id: int) -> pd.DataFrame:
    """Click the given tab (1=Performance, 2=Technical), wait for the table, parse it into a DataFrame."""
    # Click tab
    btn = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, f'button[data-test-tab-id="{tab_id}"]')
    ))
    btn.click()
    # Wait for table to appear
    table_el = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    time.sleep(1)
    html = table_el.get_attribute("outerHTML")
    df = pd.read_html(html)[0]
    return df

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    # Ensure directories exist
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        driver.get(URL)
        # dismiss cookie banner if present
        try:
            wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
        except:
            pass

        # Scrape Performance and Technical tables
        df_perf = load_and_parse(1)  # Performance
        df_tech = load_and_parse(2)  # Technical

    finally:
        driver.quit()

    # Merge and clean
    combined = pd.merge(df_perf, df_tech, on="Name", how="outer")
    combined.fillna("N/A", inplace=True)
    combined.drop(columns=["Unnamed: 0_x", "Unnamed: 0_y"], errors="ignore", inplace=True)

    # Save CSV with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_name = f"{CSV_PREFIX}.csv"
    csv_path = os.path.join(OUTPUT_DIR, csv_name)
    combined.to_csv(csv_path, index=False)
    combined.to_csv(r"C:\Users\rohit\Documents\csvtohtml\investing_data,csv", index=False)
    print(f"✔️  Saved CSV: {csv_path}")


    # Build diff HTML using last 10 CSVs
    pattern = os.path.join(OUTPUT_DIR, f"{CSV_PREFIX}_*.csv")
    all_csvs = sorted(glob.glob(pattern), key=os.path.getmtime)
    last_ten = all_csvs[-10:]

    if len(last_ten) >= 2:
        old_df = pd.read_csv(last_ten[0])
        new_df = pd.read_csv(last_ten[-1])
        # define numeric percentage columns to diff
        metrics = ["Hourly", "Daily_y", "Weekly", "Monthly",
                   "Daily_x", "1 Week", "1 Month", "YTD", "1 Year"]
        diff = pd.DataFrame({"Name": new_df["Name"]})

        # helper: strip % and convert to number, non-numeric -> NaN
        def to_numeric(col):
            return pd.to_numeric(
                new_df[col].astype(str)
                          .str.replace("[%+,]", "", regex=True),
                errors="coerce"
            ) - pd.to_numeric(
                old_df[col].astype(str)
                         .str.replace("[%+,]", "", regex=True),
                errors="coerce"
            )

        for col in metrics:
            diff[col] = to_numeric(col).round(2)

        # generate HTML table
        html_name = f"{HTML_PREFIX}_{timestamp}.html"
        html_path = os.path.join(OUTPUT_DIR, html_name)
        tbl_html = diff.to_html(
            index=False,
            classes="table table-striped table-hover",
            na_rep=""
        )
        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset=\"utf-8\">
  <title>Investing Diff {timestamp}</title>
  <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
</head>
<body class=\"container p-4\">
  <h1>Diff: {os.path.basename(last_ten[-1])} vs {os.path.basename(last_ten[0])}</h1>
  {tbl_html}
  <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js\"></script>
</body>
</html>"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✔️  Saved diff HTML: {html_path}")
    else:
        print("⚠️  Not enough CSV files to compute diff (need at least 2)")

if __name__ == "__main__":
    main()

subprocess.run(['python', 'csvtohtml.py'])