from flask import Blueprint, render_template
from models.stock_patterns import load_stock_patterns
from models.preclose import load_preclose_prices, clean_and_capitalize_stock_name

bp = Blueprint('home', __name__)

@bp.route('/')
@bp.route('/home')
def home():
    stock_patterns = load_stock_patterns()  # Load stock patterns from CSV
    stock_names = list(stock_patterns.keys())  # Get stock names for market action data
    preclose_prices = load_preclose_prices()
    # Debugging output
    # print("Stock patterns loaded:", stock_patterns)  
    # print("Stock names:", stock_names)
    # Clean and capitalize stock names for display
    cleaned_preclose_prices = {
        clean_and_capitalize_stock_name(stock): details
        for stock, details in preclose_prices.items()
    }
    # Pass stock patterns and stock names to the template
    return render_template('home.html', stock_patterns=stock_patterns, stock_names=stock_names, preclose_prices=cleaned_preclose_prices)
