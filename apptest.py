#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import numpy as np
from geopy import distance
from geopy import Point
import random
import plotly.express as px
import pandas as pd
from dash import Dash, html, dcc, callback, Output, Input




app = Dash(__name__)
            
df = pd.read_csv("waterrightstest2.csv")

df.dropna(
    axis=0,
    how='any',
    subset=None,
    inplace=True
)

df_diffq = (df["Water Quantity"].max() - df["Water Quantity"].min()) / 16

df["scale"] = (df["Water Quantity"] - df["Water Quantity"].min()) / df_diffq + 1

df["size"] = np.where(df['Water Quantity'] > 0, 1, 0.1)
#color_scale = [(0, 'orange'), (1,'red'), (2,'green')]

qmax = 0
for i in range(len(df)):
    qmax = qmax + df.loc[i, 'Water Quantity']
    
    
app.layout = html.Div([
    html.H1(children='Washington Water Banking Data', style={'textAlign':'center'}),
    html.Div(className='row', children=[
        dcc.RadioItems(options=[
                            {'label': 'Set Desired Distance', 'value': 'Distance'},
                            {'label': 'Highlight Nearest Point', 'value': 'Nearest'},
                            {'label': 'Set Desired Water Quantity', 'value': 'Quantity'}
                        ],
                       value='Distance',
                       inline=True,
                       id='radios')
    ]),
    dcc.Input(
        placeholder='Latitude',
        type='number',
        value=48,
        id = 'latit',
    ),
    dcc.Input(
        placeholder='Longitude',
        type='number',
        value=-120,
        id = 'long',
    ),
    dcc.Input(
        placeholder='Distance/Quantity',
        type='number',
        value=0,
        id = 'distq',
        min = 0,
        max = qmax
    ),
#     dcc.Graph(
#         figure = fig,
#         id = 'fig1test',
#     ),
    html.Div(id='test123'),
])


# @callback(
#     [Output('test123','children')],
#     [Input('latit','value')]
# ) 
# def testfunc(val):
#     return str(val)
@app.callback(
    Output('test123', 'children'),
    [Input('latit', 'value'),
    Input('long', 'value'),
    Input('distq', 'value'),
    Input('radios','value')]
)
def update_graph(lat_value,long_value,distquant_value,radio_value):
    dff = locupdate(lat_value,long_value,df)
    if radio_value == 'Distance':
        dff = ColorUpdate1(lat_value,long_value,distquant_value,dff)
    elif radio_value == 'Nearest':
        dff = ColorUpdate2(lat_value,long_value,dff)
    elif radio_value == 'Quantity':
        dff = ColorUpdate3(lat_value,long_value,distquant_value,dff)
    fig = px.scatter_mapbox(dff, 
                        lat="Latitude", 
                        lon="Longitude", 
                        hover_name="WR Doc ID", 
                        hover_data={'size':False,
                                   'Latitude':False,
                                   'Longitude':False,
                                   'WR Doc ID':False,
                                   'Water Quantity':True},
                        color="Color",
                        color_discrete_map = 'identity',
                        size="size",
                        size_max=14,
                        zoom=6,
                        center={'lat': lat_value,'lon': long_value},
                        height=800,
                        width=800)
    fig.update_layout(transition_duration = 100)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(showlegend=True)
    graph = dcc.Graph(
        figure = fig,
        id = 'fig2test'
    )
    return graph

def locupdate(coordlat,coordlong,df):
    df.loc[df['WR Doc ID'] == "User defined", "Latitude"] = coordlat
    df.loc[df['WR Doc ID'] == "User defined", "Longitude"] = coordlong
    return df

def ColorUpdate1(coordlat,coordlong,dist,df):
    df["Color"] = "red"
    coords = (coordlat,coordlong)
    df['point'] = df.apply(lambda row: Point(latitude=row['Latitude'], longitude=row['Longitude']), axis=1)
    df['distance'] = df.apply(lambda row: distance.distance(row['point'],coords).miles, axis=1)
    df.loc[df['distance'] < dist, "Color"] = "blue"
    df.loc[df["WR Doc ID"] == "User defined", "Color"] = "green"
    df = df.drop('point', axis=1)
    df = df.drop('distance', axis=1)
    return df


def ColorUpdate2(coordlat,coordlong,df):
    df["Color"] = "red"
    coords = (coordlat,coordlong)
    df['point'] = df.apply(lambda row: Point(latitude=row['Latitude'], longitude=row['Longitude']), axis=1)
    df['distance'] = df.apply(lambda row: distance.distance(row['point'],coords).miles, axis=1)
    df.loc[df['distance'] <= 0, 'distance'] = 1000000
    df.loc[df['distance'] == df['distance'].min(), "Color"] = "blue"
    df.loc[df["WR Doc ID"] == "User defined", "Color"] = "green"
    df = df.drop('point', axis=1)
    df = df.drop('distance', axis=1)
    return df

def ColorUpdate3(coordlat,coordlong,quant,df):
    df["Color"] = "red"
    coords = (coordlat,coordlong)
    df['point'] = df.apply(lambda row: Point(latitude=row['Latitude'], longitude=row['Longitude']), axis=1)
    df['distance'] = df.apply(lambda row: distance.distance(row['point'],coords).miles, axis=1)
    df.loc[df['distance'] <= 0, 'distance'] = 1000000
    df.loc[df["WR Doc ID"] == "User defined", "Water Quantity"] = 0
    df.sort_values(by = ['distance'], inplace = True, ignore_index = True)
    df['sum_quant'] = 0
    qf = 0
    quant2 = 0
    for i in range(len(df)):
        if i == 0:
            df.loc[i,'sum_quant'] = df.loc[i,'Water Quantity']
            if qf == 0:
                if quant <= df.loc[i,'Water Quantity']:
                    quant2 = df.loc[i,'Water Quantity']
                    qf = 1
        else:
            df.loc[i,'sum_quant'] = df.loc[i-1,'sum_quant'] + df.loc[i,'Water Quantity']
            if qf == 0:
                if quant <= df.loc[i,'sum_quant']:
                    quant2 = df.loc[i,'sum_quant']
                    qf = 1
    
    if quant2 == 0:
        quant2 = df['sum_quant'].max()
    df.loc[(df['sum_quant'] <= quant2) & (df['Water Quantity'] > 0), "Color"] = "blue"
    df.loc[df["WR Doc ID"] == "User defined", "Color"] = "green"
    df = df.drop('point', axis=1)
    df = df.drop('distance', axis=1)
    df = df.drop('sum_quant', axis=1)
    return df
if __name__ == '__main__':
    app.run_server(debug=True,use_reloader=False)

