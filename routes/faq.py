from flask import Blueprint, render_template

bp = Blueprint('faq', __name__)

@bp.route('/faq')
def faq():
    return render_template('faq.html')
