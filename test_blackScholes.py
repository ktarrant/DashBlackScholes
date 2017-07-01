import pytest
import time
import numpy as np
import pandas as pd

#Project-level imports
from blackScholes import BlackScholes_byPrice, BlackScholes_byStrikeAndPrice

DEFAULT_RISK_FREE_INTEREST_RATE = 0.03

@pytest.fixture(scope='function', params=[10, 25, 50, 100, 500, 1000])
def sample_price(request):
    data = np.linspace(50, 150, num=request.param)

    start_time = time.clock()
    def fin():
        duration = time.clock() - start_time
        print("Time elapsed: {}".format(duration))
    request.addfinalizer(fin)

    return data

@pytest.fixture(scope='function')
def strike_price(request):
    return np.arange(75, 125, 5)

def test_BlackScholes(sample_price):
    prices = BlackScholes_byPrice('c', sample_price, 100, 1, DEFAULT_RISK_FREE_INTEREST_RATE, 0, 0.4)
    print(prices)

def test_BlackScholes_Panel(sample_price, strike_price):
    prices = BlackScholes_byStrikeAndPrice('c', sample_price, strike_price, 1, DEFAULT_RISK_FREE_INTEREST_RATE, 0, 0.4)
    print(prices['price'])
