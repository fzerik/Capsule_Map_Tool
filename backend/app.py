from flask import Flask, request, jsonify, send_from_directory, render_template, send_file
from flask_cors import CORS
import pandas as pd
from geopy.geocoders import GoogleV3
import requests
import re
import os
import logging
from backend.coordinate_converter import CoordinateConverter
from backend.map_generator import MapGenerator
from backend.region_map_generator import RegionMapGenerator
import tempfile
import uuid
import io
import json

# 配置日志：生产默认使用 INFO，详细级别通过环境变量显式开启。
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

# requests/urllib3 的 DEBUG 日志会把包含 API Key 的完整 URL 输出到终端，生产环境强制关闭。
for noisy_logger_name in ('urllib3', 'requests.packages.urllib3'):
    logging.getLogger(noisy_logger_name).setLevel(logging.WARNING)

# 获取当前文件所在目录的上一级目录（项目根目录）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_FOLDER = os.path.join(BASE_DIR, '')  # 静态文件目录
TEMP_DIR = tempfile.gettempdir()  # 临时文件目录

logger.debug(f"项目根目录: {BASE_DIR}")
logger.debug(f"静态文件目录: {STATIC_FOLDER}")
logger.debug(f"临时文件目录: {TEMP_DIR}")

app = Flask(__name__, 
            static_folder=STATIC_FOLDER,  # 设置静态文件目录
            static_url_path='')  # 设置静态文件URL路径

# 生产环境请将 CORS_ORIGINS 设置为实际前端域名，开发环境默认允许跨域。
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CORS_ORIGINS', '*').split(',')
    if origin.strip()
]
CORS(app, origins=CORS_ORIGINS)

# 服务端默认 API Key 仅从环境变量读取，不在源码中保存明文密钥。
# 前端也可以在请求中临时提供用户自己的 Key；服务端不会持久化该值。
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '').strip()
AMAP_API_KEY = os.environ.get('AMAP_API_KEY', '').strip()
AMAP_GEOCODE_URL = 'https://restapi.amap.com/v3/geocode/geo'

# 初始化坐标转换器
coordinate_converter = CoordinateConverter()

# 初始化地图生成器
map_generator = MapGenerator()

# 初始化区域热力图生成器
region_map_generator = RegionMapGenerator()

# 创建临时地图文件目录
os.makedirs(os.path.join(TEMP_DIR, 'maps'), exist_ok=True)

def get_lat_long_google(location, api_key=None):
    """使用Google Geocoding API获取地址的经纬度（返回WGS84坐标）"""
    effective_api_key = (api_key or GOOGLE_API_KEY).strip()
    if not effective_api_key:
        return {
            'status': 'error',
            'message': '未配置Google API密钥，请在页面填写或设置环境变量 GOOGLE_API_KEY'
        }

    try:
        # 每次请求使用本次调用的 Key；用户 Key 只存在于当前请求内，不写入服务端。
        geolocator = GoogleV3(api_key=effective_api_key)
        loc = geolocator.geocode(location)
        if loc:
            return {
                'status': 'success',
                'latitude': loc.latitude,
                'longitude': loc.longitude,
                'formatted_address': loc.address,
                'provider': 'google',
                'coordinate_system': 'WGS84'
            }
        else:
            return {
                'status': 'error',
                'message': f'无法找到地址: {location}'
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'地理编码错误: {str(e)}'
        }


