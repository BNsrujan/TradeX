from flask import Blueprint, render_template

bp = Blueprint('educationresorce', __name__)

@bp.route('/educationresorce')
def educationresorce():
    return render_template('educationresorce.html')
