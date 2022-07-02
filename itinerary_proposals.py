import numpy as np 
import pandas as pd 

import requests
import json
import bs4 as bs

import folium
import networkx as nx
import osmnx as ox

import plotly.graph_objects as go
from plotly.subplots import make_subplots


import warnings
warnings.simplefilter(action='ignore')

df_points = pd.DataFrame()
G = ""
G_proj = ""

def plot_path(cord, origin_point, destination_point):
    lat = cord[0]
    long = cord[1]
    
    # adding the lines joining the nodes
    fig = go.Figure(go.Scattermapbox(
        name = "Path",
        mode = "lines",
        lon = long,
        lat = lat,
        marker = {'size': 8},
        line = dict(width = 4.5, color = 'blue')))
    
    
    # adding source marker
    fig.add_trace(go.Scattermapbox(
        name = "Source",
        mode = "markers",
        lon = [origin_point[1]],
        lat = [origin_point[0]],
        marker = {'size': 12, 'color':"red"}))
     
    # adding destination marker
    fig.add_trace(go.Scattermapbox(
        name = "Destination",
        mode = "markers",
        lon = [destination_point[1]],
        lat = [destination_point[0]],
        marker = {'size': 11, 'color':'green'}))
    
    
    # getting center for plots:
    lat_center = np.mean(lat)
    long_center = np.mean(long)
    
    
    # defining the layout using mapbox_style
    fig.update_layout(mapbox_style="stamen-terrain",
        mapbox_center_lat = 30, mapbox_center_lon=-80)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                      mapbox = {
                          'center': {'lat': lat_center, 
                          'lon': long_center},
                          'zoom': 10})
    return fig


def node_list_to_path(G, node_list):
    edge_nodes = list(zip(node_list[:-1], node_list[1:]))
    lines = []
    for u, v in edge_nodes:
        # if there are parallel edges, select the shortest in length
        data = min(G.get_edge_data(u, v).values(), 
                   key=lambda x: x['length'])
        # if it has a geometry attribute
        if 'geometry' in data:
            # add them to the list of lines to plot
            xs, ys = data['geometry'].xy
            lines.append(list(zip(xs, ys)))
        else:
            # if it doesn't have a geometry attribute,
            # then the edge is a straight line from node to node
            x1 = G.nodes[u]['x']
            y1 = G.nodes[u]['y']
            x2 = G.nodes[v]['x']
            y2 = G.nodes[v]['y']
            line = [(x1, y1), (x2, y2)]
            lines.append(line)
    return lines


def generate_list_of_coordinates(G_,rout_):
    lines = node_list_to_path(G_, rout_)
    long = []
    lat = []
    for i in range(len(lines)):
        z = list(lines[i])
        l1 = list(list(zip(*z))[0])
        l2 = list(list(zip(*z))[1])
        for j in range(len(l1)):
            long.append(l1[j])
            lat.append(l2[j])
    return (lat,long)


def get_path_on_map(city, points_to_vist):
    global df_points, G, G_proj

    G = ox.graph_from_place(city, network_type='all')
   
    df_points = pd.DataFrame(points_to_vist, columns=["latitud", 'longitud'])
    df_points["Cordinates"] = df_points[["latitud","longitud"]].apply(tuple, axis=1)
    df_points.drop(["latitud","longitud"], axis=1, inplace=True)

    df_points['nearest_point_to_graph'] = df_points.Cordinates.apply(lambda point: ox.get_nearest_node(G, point))

    G = ox.speed.add_edge_speeds(G)
    G = ox.speed.add_edge_travel_times(G)
    G_proj = ox.project_graph(G)

    my_path_length = []
    osmids = list(df_points.nearest_point_to_graph)
    for u,v in zip(osmids, osmids[1:]):
        my_path_length.extend(nx.shortest_path(G, u, v, weight = 'length')[1:])

    dl = df_points.Cordinates
    return plot_path(generate_list_of_coordinates(G,my_path_length), dl[0], dl[len(dl)-1]), G_proj, my_path_length



def get_route_attributes(G, route):
    route_att = ox.utils_graph.get_route_edge_attributes(G, route)
    route_highways = ox.utils_graph.get_route_edge_attributes(G, route, "highway")
    route_length = ox.utils_graph.get_route_edge_attributes(G, route, "length")
    route_travel_time = ox.utils_graph.get_route_edge_attributes(G, route, "travel_time")
    edges = pd.DataFrame({'highways': route_highways, 'length': route_length, "travel_time": route_travel_time})
    return (edges, pd.json_normalize(route_att))