def get_lat_long_amap(location, api_key=None):
    """使用高德地理编码API获取地址的经纬度（返回GCJ02坐标）"""
    effective_api_key = (api_key or AMAP_API_KEY).strip()
    if not effective_api_key:
        return {
            'status': 'error',
            'message': '未配置高德API密钥，请在页面填写或设置环境变量 AMAP_API_KEY'
        }
    try:
        response = requests.get(AMAP_GEOCODE_URL, params={
            'key': effective_api_key,
            'address': location,
            'output': 'JSON'
        }, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == '1' and data.get('geocodes'):
            geocode = data['geocodes'][0]
            lng_str, lat_str = geocode['location'].split(',')
            return {
                'status': 'success',
                'latitude': float(lat_str),
                'longitude': float(lng_str),
                'formatted_address': geocode.get('formatted_address', location),
                'provider': 'amap',
                'coordinate_system': 'GCJ02'
            }
        else:
            info = data.get('info', '')
            if info and info != 'OK':
                return {
                    'status': 'error',
                    'message': f'高德地理编码错误: {info}'
                }
            return {
                'status': 'error',
                'message': f'无法找到地址: {location}'
            }
    except requests.exceptions.RequestException as e:
        return {
            'status': 'error',
            'message': f'高德API请求失败: {str(e)}'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'地理编码错误: {str(e)}'
        }


def geocode_with_provider(location, provider='google', api_key=None):
    """根据指定的服务商进行地理编码。api_key 仅用于当前请求，不会被保存。"""
    if provider == 'amap':
        return get_lat_long_amap(location, api_key)
    return get_lat_long_google(location, api_key)

def clean_location(location_str):
    """清理地址字符串，移除括号内容和多余空格"""
    if not location_str or not isinstance(location_str, str):
        return ""
    location_str = re.sub(r'\([^)]*\)', '', location_str)  # 移除括号及其内容
    location_str = location_str.strip()  # 移除首尾空格
    return location_str

# 主页路由
@app.route('/')
def index():
    logger.debug("访问主页路由")
    index_path = os.path.join(STATIC_FOLDER, 'index.html')
    logger.debug(f"index.html 路径: {index_path}")
    logger.debug(f"文件是否存在: {os.path.exists(index_path)}")
    response = send_from_directory(STATIC_FOLDER, 'index.html')
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

# 处理所有静态文件请求
@app.route('/<path:path>')
def serve_static(path):
    logger.debug(f"请求静态文件: {path}")
    file_path = os.path.join(STATIC_FOLDER, path)
    logger.debug(f"文件路径: {file_path}")
    logger.debug(f"文件是否存在: {os.path.exists(file_path)}")
    if os.path.exists(file_path):
        return send_from_directory(STATIC_FOLDER, path)
    else:
        logger.error(f"文件不存在: {file_path}")
        return "File not found", 404

@app.route('/api/geocode', methods=['POST'])
def geocode_address():
    """单个地址转换为经纬度的API端点"""
    logger.debug("访问 /api/geocode 端点")
    data = request.get_json(silent=True) or {}
    if 'address' not in data:
        return jsonify({'status': 'error', 'message': '请提供地址'}), 400

    address = data['address']
    provider = data.get('provider', 'google')
    api_key = str(data.get('api_key', '') or '').strip()
    if provider not in ('google', 'amap'):
        return jsonify({'status': 'error', 'message': '无效的地理编码服务商'}), 400

    cleaned_address = clean_location(address)
    if not cleaned_address:
        return jsonify({'status': 'error', 'message': '地址无效'}), 400

    result = geocode_with_provider(cleaned_address, provider, api_key)
    return jsonify(result)


@app.route('/api/batch-geocode', methods=['POST'])
def batch_geocode():
    """批量地址转换为经纬度的API端点"""
    logger.debug("访问 /api/batch-geocode 端点")
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '没有上传文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择文件'}), 400

    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        return jsonify({'status': 'error', 'message': '仅支持Excel或CSV文件'}), 400

    provider = request.form.get('provider', 'google')
    api_key = request.form.get('api_key', '').strip()
    if provider not in ('google', 'amap'):
        return jsonify({'status': 'error', 'message': '无效的地理编码服务商'}), 400

    try:
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)

        if df.shape[1] == 0:
            return jsonify({'status': 'error', 'message': '文件不包含任何列'}), 400

        address_column = df.columns[0]
        results = []

        for _, row in df.iterrows():
            address = str(row[address_column])
            cleaned_address = clean_location(address)

            if not cleaned_address:
                results.append({
                    'original_address': address,
                    'cleaned_address': '',
                    'status': 'error',
                    'message': '地址无效',
                    'provider': provider
                })
                continue

            geocode_result = geocode_with_provider(cleaned_address, provider, api_key)

            if geocode_result['status'] == 'success':
                results.append({
                    'original_address': address,
                    'cleaned_address': cleaned_address,
                    'status': 'success',
                    'latitude': geocode_result['latitude'],
                    'longitude': geocode_result['longitude'],
                    'formatted_address': geocode_result['formatted_address'],
                    'provider': provider,
                    'coordinate_system': geocode_result.get('coordinate_system')
                })
            else:
                results.append({
                    'original_address': address,
                    'cleaned_address': cleaned_address,
                    'status': 'error',
                    'message': geocode_result['message'],
                    'provider': provider
                })

        return jsonify({
            'status': 'success',
            'provider': provider,
            'coordinate_system': 'GCJ02' if provider == 'amap' else 'WGS84',
            'results': results
        })

    except Exception as e:
        logger.exception("处理批量地址时出错")
        return jsonify({
            'status': 'error',
            'message': f'处理文件时出错: {str(e)}'
        }), 500

