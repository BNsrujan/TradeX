from flask import Blueprint, render_template

bp = Blueprint('Discipline', __name__)

@bp.route('/Discipline')
def Discipline():
    return render_template('Discipline.html')
