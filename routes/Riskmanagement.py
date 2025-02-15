from flask import Blueprint, render_template

bp = Blueprint('Riskmanagement', __name__)

@bp.route('/Riskmanagement')
def Riskmanagement():
    return render_template('Riskmanagement.html')