@app.route('/api/convert-coordinate', methods=['POST'])
def convert_coordinate():
    """单个坐标转换的API端点"""
    logger.debug("访问 /api/convert-coordinate 端点")
    data = request.json
    
    # 验证请求数据
    if not data:
        return jsonify({'status': 'error', 'message': '请提供坐标数据'}), 400
    
    required_fields = ['source_system', 'target_system', 'longitude', 'latitude']
    for field in required_fields:
        if field not in data:
            return jsonify({'status': 'error', 'message': f'缺少必要字段: {field}'}), 400
    
    # 获取请求参数
    source_system = data['source_system']
    target_system = data['target_system']
    lng = data['longitude']
    lat = data['latitude']
    
    # 验证坐标系统
    valid_systems = ['WGS84', 'GCJ02', 'BD09']
    if source_system not in valid_systems or target_system not in valid_systems:
        return jsonify({'status': 'error', 'message': '无效的坐标系统'}), 400
    
    # 验证经纬度
    try:
        lng = float(lng)
        lat = float(lat)
    except ValueError:
        return jsonify({'status': 'error', 'message': '经纬度必须是有效的数字'}), 400
    
    # 执行坐标转换
    try:
        result_lng, result_lat = coordinate_converter.convert(lng, lat, source_system, target_system)
        
        return jsonify({
            'status': 'success',
            'result': {
                'longitude': result_lng,
                'latitude': result_lat
            }
        })
    except Exception as e:
        logger.exception("坐标转换出错")
        return jsonify({
            'status': 'error',
            'message': f'坐标转换出错: {str(e)}'
        }), 500

@app.route('/api/batch-convert-coordinate', methods=['POST'])
def batch_convert_coordinate():
    """批量坐标转换的API端点"""
    logger.debug("访问 /api/batch-convert-coordinate 端点")
    
    # 验证请求数据
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择文件'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        return jsonify({'status': 'error', 'message': '仅支持Excel或CSV文件'}), 400
    
    source_system = request.form.get('source_system')
    target_system = request.form.get('target_system')
    
    # 验证坐标系统
    valid_systems = ['WGS84', 'GCJ02', 'BD09']
    if source_system not in valid_systems or target_system not in valid_systems:
        return jsonify({'status': 'error', 'message': '无效的坐标系统'}), 400
    
    try:
        # 读取文件
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)
        
        # 确保至少有两列数据（经度和纬度）
        if df.shape[1] < 2:
            return jsonify({'status': 'error', 'message': '文件至少需要包含两列数据（经度和纬度）'}), 400
        
        # 使用前两列作为经度和纬度列
        lng_column = df.columns[0]
        lat_column = df.columns[1]
        results = []
        
        # 处理每一行数据
        for idx, row in df.iterrows():
            try:
                source_lng = float(row[lng_column])
                source_lat = float(row[lat_column])
                
                # 执行坐标转换
                target_lng, target_lat = coordinate_converter.convert(
                    source_lng, source_lat, source_system, target_system
                )
                
                results.append({
                    'source_longitude': source_lng,
                    'source_latitude': source_lat,
                    'target_longitude': target_lng,
                    'target_latitude': target_lat,
                    'status': 'success'
                })
            except Exception as e:
                results.append({
                    'source_longitude': row[lng_column] if pd.notna(row[lng_column]) else 0,
                    'source_latitude': row[lat_column] if pd.notna(row[lat_column]) else 0,
                    'target_longitude': 0,
                    'target_latitude': 0,
                    'status': 'error',
                    'message': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'results': results
        })
    
    except Exception as e:
        logger.exception("处理批量坐标转换时出错")
        return jsonify({
            'status': 'error',
            'message': f'处理文件时出错: {str(e)}'
        }), 500

