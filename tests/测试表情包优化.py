#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试表情包优化效果

对比V1和V2的差异：
- 文件大小
- 生成速度
- 视觉质量
"""

import sys
import os
import time
import logging
from typing import Dict

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from emoji_generator_v2 import EmojiGeneratorV2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_gif_generation(video_path: str, output_dir: str):
    """测试GIF生成"""
    logger.info("="*80)
    logger.info("测试 GIF 表情包生成")
    logger.info("="*80)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 测试片段
    test_segments = [
        {'start': 60, 'duration': 3, 'name': '测试1_3秒'},
        {'start': 120, 'duration': 5, 'name': '测试2_5秒'},
        {'start': 180, 'duration': 2, 'name': '测试3_2秒'}
    ]
    
    results = []
    
    for quality in ['high', 'medium', 'low']:
        logger.info(f"\n--- 测试质量级别: {quality} ---")
        
        generator = EmojiGeneratorV2({
            'gif_quality': quality,
            'fps': 20,
            'max_gif_size_kb': 2000
        })
        
        for segment in test_segments:
            output_file = os.path.join(
                output_dir,
                f"test_{segment['name']}_{quality}.gif"
            )
            
            start_time = time.time()
            
            success = generator.generate_emoji_gif(
                video_path,
                segment['start'],
                segment['duration'],
                output_file,
                size='medium'
            )
            
            elapsed = time.time() - start_time
            
            if success and os.path.exists(output_file):
                file_size_kb = os.path.getsize(output_file) / 1024
                
                result = {
                    'name': segment['name'],
                    'quality': quality,
                    'duration': segment['duration'],
                    'file_size_kb': file_size_kb,
                    'generation_time': elapsed,
                    'path': output_file
                }
                
                results.append(result)
                
                logger.info(f"  ✓ {segment['name']}: {file_size_kb:.1f}KB, {elapsed:.1f}s")
            else:
                logger.error(f"  ✗ {segment['name']}: 生成失败")
    
    # 统计分析
    logger.info("\n" + "="*80)
    logger.info("统计分析")
    logger.info("="*80)
    
    for quality in ['high', 'medium', 'low']:
        quality_results = [r for r in results if r['quality'] == quality]
        
        if quality_results:
            avg_size = sum(r['file_size_kb'] for r in quality_results) / len(quality_results)
            avg_time = sum(r['generation_time'] for r in quality_results) / len(quality_results)
            
            logger.info(f"\n{quality.upper()} 质量:")
            logger.info(f"  平均文件大小: {avg_size:.1f}KB")
            logger.info(f"  平均生成时间: {avg_time:.1f}s")
    
    return results


def test_png_generation(video_path: str, output_dir: str):
    """测试PNG生成"""
    logger.info("\n" + "="*80)
    logger.info("测试 PNG 表情包生成")
    logger.info("="*80)
    
    os.makedirs(output_dir, exist_ok=True)
    
    generator = EmojiGeneratorV2({
        'png_quality': 95
    })
    
    # 测试时间点
    test_timestamps = [60, 120, 180]
    
    results = []
    
    for i, timestamp in enumerate(test_timestamps):
        for size in ['small', 'medium', 'large']:
            output_file = os.path.join(
                output_dir,
                f"test_png_{i+1}_{size}.png"
            )
            
            start_time = time.time()
            
            success = generator.generate_emoji_png(
                video_path,
                timestamp,
                output_file,
                size=size
            )
            
            elapsed = time.time() - start_time
            
            if success and os.path.exists(output_file):
                file_size_kb = os.path.getsize(output_file) / 1024
                
                result = {
                    'index': i + 1,
                    'size': size,
                    'file_size_kb': file_size_kb,
                    'generation_time': elapsed,
                    'path': output_file
                }
                
                results.append(result)
                
                logger.info(f"  ✓ PNG{i+1}_{size}: {file_size_kb:.1f}KB, {elapsed:.2f}s")
    
    # 统计
    logger.info("\n统计:")
    for size in ['small', 'medium', 'large']:
        size_results = [r for r in results if r['size'] == size]
        if size_results:
            avg_size = sum(r['file_size_kb'] for r in size_results) / len(size_results)
            logger.info(f"  {size}: 平均 {avg_size:.1f}KB")
    
    return results


def test_multi_size(video_path: str, output_dir: str):
    """测试多尺寸生成"""
    logger.info("\n" + "="*80)
    logger.info("测试多尺寸生成")
    logger.info("="*80)
    
    os.makedirs(output_dir, exist_ok=True)
    
    generator = EmojiGeneratorV2({
        'gif_quality': 'high',
        'fps': 20
    })
    
    # 测试GIF多尺寸
    logger.info("\nGIF 多尺寸:")
    gif_results = generator.generate_multi_size_gif(
        video_path,
        60,
        3,
        output_dir,
        'test_multi_gif'
    )
    
    for size, path in gif_results.items():
        file_size_kb = os.path.getsize(path) / 1024
        logger.info(f"  {size}: {file_size_kb:.1f}KB - {os.path.basename(path)}")
    
    # 测试PNG多尺寸
    logger.info("\nPNG 多尺寸:")
    png_results = generator.generate_multi_size_png(
        video_path,
        120,
        output_dir,
        'test_multi_png'
    )
    
    for size, path in png_results.items():
        file_size_kb = os.path.getsize(path) / 1024
        logger.info(f"  {size}: {file_size_kb:.1f}KB - {os.path.basename(path)}")


def main():
    """主函数"""
    logger.info("="*80)
    logger.info("表情包优化效果测试")
    logger.info("="*80)
    
    # 查找测试视频
    recordings_dir = os.path.expanduser("~/shanshan_materials/01_完整录播")
    
    if not os.path.exists(recordings_dir):
        logger.error(f"❌ 录播目录不存在: {recordings_dir}")
        return
    
    # 查找最新视频
    import glob
    video_files = glob.glob(os.path.join(recordings_dir, "**/*_完整.ts"), recursive=True)
    
    if not video_files:
        logger.error("❌ 没有找到录播视频")
        return
    
    video_files.sort(key=os.path.getmtime, reverse=True)
    video_path = video_files[0]
    
    logger.info(f"\n使用视频: {os.path.basename(video_path)}")
    logger.info(f"视频大小: {os.path.getsize(video_path) / (1024**3):.2f} GB")
    
    # 创建测试输出目录
    from datetime import datetime
    output_dir = os.path.expanduser(
        f"~/shanshan_materials/测试_表情包优化_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"输出目录: {output_dir}\n")
    
    # 运行测试
    try:
        # 测试1: GIF生成
        gif_results = test_gif_generation(
            video_path,
            os.path.join(output_dir, 'gif')
        )
        
        # 测试2: PNG生成
        png_results = test_png_generation(
            video_path,
            os.path.join(output_dir, 'png')
        )
        
        # 测试3: 多尺寸生成
        test_multi_size(
            video_path,
            os.path.join(output_dir, 'multi_size')
        )
        
        # 总结
        logger.info("\n" + "="*80)
        logger.info("✅ 所有测试完成！")
        logger.info("="*80)
        logger.info(f"\n测试结果保存在: {output_dir}")
        logger.info(f"  • GIF测试: {len(gif_results)} 个文件")
        logger.info(f"  • PNG测试: {len(png_results)} 个文件")
        logger.info(f"\n请手动检查生成的文件质量")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()



