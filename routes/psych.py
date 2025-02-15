
from flask import Blueprint, render_template
bp = Blueprint('psych', __name__)

@bp.route('/psych')
def psych():
    return render_template('psych.html')
