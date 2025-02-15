from flask import Blueprint, render_template

bp = Blueprint('marketinsights', __name__)

@bp.route('/marketinsights')
def marketinsights():
    return render_template('marketinsights.html')
