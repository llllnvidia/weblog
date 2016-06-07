# -*- coding: utf-8 -*-
from . import tools

from flask import redirect, render_template, request, make_response, url_for, flash


@tools.route('/calculator', methods=['GET', 'POST'])
def calculator():
    number_list_string = request.cookies.get('number_list', None)
    table_method = request.args.get('table_method', None)

    # table_method clear
    if table_method == "clear":
        resp = make_response(redirect(url_for('tools.calculator')))
        resp.set_cookie('number_list', '', path=url_for('tools.calculator'), max_age=0)
        return resp

    # get the number list
    if number_list_string:
        number_list = number_list_string.split(' ')
    else:
        number_list = None

    # table_method chauvenet
    if table_method == "chauvenet":
        from .calculator import list_handler
        number_list, number_erase_list = list_handler(number_list)
        # end
        resp = make_response(redirect(url_for('tools.calculator', number_erase_list=number_erase_list)))
        resp.set_cookie('number_list', number_list_string, path=url_for('tools.calculator'), max_age=60 * 60 * 24)
        return resp

    # number erase
    number_erase = request.args.get('number_erase')
    if number_erase and number_list:
        number_erase = number_erase.replace(' ', '+', 1)
        if number_erase in number_list:
            number_list.remove(number_erase)
        number_list_string = ' '.join(number_list)
        resp = make_response(redirect(url_for('tools.calculator')))
        resp.set_cookie('number_list', number_list_string, path=url_for('tools.calculator'), max_age=60 * 60 * 24)
        return resp

    if request.method == "POST":
        number_raw = request.form.get('number', None)

        # is number?
        number = ""
        if number_raw:
            number = "".join([a for a in number_raw
                              if a.isdigit() or a == '+' or a == '-' or a == 'e' or a == '.'])
            if len(number) < len(number_raw):
                flash('请输入一个数字')
                return render_template('tools/calculator.html', number_list=number_list)

        # list show
        if number_list and number:
            number_list.append(number)
            number_list_string = ' '.join(number_list)
        elif not number_list and number:
            number_list = number
            number_list_string = number_list
        else:
            number_list_string = ""
        resp = make_response(redirect(url_for('tools.calculator')))
        resp.set_cookie('number_list', number_list_string, path=url_for('tools.calculator'), max_age=60 * 60 * 24)
        return resp
    return render_template('tools/calculator.html', number_list=number_list)
