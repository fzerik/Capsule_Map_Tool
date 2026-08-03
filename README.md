<div align="center">

<img src="img/logo.png" alt="Capsule Map Tool Logo" width="120" height="120">

# 💊 胶囊地图工具 (Capsule Map Tool)

*用于地址地理编码、坐标转换和地图可视化的轻量工具*

![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Flask](https://img.shields.io/badge/Backend-Flask-green.svg)
![Leaflet](https://img.shields.io/badge/Frontend-Leaflet.js-orange.svg)

</div>

---

## 项目简介

胶囊地图工具是一个基于 Flask 和 JavaScript 的地理数据处理工具，提供地址转经纬度、坐标系转换、点位图与热力图生成，以及区域 GeoJSON 地图展示等功能。

项目同时提供 Web 界面和命令行坐标转换脚本，适合进行日常地址数据处理、坐标转换和简单地图可视化。

## 功能

### 1. 地址转经纬度

- 支持单条地址查询。
- 支持 Excel 和 CSV 文件批量处理。
- 支持 Google Maps 等地理编码服务，具体服务以页面和后端配置为准。
- 查询结果可查看地址、经纬度和坐标系信息。

### 2. 坐标系转换

支持以下坐标系之间的转换：

- **WGS84**：GPS、Google Maps 和 OpenStreetMap 常用坐标系。
- **GCJ02**：高德、腾讯等地图常用坐标系。
- **BD09**：百度地图使用的坐标系。

坐标转换使用本地算法完成，不需要网络请求；支持单点转换和文件批量转换。

### 3. 地图生成

- 根据经纬度数据生成点位图。
- 根据坐标和权重数据生成热力图。
- 支持点聚合、弹窗字段和 GeoJSON 边界图层。
- 支持预览并导出独立 HTML 地图文件。
- 支持高德地图和 OpenStreetMap 等底图。

### 4. 区域地图

支持根据区域数据和 GeoJSON 边界生成世界、中国、省级或市级区域地图，也可以生成空气质量等区域数据的可视化图表。

## 技术栈

- **后端**：Python 3.8+、Flask、Pandas、GeoPy
- **前端**：HTML5、CSS3、JavaScript
- **地图与可视化**：Leaflet.js、Folium、Branca、ECharts
- **数据格式**：CSV、Excel（`.xlsx` / `.xls`）、GeoJSON

## 快速开始

### 1. 创建虚拟环境

确保系统已安装 Python 3.8 或更高版本。

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python -m venv venv
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

地址转经纬度功能需要配置对应的地图服务 API Key。推荐通过环境变量配置：

```bash
# Windows PowerShell
$env:GOOGLE_API_KEY="your_google_api_key"

# Windows CMD
set GOOGLE_API_KEY=your_google_api_key

# Linux / macOS
export GOOGLE_API_KEY="your_google_api_key"
```

也可以在 Web 页面中按提示填写 API Key。API Key 属于敏感信息，不要提交到 Git 仓库。

坐标转换、地图生成和区域地图功能不需要 Google API Key。

## 启动应用

激活虚拟环境后运行：

```bash
python -m backend.app
```

Windows 也可以运行：

```bash
start.bat
```

启动后访问：

```text
http://127.0.0.1:5000
```

## CLI 命令行工具

`coordinate_converter_cli.py` 可在不启动 Web 服务的情况下进行坐标转换。

```bash
# 单点转换：GCJ02 转 WGS84
python coordinate_converter_cli.py single --lng 116.404 --lat 39.915 --from GCJ02 --to WGS84

# 批量转换 Excel 或 CSV 文件
python coordinate_converter_cli.py batch --file input.xlsx --output output.xlsx --from BD09 --to WGS84
```

## 项目结构

```text
capsule_map/
├── backend/
│   ├── app.py                       # Flask 应用和接口
│   ├── coordinate_converter.py      # 坐标转换算法
│   ├── map_generator.py              # 点位图和热力图生成
│   └── region_map_generator.py       # 区域地图生成
├── css/
│   └── style.css                    # 页面样式
├── js/
│   ├── app.js                       # 页面交互
│   ├── coordinate_converter.js      # 坐标转换页面逻辑
│   ├── map_generator.js             # 地图生成页面逻辑
│   └── region_map_generator.js      # 区域地图页面逻辑
├── img/
│   └── logo.png                     # 项目 Logo
├── coordinate_converter_cli.py      # 命令行工具
├── index.html                       # Web 主页面
├── requirements.txt                 # Python 依赖
├── run.py                           # 项目入口
├── start.bat                        # Windows 启动脚本
└── start.sh                         # Linux / macOS 启动脚本
```

## 坐标系参考

| 坐标系 | 常见用途 |
| --- | --- |
| WGS84 | GPS、Google Maps（国际版）、OpenStreetMap |
| GCJ02 | 高德地图、腾讯地图 |
| BD09 | 百度地图 |

## 许可证

本项目基于 MIT License 开源。