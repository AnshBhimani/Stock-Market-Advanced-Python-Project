import logging
from bsedata.bse import BSE
from bsedata.exceptions import InvalidStockException
import csv
import os
import time
from datetime import datetime, time as dt_time

# Configure logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)
logger = logging.getLogger(__name__)  # Corrected the logger name

print("Script Started")
logger.info("Script started.")

try:
    b = BSE(update_codes=True)

    # Define the CSV file name
    csv_filename = "bse_stocks.csv"

    # Initialize the total number of stocks and a counter
    total_stocks = len(b.getScripCodes())
    processed_stocks = 0

    # Check if the CSV file exists
    csv_file_exists = os.path.exists(csv_filename)

    if not csv_file_exists:
        logger.info(f"CSV file '{csv_filename}' does not exist. Creating a new one.")
        fieldnames = ['Stock Code', 'Stock Name', 'Current Value', 'Change', 'Percentage Change', 'Day High', 'Day Low', 'Month High/Low', 'Market Cap', 'Industry']
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

    while True:
        current_time = datetime.now().time()
        ist_start_time = dt_time(9, 15)  # 9.15 AM IST
        ist_end_time = dt_time(15, 30)   # 3.30 PM IST

        # Check if the current time is within market hours
        if ist_start_time <= current_time <= ist_end_time:
            # Fetch stock information for all stocks
            for stock_code, stock_name in b.getScripCodes().items():
                try:
                    stock_info = b.getQuote(stock_code)
                    stock_data = {
                        'Stock Code': stock_code,
                        'Stock Name': stock_name,
                        'Current Value': stock_info.get('currentValue', ''),
                        'Change': stock_info.get('change', ''),
                        'Percentage Change': stock_info.get('pChange', ''),
                        'Day High': stock_info.get('dayHigh', ''),
                        'Day Low': stock_info.get('dayLow', ''),
                        'Month High/Low': stock_info.get('52weekHighLow', ''),  # Corrected key
                        'Market Cap': stock_info.get('marketCap', ''),  # Corrected key
                        'Industry': stock_info.get('group', '')  # Corrected key
                    }

                    # Append the stock's data to the CSV file
                    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
                        fieldnames = ['Stock Code', 'Stock Name', 'Current Value', 'Change', 'Percentage Change', 'Day High', 'Day Low', 'Month High/Low', 'Market Cap', 'Industry']
                        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                        writer.writerow(stock_data)

                    processed_stocks += 1
                    logger.info(f"Processed: {processed_stocks}/{total_stocks} - Stock Code: {stock_code}")

                except InvalidStockException:
                    logger.warning(f"Stock {stock_code} is inactive.")

            logger.info("Data updating completed.")

        else:
            logger.info("Markets are closed now!! Please come back tomorrow between 9.15 AM and 3.30 PM")
            print("Markets are closed now!! Please come back tomorrow between 9.15 AM and 3.30 PM")
            exit()  # Exit the program

        time.sleep(1)
# The code snippet fetches stock information from the Bombay Stock Exchange (BSE) and writes it to a CSV file. It checks if the stock market is open and updates the data accordingly. The script logs various events and handles exceptions.

except KeyboardInterrupt:
    logger.critical("Script interrupted by the user.")
except Exception as e:
    logger.error("An error occurred:", exc_info=True)
finally:
    logger.info("Script ended.")
