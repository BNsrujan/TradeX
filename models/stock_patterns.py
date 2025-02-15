import csv


def load_stock_patterns():
    stock_patterns = {}
    with open('stock_patterns.csv', mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            stock_name = row['Symbol']
            stock_patterns[stock_name] = {
                'Inside Bar Count': int(row['Inside Bar']),
                'Double Patterns Count': int(row['Double top/bottom']),
                # 'Cup and Handle Count': int(row['Cup and Handle']),
                'Head and Shoulders Count': int(row['Head and Shoulders']),
                'V Shape Count': int(row['VShape'])
            }
    return stock_patterns
