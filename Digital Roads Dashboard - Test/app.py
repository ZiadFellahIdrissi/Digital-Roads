import os
import pathlib
from pydoc import classname

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
import plotly.graph_objs as go
import dash_daq as daq

import pandas as pd
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=external_stylesheets
)
app.title = "Digital Roads Dashboard"
server = app.server
app.config["suppress_callback_exceptions"] = True

APP_PATH = str(pathlib.Path(__file__).parent.resolve())
df = pd.read_csv(os.path.join(APP_PATH, os.path.join("data", "spc_data.csv")))

params = list(df)
max_length = len(df)

suffix_row = "_row"
suffix_button_id = "_button"
suffix_sparkline_graph = "_sparkline_graph"
suffix_count = "_count"
suffix_ooc_n = "_OOC_number"
suffix_ooc_g = "_OOC_graph"
suffix_indicator = "_indicator"


def build_banner():
    return html.Div(
        id="banner",
        className="banner",
        children=[
            html.Div(
                id="banner-text",
                children=[
                    html.H5("Digital Roads"),
                    html.H6("Cites Clutering and Suggesting of Itineraries"),
                ],
            ),
            html.Div(
                id="banner-logo",
                children=[
                    html.Button(
                        id="learn-more-button", children="LEARN MORE", n_clicks=0
                    ),
                    html.A(
                        html.Img(id="logo", src=app.get_asset_url("altran.png")),
                        href="",
                    ),
                ],
            ),
        ],
    )


def build_tabs():
    return html.Div(
        id="tabs",
        className="tabs",
        children=[
            dcc.Tabs(
                id="app-tabs",
                value="tab_clustering",
                className="custom-tabs",
                children=[
                    dcc.Tab(
                        id="Specs-tab",
                        label="Clustering",
                        value="tab_clustering",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                    ),
                    dcc.Tab(
                        id="Control-chart-tab",
                        label="Itinerary proposals",
                        value="tab_itinerary",
                        className="custom-tab",
                        selected_className="custom-tab--selected",
                    ),
                ],
            )
        ],
    )


def generate_modal():
    return html.Div(
        id="markdown",
        className="modal",
        children=(
            html.Div(
                id="markdown-container",
                className="markdown-container",
                children=[
                    html.Div(
                        className="close-container",
                        children=html.Button(
                            "Close X",
                            id="markdown_close",
                            n_clicks=0,
                            className="closeButton",
                        ),
                    ),
                    html.A(
                        html.Img(id="logod", src=app.get_asset_url("logo digital roads 1.png")),
                        href="",
                    ),
                    html.Div(
                        className="markdown-text",
                        children=dcc.Markdown(
                            children=(
                                """
                        ##### Digital roads

                        This is a dashboard for the visualization of the different clusters and different itineraries.

                        ##### The main goal of Digital Roads

                        The goal of Digital Roads is to identify cities with similar characteristics for each country, to help you choose a city from each group. 

                        In addition, Digital Roads is able to suggest a variety of itineraries in different cities to suit your needs.


                    """
                            )
                        ),
                    ),
                  
                ],
            )
        ),
    )

