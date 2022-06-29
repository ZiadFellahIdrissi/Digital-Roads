import os
import pathlib
from pydoc import classname
from cv2 import GC_INIT_WITH_MASK
import dash_leaflet as dl

import dash
from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State
import plotly.express as px 
import plotly.graph_objs as go
import dash_daq as daq
import pandas as pd 
import folium


from itinerary_proposals import get_path_on_map, generate_KPIs
from clustering_model import train_clustring_modal, data_processing

app = Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

app.title = "Digital Roads Dashboard"
server = app.server
app.config["suppress_callback_exceptions"] = True
app._favicon = "DR.ico"

APP_PATH = str(pathlib.Path(__file__).parent.resolve())
cites_in_MA = pd.read_csv(os.path.join(APP_PATH, os.path.join("data", "maroc_cites.csv")), sep=';')


folium.Map(zoom_start=12).save("wordmap.html")

df_final = pd.DataFrame()
cities_base_final = pd.DataFrame()
best_model = ""
current_k = 0
sunchart = {}
points_to_vist = []
df_points = pd.DataFrame()
G = None
G_proj = None
my_path_length = None

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
                        html.Img(id="logod", src=app.get_asset_url("digital roads.png")),
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
                        id = 'select_country',
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
                        id="clustering-based-on",
                        options=[
                        
                            {'label': 'Cites', 'value': 'cites'},
                            {'label': 'Regions', 'value': 'regions'},
                            {'label': 'Districts', 'value': 'districts', 'disabled': True}
                        ],
                        value='cites',
                    ),
                ],
            ),
            html.Div(
                id="metric-select-menu",
                children = [
                    html.H6("Feauters Selector"),
                    dcc.Dropdown(
                    id="features_selector_id",
                    multi= True,
                    options=[
                        {'label': 'Traffic Calming', 'value': 'traffic_calming'},
                        {'label': 'Traffic Signals	', 'value': 'traffic_signals'},
                        {'label': 'Junctions', 'value': 'junction'},
                        {'label': 'Motorway Junction', 'value': 'motorway_junction'},
                        {'label': 'Turning Circles', 'value': 'turning_circle'},
                        {'label': 'Turning Loops', 'value': 'turning_loop'},
                        {'label': 'Mini Roundabout', 'value': 'mini_roundabout'},
                        {'label': 'Crossing', 'value': 'crossing'},
                        {'label': 'Tunnels', 'value': 'tunnel'},
                        {'label': 'Bridges', 'value': 'bridge'},
                        {'label': 'stops', 'value': 'stop'},
                        
                        
                    ],
                    value=['traffic_calming', 'traffic_signals','junction', "motorway_junction",'turning_circle','turning_loop','mini_roundabout','crossing','tunnel','bridge','stop'],
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
                ],
            ),
        ]
    )


def base_map():
    return html.Iframe(id= 'map', srcDoc= open("wordmap.html", 'r').read(), width="100%", height="760")


def generate_section_banner(title):
    return html.Div(className="section-banner", children=title)


def build_top_panel(stopped_interval):
    return html.Div(
        id="top-section-container",
        className="row",
        children=[
            # the Map
            html.Div(
                id="metric-summary-session",
                className="eight columns",
                children=[
                    dcc.Loading(
                        id="myspinner",
                        children=[
                            html.Div(
                                id="section-banner-number-of-clusters",
                                children=[]
                            ),

                            html.Div(
                                id="map-div",
                                children = []
                            ),
                            
                        ], 
                        color="#119DFF",
                        type="dot",
                        fullscreen=False,
                    ),
                    dcc.Loading(
                        id="myspinner",
                        children=[
                            html.Div(
                                className='for_cluster_contianes',
                                id = "cluster_contianes",
                                children = [
                                    dcc.Graph(
                                        id="cites-in-every-cluster",
                                        figure = {},
                                    ),
                                ],
                            )  
                        ],
                        color="#119DFF",
                        type="dot",
                        fullscreen=False,
                    )
                ]
            ), 


        ]
    )

# def build_chart_panel():
#     return html.Div(
#         id="control-chart-container",
#         className="twelve s",
#         children=[
#             html.Div(className="section-what-cluster-contain", children="Clusters"),
#             dcc.Graph(
#                 id="control-chart-live",
#             ),
#         ],
#     )


