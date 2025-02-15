from flask import Blueprint, render_template

bp = Blueprint('stocktradingpattern', __name__)

@bp.route('/stocktradingpattern')
def stocktradingpattern():
    return render_template('stocktradingpattern.html')
