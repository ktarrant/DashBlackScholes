from scipy.stats import norm
import numpy as np
import pandas as pd
from collections import OrderedDict

def BlackScholes(optionType, stockPrice, strikePrice, timeToMaturity, interestRate, dividendYield, volatility):
    """
    The Black Scholes Formula
    Args:
        optionType(str): "call" or "put"
        stockPrice(float): Current stock price in $
        strikePrice(float): Strike price of the contract in $
        timeToMaturity(float): Number of days until maturity
        interestRate(float): The risk-free interest rate.
        dividendYield (float): Annualized dividend yield of underlying.
        volatility(float): Daily volatility of the underlying

    Returns:
        float: Theoretical price of the option contract
    """
    result = OrderedDict()
    d1_A = np.log(np.outer(stockPrice, 1 / strikePrice))
    # TODO: Is there a cleaner/safer/better way to take off the extra dimension if it is 1?
    if d1_A.shape[1] == 1:
        d1_A = d1_A[:, 0]
    d1_B = ((interestRate - dividendYield) / 365.0) + (volatility * volatility / 2.0)
    d1_C = (volatility * np.sqrt(timeToMaturity))
    d1 = (d1_A + d1_B * timeToMaturity) / d1_C
    d2 = d1 - d1_C
    if 'p' in optionType.lower():
        d1 = -d1
        d2 = -d2
    c1 = np.transpose(stockPrice * np.transpose(norm.cdf(d1)))
    c2 = strikePrice * np.exp(-interestRate * timeToMaturity / 365.0) * norm.cdf(d2)
    if 'p' in optionType.lower():
        c1 = -c1
        c2 = -c2

    result["price"] = c1 - c2
    result["delta"] = norm.cdf(d1)
    result["gamma"] = 1 / (volatility * stockPrice * np.sqrt(timeToMaturity))
    result["rho"] = timeToMaturity * c2
    # TODO: Theta and Vega. They involve I think the derivative of norm.cdf (N') ?
    return result

def BlackScholes_byPrice(optionType, stockPrice, *args):
    data = BlackScholes(optionType, stockPrice, *args)
    return pd.DataFrame(data, index=stockPrice)

def BlackScholes_byStrikeAndPrice(optionType, stockPrice, strikePrice, *args):
    data = BlackScholes(optionType, stockPrice, strikePrice, *args)
    return pd.Panel(data,
                    items=["price", "delta", "gamma", "rho"],
                    major_axis=stockPrice,
                    minor_axis=strikePrice)