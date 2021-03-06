"""Instantiate a Dash app."""
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from .data import create_cost_dataframe, create_all_dataframe

dash_url = "/dash/app1/"
df = create_cost_dataframe()
categories = list(set(df.category))
date = list(sorted(set(df.timeslot)))


# amountAvg = [df[df['category'] == i]['amount'].sum() / len(date) for i in categories]

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
            dcc.Graph(id="monthly-cost-pct-graph"),
            dcc.Graph(id="monthly-ICI-graph")  # income / cost / invest
        ],
        id="dash-container",
    )
    init_callbacks(dash_app)

    return dash_app.server


def init_callbacks(dash_app):
    @dash_app.callback(Output('monthly-cost-graph', 'figure'), [Input('month-slider', 'value')])
    def make_category_bar_figure(value):
        notshow = ['CardPay', 'Invest', 'Unknown']
        tmp = df[df['timeslot'] == date[value]]
        amount = [tmp[tmp['category'] == i]['amount'].sum() for i in categories if i not in notshow]
        amountAvg = [df[df['category'] == i]['amount'].sum() / len(date) for i in categories if i not in notshow]

        figure = {
            "data": [
                {'x': [x for x in categories if x not in notshow], 'y': amount, 'type': 'bar', 'name': 'MonthlyCost'},
                {'x': [x for x in categories if x not in notshow], 'y': amountAvg, 'type': 'bar', 'name': 'AvgCost'}
            ],
            "layout": {
                "title": "{}/{}".format(date[value].year, date[value].month) + " Monthly Cost vs. Avg Monthly Cost",
                "height": 500,
                "padding": 150,
            },
        }
        return figure

    @dash_app.callback(Output('monthly-cost-pct-graph', 'figure'), [Input('month-slider', 'value')])
    def make_category_pie_figure(value):
        notshow = ['CardPay', 'Invest', 'Unknown']
        tmp = df[df['timeslot'] == date[value]]
        amount = [tmp[tmp['category'] == i]['amount'].sum() for i in categories if i not in notshow]

        fig = go.Figure(data=[go.Pie(labels=[x for x in categories if x not in notshow], values=amount, hole=.4)],
                        layout={
                            'title': "{}/{}".format(date[value].year, date[value].month) + " Monthly Cost Percentage",
                            'height': 500,
                        })
        return fig

    @dash_app.callback(Output('monthly-ICI-graph', 'figure'), [Input('button', 'n_clicks')])
    def make_ICI_bar_figure(value):
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        df = create_all_dataframe()
        date = list(sorted(set(df.timeslot)))
        cost = ["Restaurant", "Grocery", "Utilities", "Clothes",
                "HouseImprovement", "Vacation", "Gas", "Cars",
                "Play", "Medicals", "White", "Parents", "Shits"]

        cost_amount = [df[(df['timeslot'] == i)][(df['category'].isin(cost))]['amount'].sum() for i in date]
        income_amount = [df[df['timeslot'] == i][df['category'] == 'Income']['amount'].sum() for i in date]
        invest_amount = [df[df['timeslot'] == i][df['category'] == 'Invest']['amount'].sum() for i in date]

        trace1 = go.Bar(
            x = date,
            y = income_amount,
            name = 'Income'
        )
        trace2 = go.Bar(
            x = date,
            y = cost_amount,
            name = 'Cost'
        )
        trace3 = go.Scatter(
            x = date,
            y = invest_amount,
            name = 'Invest'
        )

        fig.add_trace(trace1, secondary_y=False)
        fig.add_trace(trace2, secondary_y=False)
        fig.add_trace(trace3, secondary_y=True)

        return fig

    @dash_app.callback(Output('month-slider', 'marks'), Output('month-slider', 'max'), Input('button', 'n_clicks'))
    def update_slider(value):
        df = create_cost_dataframe()
        categories = list(set(df.category))
        date = list(sorted(set(df.timeslot)))
        # amountAvg = [df[df['category'] == i]['amount'].sum() / len(date) for i in categories]
        return {i: '{}/{}'.format(date[i].year, date[i].month) for i in range(len(date))}, len(date) - 1
