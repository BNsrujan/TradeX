from flask import Blueprint, render_template

bp = Blueprint('help', __name__)

@bp.route('/helptrader')
def helptrader():
    return render_template('helptrader.html')

@bp.route('/impactontrader')
def impactontrader():
    return render_template('impactontrader.html')

@bp.route('/advantages')
def advantages():
    return render_template('advantages.html')
