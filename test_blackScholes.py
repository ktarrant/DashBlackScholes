import pytest
import time
import numpy as np
from blackScholes import BlackScholes

@pytest.fixture(scope='function', params=[25, 50, 100, 500, 1000])
def sample_price(request):
    data = np.linspace(50, 150, num=request.param)

    start_time = time.clock()
    def fin():
        duration = time.clock() - start_time
        print("Time elapsed: {}".format(duration))
    request.addfinalizer(fin)

    return data

def test_BlackScholes(sample_price):
    prices = BlackScholes('c', sample_price, 100, 0.005, 0.06, 0, 0.4)