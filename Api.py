import logging
from bsedata.bse import BSE
from bselib.bse import BSE as BSE2
from bsedata.exceptions import InvalidStockException
import csv
import os
import time
from datetime import datetime, time as dt_time, timedelta

# Configure logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

print("Script Started")
logger.info("Script started.")

try:
    b = BSE(update_codes=True)
    b2 = BSE2()

    # Define the CSV file name
    csv_filename = "bse_stocks.csv"

    # Initialize the total number of stocks and a counter
    total_stocks = len(b.getScripCodes())
    processed_stocks = 0

    # Phase 1: Initial listing of all stocks in the CSV
    if not os.path.exists(csv_filename):
        fieldnames = ['Stock Code', 'Stock Name', 'Current Value', 'Change', 'Percentage Change', 'Day High', 'Day Low', 'Month High/Low', 'Market Cap', 'Industry']
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for stock_code, stock_name in b.getScripCodes().items():
                writer.writerow({
                    'Stock Code': stock_code,
                    'Stock Name': stock_name,
                    'Current Value': '',
                    'Change': '',
                    'Percentage Change': '',
                    'Day High': '',
                    'Day Low': '',
                    'Month High/Low': '',
                    'Market Cap': '',
                    'Industry': ''
                })

                processed_stocks += 1
                logger.info(f"Processed: {processed_stocks}/{total_stocks} - Stock Code: {stock_code}")

        logger.info("All stocks listed in the CSV.")
    else:
        logger.warning(f"CSV file '{csv_filename}' already exists.")

    # Controlled loop between 9:15 AM and 3:30 PM IST on weekdays
    while True:
        days_on = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        current_day = datetime.today().strftime("%A")
        current_time = datetime.now().time()
        ist_start_time = dt_time(9, 15)  # 9.15 AM IST
        ist_end_time = dt_time(15, 30)   # 3.30 PM IST

        if (
            (ist_start_time <= current_time <= ist_end_time
            and current_day in days_on) or True
        ):
            with open(csv_filename, mode='a', newline='', encoding='utf-8') as csv_file:
                rows = list(csv.DictWriter(csv_file))

            updated_rows = []

            for index, row in enumerate(rows):
                try:
                    stock_info = b.getQuote(row['Stock Code'])
                    logger.info(f"Available keys in stock_info: {stock_info.keys()}")

                    updated_row = row.copy()
                    updated_row['Current Value'] = stock_info.get('currentValue', '')
                    updated_row['Change'] = stock_info.get('change', '')
                    updated_row['Percentage Change'] = stock_info.get('pChange', '')
                    updated_row['Day High'] = stock_info.get('dayHigh', '')  # Corrected key
                    updated_row['Day Low'] = stock_info.get('dayLow', '')  # Corrected key
                    updated_row['Market Cap'] = stock_info.get('marketCapFull', '')  # Corrected key
                    updated_row['Month High/Low'] = stock_info.get('monthHighLow', '')  # Corrected key

                    updated_rows.append(updated_row)

                    logger.info(f"Updated: {index + 1}/{total_stocks} - Stock Code: {row['Stock Code']}")
                except InvalidStockException:
                    logger.warning(f"Stock {row['Stock Code']} is inactive.")

            # Write the updated rows back to the CSV
            with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
                fieldnames = ['Stock Code', 'Stock Name', 'Current Value', 'Change', 'Percentage Change', 'Day High', 'Day Low', 'Month High/Low', 'Market Cap', 'Industry']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(updated_rows)

            # New functionality: Analysis Reports for all stocks
            csv_dir = "analysis_reports"
            os.makedirs(csv_dir, exist_ok=True)

            for row in rows:
                stock_code_to_analyze = row['Stock Code']

                # Cashflow
                his_data = b2.historical_stats(stock_code_to_analyze, stats="cashflow")
                his_data_path = os.path.join(csv_dir, f"{stock_code_to_analyze}_cashflow.csv")
                with open(his_data_path, "w") as file:
                    for key, value in his_data.items():
                        file.write(f"{key},{value}\n")

                # YOY Results
                his_data2 = b2.historical_stats(stock_code_to_analyze, stats="yoy_results")
                his_data2_path = os.path.join(csv_dir, f"{stock_code_to_analyze}_yoy_results.csv")
                with open(his_data2_path, "w") as file:
                    for key, value in his_data2.items():
                        file.write(f"{key},{value}\n")

                # Performance Analysis
                performance_analysis = b2.analysis(stock_code_to_analyze)
                performance_analysis_path = os.path.join(csv_dir, f"{stock_code_to_analyze}_performance_analysis.csv")
                with open(performance_analysis_path, "w") as file:
                    for key, value in performance_analysis.items():
                        if isinstance(value, str):
                            value = value.replace(",", ";")
                        file.write(f"{key},{value}\n")

                # Holding Info
                holding_info = b2.holdings(stock_code_to_analyze)
                holding_info_path = os.path.join(csv_dir, f"{stock_code_to_analyze}_holding_info.csv")
                with open(holding_info_path, "w") as file:
                    for key, value in holding_info.items():
                        file.write(f"{key},{value}\n")

                # Annual Reports
                annual_reports = b2.annual_reports(stock_code_to_analyze)
                annual_reports_path = os.path.join(csv_dir, f"{stock_code_to_analyze}_annual_reports.csv")
                with open(annual_reports_path, "w") as file:
                    for key, value in annual_reports.items():
                        file.write(f"{key},{value}\n")

                # Credit Reports
                credit_reports = b2.credit_reports(stock_code_to_analyze)
                credit_reports_path = os.path.join(csv_dir, f"{stock_code_to_analyze}_credit_reports.csv")
                with open(credit_reports_path, "w") as file:
                    for key, value in credit_reports.items():
                        file.write(f"{key},{value}\n")

            logger.info("Analysis reports saved for all stocks in the directory: %s", csv_dir)

            current_datetime = datetime.now()
            end_datetime = datetime.combine(current_datetime.date(), ist_end_time)
            if current_datetime > end_datetime:
                next_day = current_datetime + timedelta(days=1)
                next_start_datetime = datetime.combine(next_day.date(), ist_start_time)
                sleep_duration = (next_start_datetime - current_datetime).total_seconds()
            else:
                sleep_duration = (end_datetime - current_datetime).total_seconds()

            logger.info("Data updating completed.")
            logger.info("Sleeping until the next update time.")
            time.sleep(sleep_duration)

        else:
            logger.info("Markets are closed now!! Please come back between 9.15 AM and 3.30 PM on Weekdays")
            print("Markets are closed now!! Please come back between 9.15 AM and 3.30 PM on Weekdays")
            current_datetime = datetime.now()
            next_weekday = current_datetime + timedelta(days=(1 - current_datetime.weekday() + 7) % 7)
            next_open_time = datetime.combine(next_weekday.date(), ist_start_time)
            sleep_duration = (next_open_time - current_datetime).total_seconds()

            logger.info(f"Sleeping until the market opens on the next weekday at {ist_start_time}.")
            time.sleep(sleep_duration)
            exit()  # Exit the program

except KeyboardInterrupt:
    logger.critical("Script interrupted by user.")
except Exception as e:
    logger.error("An error occurred:", exc_info=True)
finally:
    logger.info("Script ended.")