def build_tab_itinerary():
    return [
        html.Div(
            id="set-specs-intro-container",
            children=html.P(
                "Digital Roads will help you find best Itinerarie in every City you want !"
            ),
        ),
        html.Div(
            id="settings-menu",
            children=[
                html.Div(
                    id="metric-select-menu",
                    # className='five columns',
                    children = [
                        html.H6("Choose Country"),
                        dcc.Dropdown(
                            id = 'select_country_iten',
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
                            ],
                            value="morocco",
                        ),
                        html.Div(
                            className = 'for_cluster_contianes',
                            id = "map_choose_KPI",
                            children = [],
                            style = {},
                        ),

                    ],
                ),
                html.Div(
                    id="value-setter-menu",
                    # className='six columns',
                    children = [
                        html.H6("Choose city"),
                        dcc.Dropdown(
                            id = 'select_city_iten',
                            options = [],
                            value = "casablanca",
                        ),
                        html.Div(
                            className = 'for_cluster_contianes',
                            id = "map_choose",
                            children = [],
                            style = {},
                        ),
                        
                    ],
                ),
            ],
        ),
    ]




@app.callback(
    Output(component_id="select_city_iten", component_property = "options"),
    [
        Input(component_id="select_country_iten", component_property= "value")
    ],

)
def cites_option(country):
    return [{'label': col, 'value': col} for col in cites_in_MA.NAME2]
    


@app.callback(
    [Output(component_id="map_choose", component_property = "children"), 
     Output(component_id="map_choose_KPI", component_property = "children")],
    [Input(component_id="select_city_iten", component_property= "value")],prevent_initial_call= True
)
def display_map_to_choose(city):
    cordinates = cites_in_MA[cites_in_MA.NAME2 == city][["X","y"]]   
    print(float(cordinates.y), float(cordinates.X))
    html_com = html.Div(
        className='let_client_choose',
        id = "let_client_chos",
        children = [
            dl.Map(
                [dl.TileLayer(), dl.LayerGroup(id="layer")],
                zoom=10,
                center=(float(cordinates.y), float(cordinates.X)),
                id="map_client_want_choose",
                style={'width': '100%', 'height': '70vh', 'margin': "auto", "display": "block"}
                ),
            html.Button(
                "Export as KML",
                id="btn-get_itine",
                title="Click Generate Itinerary, computing could take up to minute to complete.",
                n_clicks=0,
            ),
            dcc.Loading(
                id="myspinnerformap_ti",
                children=[
                    dcc.Graph(
                        id="map_updated_for_itine",
                        figure = {},
                        style={'display': 'none'}
                    ), 
                ],
                color="#119DFF",
                type="dot",
                fullscreen=False,
            )
        ]
    )
    html_com_KPI = html.Div(
        id = "Visualize_KPI",
        children = [
            dcc.Loading(
                id="myspinnerforKPI_ti",
                children=[
                    dcc.Graph(
                        id="type_of_routes_KPI",
                        figure = {},
                        style={'display': 'none'}
                    ), 
                    dcc.Graph(
                        id="Number_of_obs_KPI",
                        figure = {},
                        style={'display': 'none'}
                    ), 
                ],
                color="#119DFF",
                type="dot",
                fullscreen=False,
            )
            
        ]
    )
    return html_com, html_com_KPI



@app.callback(
    Output("layer", "children"), 
    [Input("map_client_want_choose", "click_lat_lng")], prevent_initial_call= True
)
def map_click(click_lat_lng):
    points_to_vist.append(tuple(click_lat_lng))
    return [dl.Marker(position=[i[0], i[1]], children=dl.Tooltip("({:.3f}, {:.3f})".format(i[0], i[1]))) for i in points_to_vist]
    


@app.callback(
    [
        Output(component_id="map_updated_for_itine", component_property = "figure"),
        Output(component_id="map_updated_for_itine", component_property = "style"),

        Output(component_id="type_of_routes_KPI", component_property = "figure"),
        Output(component_id="type_of_routes_KPI", component_property = "style"),

        Output(component_id="Number_of_obs_KPI", component_property = "figure"),
        Output(component_id="Number_of_obs_KPI", component_property = "style"),
    ],  
    [Input(component_id="btn-get_itine", component_property = "n_clicks")],
    State(component_id="select_city_iten", component_property= "value"),
    prevent_initial_call= True
)
def update_the_map_for_itenirers(get_itine, city):
    if get_itine != 0:
        fig, G_proj, my_path_length = get_path_on_map(city+", Maroc", points_to_vist)
        fig_highways, fig_obstacls = generate_KPIs(G_proj, my_path_length)
        return fig, {'display': 'block'}, fig_highways, {'display': 'block'}, fig_obstacls,  {'display': 'block'}
    
    


