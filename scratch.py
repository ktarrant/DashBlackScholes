
# --------------------------------------------------------------------------------------------------
# THIS FILE NOT INTENDED FOR USE
# I simply use this as a place to keep code snippets that I plan to use later
# --------------------------------------------------------------------------------------------------

CHANGE_LABEL = html.Div(id="label-change")
CHANGE_CONTROL = dcc.Slider(id="slider-change", value=0,
                            min=-VOLATILITY_MAX, max=VOLATILITY_MAX, step=VOLATILITY_STEP)

CHANGE_LABEL,
CHANGE_CONTROL,
dcc.Graph(id='graph-change'),

@app.callback(Output('label-change', 'children'), [Input('slider-change', 'value')])
def update_volatility(volatility):
    return "Price Change: {}".format(volatility)

# --------------------------------------------------------------------------------------------------
# Change Graph Callback
@app.callback(Output('output-bs', 'figure'), [
    Input('combo-optionType', 'value'),
    Input('slider-maturity', 'value'),
    Input('slider-volatility', 'value'),
    Input('slider-change', 'value'),
])
def update_graph_price(optionType, maturity, volatility, change):
    optionPrices_before = BlackScholes(optionType, PRICE_INDEX_DEFAULT, STRIKE_INDEX, maturity,
                                INTEREST_RATE_DEFAULT, DIVIDEND_YIELD_DEFAULT, volatility)
    optionPrices_after = BlackScholes(optionType, PRICE_INDEX_DEFAULT + change, STRIKE_INDEX,
                                maturity, INTEREST_RATE_DEFAULT, DIVIDEND_YIELD_DEFAULT, volatility)

    return {'data': []} # TODO: How to draw a heatmap??