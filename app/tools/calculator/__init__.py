# -*- coding: utf-8 -*-
from scipy.special import erfc
import numpy


# 判断数字是否合法
def is_number(number_str):
    import re
    regex = re.match('(-?\d+.\d+e(-|\+)\d+)|(-?\d+\.\d+)|(-?\d+)', number_str)
    if regex:
        if regex.group() == number_str:
            return True
        else:
            return False
    else:
        return False


# 肖维捏准则
def chauvenet(y, mean=None, stdv=None):
    if mean is None:
      mean = y.mean()
    if stdv is None:
      stdv = y.std()
    n = len(y)
    criterion = 1.0/(2*n)
    d = abs(y-mean) / stdv
    d /= 2.0**0.5
    prob = erfc(d)
    filter_true = prob >= criterion
    return filter_true


def str_list_to_num_list(y):
    number_list = [float(a) if '.' in a else int(a) for a in y]
    return number_list


def get_bool_list_of_number_list(str_list):
    array_list = numpy.array(str_list_to_num_list(str_list))
    list_bool = chauvenet(array_list)
    get_list_bool_showed = list_bool.tolist()
    return get_list_bool_showed


def handle(str_list):
    array_list = numpy.array(str_list_to_num_list(str_list))
    return array_list.mean(), array_list.std(ddof=1), array_list.std(ddof=1)/numpy.sqrt(len(array_list))
