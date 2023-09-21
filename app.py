import importlib
import os
import time
import colorlog
from flask import Flask, render_template, request, jsonify
from threading import Thread
import logging
import pandas as pd
from datetime import datetime, time as dt_time, timedelta
from bsedata.exceptions import InvalidStockException
from bsedata.bse import BSE
import csv
import webbrowser
import subprocess

# Check and install the dependencies 
# List of dependencies to check
dependencies = ["beautifulsoup4", "requests", "lxml", "colorlog", "Flask", "bsedata", "pandas"]

# Function to check and install dependencies
def check_and_install_dependencies(dependencies):
    for dependency in dependencies:
        try:
            importlib.import_module(dependency)
            print(f"{dependency} is already installed.")
        except ImportError:
            print(f"{dependency} is not installed. Installing...")
            try:
                subprocess.check_call(["pip", "install", dependency])
                print(f"{dependency} has been successfully installed.")
            except Exception as e:
                print(f"An error occurred while installing {dependency}: {e}")

check_and_install_dependencies(dependencies)

# Create a custom color formatter with timestamp
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

# Configure logging settings with the custom formatter
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('app.log')])
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

logger = logging.getLogger(__name__)

app = Flask(__name__)

class StockUpdater:
    def __init__(self):
        self.running = False
        self.markets_open = False
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = Thread(target=self.update_loop)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def update_loop(self):
        try:
            b = BSE(update_codes=True)

            while self.running:
                days_on = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
                current_day = datetime.today().strftime("%A")
                current_time = datetime.now().time()
                ist_start_time = dt_time(9, 15)  # 9.15 AM IST
                ist_end_time = dt_time(15, 30)   # 3.30 PM IST

                if (ist_start_time <= current_time <= ist_end_time and current_day in days_on):
                    self.markets_open = True
                    csv_filename = 'bse_stocks.csv'
                    if not os.path.exists(csv_filename):
                        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
                            fieldnames = ['Stock Code', 'Stock Name', 'Current Value', 'Change', 'Percentage Change', 'Market Cap', 'Industry', 'Day High', 'Day Low', 'Month High/Low']
                            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                            writer.writeheader()

                    with open('bse_stocks.csv', mode='r', newline='', encoding='utf-8') as csv_file:
                        rows = list(csv.DictReader(csv_file))

                    for index, row in enumerate(rows):
                        try:
                            stock_info = b.getQuote(row['Stock Code'])
                            logger.info(f"Available keys in stock_info: {stock_info.keys()}")

                            rows[index]['Current Value'] = stock_info.get('currentValue', '')
                            rows[index]['Change'] = stock_info.get('change', '')
                            rows[index]['Percentage Change'] = stock_info.get('pChange', '')
                            rows[index]['Day High'] = stock_info.get('dayHigh', '')
                            rows[index]['Day Low'] = stock_info.get('dayLow', '')
                            rows[index]['Market Cap'] = stock_info.get('marketCapFull', '')
                            rows[index]['Month High/Low'] = stock_info.get('monthHighLow', '')

                            logger.info(f"Updated: {index + 1}/{len(rows)} - Stock Code: {row['Stock Code']}")
                        except InvalidStockException:
                            logger.warning(f"Stock {row['Stock Code']} is inactive.")
                        except Exception as e:
                            logger.error(f"An error occurred while updating stock info for {row['Stock Code']}: {e}")

                    # Write the updated rows back to the CSV
                    with open('bse_stocks.csv', mode='w', newline='', encoding='utf-8') as csv_file:
                        fieldnames = ['Stock Code', 'Stock Name', 'Current Value', 'Change', 'Percentage Change', 'Day High', 'Day Low', 'Month High/Low', 'Market Cap', 'Industry']
                        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(rows)

                    logger.info("Data updating completed.")
                    time.sleep(10)
                
                else:
                    self.markets_open = False
                    logger.info("Markets are closed now!! Please come back between 9.15 AM and 3.30 PM on Weekdays")
                    time.sleep(600)  # Sleep for 10 minutes and check again
                    
        except Exception as e:
            logger.error("An error occurred:", exc_info=True)
        finally:
            self.running = False

updater = StockUpdater()

@app.route('/')
def index():
    updater.start()
    return render_template('index.html', markets_open = updater.markets_open)

@app.route('/analyze')
def analyse_dashboard():
    stock_names = []
    with open('bse_stocks.csv', 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            stock_names.append(row['Stock Name'])
    return render_template('analyze.html', stock_names=stock_names)

# Define a route to handle stock analysis
@app.route('/analyze/<stock_name>')
def analyze_stock(stock_name):
    with open('bse_stocks.csv', mode='r', newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if row['Stock Name'] == stock_name:
                stock_info = {
                    'Stock Code': row['Stock Code'],
                    'Stock Name': row['Stock Name'],
                    'Current Value': row['Current Value'],
                    'Day High': row['Day High'],
                    'Day Low': row['Day Low'],
                    'Month High/Low': row['Month High/Low'],
                    'Change': row['Change'],
                    'Percentage Change': row['Percentage Change'],
                    'Market Cap': row['Market Cap'],
                    'Industry': row['Industry']
                }
                return jsonify(stock_info)

    return "Stock not found"

if __name__ == "__main__":
    try:
        subprocess.Popen(['python', 'Api.py'])
        app.run(debug=True, port=8000)

        # Open the browser automatically
        url = f"http://127.0.0.1:8000"
        webbrowser.open(url)
        print("App running on url : " + url)

    except KeyboardInterrupt:
        logger.critical("Script interrupted by user.")
    except Exception as e:
        logger.error("An error occurred:", exc_info=True)