@app.callback(
    [
        Output(component_id="section-banner-number-of-clusters", component_property = "children"),
        Output(component_id="map-div", component_property= "children"),
        Output(component_id="cites-in-every-cluster", component_property= "figure"),
        Output(component_id="cites-in-every-cluster", component_property= "style"),
        
    ],
    [
        Input(component_id="btn-updt-map", component_property= "n_clicks"),
    ],
    [
        State(component_id="features_selector_id", component_property= "value"),
        State(component_id="clustering-based-on", component_property= "value"), 
    ],
)
def run_clustering_and_update_map(btn_update, features_selector, type_clustering):
    html_comp = ""
    fig_sunburst = {}
    style = {'display' : 'none'}
    if btn_update != 0:
        style = {'display' : 'block'}
        global df_final,cities_base_final, best_model, current_k, sunchart

        cities_base_final,df_final, best_model, current_k, geo_df, fig = data_processing(features_selector, type_clustering)
        geo_df.city_name = geo_df.city_name.str.replace("Province de", "").str.replace("Préfecture de", "").str.replace("Prefecture de", "").str.replace("Province d'", "").str.replace("Préfecture d'", "").str.replace("إقليم", "").str.replace("عمالة", "")
        fig.save("countrychoosen.html")

        html_comp = html.Div([
                        html.H6("Number of Clusters"),
                        dcc.Slider(
                            min = abs(current_k - 3),
                            max = current_k + 3,
                            step = 1,
                            value = current_k,
                            id='slider-of-clusters',
                            marks={i: '{}'.format(str(i)) for i in range(abs(current_k - 3),(current_k + 4))},
                            tooltip={"placement": "bottom"}
                        ),     
                        html.Div(
                            id="map-div-cluster",
                            children = []
                        ),
                        dcc.Graph(
                            id="map-div-cluster-based_on_cites",
                        ),
                        
                    ])

        sunchart = px.sunburst(geo_df, path=['classe', 'city_name'] , values='city_population')   
        # fig_sunburst.update_layout(margin=dict(t=16,l=0,r=0,b=16)) 
        sunchart.update_layout(
            margin= dict(l=20, r=20, t=20, b=20),
            paper_bgcolor = '#161a28',
            plot_bgcolor = "#161a28",
            font = {"color": "white"},
            autosize = True 
            ) 

  
        return html_comp, html.Iframe(id= 'map_updated', srcDoc= open("countrychoosen.html", 'r').read(), width="100%", height="450"), sunchart, style
    else:
        return html_comp, base_map(), sunchart, style


@app.callback(
    [
        Output(component_id="map-div-cluster", component_property= "children"),
        Output(component_id="map-div", component_property= "style"),
        Output(component_id="map-div-cluster-based_on_cites", component_property= "figure"),
        Output(component_id="cluster_contianes", component_property= "style")
        
    ],
    [
        Input(component_id="slider-of-clusters", component_property= "value")
    ],
    prevent_initial_call= True
)
def slider_of_clusters(slider_value):
    ctx = dash.callback_context
    global sunchart
    style = {'display' : 'none'}
    if ctx.triggered:
        df, fig = train_clustring_modal(cities_base_final, df_final, best_model, slider_value)
        df.city_name = df.city_name.str.replace("Province de", "").str.replace("Préfecture de", "").str.replace("Prefecture de", "").str.replace("Province d'", "").str.replace("Préfecture d'", "").str.replace("إقليم", "").str.replace("عمالة", "")
        fig.save("countrychoosen.html")
        
        fig_sunburst = px.sunburst(df, path=['classe', 'city_name'] , values='city_population')   
        # fig_sunburst.update_layout(margin=dict(t=16,l=0,r=0,b=16)) 
        fig_sunburst.update_layout(
            margin= dict(l=20, r=20, t=20, b=20),
            paper_bgcolor = '#161a28',
            plot_bgcolor = "#161a28",
            font = {"color": "white"},
            autosize = True 
            ) 

        return html.Iframe(id= 'map_updated', srcDoc= open("countrychoosen.html", 'r').read(), width="100%", height="450"), style, fig_sunburst, {'display' : 'none'}
    else:
        return slider_value, style, sunchart, {'display' : 'block'}

# cluster_contianes








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
