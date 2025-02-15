from flask import Blueprint, render_template
from models.data_fetch import fetch_from_fyers
from models.data_fetch import fetch_data_from_db, compare_db_current_date, fetch_currentday_data, get_livemint_data, get_usi_data, store_data, fetch_data_for_current_month


bp = Blueprint('news', __name__)

@bp.route('/news')
def news_page():
    livemint_df = get_livemint_data()
    usi_df = get_usi_data()

    # Store data in the database
    store_data(livemint_df, 'livemint_data')
    store_data(usi_df, 'usi_data')

    # Fetch data for the current month
    livemint_df, usi_df = fetch_data_for_current_month()

    # Convert DataFrames to HTML tables
    livemint_html = livemint_df.to_html(classes='data', index=False)
    usi_html = usi_df.to_html(classes='data', index=False)

    return render_template('newsorig.html',
                           livemint_data=livemint_html,
                           usi_data=usi_html)
