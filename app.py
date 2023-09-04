import importlib
import os
import time
import colorlog
from flask import Flask, render_template, request, jsonify
import logging
import pandas as pd
from bsedata.exceptions import InvalidStockException
from bsedata.bse import BSE
from bselib.bse import BSE as BSE2
import csv
import webbrowser
import subprocess
from threading import Thread

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
        'DEBUG': 'reset',
        'INFO': 'reset',
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

        except Exception as e:
            logger.error("An error occurred:", exc_info=True)
        finally:
            self.running = False

    def fetch_and_analyze_data(self, stock_code):
        b2 = BSE2()

        # Initialize data dictionaries for different parameters
        cashflow_data = {}
        yoy_results_data = {}
        performance_analysis_data = {}
        annual_reports_data = {}

        try:
            # Fetch data for each parameter
            cashflow_data = b2.historical_stats(stock_code, stats="cashflow")
            yoy_results_data = b2.historical_stats(stock_code, stats="yoy_results")
            performance_analysis_data = b2.analysis(stock_code)
            annual_reports_data = b2.annual_reports(stock_code)

            # Calculate average, minimum, and maximum values for each parameter
            cashflow_average = sum(cashflow_data.values()) / len(cashflow_data)
            cashflow_min = min(cashflow_data.values())
            cashflow_max = max(cashflow_data.values())

            yoy_results_average = sum(yoy_results_data.values()) / len(yoy_results_data)
            yoy_results_min = min(yoy_results_data.values())
            yoy_results_max = max(yoy_results_data.values())

            # You can similarly calculate average, min, and max for performance_analysis and annual_reports
            performance_analysis_average = sum(performance_analysis_data.values()) / len(performance_analysis_data)
            performance_analysis_min = min(performance_analysis_data.values())
            performance_analysis_max = max(performance_analysis_data.values())

            annual_reports_average = sum(annual_reports_data.values()) / len(annual_reports_data)
            annual_reports_min = min(annual_reports_data.values())
            annual_reports_max = max(annual_reports_data.values())

            performance_metrics = {
                'Cashflow': {
                    'Data': cashflow_data,
                    'Average': cashflow_average,
                    'Min': cashflow_min,
                    'Max': cashflow_max
                },
                'YOY Results': {
                    'Data': yoy_results_data,
                    'Average': yoy_results_average,
                    'Min': yoy_results_min,
                    'Max': yoy_results_max
                },
                'Performance Analysis': {
                    'Data': performance_analysis_data,
                    'Average': performance_analysis_average,
                    'Min': performance_analysis_min,
                    'Max': performance_analysis_max
                },
                'Annual Reports': {
                    'Data': annual_reports_data,
                    'Average': annual_reports_average,
                    'Min': annual_reports_min,
                    'Max': annual_reports_max
                }
            }

            return performance_metrics

        except InvalidStockException:
            logger.error("Invalid Stock for analysis")
            return "Invalid Stock"

updater = StockUpdater()

@app.route('/')
def index():
    return render_template('index.html')

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
        # Create the CSV file if not found
        csv_filename = 'bse_stocks.csv'
        if not os.path.exists(csv_filename):
            with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
                fieldnames = ['Stock Code', 'Stock Name', 'Current Value', 'Change', 'Percentage Change', 'Market Cap', 'Industry', 'Day High', 'Day Low', 'Month High/Low']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()

        # Start the Api.py script in a separate process
        api_process = subprocess.Popen(["python", "Api.py"])

        app.run(debug=True, port=8000)

        # Open the browser automatically
        url = f"http://127.0.0.1:8000"
        webbrowser.open(url)
        print("App running on url : " + url)

    except KeyboardInterrupt:
        logger.critical("Script interrupted by the user.")
    except Exception as e:
        logger.error("An error occurred:", exc_info=True)
