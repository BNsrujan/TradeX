from flask import Blueprint, render_template, request, redirect, url_for, session
from models.db import execute_query
from models.data_fetch import is_email_registered, insert_user, check_user_credentials
import urllib.parse

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        symbol = request.form.get('symbol')  # Fetch symbol from the form (hidden input)

        # Debugging: Check if the symbol is passed correctly
        # print("Symbol from form:", symbol)

        user = check_user_credentials(email, password)
        if user:
            session['symbol'] = symbol  # Save symbol to session
            session['email'] = email
            session['user_type'] = user[8]  # Adjust index as per your user schema

            # Fetch patterns from session
            patterns = session.get('patterns', [])  # Default to an empty list if not set
            # print("Patterns in session:", patterns)  # Debugging output

            return redirect(url_for('data.graph'))  # Adjust to your graph page endpoint
        else:
            return render_template('graph.html', login_status=0)

    # Extract the 'symbol' and 'patterns' from the query parameters
    symbol = request.args.get('symbol', '')
    encoded_patterns = request.args.get('patterns', '')

    # Decode the patterns string and split into a list
    if encoded_patterns:
        decoded_patterns = urllib.parse.unquote(encoded_patterns)  # Decode URL-encoded string
        patterns_list = decoded_patterns.split(',')  # Split into list
        session['patterns'] = patterns_list  # Store patterns in the session
        # print("Patterns extracted and decoded:", patterns_list)  # Debugging output

    return render_template('graph.html', login_status=-1, symbol=symbol, patterns=encoded_patterns)


@bp.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('user_type', None)
    return redirect(url_for('auth.login'))

@bp.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['mailid']
        if is_email_registered(email):
            return render_template('signup.html', email_exists=True)

        user_data = {
            'name': request.form['name'],
            'lastname': request.form['lastname'],
            'mailid': email,
            'phone': request.form['phone'],
            'experience': request.form['experience'],
            'capital': request.form['capital'],
            'password': request.form['password'],
            'user_type': 'admin',
            'trader_type': request.form.get('trader_type', '')
        }

        insert_user(user_data)
        return redirect(url_for('auth.login'))

    return render_template('signup.html', email_exists=False)
