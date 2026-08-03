#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
区域热力图生成器
支持世界国家、中国省市、区县热力图以及空气质量图的生成
"""

import os
import uuid
import tempfile
import pandas as pd
import numpy as np
from pyecharts import options as opts
from pyecharts.charts import Map, Geo
from pyecharts.globals import ChartType
import logging

# 日志级别由应用入口统一配置，避免模块导入时强制开启 DEBUG。
logger = logging.getLogger(__name__)

class RegionMapGenerator:
    """区域热力图生成器类"""
    
    def __init__(self):
        """初始化区域热力图生成器"""
        self.temp_dir = tempfile.gettempdir()
        # 创建临时地图文件目录
        os.makedirs(os.path.join(self.temp_dir, 'region_maps'), exist_ok=True)
        
        # 支持的地图类型
        self.map_types = {
            'world': '世界地图',
            'china': '中国地图',
            'province': '省级地图',
            'city': '市级地图',
            'air_quality': '空气质量热力图'
        }
        
        # 支持的导出格式
        self.export_formats = ['html']
    
    def generate_world_map(self, data, title="世界地图", subtitle="", width="900px", height="600px", 
                          background_color="#fff", min_value=None, max_value=None, 
                          color_range=None, is_visualmap_piecewise=False, pieces=None):
        """
        生成世界地图
        
        参数:
            data (list/DataFrame): 数据，格式为 [["国家名", 值], ...] 或包含 country 和 value 列的 DataFrame
            title (str): 地图标题
            subtitle (str): 地图副标题
            width (str): 地图宽度，如 '900px'
            height (str): 地图高度，如 '600px'
            background_color (str): 背景颜色，如 '#fff'
            min_value (float): 最小值，用于视觉映射
            max_value (float): 最大值，用于视觉映射
            color_range (list): 颜色范围，如 ['#50a3ba', '#eac763', '#d94e5d']
            is_visualmap_piecewise (bool): 是否使用分段视觉映射
            pieces (list): 分段设置，如 [{"min": 1000, "max": 10000, "color": "#FF0000"}, ...]
            
        返回:
            str: 生成的地图文件路径
        """
        logger.debug("生成世界地图")
        
        # 处理数据
        if isinstance(data, pd.DataFrame):
            if 'country' in data.columns and 'value' in data.columns:
                map_data = [[row['country'], row['value']] for _, row in data.iterrows()]
            else:
                raise ValueError("DataFrame必须包含'country'和'value'列")
        else:
            map_data = data
        
        # 创建地图实例
        map_chart = Map(init_opts=opts.InitOpts(
            width=width, 
            height=height,
            bg_color=background_color
        ))
        
        # 添加数据到地图
        map_chart.add(
            series_name="",
            data_pair=map_data,
            maptype="world",
            is_map_symbol_show=False,
        )
        
        # 设置全局配置
        visualmap_opts = None
        if is_visualmap_piecewise and pieces:
            visualmap_opts = opts.VisualMapOpts(
                is_piecewise=True,
                pieces=pieces
            )
        else:
            visualmap_opts = opts.VisualMapOpts(
                min_=min_value if min_value is not None else min([item[1] for item in map_data]),
                max_=max_value if max_value is not None else max([item[1] for item in map_data]),
                range_color=color_range if color_range else ["#50a3ba", "#eac763", "#d94e5d"]
            )
        
        map_chart.set_global_opts(
            title_opts=opts.TitleOpts(
                title=title,
                subtitle=subtitle,
                pos_left="center"
            ),
            visualmap_opts=visualmap_opts,
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(
                trigger="item",
                formatter="{b}: {c}"
            )
        )
        
        # 生成临时文件路径
        file_name = f"world_map_{uuid.uuid4().hex}.html"
        file_path = os.path.join(self.temp_dir, 'region_maps', file_name)
        
        # 渲染地图
        map_chart.render(file_path)
        
        return file_path
    
    def generate_china_map(self, data, title="中国地图", subtitle="", width="900px", height="600px", 
                          background_color="#fff", min_value=None, max_value=None, 
                          color_range=None, is_visualmap_piecewise=False, pieces=None):
        """
        生成中国地图
        
        参数:
            data (list/DataFrame): 数据，格式为 [["省份名", 值], ...] 或包含 province 和 value 列的 DataFrame
            title (str): 地图标题
            subtitle (str): 地图副标题
            width (str): 地图宽度，如 '900px'
            height (str): 地图高度，如 '600px'
            background_color (str): 背景颜色，如 '#fff'
            min_value (float): 最小值，用于视觉映射
            max_value (float): 最大值，用于视觉映射
            color_range (list): 颜色范围，如 ['#50a3ba', '#eac763', '#d94e5d']
            is_visualmap_piecewise (bool): 是否使用分段视觉映射
            pieces (list): 分段设置，如 [{"min": 1000, "max": 10000, "color": "#FF0000"}, ...]
            
        返回:
            str: 生成的地图文件路径
        """
        logger.debug("生成中国地图")
        
        # 处理数据
        if isinstance(data, pd.DataFrame):
            if 'province' in data.columns and 'value' in data.columns:
                map_data = [[row['province'], row['value']] for _, row in data.iterrows()]
            else:
                raise ValueError("DataFrame必须包含'province'和'value'列")
        else:
            map_data = data
        
        # 创建地图实例
        map_chart = Map(init_opts=opts.InitOpts(
            width=width, 
            height=height,
            bg_color=background_color
        ))
        
        # 添加数据到地图
        map_chart.add(
            series_name="",
            data_pair=map_data,
            maptype="china",
            is_map_symbol_show=False,
        )
        
        # 设置全局配置
        visualmap_opts = None
        if is_visualmap_piecewise and pieces:
            visualmap_opts = opts.VisualMapOpts(
                is_piecewise=True,
                pieces=pieces
            )
        else:
            visualmap_opts = opts.VisualMapOpts(
                min_=min_value if min_value is not None else min([item[1] for item in map_data]),
                max_=max_value if max_value is not None else max([item[1] for item in map_data]),
                range_color=color_range if color_range else ["#50a3ba", "#eac763", "#d94e5d"]
            )
        
        map_chart.set_global_opts(
            title_opts=opts.TitleOpts(
                title=title,
                subtitle=subtitle,
                pos_left="center"
            ),
            visualmap_opts=visualmap_opts,
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(
                trigger="item",
                formatter="{b}: {c}"
            )
        )
        
        # 生成临时文件路径
        file_name = f"china_map_{uuid.uuid4().hex}.html"
        file_path = os.path.join(self.temp_dir, 'region_maps', file_name)
        
        # 渲染地图
        map_chart.render(file_path)
        
        return file_path
    
    def generate_province_map(self, data, province, title=None, subtitle="", width="900px", height="600px", 
                             background_color="#fff", min_value=None, max_value=None, 
                             color_range=None, is_visualmap_piecewise=False, pieces=None):
        """
        生成省级地图
        
        参数:
            data (list/DataFrame): 数据，格式为 [["城市名", 值], ...] 或包含 city 和 value 列的 DataFrame
            province (str): 省份名称，如 '贵州'
            title (str): 地图标题，默认为 '{province}地图'
            subtitle (str): 地图副标题
            width (str): 地图宽度，如 '900px'
            height (str): 地图高度，如 '600px'
            background_color (str): 背景颜色，如 '#fff'
            min_value (float): 最小值，用于视觉映射
            max_value (float): 最大值，用于视觉映射
            color_range (list): 颜色范围，如 ['#50a3ba', '#eac763', '#d94e5d']
            is_visualmap_piecewise (bool): 是否使用分段视觉映射
            pieces (list): 分段设置，如 [{"min": 1000, "max": 10000, "color": "#FF0000"}, ...]
            
        返回:
            str: 生成的地图文件路径
        """
        logger.debug(f"生成{province}省级地图")
        
        if title is None:
            title = f"{province}地图"
        
        # 处理数据
        if isinstance(data, pd.DataFrame):
            if 'city' in data.columns and 'value' in data.columns:
                map_data = [[row['city'], row['value']] for _, row in data.iterrows()]
            else:
                raise ValueError("DataFrame必须包含'city'和'value'列")
        else:
            map_data = data
        
        # 创建地图实例
        map_chart = Map(init_opts=opts.InitOpts(
            width=width, 
            height=height,
            bg_color=background_color
        ))
        
        # 添加数据到地图
        map_chart.add(
            series_name="",
            data_pair=map_data,
            maptype=province,
            is_map_symbol_show=False,
        )
        
        # 设置全局配置
        visualmap_opts = None
        if is_visualmap_piecewise and pieces:
            visualmap_opts = opts.VisualMapOpts(
                is_piecewise=True,
                pieces=pieces
            )
        else:
            visualmap_opts = opts.VisualMapOpts(
                min_=min_value if min_value is not None else min([item[1] for item in map_data]),
                max_=max_value if max_value is not None else max([item[1] for item in map_data]),
                range_color=color_range if color_range else ["#50a3ba", "#eac763", "#d94e5d"]
            )
        
        map_chart.set_global_opts(
            title_opts=opts.TitleOpts(
                title=title,
                subtitle=subtitle,
                pos_left="center"
            ),
            visualmap_opts=visualmap_opts,
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(
                trigger="item",
                formatter="{b}: {c}"
            )
        )
        
        # 生成临时文件路径
        file_name = f"{province}_map_{uuid.uuid4().hex}.html"
        file_path = os.path.join(self.temp_dir, 'region_maps', file_name)
        
        # 渲染地图
        map_chart.render(file_path)
        
        return file_path
    
    def generate_city_map(self, data, city, title=None, subtitle="", width="900px", height="600px", 
                         background_color="#fff", min_value=None, max_value=None, 
                         color_range=None, is_visualmap_piecewise=False, pieces=None):
        """
        生成市级地图
        
        参数:
            data (list/DataFrame): 数据，格式为 [["区县名", 值], ...] 或包含 district 和 value 列的 DataFrame
            city (str): 城市名称，如 '贵阳'
            title (str): 地图标题，默认为 '{city}地图'
            subtitle (str): 地图副标题
            width (str): 地图宽度，如 '900px'
            height (str): 地图高度，如 '600px'
            background_color (str): 背景颜色，如 '#fff'
            min_value (float): 最小值，用于视觉映射
            max_value (float): 最大值，用于视觉映射
            color_range (list): 颜色范围，如 ['#50a3ba', '#eac763', '#d94e5d']
            is_visualmap_piecewise (bool): 是否使用分段视觉映射
            pieces (list): 分段设置，如 [{"min": 1000, "max": 10000, "color": "#FF0000"}, ...]
            
        返回:
            str: 生成的地图文件路径
        """
        logger.debug(f"生成{city}市级地图")
        
        if title is None:
            title = f"{city}地图"
        
        # 处理数据
        if isinstance(data, pd.DataFrame):
            if 'district' in data.columns and 'value' in data.columns:
                map_data = [[row['district'], row['value']] for _, row in data.iterrows()]
            else:
                raise ValueError("DataFrame必须包含'district'和'value'列")
        else:
            map_data = data
        
        # 创建地图实例
        map_chart = Map(init_opts=opts.InitOpts(
            width=width, 
            height=height,
            bg_color=background_color
        ))
        
        # 添加数据到地图
        map_chart.add(
            series_name="",
            data_pair=map_data,
            maptype=city,
            is_map_symbol_show=False,
        )
        
        # 设置全局配置
        visualmap_opts = None
        if is_visualmap_piecewise and pieces:
            visualmap_opts = opts.VisualMapOpts(
                is_piecewise=True,
                pieces=pieces
            )
        else:
            visualmap_opts = opts.VisualMapOpts(
                min_=min_value if min_value is not None else min([item[1] for item in map_data]),
                max_=max_value if max_value is not None else max([item[1] for item in map_data]),
                range_color=color_range if color_range else ["#50a3ba", "#eac763", "#d94e5d"]
            )
        
        map_chart.set_global_opts(
            title_opts=opts.TitleOpts(
                title=title,
                subtitle=subtitle,
                pos_left="center"
            ),
            visualmap_opts=visualmap_opts,
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(
                trigger="item",
                formatter="{b}: {c}"
            )
        )
        
        # 生成临时文件路径
        file_name = f"{city}_map_{uuid.uuid4().hex}.html"
        file_path = os.path.join(self.temp_dir, 'region_maps', file_name)
        
        # 渲染地图
        map_chart.render(file_path)
        
        return file_path
    
    def generate_air_quality_map(self, data, title="全国主要城市空气质量热力图", subtitle="", width="900px", height="600px", 
                                background_color="#fff", min_value=None, max_value=None, 
                                color_range=None, is_visualmap_piecewise=False, pieces=None):
        """
        生成空气质量热力图
        
        参数:
            data (list/DataFrame): 数据，格式为 [["城市名", 值], ...] 或包含 city 和 value 列的 DataFrame
            title (str): 地图标题
            subtitle (str): 地图副标题
            width (str): 地图宽度，如 '900px'
            height (str): 地图高度，如 '600px'
            background_color (str): 背景颜色，如 '#fff'
            min_value (float): 最小值，用于视觉映射
            max_value (float): 最大值，用于视觉映射
            color_range (list): 颜色范围，如 ['#50a3ba', '#eac763', '#d94e5d']
            is_visualmap_piecewise (bool): 是否使用分段视觉映射
            pieces (list): 分段设置，如 [{"min": 1000, "max": 10000, "color": "#FF0000"}, ...]
            
        返回:
            str: 生成的地图文件路径
        """
        logger.debug("生成空气质量热力图")
        
        # 处理数据
        if isinstance(data, pd.DataFrame):
            if 'city' in data.columns and 'value' in data.columns:
                map_data = [[row['city'], row['value']] for _, row in data.iterrows()]
            else:
                raise ValueError("DataFrame必须包含'city'和'value'列")
        else:
            map_data = data
        
        # 创建地图实例
        geo_chart = Geo(init_opts=opts.InitOpts(
            width=width, 
            height=height,
            bg_color=background_color
        ))
        
        # 添加地图架构
        geo_chart.add_schema(maptype="china")
        
        # 添加数据到地图
        geo_chart.add(
            series_name="",
            data_pair=map_data,
            type_=ChartType.EFFECT_SCATTER,
        )
        
        # 设置全局配置
        visualmap_opts = None
        if is_visualmap_piecewise and pieces:
            visualmap_opts = opts.VisualMapOpts(
                is_piecewise=True,
                pieces=pieces
            )
        else:
            visualmap_opts = opts.VisualMapOpts(
                min_=min_value if min_value is not None else min([item[1] for item in map_data]),
                max_=max_value if max_value is not None else max([item[1] for item in map_data]),
                range_color=color_range if color_range else ["#50a3ba", "#eac763", "#d94e5d"]
            )
        
        geo_chart.set_global_opts(
            title_opts=opts.TitleOpts(
                title=title,
                subtitle=subtitle,
                pos_left="center"
            ),
            visualmap_opts=visualmap_opts,
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(
                trigger="item",
                formatter="{b}: {c}"
            )
        )
        
        # 生成临时文件路径
        file_name = f"air_quality_map_{uuid.uuid4().hex}.html"
        file_path = os.path.join(self.temp_dir, 'region_maps', file_name)
        
        # 渲染地图
        geo_chart.render(file_path)
        
        return file_path
    
    def export_map(self, html_path, format='html', output_path=None):
        """
        导出地图为指定格式
        
        参数:
            html_path (str): HTML地图文件路径
            format (str): 导出格式，目前仅支持'html'
            output_path (str): 输出文件路径，如果为None则生成临时文件
            
        返回:
            str: 导出的文件路径
        """
        logger.debug(f"导出地图为{format}格式")
        
        if format not in self.export_formats:
            raise ValueError(f"不支持的导出格式: {format}，支持的格式有: {', '.join(self.export_formats)}")
        
        if format == 'html':
            if output_path:
                # 如果指定了输出路径，复制HTML文件
                import shutil
                shutil.copy2(html_path, output_path)
                return output_path
            else:
                # 否则直接返回HTML文件路径
                return html_path
        else:
            raise ValueError(f"不支持的导出格式: {format}")

# 示例用法
if __name__ == "__main__":
    # 创建区域热力图生成器实例
    generator = RegionMapGenerator()
    
    # 示例1：生成世界地图
    world_data = [
        ["China", 95.1], ["Canada", 23.2], ["Brazil", 43.3], 
        ["Russia", 66.4], ["United States", 88.5]
    ]
    world_map_path = generator.generate_world_map(
        data=world_data,
        title="世界地图示例",
        min_value=0,
        max_value=100
    )
    print(f"世界地图已生成: {world_map_path}")
    
    # 示例2：生成中国地图
    china_data = [
        ["北京市", 2154], ["天津市", 1560], ["上海市", 2424], ["重庆市", 3102],
        ["河北省", 7556], ["山西省", 3684], ["辽宁省", 4359], ["吉林省", 2749],
        ["黑龙江省", 3834], ["江苏省", 8050], ["浙江省", 5737], ["安徽省", 6303],
        ["福建省", 3941], ["江西省", 4648], ["山东省", 10047], ["河南省", 9451],
        ["湖北省", 5917], ["湖南省", 6899], ["广东省", 11346], ["广西壮族自治区", 4900],
        ["海南省", 930], ["四川省", 8341], ["贵州省", 3600], ["云南省", 4830],
        ["西藏自治区", 343], ["陕西省", 3835], ["甘肃省", 2637], ["青海省", 603],
        ["宁夏回族自治区", 683], ["新疆维吾尔自治区", 2487]
    ]
    china_map_path = generator.generate_china_map(
        data=china_data,
        title="中国各省人口分布",
        is_visualmap_piecewise=True,
        pieces=[
            {"min": 10000, "color": "#FF0000"},
            {"min": 5000, "max": 9999, "color": "#FF4500"},
            {"min": 1000, "max": 4999, "color": "#FF6347"},
            {"min": 300, "max": 999, "color": "#FFD700"},
            {"max": 299, "color": "#90EE90"}
        ]
    )
    print(f"中国地图已生成: {china_map_path}")
    
    # 示例3：生成省级地图（贵州省）
    province_data = [
        ["贵阳市", 1.07], ["六盘水市", 3.85], ["遵义市", 6.38], 
        ["安顺市", 8.21], ["毕节市", 2.53], ["铜仁市", 4.37], 
        ["黔西南布依族苗族自治州", 9.38], ["黔东南苗族侗族自治州", 4.29], 
        ["黔南布依族苗族自治州", 6.1]
    ]
    province_map_path = generator.generate_province_map(
        data=province_data,
        province="贵州",
        title="贵州省地图示例"
    )
    print(f"贵州省地图已生成: {province_map_path}")
    
    # 示例4：生成市级地图（贵阳市）
    city_data = [
        ["观山湖区", 3], ["云岩区", 5], ["南明区", 7], 
        ["花溪区", 8], ["乌当区", 2], ["白云区", 4], 
        ["修文县", 7], ["息烽县", 8], ["开阳县", 2], 
        ["清镇市", 4]
    ]
    city_map_path = generator.generate_city_map(
        data=city_data,
        city="贵阳",
        title="贵阳市地图示例"
    )
    print(f"贵阳市地图已生成: {city_map_path}")
    
    # 示例5：生成空气质量热力图
    air_quality_data = [
        ["上海", 4.07], ["北京", 1.85], ["合肥", 4.38], ["哈尔滨", 2.21], 
        ["广州", 3.53], ["成都", 4.37], ["无锡", 1.38], ["杭州", 4.29], 
        ["武汉", 4.1], ["深圳", 1.31], ["西安", 3.92], ["郑州", 4.47], 
        ["重庆", 2.40], ["长沙", 3.60], ["贵阳", 1.2], ["乌鲁木齐", 3.7]
    ]
    air_quality_map_path = generator.generate_air_quality_map(
        data=air_quality_data,
        title="全国主要城市空气质量热力图示例"
    )
    print(f"空气质量热力图已生成: {air_quality_map_path}") 