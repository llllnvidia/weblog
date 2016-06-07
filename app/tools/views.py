# -*- coding: utf-8 -*-
from . import tools

from flask import redirect, render_template, request, make_response, url_for, flash


@tools.route('/calculator', methods=['GET', 'POST'])
def calculator():
    number_list_string = request.cookies.get('number_list', None)
    table_method = request.args.get('table_method', None)
    bool_number_list_show_str = request.cookies.get('bool_number_list_show', None)

    # get the bool_number_list_show
    if bool_number_list_show_str:
        bool_number_list_show = [int(a) for a in bool_number_list_show_str.split(' ')]
    else:
        bool_number_list_show = None

    # get the number list
    if number_list_string:
        number_list = number_list_string.split(' ')
    else:
        number_list = None

    # table_method clear
    if table_method == "clear":
        resp = make_response(redirect(url_for('tools.calculator')))
        resp.set_cookie('bool_number_list_show', '', path=url_for('tools.calculator'), max_age=0)
        resp.set_cookie('number_list', '', path=url_for('tools.calculator'), max_age=0)
        resp.set_cookie('mean', '', path=url_for('tools.calculator'), max_age=0)
        resp.set_cookie('std_dev', '', path=url_for('tools.calculator'), max_age=0)
        resp.set_cookie('std_dev_mean', '', path=url_for('tools.calculator'), max_age=0)
        return resp

    # table_method chauvenet
    if table_method == "chauvenet":
        import calculator
        bool_number_list_show = calculator.get_bool_list_of_number_list(number_list)
        # end
        resp = make_response(redirect(url_for('tools.calculator')))
        resp.set_cookie('mean', '', path=url_for('tools.calculator'), max_age=0)
        resp.set_cookie('std_dev', '', path=url_for('tools.calculator'), max_age=0)
        resp.set_cookie('std_dev_mean', '', path=url_for('tools.calculator'), max_age=0)

        resp.set_cookie('bool_number_list_show', ' '.join(['1' if bo else '0' for bo in bool_number_list_show]),
                        path=url_for('tools.calculator'), max_age=60 * 3)
        return resp

    # table_method handle
    if table_method == "handle":
        import calculator
        mean, std_dev, std_dev_mean = calculator.handle(number_list)
        resp = make_response(redirect(url_for('tools.calculator')))
        resp.set_cookie('mean', str(mean), path=url_for('tools.calculator'), max_age=60 * 3)
        resp.set_cookie('std_dev', str(std_dev), path=url_for('tools.calculator'), max_age=60 * 3)
        resp.set_cookie('std_dev_mean', str(std_dev_mean), path=url_for('tools.calculator'), max_age=60 * 3)
        return resp
    # number erase
    number_erase = request.args.get('number_erase')
    if number_erase and number_list:
        number_erase = number_erase.replace(' ', '+', 1)
        if number_erase in number_list:
            number_list.remove(number_erase)
        number_list_string = ' '.join(number_list)
        resp = make_response(redirect(url_for('tools.calculator')))
        resp.set_cookie('bool_number_list_show', '', path=url_for('tools.calculator'), max_age=0)
        resp.set_cookie('mean', '', path=url_for('tools.calculator'), max_age=0)
        resp.set_cookie('std_dev', '', path=url_for('tools.calculator'), max_age=0)
        resp.set_cookie('std_dev_mean', '', path=url_for('tools.calculator'), max_age=0)

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
                render_template('tools/calculator.html', number_list=number_list,
                                bool_number_list_show=bool_number_list_show)

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
        resp.set_cookie('bool_number_list_show', '', path=url_for('tools.calculator'), max_age=0)
        resp.set_cookie('mean', '', path=url_for('tools.calculator'), max_age=0)
        resp.set_cookie('std_dev', '', path=url_for('tools.calculator'), max_age=0)
        resp.set_cookie('std_dev_mean', '', path=url_for('tools.calculator'), max_age=0)
        return resp
    return render_template('tools/calculator.html', number_list=number_list, bool_number_list_show=bool_number_list_show)
