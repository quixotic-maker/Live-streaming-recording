#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表情包生成器 V2 - 优化版

改进：
- 集成gifsicle进行GIF优化
- 更好的色彩处理（避免失真）
- 多级压缩策略
- 更快的处理速度
"""

import os
import logging
import subprocess
import tempfile
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class EmojiGeneratorV2:
    """表情包生成器 V2 - 优化版"""
    
    def __init__(self, config: Dict = None):
        """
        初始化
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 质量配置
        self.gif_quality = self.config.get('gif_quality', 'high')  # high/medium/low
        self.png_quality = self.config.get('png_quality', 95)
        
        # 尺寸配置（抖音规格）
        self.sizes = self.config.get('sizes', {
            'small': (240, 240),    # 小表情
            'medium': (320, 320),   # 中表情
            'large': (480, 480)     # 大表情
        })
        
        # 文件大小限制
        self.max_gif_size_kb = self.config.get('max_gif_size_kb', 2000)  # 2MB
        self.max_png_size_kb = self.config.get('max_png_size_kb', 500)   # 500KB
        
        # FPS配置
        self.fps = self.config.get('fps', 20)
        
        # 检查依赖
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查必需的依赖"""
        # 检查FFmpeg
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            raise RuntimeError("FFmpeg 未安装")
        
        # 检查gifsicle
        try:
            subprocess.run(['gifsicle', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            raise RuntimeError("gifsicle 未安装")
        
        logger.info("✓ 依赖检查通过（FFmpeg + gifsicle）")
    
    def generate_emoji_gif(
        self,
        video_path: str,
        start_time: float,
        duration: float,
        output_path: str,
        size: str = 'medium'
    ) -> bool:
        """
        生成GIF表情包（优化版）
        
        Args:
            video_path: 视频路径
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            output_path: 输出路径
            size: 尺寸（small/medium/large）
        
        Returns:
            是否成功
        """
        width, height = self.sizes.get(size, (320, 320))
        
        try:
            # 步骤1: 使用FFmpeg生成高质量的临时GIF
            temp_gif = output_path + '.temp.gif'
            
            success = self._ffmpeg_extract_gif(
                video_path,
                start_time,
                duration,
                temp_gif,
                width,
                height
            )
            
            if not success or not os.path.exists(temp_gif):
                logger.error(f"FFmpeg提取GIF失败")
                return False
            
            # 步骤2: 使用gifsicle优化GIF
            success = self._gifsicle_optimize(temp_gif, output_path)
            
            # 清理临时文件
            if os.path.exists(temp_gif):
                os.remove(temp_gif)
            
            if not success:
                logger.error(f"gifsicle优化失败")
                return False
            
            # 检查文件大小
            file_size_kb = os.path.getsize(output_path) / 1024
            
            if file_size_kb > self.max_gif_size_kb:
                logger.warning(f"GIF文件过大: {file_size_kb:.1f}KB > {self.max_gif_size_kb}KB")
                # 尝试进一步压缩
                success = self._gifsicle_compress_further(output_path)
                if success:
                    file_size_kb = os.path.getsize(output_path) / 1024
                    logger.info(f"进一步压缩后: {file_size_kb:.1f}KB")
            
            logger.info(f"✓ GIF生成成功: {os.path.basename(output_path)} ({file_size_kb:.1f}KB)")
            return True
            
        except Exception as e:
            logger.error(f"生成GIF失败: {e}")
            return False
    
    def _ffmpeg_extract_gif(
        self,
        video_path: str,
        start_time: float,
        duration: float,
        output_path: str,
        width: int,
        height: int
    ) -> bool:
        """
        使用FFmpeg提取GIF（高质量调色板）
        
        使用两阶段方法：
        1. 生成优化的调色板
        2. 使用调色板生成GIF
        """
        try:
            # 步骤1: 生成调色板
            palette_file = output_path + '.palette.png'
            
            palette_cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-t', str(duration),
                '-i', video_path,
                '-vf', (
                    f'fps={self.fps},'
                    f'scale={width}:{height}:flags=lanczos,'
                    'palettegen=stats_mode=diff:max_colors=256'
                ),
                '-y',
                palette_file
            ]
            
            result = subprocess.run(
                palette_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60
            )
            
            if result.returncode != 0 or not os.path.exists(palette_file):
                logger.error("生成调色板失败")
                return False
            
            # 步骤2: 使用调色板生成GIF
            gif_cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-t', str(duration),
                '-i', video_path,
                '-i', palette_file,
                '-filter_complex', (
                    f'[0:v]fps={self.fps},'
                    f'scale={width}:{height}:flags=lanczos[v];'
                    '[v][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle'
                ),
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                gif_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120
            )
            
            # 清理调色板文件
            if os.path.exists(palette_file):
                os.remove(palette_file)
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg超时")
            return False
        except Exception as e:
            logger.error(f"FFmpeg提取GIF失败: {e}")
            return False
    
    def _gifsicle_optimize(self, input_path: str, output_path: str) -> bool:
        """
        使用gifsicle优化GIF
        
        优化策略：
        - 使用--optimize=3（最高优化级别）
        - 使用--lossy压缩（质量可控的有损压缩）
        - 使用--colors减少颜色数（如果需要）
        """
        try:
            # 根据质量设置选择优化参数
            if self.gif_quality == 'high':
                lossy_level = 30  # 轻度压缩
                colors = 256
            elif self.gif_quality == 'medium':
                lossy_level = 50
                colors = 200
            else:  # low
                lossy_level = 80
                colors = 128
            
            cmd = [
                'gifsicle',
                '--optimize=3',           # 最高优化级别
                f'--lossy={lossy_level}', # 有损压缩
                f'--colors={colors}',     # 颜色数
                '--no-warnings',
                input_path,
                '-o', output_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            logger.error("gifsicle优化超时")
            return False
        except Exception as e:
            logger.error(f"gifsicle优化失败: {e}")
            return False
    
    def _gifsicle_compress_further(self, gif_path: str) -> bool:
        """进一步压缩GIF（如果文件过大）"""
        try:
            cmd = [
                'gifsicle',
                '--optimize=3',
                '--lossy=100',      # 更激进的压缩
                '--colors=128',     # 减少颜色
                '--resize-width', str(int(self.sizes['medium'][0] * 0.8)),  # 缩小20%
                '--no-warnings',
                gif_path,
                '-o', gif_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"进一步压缩失败: {e}")
            return False
    
    def generate_emoji_png(
        self,
        video_path: str,
        timestamp: float,
        output_path: str,
        size: str = 'medium'
    ) -> bool:
        """
        生成PNG表情包（静态图）
        
        Args:
            video_path: 视频路径
            timestamp: 时间戳（秒）
            output_path: 输出路径
            size: 尺寸（small/medium/large）
        
        Returns:
            是否成功
        """
        width, height = self.sizes.get(size, (320, 320))
        
        try:
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', video_path,
                '-vframes', '1',
                '-vf', f'scale={width}:{height}:flags=lanczos',
                '-q:v', '2',  # 高质量
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                file_size_kb = os.path.getsize(output_path) / 1024
                logger.info(f"✓ PNG生成成功: {os.path.basename(output_path)} ({file_size_kb:.1f}KB)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"生成PNG失败: {e}")
            return False
    
    def generate_multi_size_gif(
        self,
        video_path: str,
        start_time: float,
        duration: float,
        output_dir: str,
        base_name: str
    ) -> Dict[str, str]:
        """
        生成多尺寸GIF表情包
        
        Args:
            video_path: 视频路径
            start_time: 开始时间
            duration: 持续时间
            output_dir: 输出目录
            base_name: 基础文件名
        
        Returns:
            各尺寸的文件路径
        """
        os.makedirs(output_dir, exist_ok=True)
        
        results = {}
        
        for size in ['small', 'medium', 'large']:
            output_path = os.path.join(output_dir, f"{base_name}_{size}.gif")
            
            success = self.generate_emoji_gif(
                video_path,
                start_time,
                duration,
                output_path,
                size
            )
            
            if success:
                results[size] = output_path
        
        return results
    
    def generate_multi_size_png(
        self,
        video_path: str,
        timestamp: float,
        output_dir: str,
        base_name: str
    ) -> Dict[str, str]:
        """
        生成多尺寸PNG表情包
        
        Args:
            video_path: 视频路径
            timestamp: 时间戳
            output_dir: 输出目录
            base_name: 基础文件名
        
        Returns:
            各尺寸的文件路径
        """
        os.makedirs(output_dir, exist_ok=True)
        
        results = {}
        
        for size in ['small', 'medium', 'large']:
            output_path = os.path.join(output_dir, f"{base_name}_{size}.png")
            
            success = self.generate_emoji_png(
                video_path,
                timestamp,
                output_path,
                size
            )
            
            if success:
                results[size] = output_path
        
        return results
    
    def batch_generate_from_segments(
        self,
        video_path: str,
        segments: List[Dict],
        output_dir: str,
        category: str = 'emoji'
    ) -> List[Dict]:
        """
        批量生成表情包
        
        Args:
            video_path: 视频路径
            segments: 片段列表
            output_dir: 输出目录
            category: 类别
        
        Returns:
            生成结果列表
        """
        results = []
        
        for i, segment in enumerate(segments):
            base_name = f"{category}_{i+1:03d}"
            
            # 生成GIF
            if segment.get('duration', 0) > 0:
                gif_results = self.generate_multi_size_gif(
                    video_path,
                    segment['start'],
                    min(segment.get('duration', 3), 5),  # 最多5秒
                    os.path.join(output_dir, 'gif'),
                    base_name
                )
                
                if gif_results:
                    results.append({
                        'type': 'gif',
                        'category': category,
                        'index': i + 1,
                        'files': gif_results,
                        'metadata': segment
                    })
            
            # 生成PNG（关键帧）
            timestamp = segment['start'] + segment.get('duration', 0) / 2
            png_results = self.generate_multi_size_png(
                video_path,
                timestamp,
                os.path.join(output_dir, 'png'),
                base_name
            )
            
            if png_results:
                results.append({
                    'type': 'png',
                    'category': category,
                    'index': i + 1,
                    'files': png_results,
                    'metadata': segment
                })
        
        logger.info(f"✅ 批量生成完成: {len(results)} 个表情包")
        
        return results


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n=== 表情包生成器 V2 - 优化版 ===\n")
    print("特性：")
    print("  • FFmpeg + gifsicle双重优化")
    print("  • 高质量调色板生成")
    print("  • 多级压缩策略")
    print("  • 多尺寸输出")
    print("  • 文件大小控制")
    print()
    
    # 创建生成器
    generator = EmojiGeneratorV2({
        'gif_quality': 'high',
        'fps': 20,
        'max_gif_size_kb': 2000
    })
    
    print("✓ 生成器初始化成功")





















