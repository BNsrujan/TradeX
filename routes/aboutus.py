from flask import Blueprint, render_template

bp = Blueprint('aboutus', __name__)

@bp.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')
