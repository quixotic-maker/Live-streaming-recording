#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复表情包生成问题

问题：
1. GIF文件没有实际生成，只有metadata.json
2. libEGL警告可以忽略

解决方案：
1. 重新从metadata读取信息
2. 重新生成实际的GIF文件
"""

import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from emoji_generator import EmojiGenerator


def fix_emoji_generation():
    """修复表情包生成"""
    
    print("=" * 80)
    print("表情包生成修复工具")
    print("=" * 80)
    print()
    
    temp_dir = Path("temp_emojis")
    
    # 查找所有metadata文件
    metadata_files = list(temp_dir.rglob("*_metadata.json"))
    
    print(f"找到 {len(metadata_files)} 个metadata文件")
    print()
    
    if len(metadata_files) == 0:
        print("未找到metadata文件，请先运行 生成表情包素材_优化版.py")
        return
    
    # 初始化生成器
    generator = EmojiGenerator()
    
    success_count = 0
    fail_count = 0
    
    for i, metadata_file in enumerate(metadata_files, 1):
        print(f"[{i}/{len(metadata_files)}] 处理: {metadata_file.name}")
        
        try:
            # 读取metadata
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            source = metadata.get("source", {})
            video_path = source.get("video_path")
            start = source.get("start")
            end = source.get("end")
            
            if not all([video_path, start is not None, end is not None]):
                print(f"  ✗ metadata不完整")
                fail_count += 1
                continue
            
            if not os.path.exists(video_path):
                print(f"  ✗ 视频文件不存在: {video_path}")
                fail_count += 1
                continue
            
            # 检查GIF是否已存在
            gifs_exist = True
            for spec_name, gif_info in metadata.get("gifs", {}).items():
                gif_path = gif_info.get("path", "")
                if not os.path.exists(gif_path):
                    gifs_exist = False
                    break
            
            if gifs_exist:
                print(f"  ✓ GIF文件已存在，跳过")
                success_count += 1
                continue
            
            # 提取帧
            print(f"    提取视频片段: {start:.2f}s - {end:.2f}s")
            frames = generator.extract_frames(video_path, start, end)
            
            if not frames:
                print(f"  ✗ 未提取到帧")
                fail_count += 1
                continue
            
            print(f"    提取了 {len(frames)} 帧")
            
            # 生成各规格GIF
            output_dir = metadata_file.parent
            base_name = metadata_file.stem.replace("_metadata", "")
            
            generated_count = 0
            
            for spec_name, gif_info in metadata.get("gifs", {}).items():
                size = tuple(gif_info.get("size", [240, 240]))
                gif_path = gif_info.get("path", "")
                
                # 确保使用绝对路径
                if not os.path.isabs(gif_path):
                    gif_path = os.path.join(os.path.dirname(__file__), gif_path)
                
                # 确保父目录存在
                Path(gif_path).parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    # 生成GIF
                    result = generator.create_gif(
                        frames=frames,
                        output_path=gif_path,
                        size=size
                    )
                    
                    print(f"    ✓ 生成 {spec_name}: {result['file_size_kb']:.2f}KB")
                    generated_count += 1
                    
                except Exception as e:
                    print(f"    ✗ {spec_name} 失败: {e}")
            
            # 生成静态图
            if metadata.get("static") and frames:
                static_info = metadata["static"]
                static_path = static_info.get("path", "")
                
                if not os.path.isabs(static_path):
                    static_path = os.path.join(os.path.dirname(__file__), static_path)
                
                Path(static_path).parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    best_frame_idx = len(frames) // 2
                    best_frame = frames[best_frame_idx]
                    
                    result = generator.create_static_image(best_frame, static_path)
                    print(f"    ✓ 生成静态图: {result['file_size_kb']:.2f}KB")
                    generated_count += 1
                    
                except Exception as e:
                    print(f"    ✗ 静态图失败: {e}")
            
            if generated_count > 0:
                print(f"  ✓ 成功生成 {generated_count} 个文件")
                success_count += 1
            else:
                print(f"  ✗ 生成失败")
                fail_count += 1
        
        except Exception as e:
            print(f"  ✗ 处理失败: {e}")
            fail_count += 1
        
        print()
    
    print("=" * 80)
    print("修复完成")
    print("=" * 80)
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"总计: {len(metadata_files)}")
    print()
    
    # 检查生成的文件
    print("验证生成的文件...")
    gif_files = list(temp_dir.rglob("*.gif"))
    png_files = list(temp_dir.rglob("*.png"))
    
    print(f"  GIF文件: {len(gif_files)} 个")
    print(f"  PNG文件: {len(png_files)} 个")
    
    if len(gif_files) > 0:
        print()
        print("✅ 表情包生成成功！")
        print()
        print("下一步：")
        print("  1. 检查表情包质量: ls -lh temp_emojis/thank/")
        print("  2. 适配抖音规格: python3 抖音表情包完整适配.py")
        print("  3. 移动到最终目录: 手动执行或运行organize步骤")
    else:
        print()
        print("⚠️  仍未生成GIF文件")
        print("    可能原因：")
        print("    1. 视频文件路径不正确")
        print("    2. FFmpeg或PIL安装有问题")
        print("    3. 磁盘空间不足")


if __name__ == "__main__":
    fix_emoji_generation()



