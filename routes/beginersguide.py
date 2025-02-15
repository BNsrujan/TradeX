from flask import Blueprint, render_template

bp = Blueprint('beginersguide', __name__)

@bp.route('/beginersguide')
def beginersguide():
    return render_template('beginersguide.html')
