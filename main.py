import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import datetime
import numpy as np
import plotly.graph_objs as go

from googlefinance import getQuotes

from blackScholes import BlackScholes_byPrice

# --------------------------------------------------------------------------------------------------
# Global Defaults
TICKER_DEFAULT = 'AAPL'
# TODO: This is expensive loading. What's the best way to handle this? A button?
#QUOTE_DEFAULT = getQuotes(TICKER_DEFAULT)[0]
PRICE_DEFAULT = 150.00 #float(QUOTE_DEFAULT["LastTradePrice"])
PRICE_INDEX_RESOLUTION_DEFAULT = 20
PRICE_INDEX_DEFAULT = np.linspace(
    PRICE_DEFAULT * 0.75, PRICE_DEFAULT * 1.25, num=PRICE_INDEX_RESOLUTION_DEFAULT)
# TODO: Load the Risk-Free Interest Rate From the US T-Bill
INTEREST_RATE_DEFAULT = 0.03
# TODO: Load the current security's dividend yield. This will likely be an expensive load.
DIVIDEND_YIELD_DEFAULT = 0

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
MATURITY_MAX = 365.0
MATURITY_DEFAULT = 5.0
VOLATILITY_MAX = 1.0
VOLATILITY_STEP = 0.01
VOLATILITY_MIN = VOLATILITY_STEP
VOLATILITY_DEFAULT = 0.05

# --------------------------------------------------------------------------------------------------
# Create Labels and Controls
PAGE_HEADER = html.Div(children="Ticker: {} Price: {}".format(TICKER_DEFAULT, PRICE_DEFAULT))
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
    return "Strike: {}".format(strike)
@app.callback(Output('label-maturity', 'children'), [Input('slider-maturity', 'value')])
def update_maturity(maturity):
    return "Maturity: {}".format(maturity)
@app.callback(Output('label-volatility', 'children'), [Input('slider-volatility', 'value')])
def update_volatility(volatility):
    return "Volatility: {}".format(volatility)

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
                                INTEREST_RATE_DEFAULT, DIVIDEND_YIELD_DEFAULT, volatility)

    return {'data': [
        go.Scatter(x=PRICE_INDEX_DEFAULT, y=optionPrices_today.price),
        go.Scatter(x=PRICE_INDEX_DEFAULT, y=optionPrices_expiry.price),
    ]}

# --------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server()
