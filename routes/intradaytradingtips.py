from flask import Blueprint, render_template

bp = Blueprint('intradaytradingtips', __name__)

@bp.route('/intradaytradingtips')
def intradaytradingtips():
    return render_template('intradaytradingtips.html')