def build_cluters_settings():
    return html.Div(
        id="quick-stats",
        className="row",
        children=[
            html.Div(
                id="metric-select-menu",
                children = [
                    html.H6("Choose Country"),
                    dcc.Dropdown(
                        options = [
                            {'label': 'Morocco', 'value': 'morocco'},
                            {'label': 'Algeria', 'value': 'algeria'},
                            {'label': 'Tunisia', 'value': 'tunisia'},
                            {'label': 'Iraq', 'value': 'iraq'},
                            {'label': 'Egypt', 'value': 'egypt'},
                            {'label': 'Libya', 'value': 'libya'},
                            {'label': 'Oman', 'value': 'oman'},
                            {'label': 'Qatar', 'value': 'qatar'},
                            {'label': 'United Kingdom', 'value': 'UK'},
                            {'label': 'New Zealand', 'value': 'NZ'},
                            {'label': 'Australia', 'value': 'australia'},
                            {'label': 'Brazil', 'value': 'brazil'},
                            {'label': 'Canada', 'value': 'canada'},
                            {'label': 'France', 'value': 'france'},
                            {'label': 'Germany', 'value': 'germany'},
                            
                            
                        ],
                        value="morocco",
                    ),
                ],
            ),
            html.Div(
                id="metric-select-menu",
                children = [
                    html.H6("Clustering Based on"),
                    dcc.RadioItems(
                        id="radio",
                        options=[
                        
                            {'label': 'Cites', 'value': 'cites'},
                            {'label': 'Regions', 'value': 'regions'},
                            {'label': 'Districts', 'value': 'districts',}
                        ],
                        value='cites',
                    ),
                ],
            ),
            html.Div(
                id="metric-select-menu",
                children = [
                    html.H6("Feauters Selector"),
                    dcc.Checklist(
                    options=[
                        {'label': 'Traffic Calming', 'value': 'traffic_calming'},
                        {'label': 'Traffic Signals	', 'value': 'traffic_signals'},
                        {'label': 'Junctions', 'value': 'junction'},
                        {'label': 'Tunnels', 'value': 'tunnel'},
                        {'label': 'Bridges', 'value': 'bridge'},
                        {'label': 'Turning Circles', 'value': 'turning_circle'},
                    ],
                    value=['traffic_calming', 'traffic_signals','junction'],
                    # inline=True,
                    ),
                ],
            ),
            html.Div(
                id="metric-select-menu",
                children = [
                    html.H6("Number of Clusters"),
                    dcc.Slider(min=5,
                               max=17,
                               step=2,
                               value=10,
                               id='my-slider',
                               marks={
                                        6: "6",
                                        8: "8",
                                        10: "10",
                                        12: "12",
                                        14: "14",
                                        16: "15",
                                },
                                tooltip={"placement": "bottom"}
                               ),     
                ],
            ),
            
            html.Div(
                id="utility-card",
                children = [
                html.Button(
                    "Run Clustering & Update Map",
                    id="btn-updt-map",
                    title="Click to run spatial clustering, computing could take seconds to complete.",
                    n_clicks=0,
                ),
                ]
            ),
        ]
    )


def generate_section_banner(title):
    return html.Div(className="section-banner", children=title)


def build_top_panel(stopped_interval):
    return html.Div(
        id="top-section-container",
        className="row",
        children=[
            # Metrics summary
            html.Div(
                id="metric-summary-session",
                className="eight columns",
                children=[
                    generate_section_banner("Map"),
                    html.Div(
                        id="metric-div",
                        # children=[
                        # dcc.Graph(id="map", config={"responsive": True}),
                        # ]
                    )
                ]
            )
        ]
    )


def build_tab_itinerary():
    return [
        # Manually select metrics
        html.Div(
            id="set-specs-intro-container",
            # className='twelve columns',
            children=html.P(
                "Digital Roads will help you find best Itineraries in every City you want !"
            ),
        ),
        html.Div(
            id="settings-menu",
            children=[
                html.Div(
                    id="metric-select-menu",
                ),
                html.Div(
                    id="value-setter-menu",
                ),
            ],
        ),
    ]


@app.callback(
    [Output("app-content", "children"), Output("interval-component", "n_intervals")],
    [Input("app-tabs", "value")],
    [State("n-interval-stage", "data")],
)
def render_tab_content(tab_switch, stopped_interval):
    if tab_switch == "tab_itinerary":
        return build_tab_itinerary(), stopped_interval
    return (
        html.Div(
            id="status-container",
            children=[
                build_cluters_settings(),
                html.Div(
                    id="graphs-container",
                    children=[build_top_panel(stopped_interval)],
                ),
            ],
        ),
        stopped_interval,
    )



# ======= Callbacks for modal popup =======
@app.callback(
    Output("markdown", "style"),
    [Input("learn-more-button", "n_clicks"), Input("markdown_close", "n_clicks")],
)
def update_click_output(button_click, close_click):
    ctx = dash.callback_context

    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if prop_id == "learn-more-button":
            return {"display": "block"}

    return {"display": "none"}





app.layout = html.Div(
    id="big-app-container",
    children=[
        build_banner(),
        dcc.Interval(
            id="interval-component",
            interval=2 * 1000,  # in milliseconds
            n_intervals=50,  # start at batch 50
            disabled=True,
        ),
        html.Div(
            id="app-container",
            children=[
                build_tabs(),
                # Main app
                html.Div(id="app-content"),
            ],
        ),
        # dcc.Store(id="value-setter-store", data=init_value_setter_store()),
        dcc.Store(id="n-interval-stage", data=50),
        generate_modal(),
    ],
)


# Running the server
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
