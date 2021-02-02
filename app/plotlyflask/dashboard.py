"""Instantiate a Dash app."""
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output

from .data import create_dataframe
from .layout import html_layout

def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix="/dashapp/",
        external_stylesheets=[
            #"app/static/dist/css/styles.css",
            #"https://fonts.googleapis.com/css?family=Lato",
        ],
    )

    # Load DataFrame
    df = create_dataframe()

    date = list(sorted(set(df.timeslot)))
    categories = list(set(df.category))
    amountAvg = [df[df['category'] == i]['amount'].sum() / len(date) for i in categories]

    # Custom HTML layout
    dash_app.index_string = html_layout

    # Create Layout
    dash_app.layout = html.Div(
        children=[
            dcc.Graph(id="histogram-graph"),
            dcc.Slider(
                id='month-slider',
                marks={i: '{}/{}'.format(date[i].year, date[i].month) for i in range(len(date))},
                min=0,
                max=len(date)-1,
                step=1,
                value=2
            ),
            create_data_table(df),
        ],
        id="dash-container",
    )
    init_callbacks(dash_app, categories, date, amountAvg, df)

    return dash_app.server


def create_data_table(df):
    """Create Dash datatable from Pandas DataFrame."""
    table = dash_table.DataTable(
        id="database-table",
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict("records"),
        sort_action="native",
        sort_mode="native",
        page_size=300,
    )
    return table


def init_callbacks(dash_app, categories, date, amountAvg, df):
    @dash_app.callback(Output('histogram-graph', 'figure'), [Input('month-slider', 'value')])
    def make_figure(value):
        tmp = df[df['timeslot'] == date[value]]
        amount = [tmp[tmp['category'] == i]['amount'].sum() for i in categories]

        figure = {
            "data": [
                {'x': categories, 'y': amount, 'type': 'bar', 'name': 'MonthlyCost'},
                {'x': categories, 'y': amountAvg, 'type': 'bar', 'name': 'AvgCost'}
            ],
            "layout": {
                "title": "Monthly Cost",
                "height": 500,
                "padding": 150,
            },
        }
        return figure