@app.route('/api/generate-heatmap', methods=['POST'])
def generate_heatmap():
    """生成热力图的API端点"""
    logger.debug("访问 /api/generate-heatmap 端点")
    
    # 验证请求数据
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择文件'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        return jsonify({'status': 'error', 'message': '仅支持Excel或CSV文件'}), 400
    
    # 获取请求参数
    center_lat = float(request.form.get('center_lat', 39.90923))
    center_lng = float(request.form.get('center_lng', 116.65722))
    zoom_start = int(request.form.get('zoom_start', 11))
    tile_type = request.form.get('tile_type', 'gaode_normal')
    include_plugins = request.form.get('include_plugins', 'true').lower() == 'true'
    
    # 处理GeoJSON文件（如果有）
    geojson_path = None
    if 'geojson_file' in request.files:
        geojson_file = request.files['geojson_file']
        if geojson_file.filename != '':
            # 保存GeoJSON文件到临时目录
            geojson_filename = f"geojson_{uuid.uuid4().hex}.json"
            geojson_path = os.path.join(TEMP_DIR, geojson_filename)
            geojson_file.save(geojson_path)
    
    try:
        # 读取数据文件
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)
        
        # 确保数据包含必要的列
        required_columns = ['lat', 'lng', 'count']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'status': 'error', 
                'message': f'文件缺少必要的列: {", ".join(missing_columns)}'
            }), 400
        
        # 生成热力图
        map_file_path = map_generator.generate_heatmap(
            data=df,
            center_lat=center_lat,
            center_lng=center_lng,
            zoom_start=zoom_start,
            tile_type=tile_type,
            include_plugins=include_plugins,
            geojson_path=geojson_path
        )
        
        # 返回生成的地图文件
        return send_file(
            map_file_path,
            mimetype='text/html',
            as_attachment=True,
            download_name=f"heatmap_{uuid.uuid4().hex}.html"
        )
    
    except Exception as e:
        logger.exception("生成热力图时出错")
        return jsonify({
            'status': 'error',
            'message': f'生成热力图时出错: {str(e)}'
        }), 500
    
    finally:
        # 清理临时GeoJSON文件
        if geojson_path and os.path.exists(geojson_path):
            try:
                os.remove(geojson_path)
            except:
                pass

