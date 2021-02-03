"""Instantiate a Dash app."""
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

from .data import create_dataframe

dash_url = "/dash/app1/"
df = create_dataframe()
categories = list(set(df.category))
date = list(sorted(set(df.timeslot)))
amountAvg = [df[df['category'] == i]['amount'].sum() / len(date) for i in categories]

def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = dash.Dash(
        server=server,
        url_base_pathname=dash_url,
        external_stylesheets=[
            # "app/static/dist/css/styles.css",
            # "https://fonts.googleapis.com/css?family=Lato",
        ],
    )

    # Create Layout
    dash_app.layout = html.Div(
        children=[
            dcc.Graph(id="monthly-cost-graph"),
            dcc.Slider(id='month-slider',
                       min=0,
                       step=1,
                       value=2),
            html.Button('Refresh', id='button'),
            dcc.Graph(id="monthly-cost-pct-graph")
        ],
        id="dash-container",
    )
    init_callbacks(dash_app)

    return dash_app.server


def init_callbacks(dash_app):
    @dash_app.callback(Output('monthly-cost-graph', 'figure'), [Input('month-slider', 'value')])
    def make_figure(value):
        tmp = df[df['timeslot'] == date[value]]
        amount = [tmp[tmp['category'] == i]['amount'].sum() for i in categories]

        figure = {
            "data": [
                {'x': categories, 'y': amount, 'type': 'bar', 'name': 'MonthlyCost'},
                {'x': categories, 'y': amountAvg, 'type': 'bar', 'name': 'AvgCost'}
            ],
            "layout": {
                "title": "{}/{}".format(date[value].year, date[value].month) + " Monthly Cost vs. Avg Monthly Cost",
                "height": 500,
                "padding": 150,
            },
        }
        return figure

    @dash_app.callback(Output('monthly-cost-pct-graph', 'figure'), [Input('month-slider', 'value')])
    def make_figure(value):
        tmp = df[df['timeslot'] == date[value]]
        amount = [tmp[tmp['category'] == i]['amount'].sum() for i in categories]

        fig = go.Figure(data=[go.Pie(labels=categories, values=amount, hole=.4)],
                        layout={
                            'title': "{}/{}".format(date[value].year, date[value].month) + " Monthly Cost Percentage",
                            'height': 500,
                        })
        return fig


    @dash_app.callback(Output('month-slider', 'marks'), Output('month-slider', 'max'), Input('button', 'n_clicks'))
    def update_slider(value):
        global df, categories, date, amountAvg
        df = create_dataframe()
        categories = list(set(df.category))
        date = list(sorted(set(df.timeslot)))
        amountAvg = [df[df['category'] == i]['amount'].sum() / len(date) for i in categories]
        return {i: '{}/{}'.format(date[i].year, date[i].month) for i in range(len(date))}, len(date) - 1
