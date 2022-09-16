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


if __name__ =='__main__':


    font_location = 'C:/Windows/Fonts/NanumGothic.ttf' # For Windows
    font_name = fm.FontProperties(fname=font_location).get_name()
    matplotlib.rc('font', family=font_name)

    # 산업단지 경계
    # http://data.nsdi.go.kr/dataset/12896
    # 산단경계의 좌표계는 EPSG:3857임 (QGIS 확인)
    # 홈페이지에는 데이터 좌표계가 GRS80중부로 기재되어 있음

    data_path = Path(r'D:\python_dev\nc_read\industrial_complex_nsdi')
    filename = 'dam_dan.shp'
    indus = gpd.read_file(data_path/filename)
    indus = indus.to_crs({'init':'epsg:5181'})

    centroids = indus['geometry'].centroid

    # test 사업장
    data_path = Path(r'D:\python_dev\nc_read\220316 산단check')
    filename = '2020년 산업부문 조사 산단확인 샘플.xlsx'
    workplaces = pd.read_excel(data_path/filename)
    workplaces['경도'] = workplaces['경도'].astype(float)
    workplaces['위도'] = workplaces['위도'].astype(float)
    workplaces['geometry'] = workplaces.apply(lambda row : Point([row['경도'], row['위도']]), axis=1)
    workplaces = gpd.GeoDataFrame(workplaces, geometry='geometry')

    # 위경도 데이터 좌표계 지정 : epsg4326
    from fiona.crs import from_string
    epsg4326 = from_string("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")

    # 위경도 데이터의 좌표계를 산단 경계 좌표계로 변경
    workplaces.crs = epsg4326
    # epsg5179 = from_string("+proj=tmerc +lat_0=38 +lon_0=127.5 +k=0.9996 +x_0=1000000 +y_0=2000000 +ellps=GRS80 +units=m +no_defs")
    epsg5181 = from_string("+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=500000 +ellps=GRS80 +units=m +no_defs")
    workplaces = workplaces.to_crs(epsg5181)

    sandan_centroids = convert_points_to_coordinates(centroids)

    result_cols = ['dan_id', 'dan_name', 'danji_type']
    result_dict = {col:[] for col in result_cols}

    for workplace_location in tqdm(workplaces['geometry']):
        # workplace_location = workplaces['geometry'][0]
        ref_point = convert_points_to_coordinates([workplace_location])
        ids = get_nearby_sandan_indexes(ref_point, sandan_centroids, 5)
        is_nearby_sandan = indus.index.isin(ids)
        nearby_sandans = indus.loc[is_nearby_sandan, :]

        # 경계 내 사업장이 존재할 경우 is_found, sandan_number를 변경
        found = False
        sandan_number = -1

        for j, sandan_boundary in enumerate(nearby_sandans['geometry']):
            if sandan_boundary.contains(workplace_location):
                found = True
                sandan_number = j
                break
        
        if found:
            result_dict['dan_id'].append(nearby_sandans.iloc[j]['dan_id'])
            result_dict['dan_name'].append(nearby_sandans.iloc[j]['dan_name'])
            result_dict['danji_type'].append(nearby_sandans.iloc[j]['danji_type'])
        else:
            result_dict['dan_id'].append(np.nan)
            result_dict['dan_name'].append(np.nan)
            result_dict['danji_type'].append(np.nan)


    pd.concat([workplaces, pd.DataFrame(result_dict)], axis=1).to_excel('result.xlsx')


