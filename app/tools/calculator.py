from scipy.special import erfc
import numpy


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
    num_list = str_list_to_num_list(str_list)
    before_list = numpy.array(num_list)
    list_bool = chauvenet(before_list)
    get_list_bool_showed = list_bool.tolist()
    return get_list_bool_showed

if __name__ == "__main__":
    test = ['1.2', '3', '4.56', '1.2e+10', '1547865', '-1']
    print test
    print str_list_to_num_list(test)
    print chauvenet(numpy.array(str_list_to_num_list(test)))
    print get_bool_list_of_number_list(test)
