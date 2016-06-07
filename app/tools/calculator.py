# -*- coding: utf-8 -*-
from scipy.special import erfc
import numpy


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


def num_list_to_str_list(y):
    str_list = [str(a) for a in y]
    return str_list


def get_bool_list_of_number_list(str_list):
    array_list = numpy.array(str_list_to_num_list(str_list))
    list_bool = chauvenet(array_list)
    get_list_bool_showed = list_bool.tolist()
    return get_list_bool_showed


def handle(str_list):
    array_list = numpy.array(str_list_to_num_list(str_list))
    return array_list.mean(), array_list.std(ddof=1), array_list.std(ddof=1)/numpy.sqrt(len(array_list))

if __name__ == "__main__":
    """test function"""
    test = ['1.54', '1.56', '1.58', '1.54', '1.56', '1.57', '1.53', '1.59']
    num_list = str_list_to_num_list(test)
    bool_list = chauvenet(numpy.array(str_list_to_num_list(test)))
    new_list = numpy.array(str_list_to_num_list(test))[bool_list].tolist()
    new_list_str = num_list_to_str_list(new_list)
    mean, std_dev, std_dev_mean = handle(new_list_str)
    print test
    print num_list
    print bool_list
    print new_list
    print mean, std_dev, std_dev_mean

