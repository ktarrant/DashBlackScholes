from scipy.stats import norm
import numpy as np
import pandas as pd

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
    result = {}
    d1_A = np.log(stockPrice / strikePrice)
    d1_B = ((interestRate - dividendYield) / 365.0) + (volatility * volatility / 2.0)
    d1_C = (volatility * np.sqrt(timeToMaturity))
    d1 = (d1_A + d1_B * timeToMaturity) / d1_C
    d2 = d1 - volatility * np.sqrt(timeToMaturity)
    if 'p' in optionType.lower():
        d1 = -d1
        d2 = -d2
    c1 = stockPrice * norm.cdf(d1)
    c2 = strikePrice * np.exp(-interestRate * timeToMaturity / 365.0) * norm.cdf(d2)
    if 'p' in optionType.lower():
        c1 = -c1
        c2 = -c2

    result["price"] = c1 - c2
    result["delta"] = norm.cdf(d1)
    return result

def BlackScholes_byPrice(optionType, stockPrice, *args):
    return pd.DataFrame(BlackScholes(optionType, stockPrice, *args), index=stockPrice)