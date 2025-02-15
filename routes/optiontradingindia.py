from flask import Blueprint, render_template

bp = Blueprint('optiontradingindia', __name__)

@bp.route('/optiontradingindia')
def optiontradingindia():
    return render_template('optiontradingindia.html')
