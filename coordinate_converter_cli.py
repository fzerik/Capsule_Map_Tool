#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
坐标转换命令行工具
支持WGS84、GCJ02和BD09三种坐标系统之间的互相转换
"""

import argparse
import pandas as pd
import os
from backend.coordinate_converter import CoordinateConverter

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='坐标系统转换工具')
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 单个坐标转换命令
    single_parser = subparsers.add_parser('single', help='单个坐标转换')
    single_parser.add_argument('--lng', type=float, required=True, help='经度')
    single_parser.add_argument('--lat', type=float, required=True, help='纬度')
    single_parser.add_argument('--from', dest='from_system', choices=['WGS84', 'GCJ02', 'BD09'], required=True, help='源坐标系统')
    single_parser.add_argument('--to', dest='to_system', choices=['WGS84', 'GCJ02', 'BD09'], required=True, help='目标坐标系统')
    
    # 批量坐标转换命令
    batch_parser = subparsers.add_parser('batch', help='批量坐标转换')
    batch_parser.add_argument('--file', type=str, required=True, help='输入文件路径 (Excel或CSV)')
    batch_parser.add_argument('--output', type=str, required=True, help='输出文件路径')
    batch_parser.add_argument('--from', dest='from_system', choices=['WGS84', 'GCJ02', 'BD09'], required=True, help='源坐标系统')
    batch_parser.add_argument('--to', dest='to_system', choices=['WGS84', 'GCJ02', 'BD09'], required=True, help='目标坐标系统')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 初始化坐标转换器
    converter = CoordinateConverter()
    
    # 根据命令执行相应的操作
    if args.command == 'single':
        # 单个坐标转换
        result_lng, result_lat = converter.convert(
            args.lng, args.lat, args.from_system, args.to_system
        )
        
        print(f"源坐标 ({args.from_system}): 经度={args.lng}, 纬度={args.lat}")
        print(f"转换结果 ({args.to_system}): 经度={result_lng}, 纬度={result_lat}")
    
    elif args.command == 'batch':
        # 批量坐标转换
        # 检查输入文件是否存在
        if not os.path.exists(args.file):
            print(f"错误: 输入文件 '{args.file}' 不存在")
            return
        
        # 读取输入文件
        try:
            if args.file.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(args.file)
            else:
                df = pd.read_csv(args.file)
        except Exception as e:
            print(f"读取文件时出错: {str(e)}")
            return
        
        # 确保至少有两列数据（经度和纬度）
        if df.shape[1] < 2:
            print("错误: 文件至少需要包含两列数据（经度和纬度）")
            return
        
        # 使用前两列作为经度和纬度列
        lng_column = df.columns[0]
        lat_column = df.columns[1]
        
        # 添加结果列
        df['target_longitude'] = None
        df['target_latitude'] = None
        df['status'] = None
        
        # 处理每一行数据
        success_count = 0
        error_count = 0
        
        for idx, row in df.iterrows():
            try:
                source_lng = float(row[lng_column])
                source_lat = float(row[lat_column])
                
                # 执行坐标转换
                target_lng, target_lat = converter.convert(
                    source_lng, source_lat, args.from_system, args.to_system
                )
                
                df.at[idx, 'target_longitude'] = target_lng
                df.at[idx, 'target_latitude'] = target_lat
                df.at[idx, 'status'] = '成功'
                
                success_count += 1
            except Exception as e:
                df.at[idx, 'target_longitude'] = None
                df.at[idx, 'target_latitude'] = None
                df.at[idx, 'status'] = f'失败: {str(e)}'
                
                error_count += 1
        
        # 保存结果
        try:
            if args.output.endswith(('.xlsx', '.xls')):
                df.to_excel(args.output, index=False)
            else:
                df.to_csv(args.output, index=False)
            
            print(f"转换完成: 成功 {success_count} 条, 失败 {error_count} 条")
            print(f"结果已保存到: {args.output}")
        except Exception as e:
            print(f"保存结果时出错: {str(e)}")
    
    else:
        # 如果没有指定命令，显示帮助信息
        parser.print_help()

if __name__ == '__main__':
    main() 