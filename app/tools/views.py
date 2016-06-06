# -*- coding: utf-8 -*-
from . import tools

from flask import redirect, render_template, request, make_response, url_for,flash


@tools.route('/calculator', methods=['GET', 'POST'])
def calculator():
    number_list_string = request.cookies.get('number_list', None)
    table_method = request.args.get('table_method', None)

    # table_method
    if table_method == "clear":
        resp = make_response(redirect(url_for('tools.calculator')))
        resp.set_cookie('number_list', '', max_age=0)
        return resp

    # table show
    if number_list_string:
        number_list = number_list_string.split(' ')
    else:
        number_list = None
    if request.method == "POST":
        number_raw = request.form.get('number', None)
        number = "".join([a for a in number_raw if a.isdigit() or a == '.'])
        if len(number) < len(number_raw):
            flash('请输入一个数字')
            return render_template('tools/calculator.html', number_list=number_list)
        if number_list:
            number_list.append(number)
            number_list_string = ' '.join(number_list)
        else:
            number_list = number
            number_list_string = str(number_list)
        resp = make_response(redirect(url_for('tools.calculator')))
        resp.set_cookie('number_list', number_list_string, max_age=60 * 60 * 24)
        return resp
    return render_template('tools/calculator.html', number_list=number_list)