@app.route('/api/generate-pointmap', methods=['POST'])
def generate_pointmap():
    """生成点位图的API端点"""
    logger.debug("访问 /api/generate-pointmap 端点")
    
    # 验证请求数据
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择文件'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        return jsonify({'status': 'error', 'message': '仅支持Excel或CSV文件'}), 400
    
    # 获取请求参数
    center_lat = float(request.form.get('center_lat', 39.90923))
    center_lng = float(request.form.get('center_lng', 116.65722))
    zoom_start = int(request.form.get('zoom_start', 11))
    tile_type = request.form.get('tile_type', 'gaode_normal')
    include_plugins = request.form.get('include_plugins', 'true').lower() == 'true'
    cluster = request.form.get('cluster', 'true').lower() == 'true'
    popup_field = request.form.get('popup_field', 'address')
    
    # 处理GeoJSON文件（如果有）
    geojson_path = None
    if 'geojson_file' in request.files:
        geojson_file = request.files['geojson_file']
        if geojson_file.filename != '':
            # 保存GeoJSON文件到临时目录
            geojson_filename = f"geojson_{uuid.uuid4().hex}.json"
            geojson_path = os.path.join(TEMP_DIR, geojson_filename)
            geojson_file.save(geojson_path)
    
    try:
        # 读取数据文件
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)
        
        # 确保数据包含必要的列
        required_columns = ['lat', 'lng']
        if popup_field and popup_field not in ['lat', 'lng']:
            required_columns.append(popup_field)
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'status': 'error', 
                'message': f'文件缺少必要的列: {", ".join(missing_columns)}'
            }), 400
        
        # 生成点位图
        map_file_path = map_generator.generate_pointmap(
            data=df,
            center_lat=center_lat,
            center_lng=center_lng,
            zoom_start=zoom_start,
            tile_type=tile_type,
            include_plugins=include_plugins,
            geojson_path=geojson_path,
            cluster=cluster,
            popup_field=popup_field
        )
        
        # 返回生成的地图文件
        return send_file(
            map_file_path,
            mimetype='text/html',
            as_attachment=True,
            download_name=f"pointmap_{uuid.uuid4().hex}.html"
        )
    
    except Exception as e:
        logger.exception("生成点位图时出错")
        return jsonify({
            'status': 'error',
            'message': f'生成点位图时出错: {str(e)}'
        }), 500
    
    finally:
        # 清理临时GeoJSON文件
        if geojson_path and os.path.exists(geojson_path):
            try:
                os.remove(geojson_path)
            except:
                pass

