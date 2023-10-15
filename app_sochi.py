import streamlit as st
from PIL import Image
import requests
import json
import ssl
ssl.create_default_https_context = ssl._create_unverified_context

import pandas as pd
import numpy as np
import osmnx as ox

# команда для запуска сервиса в терминале:
# streamlit run app_sochi.py

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

def first_sum(data_positive, data_negative):
    pos_sum = len(data_positive)
    neg_sum = len(data_negative)
    coef = (pos_sum - neg_sum) / neg_sum * 100
    return round(coef, 0)


# оформление вкладки браузера:

st.set_page_config(page_title="Sochi Komanda", page_icon=':snake:')


# логотипы:

img_hack = Image.open("logo_hack.jpg")
st.sidebar.image(img_hack, width=300)
img_logo = Image.open("logo_case.jpg")
st.sidebar.image(img_logo, width=300)


# левый блок:

st.sidebar.title("""
Сервис предлагает пользователю ввести название города и получить:
1) визуализацию и анализ данных
2) коэффициенты и параметры
3) рекомендации по улучшению качества среды
""")
st.sidebar.write("""
ЮФО, Сочи\n
'Команда'
""")
st.sidebar.caption("""
Андрей Ягелло\n
Маргарита Баталова\n
Николай Кривоногов
""")


# центральный заголовок:

st.markdown(
    "<h2 style='text-align: center;'>Web-приложение для оценки городской инфраструктуры, влияющей на здоровье населения</h1>",
    unsafe_allow_html=True
)


# запрос города:

input_city = st.text_input(
    "Введите название города и страну для анализа и нажмите 'Сгенерировать карту': (пример: Екатеринбург, Россия)",
    value="Екатеринбург, Россия"
)

# карта, легенда, статистика:

if st.button('Сгенерировать карту'):

    st.subheader("Карта")

    data_education, data_positive, data_negative = all_objs(str(input_city))

    st.map(data_education,
           latitude='lat',
           longitude='lon',
           color='#0000FF')
    st.success('Синие точки - учебные заведения.')
    st.map(data_positive,
           latitude='lat',
           longitude='lon',
           color='#00FF00')
    st.success('Зеленые точки - "положительные" объекты.')
    st.map(data_negative,
           latitude='lat',
           longitude='lon',
           color='#FF0000')
    st.success('Красные точки - "отрицательные" объекты.')

    st.markdown(
        "<h3 style='text-align: center;'>Статистика:</h1>",
        unsafe_allow_html=True
    )

    st.success(f'Соотношение "положительные"/"отрицательные" объекты: {first_sum(data_positive, data_negative)} %.')

else:
    pass
