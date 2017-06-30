from scipy.stats import norm
import numpy as np

def BlackScholes(CallPutFlag,S,K,T,r,d,v):
    """
    # The Black Scholes Formula
    # CallPutFlag - This is set to 'c' for call option, anything else for put
    # S - Stock price
    # K - Strike price
    # T - Time to maturity
    # r - Riskfree interest rate
    # d - Dividend yield
    # v - Volatility
    """
    d1 = (np.log(S/K) + ((r-d) + v*v/2.) * T) / (v * np.sqrt(T))
    d2 = d1 - v * np.sqrt(T)
    if 'c' in CallPutFlag.lower():
        return (S * np.exp(-d*T) * norm.cdf(d1)) - (K * np.exp(-r*T) * norm.cdf(d2))
    else:
        return (K * np.exp(-r*T) * norm.cdf(-d2)) - (S * np.exp(-d*T) * norm.cdf(-d1))