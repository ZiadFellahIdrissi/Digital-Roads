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

    G_proj = ox.project_graph(G)

    my_path_length = []
    osmids = list(df_points.nearest_point_to_graph)
    for u,v in zip(osmids, osmids[1:]):
        my_path_length.extend(nx.shortest_path(G, u, v, weight = 'length')[1:])

    dl = df_points.Cordinates
    return plot_path(generate_list_of_coordinates(G,my_path_length), dl[0], dl[len(dl)-1])