import importlib
import os
import colorlog
from flask import Flask, render_template, request, jsonify
import logging
import csv
import webbrowser
import time
from datetime import datetime, time as dt_time
import subprocess
from bsedata.bse import BSE
from datetime import datetime  # Add this import for timestamp

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze')
def analyze_dashboard():
    stock_names = []
    with open('stock_list.csv', 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            stock_names.append(row['Stock Name'])
    return render_template('analyze.html', stock_names=stock_names)

def get_stock_code(stock_name):
    try:
        bse = BSE(update_codes=True)  # Create a BSE object
        for stock_code, name in bse.getScripCodes().items():
            if name.lower() == stock_name.lower():
                return stock_code
        return "Stock Not Found"  # Stock name not found
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

@app.route('/analyze/<stock_name>')
def analyze_stock(stock_name):
    stock_code = get_stock_code(stock_name)
    if stock_code is None:
        return "Stock code not found."

    csv_filename = f"{stock_code}.csv"
    csv_path = f"stock_data/{csv_filename}"
    if not os.path.exists(csv_path):
        return "CSV file not found."

    try:
        with open(csv_path, mode='r', newline='', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            last_row = None  # Initialize a variable to store the last row

            for row in csv_reader:
                last_row = row

            if last_row is not None:
                stock_info = {
                    'Stock Name': stock_name,
                    'Time': last_row['time'],
                    'Current Price': last_row['current price'],
                    'Day High': last_row['day high'],
                    'Day Low': last_row['day low'],
                }
                return jsonify(stock_info)
            else:
                return "No data found in the CSV file."

    except FileNotFoundError:
        return "CSV file not found."
    
if __name__ == "__main__":
    while True:
        try:
            current_time = datetime.now().time()
            ist_start_time = dt_time(9, 15)  # 9.15 AM IST
            ist_end_time = dt_time(15, 30)   # 3.30 PM IST
            
            # if ist_start_time <= current_time <= ist_end_time:
            if True:
                logger.info("Markets are opened!!")
                subprocess.Popen(['python', 'api.py'])
            
            else:
                logger.info("Markets are closed right now!!")
                logger.info("Come back between {ist_start_time} and {ist_end_time}")
            
            app.run(debug=True, host = '0.0.0.0', port=8000)

            # Open the browser automatically
            url = f"http://127.0.0.1:8000"
            webbrowser.open(url)
            print("App running on url: " + url)

        except KeyboardInterrupt:
            logger.critical("Script interrupted by user.")
        except Exception as e:
            logger.error("From Main : An error occurred:", exc_info=True)
