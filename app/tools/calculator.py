from scipy.special import erfc
import numpy


def chauvenet(y, mean=None, stdv=None):
    if mean is None:
      mean = y.mean()
    if stdv is None:
      stdv = y.std()
    n = len(y)
    criterion = 1.0/(2*n)
    d = abs(y-mean)/stdv
    d /= 2.0**0.5
    prob = erfc(d)
    filter = prob >= criterion
    return filter


def list_handler(y):
    pass
x = numpy.array([2, 4, 6, 8, 10, 12])
y = numpy.array([3.5, 7.2, 9.5, 17.1, 20.0, 25.5])

print y
print chauvenet(y)
