import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly.graph_objs as go
from plotly import tools
import datetime
import pandas as pd
import urllib.request

from blackScholes import BlackScholes_byPrice

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
    return pd.rolling_apply(obj.iloc[::-1], *args, **kwargs).iloc[::-1]

def historical_volatility(returns):
    avg_return = returns.mean()
    return_diff = returns - avg_return
    return np.sqrt((return_diff * return_diff).sum() / (len(returns) - 1))

# --------------------------------------------------------------------------------------------------
# Global Defaults
TICKER_DEFAULT = 'NFLX'
HISTORY_DATA = get_google_data(TICKER_DEFAULT).set_index("Date")
HISTORY_WINDOW = 30
HISTORICAL_RETURN = np.log(HISTORY_DATA.Close[:-1] / HISTORY_DATA.Close.shift(-1).dropna())
HISTORICAL_ROLLING_VOLATILITY = (
    rolling_apply_left(HISTORICAL_RETURN, HISTORY_WINDOW, historical_volatility))
HISTORICAL_VOLATILITY = HISTORICAL_ROLLING_VOLATILITY.iloc[0]
HISTORICAL_VOLATILITY_LOW = HISTORICAL_ROLLING_VOLATILITY.min()
HISTORICAL_VOLATILITY_HIGH = HISTORICAL_ROLLING_VOLATILITY.max()
PRICE_DEFAULT = HISTORY_DATA.Close.iloc[0]
PRICE_INDEX_RESOLUTION_DEFAULT = 100
PRICE_INDEX_DEFAULT = np.linspace(
    PRICE_DEFAULT * (1 + HISTORICAL_VOLATILITY),
    PRICE_DEFAULT * (1 - HISTORICAL_VOLATILITY),
    num=PRICE_INDEX_RESOLUTION_DEFAULT)
# TODO: Load the Risk-Free Interest Rate From the US T-Bill
INTEREST_RATE_DEFAULT = 0.03
# TODO: Load the current security's dividend yield. This will likely be an expensive load.
DIVIDEND_YIELD_DEFAULT = 0

def toHVRank(hv):
    range = HISTORICAL_VOLATILITY_HIGH - HISTORICAL_VOLATILITY_LOW
    return (hv - HISTORICAL_VOLATILITY_LOW) / range * 100.0

def fromHVRank(rank):
    range = HISTORICAL_VOLATILITY_HIGH - HISTORICAL_VOLATILITY_LOW
    return (rank / 100.0) * range + HISTORICAL_VOLATILITY_LOW

# --------------------------------------------------------------------------------------------------
# Controllable ranges
OPTION_TYPES = ["Call", "Put"]
OPTION_DEFAULT = "Put"
STRIKE_MIN = PRICE_DEFAULT * 0.5
STRIKE_MAX = PRICE_DEFAULT * 1.5
STRIKE_DEFAULT = (STRIKE_MAX + STRIKE_MIN) / 2.0
STRIKE_STEP = 0.5
STRIKE_INDEX = np.arange(STRIKE_MIN, STRIKE_MAX, STRIKE_STEP)
MATURITY_MIN = 0.0
MATURITY_MAX = 30.0
MATURITY_DEFAULT = 5.0
VOLATILITY_MAX = HISTORICAL_VOLATILITY_HIGH
VOLATILITY_MIN = HISTORICAL_VOLATILITY_LOW
VOLATILITY_STEP = (HISTORICAL_VOLATILITY_HIGH - HISTORICAL_VOLATILITY_LOW) / 100.0
VOLATILITY_DEFAULT = HISTORICAL_VOLATILITY

# --------------------------------------------------------------------------------------------------
# Static objects
PAGE_HEADER = html.Div(children="Ticker: {} Price: ${}".format(TICKER_DEFAULT, PRICE_DEFAULT))
HISTORY_FIGURE = tools.make_subplots(2, 1, shared_xaxes=True)
HISTORY_FIGURE.append_trace(go.Scatter(x=HISTORY_DATA.index, y=HISTORY_DATA.Close, name='price'),
                            1, 1)
HISTORY_FIGURE.append_trace(go.Scatter(x=HISTORICAL_ROLLING_VOLATILITY.index,
                                       y=HISTORICAL_ROLLING_VOLATILITY,
                                       name='daily volatility'), 2, 1)
HISTORY_GRAPH = dcc.Graph(id='graph-history', figure=HISTORY_FIGURE)
HV_PREAMBLE_LABEL = html.Div(children=
    "Note: These Historical Volatility figures are adjusted to yearly values for easy comps.")
HISTORICAL_VOLATILITY_ADJUSEMENT = np.sqrt(252)
HV_CURRENT_LABEL = html.Div(children="Historical ({}-day) Volatility: {}%".format(
    HISTORY_WINDOW, HISTORICAL_VOLATILITY * 100.0 * HISTORICAL_VOLATILITY_ADJUSEMENT))