def route_att(route, attr, place_clean):
    
    in_path = []
    for i in route:
        if i in list(place_clean.osmid):
            in_path.append(i)
    
    route_length_att = place_clean[place_clean.osmid.isin(in_path)]
    
    traffic_signals = route_length_att[route_length_att.highway== "traffic_signals"]
    traffic_calmin  = route_length_att["traffic_calming"].notnull()
    
    k = attr[attr["junction"].notnull()][["osmid","junction"]]
    k['osmid'] = k['osmid'].astype('str') 
    roundabout = len(k.groupby("osmid")[["junction"]].count().reset_index())
    
    try:
        bridges = len(attr[attr.bridge == "yes"])
    finally:
        bridges = 1
#     tunnel =  len(attr_for_length_route[attr_for_length_route.tunnel == "yes"])
    
    stop = len(route_length_att[route_length_att.highway== "stop"])
    if stop < 1:
        stop = 1
    
    mini_roundabout = len(route_length_att[route_length_att.highway== "mini_roundabout"])
    if mini_roundabout < 1:
        mini_roundabout = 1
    
    oneway = len(attr[attr.oneway == True])
    morethanway = len(attr[attr.oneway == False])
    
    onewaydf = pd.DataFrame({"oneway": ["one way" , "more than one way"], "countway": [oneway, morethanway]})
    
    return (traffic_calmin, traffic_signals, roundabout, mini_roundabout, bridges,  stop, onewaydf)



def generate_KPIs(G_proj, my_path_length):

    edges_for_length_route, attr_for_length_route  = get_route_attributes(G_proj, my_path_length)
    edges_for_length_route['highways'] = edges_for_length_route['highways'].astype('str') 
    grouped_by_length_route_length = edges_for_length_route.groupby("highways")[["length"]].sum().round().reset_index()
    grouped_by_length_route_travel_time = edges_for_length_route.groupby("highways")[["travel_time"]].sum().round().reset_index()

    total_length = round(grouped_by_length_route_length.length.sum()/1000,1)
    total_time = round(grouped_by_length_route_travel_time.travel_time.sum()/3600)



    labels = grouped_by_length_route_length.highways
    values = grouped_by_length_route_length.length

    fig_highways = go.Figure(data=[go.Pie(labels=labels, values=values, )])

    fig_highways.update_layout(title_text='Distance of '+str(total_length)+' Km And ' + str(total_time) + ' hours trip')
    fig_highways.update_layout(
                            autosize=False,
                            width=450,
                            height=400,
                            paper_bgcolor = '#161a28',
                            plot_bgcolor = "#161a28",
                            font = {"color": "white"},
    )

    warnings.simplefilter(action='ignore')
    tags = {'traffic_calming': True , "highway": ["traffic_signals", "stop", "mini_roundabout"]}
    casablanca_place = ox.geometries_from_point(center_point=(33.560311, -7.611884), tags=tags, dist=30000)


    casablanca_place.reset_index()[['osmid','geometry','traffic_calming', 'highway']]


    l_not_exist = []
    for i in casablanca_place.reset_index().osmid:
        if i in G_proj:
            l_not_exist.append(i)
            
    place_clean = casablanca_place.reset_index()
    place_clean = place_clean[(place_clean.osmid.isin(l_not_exist))].reset_index()

    traffic_calmin_length, traffic_signals_length, roundabout_length, mini_roundabout, bridges, stop, oneway = route_att(my_path_length, attr_for_length_route, place_clean)


    routes=['itinerary']

    fig_obstacls = go.Figure(data=[
        go.Bar(name='Traffic Calming', x=routes, y=[len(traffic_calmin_length)], text="Traffic Calming "+str(len(traffic_calmin_length)), textposition='auto', marker_color='lightskyblue'),
        go.Bar(name='Traffic Signals', x=routes, y=[len(traffic_signals_length)], text="Traffic Signals "+str(len(traffic_signals_length)), textposition='auto', marker_color='lightslategray'),
        go.Bar(name='Roundabout', x=routes, y=[roundabout_length],  text="Roundabout "+str(roundabout_length), textposition='auto', marker_color='lightsteelblue'),
        go.Bar(name='mini_roundabout', x=routes, y=[mini_roundabout],  text="mini_roundabout "+str(mini_roundabout), textposition='auto', marker_color='teal'),
        go.Bar(name='Bridges', x=routes, y=[bridges], text="Bridges "+str(bridges), textposition='auto', marker_color='linen'),
    #     go.Bar(name='Tunnels', x=routes, y=[tunnels],  text="tunnels "+str(tunnels), textposition='auto', marker_color='limegreen'),
        go.Bar(name='Stops', x=routes, y=[stop],  text="Stops "+str(stop), textposition='auto', marker_color='limegreen')

    ])
    # Change the bar mode 
    fig_obstacls.update_layout(barmode='group')
    fig_obstacls.update_layout(title_text='Number of obstacles')
    fig_obstacls.update_layout(
                            autosize=False,
                            width=450,
                            height=400,
                            paper_bgcolor = '#161a28',
                            plot_bgcolor = "#161a28",
                            font = {"color": "white"},
    )


    return fig_highways, fig_obstacls

