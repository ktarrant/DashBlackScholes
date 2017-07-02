import datetime
import urllib.request
import numpy as np
import pandas as pd
import dash_html_components as html

def data_convert(e):
    cleaned = e.strip()
    try:
        return float(cleaned)
    except ValueError:
        try:
            return datetime.datetime.strptime(cleaned, "%d-%b-%y")
        except ValueError:
            return cleaned

def get_google_data(ticker):
    """ Retrieves a years worth of daily data for the given ticker """
    base = "http://www.google.com/finance/historical?"
    params = [
        ("q", ticker),
        ("output", "csv"),
    ]
    url = base + "&".join(["{}={}".format(key, value) for (key, value) in params])
    url = url.replace(" ", "%20")
    with urllib.request.urlopen(url) as webobj:
        contents = webobj.read().decode('utf8')
        data = [[e for e in line.split(u",")] for line in contents.split(u"\n")]
        header = [e.strip().strip('\ufeff') for e in data.pop(0)]
        df = pd.DataFrame(data, columns=header).dropna(how='any').applymap(data_convert)
        return df

def rolling_apply_left(obj, *args, **kwargs):
    """ Performs a rolling apply where the result is placed in the leftmost position """
    return pd.rolling_apply(obj.iloc[::-1], *args, **kwargs).iloc[::-1]

def computeReturns(series):
    """ Computes daily returns from a series """
    return np.log(series[:-1] / series.shift(-1).dropna())

def _historical_volatility(returns):
    avg_return = returns.mean()
    return_diff = returns - avg_return
    return np.sqrt((return_diff * return_diff).sum( ) / (len(returns) - 1))

def computeDailyHV(series, window):
    """ Compute daily historical volatility for a given series, usually close data. """
    returns = computeReturns(series)
    return rolling_apply_left(returns, window, _historical_volatility)

def toHVRank(hv, hvSeries):
    hvLow = hvSeries.min()
    hvHigh = hvSeries.max()
    range = hvHigh - hvLow
    return (hv - hvLow) / range * 100.0

def fromHVRank(rank, hvSeries):
    hvLow = hvSeries.min()
    hvHigh = hvSeries.max()
    range = hvHigh - hvLow
    return (rank / 100.0) * range + hvLow
