import pandas as pd

try:
    df = pd.read_excel('Robot01.xlsx')
    print('File read successfully. Here are the first 5 rows:')
    print(df.head())
    print('\nColumns:')
    print(df.columns.tolist())
except FileNotFoundError:
    print("Error: 'Robot01.xlsx' not found.")
except Exception as e:
    print(f"An error occurred: {e}")

