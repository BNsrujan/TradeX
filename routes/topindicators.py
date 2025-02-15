from flask import Blueprint, render_template

bp = Blueprint('topindicators', __name__)

@bp.route('/topindicators')
def topindicators():
    return render_template('topindicators.html')
