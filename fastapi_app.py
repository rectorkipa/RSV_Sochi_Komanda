import uvicorn
from fastapi import FastAPI
from typing import Optional
import pandas as pd
import numpy as np
import json
from data_request_model import *
import ssl
ssl.create_default_https_context = ssl._create_unverified_context

app = FastAPI()


# ФУНКЦИИ ДЛЯ ПОЛУЧЕНИЯ КООРДИНАТ ТРЕХ ВИДОВ ОБЪЕКТОВ:

def get_lat_lon(geometry):
    lon = geometry.apply(lambda x: x.x if x.type == 'Point' else x.centroid.x)
    lat = geometry.apply(lambda x: x.y if x.type == 'Point' else x.centroid.y)
    return lat, lon

def osm_query(tag, city):
    gdf = ox.features_from_place(city, tag).reset_index()
    gdf['city'] = np.full(len(gdf), city.split(',')[0])
    gdf['object'] = np.full(len(gdf), list(tag.keys())[0])
    gdf['type'] = np.full(len(gdf), tag[list(tag.keys())[0]])
    gdf = gdf[['city', 'object', 'type', 'geometry']]
    #print(gdf.shape)
    return gdf

# Вводим город в формате 'Екатеринбург, Россия'
# Выгрузим интересующие нас категории объектов
# {'sport':'football'}, {'shop':'farm'}
def all_objs(your_city):
    tags_education = [{'amenity': 'school'}, {'amenity': 'university'}, {'amenity': 'college'}]
    tags_positive = [{'leisure': 'swimming_pool'}, {'sport': 'fitness'}, {'leisure': 'ice_rink'},
                     {'building': 'stadium'}, {'leisure': 'park'}, {'leisure': 'playground'}]
    tags_negative = [{'amenity': 'fast_food'}, {'shop': 'tobacco'}, {'shop': 'alcohol'}, {'amenity': 'bar'}]
    cities = [your_city]

    gdfs_ed = []
    for city in cities:
        for tag in tags_education:
            gdfs_ed.append(osm_query(tag, city))

    data_education = pd.concat(gdfs_ed)
    data_education.groupby(['city', 'object', 'type'], as_index=False).agg({'geometry': 'count'})
    lat, lon = get_lat_lon(data_education['geometry'])
    data_education['lat'] = lat
    data_education['lon'] = lon

    gdfs_pos = []
    for city in cities:
        for tag in tags_positive:
            gdfs_pos.append(osm_query(tag, city))

    data_positive = pd.concat(gdfs_pos)
    data_positive.groupby(['city', 'object', 'type'], as_index=False).agg({'geometry': 'count'})
    lat, lon = get_lat_lon(data_positive['geometry'])
    data_positive['lat'] = lat
    data_positive['lon'] = lon

    gdfs_neg = []
    for city in cities:
        for tag in tags_negative:
            gdfs_neg.append(osm_query(tag, city))

    data_negative = pd.concat(gdfs_neg)
    data_negative.groupby(['city', 'object', 'type'], as_index=False).agg({'geometry': 'count'})
    lat, lon = get_lat_lon(data_negative['geometry'])
    data_negative['lat'] = lat
    data_negative['lon'] = lon

    data_education = data_education[['lat', 'lon']]
    data_positive = data_positive[['lat', 'lon']]
    data_negative = data_negative[['lat', 'lon']]

    return data_education, data_positive, data_negative

# первый пункт для районов: сумма положительных точек в муниципалитете (районе города) превышает отрицательные на 50%
def first_sum(data_positive, data_negative):
    pos_sum = len(data_positive)
    neg_sum = len(data_negative)
    coef = (pos_sum - neg_sum) / neg_sum * 100
    return coef


@app.post('/get_data')
async def get_dfs(parameters: DataRequest):
    return all_objs(parameters.input_city)#[0]
