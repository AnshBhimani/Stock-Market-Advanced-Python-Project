import logging
from bsedata.bse import BSE
from bsedata.exceptions import InvalidStockException
import csv
import os
import concurrent.futures
import colorlog
from datetime import datetime

# Configure logging settings
formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',  # Add timestamp format
    log_colors={
        'DEBUG': 'blue',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

logger = logging.getLogger(__name__)

print("Script Started")
logger.info("Script started.")

def create_stock_list(bse, csv_filename):
    try:
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Stock Code', 'Stock Name'])
            
            scrip_codes = bse.getScripCodes()
            for stock_code, stock_name in scrip_codes.items():
                writer.writerow([stock_code, stock_name])
                
        logger.info(f"Created the stock list CSV: {csv_filename}")
        print(f"Created the stock list CSV: {csv_filename}")
    
    except Exception as e:
        logger.error("An Error Occurred while listing the initial stock list!!", exc_info=True)

def create_stock_file(stock_code, csv_dir):
    try:
        # Check if the CSV file exists and create it if it doesn't
        csv_filename = os.path.join(csv_dir, f"{stock_code}.csv")
        if not os.path.exists(csv_filename):
            fieldnames = ['time', 'current price', 'day high', 'day low']
            with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
            
            logger.info(f"Created the file for Stock Code: {stock_code}")
            print(f"Created the file for Stock Code: {stock_code}")
        else:
            logger.warning(f"File {csv_filename} already exists")

    except Exception as e:
        logger.error(f"Error creating file for Stock Code: {stock_code}", exc_info=True)

def fetch_stock_data(stock_code, csv_dir):
    try:
        bse = BSE(update_codes=True)  # Create a BSE object
        stock_info = bse.getQuote(stock_code)
        # Create a separate CSV file for each stock if it doesn't exist
        create_stock_file(stock_code, csv_dir)

        # Include 'time' and 'current price' fields
        csv_filename = os.path.join(csv_dir, f"{stock_code}.csv")
        fieldnames = ['time', 'current price', 'day high', 'day low']

        # Update the day high and low in the CSV
        with open(csv_filename, mode='a+', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writerow({
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'current price': stock_info.get('currentValue', ''),
                'day high': stock_info.get('dayHigh', ''),
                'day low': stock_info.get('dayLow', ''),
            })

        logger.info(f"Updated - Stock Code: {stock_code}")
        print(f"Updated - Stock Code: {stock_code}")

    except InvalidStockException:
        logger.warning(f"Stock {stock_code} is inactive.")
        print(f"Stock {stock_code} is inactive.")
    except Exception as e:
        logger.error(f"Error updating stock data for Stock Code: {stock_code}", exc_info=True)

if __name__ == "__main__":
    bse = BSE(update_codes=True)
    # Create a directory for stock CSV files
    csv_dir = "stock_data"
    os.makedirs(csv_dir, exist_ok=True)
    
    stock_list_csv_filename = "stock_list.csv"
    create_stock_list(bse, stock_list_csv_filename)

    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for stock_code, stock_name in bse.getScripCodes().items():
                executor.submit(fetch_stock_data, stock_code, csv_dir)

        logger.info("Stock data updated for all stocks in the directory: %s", csv_dir)
    except KeyboardInterrupt:
        logger.critical("Script interrupted by user.")
    except Exception as e:
        logger.error("An error occurred:", exc_info=True)
    finally:
        logger.info("Script ended.")
