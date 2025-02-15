from flask import Blueprint, render_template

bp = Blueprint('technicalanalysis', __name__)

@bp.route('/technicalanalysis')
def technicalanalysis():
    return render_template('technicalanalysis.html')
