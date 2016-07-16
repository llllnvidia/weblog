# -*- coding: utf-8 -*-
from . import tools

from flask import render_template, request, jsonify


@tools.route('/calculator')
def calculator():
    return render_template('tools/calculator.html')


@tools.route('/calculator/_chauvenet')
def chauvenet():
    # table_method chauvenet
    number_list_string = request.args.get("number_list", None)
    if not number_list_string:
        number_list_string = request.cookies.get('number_list', None)
    # get the number list
    if number_list_string:
        number_list = number_list_string.split(' ')
        import calculator
        bool_number_list = calculator.get_bool_list_of_number_list(number_list)
        try:
            result = bool_number_list.index(False)
        # end
            return jsonify(index="list_"+str(result))
        except Exception:
            return jsonify(index="Nan")


@tools.route('/calculator/_handle')
def handle():
    # table_method handle
    number_list_string = request.args.get("number_list", None)
    if not number_list_string:
        number_list_string = request.cookies.get('number_list', None)
    # get the number list
    if number_list_string:
        number_list = number_list_string.split(' ')
        import calculator
        mean, std_dev, std_dev_mean = calculator.handle(number_list)
        return jsonify(mean=mean, std_dev=std_dev, std_dev_mean=std_dev_mean)
