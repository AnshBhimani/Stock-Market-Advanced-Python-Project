from bselib.bse import BSE
import os

# Create a directory to store CSV files
csv_dir = "analysis_reports"
os.makedirs(csv_dir, exist_ok=True)

b = BSE()

stock_code = 500325

# Cashflow
his_data = b.historical_stats(stock_code, stats="cashflow")
his_data_path = os.path.join(csv_dir, f"{stock_code}_cashflow.csv")  # Fixed formatting
with open(his_data_path, "w") as file:
    for key, value in his_data.items():
        file.write(f"{key},{value}\n")

# YOY Results
his_data2 = b.historical_stats(stock_code, stats="yoy_results")
his_data2_path = os.path.join(csv_dir, f"{stock_code}_yoy_results.csv")  # Fixed formatting
with open(his_data2_path, "w") as file:
    for key, value in his_data2.items():
        file.write(f"{key},{value}\n")

# Performance Analysis
performance_analysis = b.analysis(stock_code)
performance_analysis_path = os.path.join(csv_dir, f"{stock_code}_performance_analysis.csv")  # Fixed formatting
with open(performance_analysis_path, "w") as file:
    for key, value in performance_analysis.items():
        if isinstance(value, str):
            value = value.replace(",", ";")  # Replace commas in strings
        file.write(f"{key},{value}\n")

# Holding Info
holding_info = b.holdings(stock_code)
holding_info_path = os.path.join(csv_dir, f"{stock_code}_holding_info.csv")  # Fixed formatting
with open(holding_info_path, "w") as file:
    for key, value in holding_info.items():
        file.write(f"{key},{value}\n")

# Annual Reports
annual_reports = b.annual_reports(stock_code)
annual_reports_path = os.path.join(csv_dir, f"{stock_code}_annual_reports.csv")  # Fixed formatting
with open(annual_reports_path, "w") as file:
    for key, value in annual_reports.items():
        file.write(f"{key},{value}\n")

# Credit Reports
credit_reports = b.credit_reports(stock_code)
credit_reports_path = os.path.join(csv_dir, f"{stock_code}_credit_reports.csv")  # Fixed formatting
with open(credit_reports_path, "w") as file:
    for key, value in credit_reports.items():
        file.write(f"{key},{value}\n")

print(f"CSV files saved in the directory: {csv_dir}")
