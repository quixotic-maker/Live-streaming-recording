#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频合并功能测试脚本
用于测试分段视频合并是否正常工作
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.video_merger import merge_videos_ffmpeg, auto_merge_daily_videos, merge_by_session

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_merge_function():
    """测试视频合并功能"""
    print("=" * 70)
    print("视频自动合并功能测试")
    print("=" * 70)
    
    # 提示用户
    print("\n📋 本测试将检测您是否有分段录制的视频文件")
    print("=" * 70)
    
    # 获取默认下载目录
    default_dir = os.path.join(os.path.dirname(__file__), "downloads")
    
    if not os.path.exists(default_dir):
        print(f"\n❌ 下载目录不存在: {default_dir}")
        print("💡 提示：请先录制一些视频，或手动指定视频目录")
        return
    
    print(f"\n📁 检测下载目录: {default_dir}")
    
    # 查找所有平台目录
    platforms = [d for d in os.listdir(default_dir) 
                if os.path.isdir(os.path.join(default_dir, d))]
    
    if not platforms:
        print("\n❌ 未找到任何平台目录")
        return
    
    print(f"\n✅ 找到 {len(platforms)} 个平台目录: {', '.join(platforms)}")
    
    # 查找分段视频
    found_segments = False
    for platform in platforms:
        platform_dir = os.path.join(default_dir, platform)
        
        # 查找主播目录
        if not os.path.isdir(platform_dir):
            continue
            
        anchors = [d for d in os.listdir(platform_dir) 
                  if os.path.isdir(os.path.join(platform_dir, d))]
        
        for anchor in anchors:
            anchor_dir = os.path.join(platform_dir, anchor)
            
            # 查找TS分段文件（格式：主播名_时间_001.ts）
            import glob
            segments = glob.glob(os.path.join(anchor_dir, "*_*_[0-9][0-9][0-9].ts"))
            
            if segments:
                found_segments = True
                print(f"\n📦 平台: {platform}, 主播: {anchor}")
                print(f"   找到 {len(segments)} 个分段文件")
                
                # 分组显示
                from collections import defaultdict
                groups = defaultdict(list)
                for seg in segments:
                    basename = os.path.basename(seg)
                    # 提取基础名称（去掉_XXX.ts部分）
                    base_key = '_'.join(basename.rsplit('_', 1)[0].split('_')[:-1])
                    groups[base_key].append(seg)
                
                for base_key, files in groups.items():
                    print(f"   📹 录制会话: {base_key}")
                    print(f"      分段数: {len(files)}")
                    
                    # 询问是否合并
                    response = input(f"\n   是否合并这个会话的视频? (y/n): ").strip().lower()
                    if response == 'y':
                        # 提取信息
                        first_file = files[0]
                        file_dir = os.path.dirname(first_file)
                        file_name = os.path.basename(first_file)
                        
                        # 提取主播名和时间戳
                        name_parts = file_name.rsplit('_', maxsplit=1)[0]
                        time_pattern = name_parts.split('_', maxsplit=1)[-1]
                        
                        print(f"\n   🔄 开始合并...")
                        try:
                            merged_path = merge_by_session(
                                file_dir,
                                anchor,
                                time_pattern,
                                delete_source=False  # 测试时不删除原文件
                            )
                            
                            if merged_path:
                                print(f"   ✅ 合并成功!")
                                print(f"   📁 文件位置: {merged_path}")
                                
                                # 显示文件大小
                                merged_size = os.path.getsize(merged_path) / (1024**3)
                                print(f"   📊 文件大小: {merged_size:.2f} GB")
                            else:
                                print(f"   ❌ 合并失败")
                        except Exception as e:
                            print(f"   ❌ 合并出错: {e}")
    
    if not found_segments:
        print("\n⚠️ 未找到任何分段视频文件")
        print("\n💡 提示：")
        print("   1. 确保已开启分段录制功能")
        print("   2. 至少录制过一次直播")
        print("   3. 分段文件格式为：主播名_时间_001.ts")
    
    print("\n" + "=" * 70)
    print("测试完成!")
    print("=" * 70)


def manual_merge_example():
    """手动合并示例"""
    print("\n" + "=" * 70)
    print("手动合并视频示例")
    print("=" * 70)
    
    print("\n如果您想手动合并特定的视频文件，可以这样使用：")
    print("\n```python")
    print("from src.video_merger import merge_by_session")
    print("")
    print("# 合并某个会话的所有分段")
    print("merged_path = merge_by_session(")
    print("    base_directory='/path/to/videos',  # 视频所在目录")
    print("    anchor_name='主播名',")
    print("    start_time_pattern='2025-10-30_19-01-00',  # 录制开始时间")
    print("    delete_source=False  # 是否删除源文件")
    print(")")
    print("```")
    print("\n或者合并某天的所有视频：")
    print("\n```python")
    print("from src.video_merger import auto_merge_daily_videos")
    print("")
    print("# 合并某天的所有视频")
    print("merged_path = auto_merge_daily_videos(")
    print("    base_directory='/path/to/videos',")
    print("    anchor_name='主播名',")
    print("    date_str='2025-10-30',  # 日期")
    print("    delete_source=False")
    print(")")
    print("```")


if __name__ == "__main__":
    try:
        test_merge_function()
        manual_merge_example()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)