@app.route('/api/preview-heatmap', methods=['POST'])
def preview_heatmap():
    """预览热力图的API端点"""
    logger.debug("访问 /api/preview-heatmap 端点")
    
    # 验证请求数据
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择文件'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        return jsonify({'status': 'error', 'message': '仅支持Excel或CSV文件'}), 400
    
    # 获取请求参数
    center_lat = float(request.form.get('center_lat', 39.90923))
    center_lng = float(request.form.get('center_lng', 116.65722))
    zoom_start = int(request.form.get('zoom_start', 11))
    tile_type = request.form.get('tile_type', 'gaode_normal')
    include_plugins = request.form.get('include_plugins', 'true').lower() == 'true'
    
    # 处理GeoJSON文件（如果有）
    geojson_path = None
    if 'geojson_file' in request.files:
        geojson_file = request.files['geojson_file']
        if geojson_file.filename != '':
            # 保存GeoJSON文件到临时目录
            geojson_filename = f"geojson_{uuid.uuid4().hex}.json"
            geojson_path = os.path.join(TEMP_DIR, geojson_filename)
            geojson_file.save(geojson_path)
    
    try:
        # 读取数据文件
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)
        
        # 确保数据包含必要的列
        required_columns = ['lat', 'lng', 'count']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'status': 'error', 
                'message': f'文件缺少必要的列: {", ".join(missing_columns)}'
            }), 400
        
        # 生成热力图
        map_file_path = map_generator.generate_heatmap(
            data=df,
            center_lat=center_lat,
            center_lng=center_lng,
            zoom_start=zoom_start,
            tile_type=tile_type,
            include_plugins=include_plugins,
            geojson_path=geojson_path
        )
        
        # 读取生成的HTML文件内容
        with open(map_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 删除临时文件
        try:
            os.remove(map_file_path)
        except:
            pass
        
        # 返回HTML内容
        return jsonify({
            'status': 'success',
            'html_content': html_content
        })
    
    except Exception as e:
        logger.exception("预览热力图时出错")
        return jsonify({
            'status': 'error',
            'message': f'预览热力图时出错: {str(e)}'
        }), 500
    
    finally:
        # 清理临时GeoJSON文件
        if geojson_path and os.path.exists(geojson_path):
            try:
                os.remove(geojson_path)
            except:
                pass

@app.route('/api/preview-pointmap', methods=['POST'])
def preview_pointmap():
    """预览点位图的API端点"""
    logger.debug("访问 /api/preview-pointmap 端点")
    
    # 验证请求数据
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择文件'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        return jsonify({'status': 'error', 'message': '仅支持Excel或CSV文件'}), 400
    
    # 获取请求参数
    center_lat = float(request.form.get('center_lat', 39.90923))
    center_lng = float(request.form.get('center_lng', 116.65722))
    zoom_start = int(request.form.get('zoom_start', 11))
    tile_type = request.form.get('tile_type', 'gaode_normal')
    include_plugins = request.form.get('include_plugins', 'true').lower() == 'true'
    cluster = request.form.get('cluster', 'true').lower() == 'true'
    popup_field = request.form.get('popup_field', 'address')
    
    # 处理GeoJSON文件（如果有）
    geojson_path = None
    if 'geojson_file' in request.files:
        geojson_file = request.files['geojson_file']
        if geojson_file.filename != '':
            # 保存GeoJSON文件到临时目录
            geojson_filename = f"geojson_{uuid.uuid4().hex}.json"
            geojson_path = os.path.join(TEMP_DIR, geojson_filename)
            geojson_file.save(geojson_path)
    
    try:
        # 读取数据文件
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)
        
        # 确保数据包含必要的列
        required_columns = ['lat', 'lng']
        if popup_field and popup_field not in ['lat', 'lng']:
            required_columns.append(popup_field)
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'status': 'error', 
                'message': f'文件缺少必要的列: {", ".join(missing_columns)}'
            }), 400
        
        # 生成点位图
        map_file_path = map_generator.generate_pointmap(
            data=df,
            center_lat=center_lat,
            center_lng=center_lng,
            zoom_start=zoom_start,
            tile_type=tile_type,
            include_plugins=include_plugins,
            geojson_path=geojson_path,
            cluster=cluster,
            popup_field=popup_field
        )
        
        # 读取生成的HTML文件内容
        with open(map_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 删除临时文件
        try:
            os.remove(map_file_path)
        except:
            pass
        
        # 返回HTML内容
        return jsonify({
            'status': 'success',
            'html_content': html_content
        })
    
    except Exception as e:
        logger.exception("预览点位图时出错")
        return jsonify({
            'status': 'error',
            'message': f'预览点位图时出错: {str(e)}'
        }), 500
    
    finally:
        # 清理临时GeoJSON文件
        if geojson_path and os.path.exists(geojson_path):
            try:
                os.remove(geojson_path)
            except:
                pass

@app.route('/api/preview-region-map', methods=['POST'])
def preview_region_map():
    """预览区域热力图的API端点"""
    logger.debug("访问 /api/preview-region-map 端点")
    
    # 验证请求数据
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择文件'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        return jsonify({'status': 'error', 'message': '仅支持Excel或CSV文件'}), 400
    
    # 获取请求参数
    map_type = request.form.get('map_type', 'world')
    title = request.form.get('title', '')
    subtitle = request.form.get('subtitle', '')
    width = request.form.get('width', '900px')
    height = request.form.get('height', '600px')
    background_color = request.form.get('background_color', '#fff')
    
    # 可视化映射参数
    min_value = request.form.get('min_value')
    max_value = request.form.get('max_value')
    if min_value:
        min_value = float(min_value)
    if max_value:
        max_value = float(max_value)
    
    color_range = request.form.get('color_range')
    if color_range:
        try:
            color_range = json.loads(color_range)
        except:
            color_range = None
    
    is_visualmap_piecewise = request.form.get('is_visualmap_piecewise', 'false').lower() == 'true'
    pieces = request.form.get('pieces')
    if pieces:
        try:
            pieces = json.loads(pieces)
        except:
            pieces = None
    
    # 特定地图类型的参数
    province = request.form.get('province', '')
    city = request.form.get('city', '')
    
    try:
        # 读取数据文件
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)
        
        # 根据地图类型验证数据列
        required_columns = []
        if map_type == 'world':
            required_columns = ['country', 'value']
        elif map_type == 'china':
            required_columns = ['province', 'value']
        elif map_type == 'province':
            required_columns = ['city', 'value']
        elif map_type == 'city':
            required_columns = ['district', 'value']
        elif map_type == 'air_quality':
            required_columns = ['city', 'value']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'status': 'error', 
                'message': f'文件缺少必要的列: {", ".join(missing_columns)}'
            }), 400
        
        # 生成地图
        map_file_path = None
        if map_type == 'world':
            map_file_path = region_map_generator.generate_world_map(
                data=df,
                title=title,
                subtitle=subtitle,
                width=width,
                height=height,
                background_color=background_color,
                min_value=min_value,
                max_value=max_value,
                color_range=color_range,
                is_visualmap_piecewise=is_visualmap_piecewise,
                pieces=pieces
            )
        elif map_type == 'china':
            map_file_path = region_map_generator.generate_china_map(
                data=df,
                title=title,
                subtitle=subtitle,
                width=width,
                height=height,
                background_color=background_color,
                min_value=min_value,
                max_value=max_value,
                color_range=color_range,
                is_visualmap_piecewise=is_visualmap_piecewise,
                pieces=pieces
            )
        elif map_type == 'province':
            if not province:
                return jsonify({'status': 'error', 'message': '缺少省份参数'}), 400
            
            map_file_path = region_map_generator.generate_province_map(
                data=df,
                province=province,
                title=title,
                subtitle=subtitle,
                width=width,
                height=height,
                background_color=background_color,
                min_value=min_value,
                max_value=max_value,
                color_range=color_range,
                is_visualmap_piecewise=is_visualmap_piecewise,
                pieces=pieces
            )
        elif map_type == 'city':
            if not city:
                return jsonify({'status': 'error', 'message': '缺少城市参数'}), 400
            
            map_file_path = region_map_generator.generate_city_map(
                data=df,
                city=city,
                title=title,
                subtitle=subtitle,
                width=width,
                height=height,
                background_color=background_color,
                min_value=min_value,
                max_value=max_value,
                color_range=color_range,
                is_visualmap_piecewise=is_visualmap_piecewise,
                pieces=pieces
            )
        elif map_type == 'air_quality':
            map_file_path = region_map_generator.generate_air_quality_map(
                data=df,
                title=title,
                subtitle=subtitle,
                width=width,
                height=height,
                background_color=background_color,
                min_value=min_value,
                max_value=max_value,
                color_range=color_range,
                is_visualmap_piecewise=is_visualmap_piecewise,
                pieces=pieces
            )
        else:
            return jsonify({'status': 'error', 'message': f'不支持的地图类型: {map_type}'}), 400
        
        # 读取生成的HTML文件内容
        with open(map_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 删除临时文件
        try:
            os.remove(map_file_path)
        except:
            pass
        
        # 返回HTML内容
        return jsonify({
            'status': 'success',
            'html_content': html_content
        })
    
    except Exception as e:
        logger.exception("预览区域热力图时出错")
        return jsonify({
            'status': 'error',
            'message': f'预览区域热力图时出错: {str(e)}'
        }), 500

@app.route('/api/generate-region-map', methods=['POST'])
def generate_region_map():
    """生成区域热力图的API端点"""
    logger.debug("访问 /api/generate-region-map 端点")
    
    # 验证请求数据
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择文件'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        return jsonify({'status': 'error', 'message': '仅支持Excel或CSV文件'}), 400
    
    # 获取请求参数
    map_type = request.form.get('map_type', 'world')
    title = request.form.get('title', '')
    subtitle = request.form.get('subtitle', '')
    width = request.form.get('width', '900px')
    height = request.form.get('height', '600px')
    background_color = request.form.get('background_color', '#fff')
    export_format = request.form.get('export_format', 'html')
    
    # 检查导出格式
    if export_format != 'html':
        return jsonify({'status': 'error', 'message': '目前仅支持HTML格式导出'}), 400
    
    # 可视化映射参数
    min_value = request.form.get('min_value')
    max_value = request.form.get('max_value')
    if min_value:
        min_value = float(min_value)
    if max_value:
        max_value = float(max_value)
    
    color_range = request.form.get('color_range')
    if color_range:
        try:
            color_range = json.loads(color_range)
        except:
            color_range = None
    
    is_visualmap_piecewise = request.form.get('is_visualmap_piecewise', 'false').lower() == 'true'
    pieces = request.form.get('pieces')
    if pieces:
        try:
            pieces = json.loads(pieces)
        except:
            pieces = None
    
    # 特定地图类型的参数
    province = request.form.get('province', '')
    city = request.form.get('city', '')
    
    try:
        # 读取数据文件
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)
        
        # 根据地图类型验证数据列
        required_columns = []
        if map_type == 'world':
            required_columns = ['country', 'value']
        elif map_type == 'china':
            required_columns = ['province', 'value']
        elif map_type == 'province':
            required_columns = ['city', 'value']
        elif map_type == 'city':
            required_columns = ['district', 'value']
        elif map_type == 'air_quality':
            required_columns = ['city', 'value']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'status': 'error', 
                'message': f'文件缺少必要的列: {", ".join(missing_columns)}'
            }), 400
        
        # 生成地图
        map_file_path = None
        if map_type == 'world':
            map_file_path = region_map_generator.generate_world_map(
                data=df,
                title=title,
                subtitle=subtitle,
                width=width,
                height=height,
                background_color=background_color,
                min_value=min_value,
                max_value=max_value,
                color_range=color_range,
                is_visualmap_piecewise=is_visualmap_piecewise,
                pieces=pieces
            )
        elif map_type == 'china':
            map_file_path = region_map_generator.generate_china_map(
                data=df,
                title=title,
                subtitle=subtitle,
                width=width,
                height=height,
                background_color=background_color,
                min_value=min_value,
                max_value=max_value,
                color_range=color_range,
                is_visualmap_piecewise=is_visualmap_piecewise,
                pieces=pieces
            )
        elif map_type == 'province':
            if not province:
                return jsonify({'status': 'error', 'message': '缺少省份参数'}), 400
            
            map_file_path = region_map_generator.generate_province_map(
                data=df,
                province=province,
                title=title,
                subtitle=subtitle,
                width=width,
                height=height,
                background_color=background_color,
                min_value=min_value,
                max_value=max_value,
                color_range=color_range,
                is_visualmap_piecewise=is_visualmap_piecewise,
                pieces=pieces
            )
        elif map_type == 'city':
            if not city:
                return jsonify({'status': 'error', 'message': '缺少城市参数'}), 400
            
            map_file_path = region_map_generator.generate_city_map(
                data=df,
                city=city,
                title=title,
                subtitle=subtitle,
                width=width,
                height=height,
                background_color=background_color,
                min_value=min_value,
                max_value=max_value,
                color_range=color_range,
                is_visualmap_piecewise=is_visualmap_piecewise,
                pieces=pieces
            )
        elif map_type == 'air_quality':
            map_file_path = region_map_generator.generate_air_quality_map(
                data=df,
                title=title,
                subtitle=subtitle,
                width=width,
                height=height,
                background_color=background_color,
                min_value=min_value,
                max_value=max_value,
                color_range=color_range,
                is_visualmap_piecewise=is_visualmap_piecewise,
                pieces=pieces
            )
        else:
            return jsonify({'status': 'error', 'message': f'不支持的地图类型: {map_type}'}), 400
        
        # 导出为HTML格式
        export_file_path = region_map_generator.export_map(map_file_path, format='html')
        
        # 获取文件名
        file_name = f"region_map_{uuid.uuid4().hex}.html"
        
        # 返回生成的文件
        return send_file(
            export_file_path,
            mimetype='text/html',
            as_attachment=True,
            download_name=file_name
        )
    
    except Exception as e:
        logger.exception("生成区域热力图时出错")
        return jsonify({
            'status': 'error',
            'message': f'生成区域热力图时出错: {str(e)}'
        }), 500
    finally:
        # 清理临时文件
        try:
            if map_file_path and os.path.exists(map_file_path):
                os.remove(map_file_path)
        except:
            pass

if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '5000'))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug, host=host, port=port) 