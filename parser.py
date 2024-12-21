import pandas as pd
import matplotlib.pyplot as plt

file_path = "invoice-list-2024-12-21.xlsx"

try:
    df = pd.read_excel(file_path, engine="openpyxl")
    
    print(df)
    
except FileNotFoundError:
    print(f"File not found: {file_path}")
except Exception as e:
    print(f"An error occurred: {e}")