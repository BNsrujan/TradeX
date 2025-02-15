from flask import Blueprint, render_template

bp = Blueprint('optiontrading', __name__)

@bp.route('/optiontrading')
def optiontrading():
    return render_template('optiontrading.html')
