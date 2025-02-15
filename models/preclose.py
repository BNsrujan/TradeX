import csv

# Function to load preclose prices from a CSV file
def load_preclose_prices(filename="preclose_prices.csv"):
    preclose_prices = {}
    with open(filename, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            stock_name = row['Symbol']
            preclose_prices[stock_name] = {
                'Date': row['Date'],
                'Close': float(row['Close'])
            }
    return preclose_prices

# Function to clean and capitalize stock names
def clean_and_capitalize_stock_name(stock_name):
    cleaned_name = (
        stock_name.replace("NSE:", "")
        .replace("-INDEX", "")
        .replace("MCX:", "")
        .replace("-EQ", "")
        .replace('"', "")
        .replace(",", "")
        .upper()
    )
    return cleaned_name