HV_LOW_LABEL = html.Div(children="Historical Volatility 52-week Low: {}%".format(
    HISTORICAL_ROLLING_VOLATILITY.min() * 100.0 * HISTORICAL_VOLATILITY_ADJUSEMENT))
HV_HIGH_LABEL = html.Div(children="Historical Volatility 52-week High: {}%".format(
    HISTORICAL_ROLLING_VOLATILITY.max() * 100.0 * HISTORICAL_VOLATILITY_ADJUSEMENT))
HV_RANK_LABEL = html.Div(children="Historical Volatility Rank: {}".format(
    toHVRank(HISTORICAL_VOLATILITY)))

# --------------------------------------------------------------------------------------------------
# Create Labels and Controls
OPTION_TYPE_CONTROL = dcc.Dropdown(id='combo-optionType',
             options=[{'label': i, 'value': i} for i in OPTION_TYPES],
             value=OPTION_DEFAULT)
STRIKE_LABEL = html.Div(id='label-strike')
STRIKE_CONTROL = dcc.Slider(id='slider-strike',
                            min=STRIKE_MIN, max=STRIKE_MAX, step=STRIKE_STEP, value=STRIKE_DEFAULT)
MATURITY_LABEL = html.Div(id='label-maturity')
MATURITY_CONTROL = dcc.Slider(id='slider-maturity', min=MATURITY_MIN, max=MATURITY_MAX,
                              step=1, value=MATURITY_DEFAULT)
VOLATILITY_LABEL = html.Div(id='label-volatility')
VOLATILITY_CONTROL = dcc.Slider(id='slider-volatility',
                                min=VOLATILITY_MIN, max=VOLATILITY_MAX, step=VOLATILITY_STEP,
                                value=VOLATILITY_DEFAULT)

# --------------------------------------------------------------------------------------------------
# Create Dash Layout
app = dash.Dash()
app.layout = html.Div([
    PAGE_HEADER,
    HISTORY_GRAPH,
    HV_PREAMBLE_LABEL,
    HV_CURRENT_LABEL,
    HV_LOW_LABEL,
    HV_HIGH_LABEL,
    HV_RANK_LABEL,
    OPTION_TYPE_CONTROL,
    STRIKE_LABEL,
    STRIKE_CONTROL,
    MATURITY_LABEL,
    MATURITY_CONTROL,
    VOLATILITY_LABEL,
    VOLATILITY_CONTROL,
    dcc.Graph(id='graph-price'), #, animate=True),
])

# --------------------------------------------------------------------------------------------------
# Label Update Callbacks
@app.callback(Output('label-strike', 'children'), [Input('slider-strike', 'value')])
def update_strike(strike):
    return "Strike: ${}".format(strike)
@app.callback(Output('label-maturity', 'children'), [Input('slider-maturity', 'value')])
def update_maturity(maturity):
    return "Time to Maturity: {} days".format(maturity)
@app.callback(Output('label-volatility', 'children'), [Input('slider-volatility', 'value')])
def update_volatility(volatility):
    return "Daily Volatility: {} %".format(volatility * 100)

# --------------------------------------------------------------------------------------------------
# Price Graph Callback
@app.callback(Output('graph-price', 'figure'), [
    Input('combo-optionType', 'value'),
    Input('slider-strike', 'value'),
    Input('slider-maturity', 'value'),
    Input('slider-volatility', 'value'),
])
def update_graph_price(optionType, strike, maturity, volatility):
    optionPrices_today = BlackScholes_byPrice(optionType, PRICE_INDEX_DEFAULT, strike, maturity,
                                INTEREST_RATE_DEFAULT, DIVIDEND_YIELD_DEFAULT, volatility)
    optionPrices_expiry = BlackScholes_byPrice(optionType, PRICE_INDEX_DEFAULT, strike, 0,
                                INTEREST_RATE_DEFAULT, DIVIDEND_YIELD_DEFAULT, 0)

    scatters_today = [ go.Scatter(x=PRICE_INDEX_DEFAULT, y=optionPrices_today[column],
                                  name="{}_{}".format(column, 'today'))
                            for column in optionPrices_today.columns ]
    scatters_expiry = {column: go.Scatter(x=PRICE_INDEX_DEFAULT, y=optionPrices_expiry[column],
                                  name="{}_{}".format(column, 'expiry'))
                      for column in optionPrices_expiry.columns}
    fig = tools.make_subplots(rows=len(scatters_today), cols=1, shared_xaxes=True)
    for i in range(len(scatters_today)):
        fig.append_trace(scatters_today[i], i + 1, 1)

    # be selective with with expiry ones we use
    fig.append_trace(scatters_expiry['price'], 1, 1)
    fig.append_trace(scatters_expiry['delta'], 2, 1)


    return fig

# --------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server()
