import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly.graph_objs as go
from plotly import tools
import pandas as pd

# Project-level imports
from history import get_google_data, computeDailyHV, fromHVRank, toHVRank
from blackScholes import BlackScholes_byPrice

# --------------------------------------------------------------------------------------------------
# Global Defaults
TICKER_DEFAULT = 'AMZN'
HISTORY_DATA = get_google_data(TICKER_DEFAULT).set_index("Date")
HISTORICAL_VOLATILITY_ADJUSEMENT = np.sqrt(252)
PRICE_DEFAULT = HISTORY_DATA.Close.iloc[0]
PRICE_INDEX_RESOLUTION_DEFAULT = 100
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
MATURITY_MAX = 30.0
MATURITY_DEFAULT = 5.0
HISTORY_WINDOW_MIN = 5
HISTORY_WINDOW_DEFAULT = 30
HISTORY_WINDOW_MAX = len(HISTORY_DATA.index)
HVRANK_MIN = 0.0
HVRANK_MAX = 100.0
HVRANK_STEP = 1.0

# --------------------------------------------------------------------------------------------------
# Static objects
PAGE_HEADER = html.Div(children="Ticker: {} Price: ${}".format(TICKER_DEFAULT, PRICE_DEFAULT))
HISTORY_DATA_SCATTER = go.Scatter(x=HISTORY_DATA.index, y=HISTORY_DATA.Close, name='price')

# --------------------------------------------------------------------------------------------------
# Create Labels and Controls
WINDOW_LABEL = html.Div(id='label-window')
WINDOW_CONTROL = dcc.Slider(id='slider-window',
                                min=HISTORY_WINDOW_MIN, max=HISTORY_WINDOW_MAX, step=1,
                                value=HISTORY_WINDOW_DEFAULT)
HISTORY_GRAPH = dcc.Graph(id='graph-history')
OPTION_TYPE_CONTROL = dcc.Dropdown(id='combo-optionType',
             options=[{'label': i, 'value': i} for i in OPTION_TYPES],
             value=OPTION_DEFAULT)
STRIKE_LABEL = html.Div(id='label-strike')
STRIKE_CONTROL = dcc.Slider(id='slider-strike',
                            min=STRIKE_MIN, max=STRIKE_MAX, step=STRIKE_STEP, value=STRIKE_DEFAULT)
MATURITY_LABEL = html.Div(id='label-maturity')
MATURITY_CONTROL = dcc.Slider(id='slider-maturity', min=MATURITY_MIN, max=MATURITY_MAX,
                              step=1, value=MATURITY_DEFAULT)
HVRANK_LABEL = html.Div(id='label-volatility')
HVRANK_CONTROL = dcc.Slider(id='slider-volatility',
                                min=HVRANK_MIN, max=HVRANK_MAX, step=HVRANK_STEP,
                                value=50.0)
HV_STATS_DIV = html.Div(id='div-hv-stats')

# --------------------------------------------------------------------------------------------------
# Create Dash Layout
app = dash.Dash()
app.layout = html.Div([
    PAGE_HEADER,
    WINDOW_LABEL, WINDOW_CONTROL,
    HISTORY_GRAPH,
    HV_STATS_DIV,
    OPTION_TYPE_CONTROL,
    STRIKE_LABEL, STRIKE_CONTROL,
    MATURITY_LABEL, MATURITY_CONTROL,
    HVRANK_LABEL, HVRANK_CONTROL,
    dcc.Graph(id='graph-price'), #, animate=True),
])

def extract_series(figure, index):
    return pd.Series(figure['data'][index]['y'], index=figure['data'][index]['x'])

# --------------------------------------------------------------------------------------------------
# Label Update Callbacks
@app.callback(Output('label-window', 'children'), [Input('slider-window', 'value')])
def update_window(window):
    return "Window Size: {} days".format(window)

@app.callback(Output('div-hv-stats', 'children'), [Input('graph-history', 'figure')])
def update_hv_stats(figure):
    hvSeries = extract_series(figure, 1)
    hv = hvSeries.iloc[0] * 100.0 * HISTORICAL_VOLATILITY_ADJUSEMENT
    hvLow = hvSeries.min() * 100.0 * HISTORICAL_VOLATILITY_ADJUSEMENT
    hvHigh = hvSeries.max() * 100.0 * HISTORICAL_VOLATILITY_ADJUSEMENT
    hvRank = toHVRank(hvSeries.iloc[0], hvSeries)
    descriptionLabel = html.Div(children=
        "Note: These Historical Volatility figures are adjusted to yearly values for easy comps.")
    currentLabel = html.Div(children="Historical Volatility: {:.2f}%".format(hv))
    lowLabel = html.Div(children="Historical Volatility 52-week Low: {:.2f}%".format(hvLow))
    highLabel = html.Div(children="Historical Volatility 52-week High: {:.2f}%".format(hvHigh))
    hvRankLabel = html.Div(children="Historical Volatility Rank: {:.1f}".format(hvRank))
    return html.Div(children=[descriptionLabel, currentLabel, lowLabel, highLabel, hvRankLabel])

@app.callback(Output('label-strike', 'children'), [Input('slider-strike', 'value')])
def update_strike(strike):
    return "Strike: ${}".format(strike)

@app.callback(Output('label-maturity', 'children'), [Input('slider-maturity', 'value')])
def update_maturity(maturity):
    return "Time to Maturity: {} days".format(maturity)

@app.callback(Output('label-volatility', 'children'), [Input('slider-volatility', 'value')])
def update_volatility(hvRank):
    return "HVRank: {}".format(hvRank)

# --------------------------------------------------------------------------------------------------
# History Graph Callback
@app.callback(Output('graph-history', 'figure'), [Input('slider-window', 'value')])
def update_history(window):
    dailyVolatility = computeDailyHV(HISTORY_DATA.Close, window)
    figure = tools.make_subplots(2, 1, shared_xaxes=True)
    figure.append_trace(HISTORY_DATA_SCATTER, 1, 1)
    figure.append_trace(go.Scatter(x=dailyVolatility.index, y=dailyVolatility,
                                           name='daily volatility'), 2, 1)
    return figure

# --------------------------------------------------------------------------------------------------
# Price Graph Callback
@app.callback(Output('graph-price', 'figure'), [
    Input('graph-history', 'figure'),
    Input('combo-optionType', 'value'),
    Input('slider-strike', 'value'),
    Input('slider-maturity', 'value'),
    Input('slider-volatility', 'value'),
])
def update_graph_price(figure, optionType, strike, maturity, hvRank):
    hvSeries = extract_series(figure, 1)
    volatility = fromHVRank(hvRank, hvSeries)
    vol_range = 0.5 * volatility * HISTORICAL_VOLATILITY_ADJUSEMENT * PRICE_DEFAULT
    price_index = np.linspace(PRICE_DEFAULT + vol_range, PRICE_DEFAULT -vol_range,
        num=PRICE_INDEX_RESOLUTION_DEFAULT)
    optionPrices_today = BlackScholes_byPrice(optionType, price_index, strike, maturity,
                                INTEREST_RATE_DEFAULT, DIVIDEND_YIELD_DEFAULT, volatility)
    optionPrices_expiry = BlackScholes_byPrice(optionType, price_index, strike, 0,
                                INTEREST_RATE_DEFAULT, DIVIDEND_YIELD_DEFAULT, 0)

    scatters_today = [ go.Scatter(x=price_index, y=optionPrices_today[column],
                                  name="{}_{}".format(column, 'today'))
                            for column in optionPrices_today.columns ]
    scatters_expiry = {column: go.Scatter(x=price_index, y=optionPrices_expiry[column],
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
