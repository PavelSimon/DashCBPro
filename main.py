import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from CoinbaseProPublic import PublicAPI as CBPublicAPI

# import pandas as pd
import time

localtime = time.asctime(time.localtime(time.time()))
print(f"štart v čase: {localtime}")

api = CBPublicAPI()
price = api.getTicker("BTC-EUR")

app = dash.Dash(__name__)
intervaly = [60, 300, 900, 3600, 21600, 86400]

app.layout = html.Div([
    html.H1(id='nadpis'),
    html.Div([
        dcc.Checklist(
            id='toggle-rangeslider',
            options=[{'label': 'Include Rangeslider',
                      'value': 'slider'}],
            value=['slider']),
        html.P('Data odobrané z pro.CoinBase.com s využitím knižnice https://github.com/whittlem/pycryptobot')
    ],
        style={'width': '48%', 'display': 'inline-block'}),
    html.Div([
        html.Label(['Intreval obchodu v min.:',
                    dcc.Dropdown(
                        id='xaxis-column',
                        options=[{'label': i, 'value': i} for i in intervaly],
                        value='60')]),
    ],
        style={'width': '48%', 'float': 'right', 'display': 'inline-block'}),

    dcc.Graph(id="graph",
              style={'height': '600px', 'width': '100%', 'display': 'inline-block'})
])


@ app.callback(
    Output('nadpis', 'children'),
    Output("graph", "figure"),
    Input("toggle-rangeslider", "value"),
    Input('xaxis-column', 'value'))
def display_candlestick(toggle_rangeslider_value, xaxis_column_name):
    localtime = 'Čas: ' + time.asctime(time.localtime(time.time()))
    print(int(xaxis_column_name))
    print(
        f"navštívené: / a objednávky skontrolované v čase: {localtime}")
    history1 = api.getHistoricalData(
        "BTC-EUR", int(xaxis_column_name))
    # print(history1)
    nadpis = '1  BTC = '+str(api.getTicker("BTC-EUR")
                             ) + ' €; Čas: ' + localtime
    fig = go.Figure(go.Candlestick(
        x=history1['date'],
        open=history1['open'],
        high=history1['high'],
        low=history1['low'],
        close=history1['close']
    ))

    fig.update_layout(
        xaxis_rangeslider_visible='slider' in toggle_rangeslider_value
    )

    return nadpis, fig


if __name__ == "__main__":
    app.run_server(debug=True)
