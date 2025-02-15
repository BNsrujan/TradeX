from flask import Blueprint, render_template

bp = Blueprint('contactus', __name__)

@bp.route('/contactus')
def contactus():
    return render_template('contactus.html')
