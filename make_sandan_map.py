import geopandas as gpd
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Polygon, LineString, Point
import shapely
import matplotlib
from tqdm import tqdm
import numpy as np
from scipy.spatial import distance
from typing import List
import os
from xlwings import view

import folium
import io
from PIL import Image

from selenium import webdriver 
from folium.utilities import temp_html_filepath
import time


import matplotlib.font_manager as fm
fm.get_fontconfig_fonts()
# plt.rc('font', family='NanumGothic') # For Windows

def convert_points_to_coordinates(points:gpd.geoseries.GeoSeries)->np.ndarray:
    ''' 거리 계산을 위해 점 데이터를 좌표 데이터로 변환 '''
    coordinates = [(point.x, point.y) for point in points]
    return np.array(coordinates)

def get_nearby_sandan_indexes(ref_point:np.ndarray, sandan_centroids:np.ndarray, numbers:int)->List[int]:
    ''' 특정 지점 인근의 산단 중앙점을 반환'''
    distances = distance.cdist(ref_point, sandan_centroids)
    indexes_ascending_ordered = distances.argsort()[0]
    return indexes_ascending_ordered[:numbers]

def find_intercepted_area(target_area:shapely.geometry.polygon.Polygon, areas:gpd.GeoSeries)->List[shapely.geometry.polygon.Polygon]:
    ''' shape_info와 겹치는 영역에 대한 List 반환 '''

    return [area for area in areas if area.intersects(target_area)]



def save_png(m:folium.Map, delay=3):
    ''' png로 저장'''

    if m._png_image is None:

        # options = webdriver.firefox.options.Options()
        options = webdriver.ChromeOptions()
        options.add_argument('headless')

        chromedriver = 'chromedriver.exe'
        driver = webdriver.Chrome(chromedriver, options=options)

        html = m.get_root().render()
        with temp_html_filepath(html) as fname:
            # We need the tempfile to avoid JS security issues.
            driver.get('file:///{path}'.format(path=fname))
            driver.maximize_window()
            time.sleep(delay)
            png = driver.get_screenshot_as_png()
            driver.quit()
        m._png_image = png
    return m._png_image



def plot_sido_sigungu_sandan(sido_sigungu_sandan:List[shapely.geometry.multipolygon.MultiPolygon])->None:

    # sido_sigungu_sandan = plot_list['용인시기흥구']

    # 시도
    geo = gpd.GeoDataFrame(['name'], geometry = sido_sigungu_sandan[0])
    sido_tar = gpd.GeoDataFrame(geometry = sido_sigungu_sandan[0])
    ax= sido_tar.plot(facecolor = 'none', edgecolor='red', alpha=0.8)

    sigungu_tar = gpd.GeoDataFrame(geometry = [sido_sigungu_sandan[1]])
    sigungu_tar.plot(ax=ax, facecolor = 'none', edgecolor='blue', alpha=0.8)

    sandan_tar = gpd.GeoDataFrame(geometry = sido_sigungu_sandan[2])
    sandan_tar.plot(ax=ax, alpha=0.4)
    plt.show()


if __name__ =='__main__':


    os.chdir(r'D:\python_dev\nc_read\220612 시군구경계')
    font_location = 'C:/Windows/Fonts/NanumGothic.ttf' # For Windows
    font_name = fm.FontProperties(fname=font_location).get_name()
    matplotlib.rc('font', family=font_name)

    # 산업단지 경계
    # http://data.nsdi.go.kr/dataset/12896
    # 22년 3월 31일 기준

    data_path = Path(r'D:\python_dev\industrial\Z_ILIS_DAM_DAN_220331')
    filename = 'dam_dan.shp'
    indus = gpd.read_file(data_path/filename)
    # indus = indus.to_crs({'init':'epsg:5181'})
    indus = indus.to_crs({'init':'epsg:4326'})

    m = folium.Map(location=[37, 127], zoom_start=10)
    

    # df = pd.DataFrame(data={'name':['name'], 'geometry':[plot_list['부천시'][1]]})

    style_functions = {
        0 : {'fillcolor':'orange'},
        1 : {'fillcolor':'blue'},
        2 : {'fillcolor':'green'},
        3 : {'fillcolor':'purple'},
        4 : {'fillcolor':'grey'},
        5 : {'fillcolor':'pink'},
    }

    indus['유형'] = indus['danji_type'].replace(
        {'1':'국가', '2':'일반', '3':'도시', '4':'농공'}
    )

    indus['설명'] = indus['유형'] + '_' + indus['dan_name'] + '_ID:' + indus['dan_id']
    df = indus
    # indus.to_excel('indus.xlsx')
    for index, r in df.iterrows():
        
        # 필요한 경우 경계를 단순화할 수 있음
        # sim_geo = gpd.GeoSeries(r['geometry']).simplify(tolerance=0.001)
        sim_geo = gpd.GeoSeries(r['geometry'])
        geo_j = sim_geo.to_json()
        geo_j = folium.GeoJson(data=geo_j, style_function=lambda x: style_functions[index%len(style_functions)])
        folium.Popup(r['설명']).add_to(geo_j)
        geo_j.add_to(m)

    m.save('산단지도_국가공간정보포털_220331.html')

    # 그림 파일로 저장할 때
    # img_data = save_png(m, delay=10)
    # img = Image.open(io.BytesIO(img_data))
    # img.save('image.png')

