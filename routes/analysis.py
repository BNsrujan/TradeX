from flask import Blueprint, render_template

bp = Blueprint('analysis', __name__)

@bp.route('/analysis')
def supportpage():
    return render_template('analysis.html')

@bp.route('/page1')
def page1():
    return render_template('page1.html')


@bp.route('/page2')
def page2():
    return render_template('page2.html')


@bp.route('/page3')
def page3():
    return render_template('page3.html')


@bp.route('/page4')
def page4():
    return render_template('page4.html')


@bp.route('/page5')
def page5():
    return render_template('page5.html')


@bp.route('/page6')
def page6():
    return render_template('page6.html')


@bp.route('/page7')
def page7():
    return render_template('page7.html')
