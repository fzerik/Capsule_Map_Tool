import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster, LocateControl, MousePosition, Fullscreen, Draw
import json
import os
import tempfile
import uuid

class MapGenerator:
    """
    地图生成器类，用于生成热力图和点位图
    """
    
    def __init__(self):
        # 地图底图类型
        self.tile_options = {
            'gaode_normal': {
                'url': 'https://wprd01.is.autonavi.com/appmaptile?x={x}&y={y}&z={z}&lang=zh_cn&size=1&scl=1&style=7',
                'attr': '高德-常规图'
            },
            'gaode_satellite': {
                'url': 'https://webst02.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}',
                'attr': '高德-卫星影像图'
            },
            'gaode_street': {
                'url': 'https://wprd01.is.autonavi.com/appmaptile?x={x}&y={y}&z={z}&lang=zh_cn&size=1&scl=1&style=8&ltype=11',
                'attr': '高德-街道路网图'
            },
            'osm': {
                'url': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                'attr': 'OpenStreetMap'
            }
        }
        
        # 临时文件目录
        self.temp_dir = tempfile.gettempdir()
    
    def generate_heatmap(self, data, center_lat=39.90923, center_lng=116.65722, 
                         zoom_start=11, tile_type='gaode_normal', 
                         include_plugins=True, geojson_path=None):
        """
        生成热力图
        :param data: 包含lat、lng、count列的DataFrame
        :param center_lat: 中心纬度
        :param center_lng: 中心经度
        :param zoom_start: 初始缩放级别
        :param tile_type: 底图类型
        :param include_plugins: 是否包含插件
        :param geojson_path: GeoJSON文件路径（可选）
        :return: 生成的HTML文件路径
        """
        # 检查并清理数据中的NaN值
        data = data.dropna(subset=['lat', 'lng', 'count'])
        
        # 创建地图对象
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=zoom_start,
            scrollWheelZoom=True,
            control_scale=True,
            tiles=self.tile_options[tile_type]['url'],
            attr=self.tile_options[tile_type]['attr']
        )
        
        # 添加热力图
        heat_data = [[row['lat'], row['lng'], row['count']] for index, row in data.iterrows()]
        HeatMap(heat_data).add_to(m)
        
        # 添加GeoJSON图层（如果提供）
        if geojson_path and os.path.exists(geojson_path):
            try:
                with open(geojson_path, 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)
                
                # 定义边界线样式
                def style_function(feature):
                    return {
                        'fillOpacity': 0.1,
                        'color': 'blue',
                        'weight': 2
                    }
                
                # 添加GeoJSON图层
                folium.GeoJson(
                    geojson_data, 
                    name='区域边界', 
                    style_function=style_function
                ).add_to(m)
            except Exception as e:
                print(f"加载GeoJSON文件时出错: {str(e)}")
        
        # 添加插件
        if include_plugins:
            # 添加定位当前位置插件
            LocateControl().add_to(m)
            
            # 添加图层控制
            folium.LayerControl().add_to(m)
            
            # 添加绘图工具
            draw = Draw(
                draw_options={
                    'polyline': True,
                    'polygon': True,
                    'circle': True,
                    'rectangle': True,
                    'marker': True,
                    'circlemarker': False
                },
                edit_options={'edit': True}
            )
            draw.add_to(m)
            
            # 添加全屏按钮
            Fullscreen().add_to(m)
            
            # 点击任意位置出现经纬度
            m.add_child(folium.LatLngPopup())
            
            # 添加移动鼠标显示经纬度插件
            MousePosition().add_to(m)
        
        # 生成唯一文件名
        file_name = f"heatmap_{uuid.uuid4().hex}.html"
        file_path = os.path.join(self.temp_dir, file_name)
        
        # 保存地图到HTML文件
        m.save(file_path)
        
        return file_path
    
    def generate_pointmap(self, data, center_lat=39.90923, center_lng=116.65722, 
                          zoom_start=11, tile_type='gaode_normal', 
                          include_plugins=True, geojson_path=None, 
                          cluster=True, popup_field='address'):
        """
        生成点位图
        :param data: 包含lat、lng列的DataFrame，以及可选的popup_field列
        :param center_lat: 中心纬度
        :param center_lng: 中心经度
        :param zoom_start: 初始缩放级别
        :param tile_type: 底图类型
        :param include_plugins: 是否包含插件
        :param geojson_path: GeoJSON文件路径（可选）
        :param cluster: 是否启用点聚合
        :param popup_field: 弹出窗口显示的字段名
        :return: 生成的HTML文件路径
        """
        # 检查并清理数据中的NaN值
        required_fields = ['lat', 'lng']
        if popup_field and popup_field not in ['lat', 'lng']:
            required_fields.append(popup_field)
        
        data = data.dropna(subset=required_fields)
        
        # 创建地图对象
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=zoom_start,
            scrollWheelZoom=True,
            control_scale=True,
            tiles=self.tile_options[tile_type]['url'],
            attr=self.tile_options[tile_type]['attr']
        )
        
        # 创建一个MarkerCluster对象（如果启用聚合）
        if cluster:
            marker_cluster = MarkerCluster().add_to(m)
        
        # 遍历数据并添加标记
        for index, row in data.iterrows():
            # 创建标记图标
            icon = folium.Icon(color='red', icon='info-sign')
            
            # 创建弹出窗口内容
            popup_content = f"经度: {row['lng']}<br>纬度: {row['lat']}"
            if popup_field and popup_field not in ['lat', 'lng'] and popup_field in row:
                popup_content = f"{popup_field}: {row[popup_field]}<br>" + popup_content
            
            # 添加标记
            marker = folium.Marker(
                location=[row['lat'], row['lng']],
                popup=popup_content,
                icon=icon
            )
            
            # 将标记添加到地图或聚合图层
            if cluster:
                marker.add_to(marker_cluster)
            else:
                marker.add_to(m)
        
        # 添加GeoJSON图层（如果提供）
        if geojson_path and os.path.exists(geojson_path):
            try:
                with open(geojson_path, 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)
                
                # 定义边界线样式
                def style_function(feature):
                    return {
                        'fillOpacity': 0.1,
                        'color': 'blue',
                        'weight': 2
                    }
                
                # 添加GeoJSON图层
                folium.GeoJson(
                    geojson_data, 
                    name='区域边界', 
                    style_function=style_function
                ).add_to(m)
            except Exception as e:
                print(f"加载GeoJSON文件时出错: {str(e)}")
        
        # 添加插件
        if include_plugins:
            # 添加定位当前位置插件
            LocateControl().add_to(m)
            
            # 添加图层控制
            folium.LayerControl().add_to(m)
            
            # 添加绘图工具
            draw = Draw(
                draw_options={
                    'polyline': True,
                    'polygon': True,
                    'circle': True,
                    'rectangle': True,
                    'marker': True,
                    'circlemarker': False
                },
                edit_options={'edit': True}
            )
            draw.add_to(m)
            
            # 添加全屏按钮
            Fullscreen().add_to(m)
            
            # 点击任意位置出现经纬度
            m.add_child(folium.LatLngPopup())
            
            # 添加移动鼠标显示经纬度插件
            MousePosition().add_to(m)
        
        # 生成唯一文件名
        file_name = f"pointmap_{uuid.uuid4().hex}.html"
        file_path = os.path.join(self.temp_dir, file_name)
        
        # 保存地图到HTML文件
        m.save(file_path)
        
        return file_path 