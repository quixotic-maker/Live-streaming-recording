#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
录屏数据预处理工具

功能：
1. 视频裁剪 - 去除录屏边缘的UI界面
2. OCR识别 - 从评论区提取弹幕
3. 数据整合 - 生成标准弹幕文件

用法：
    python 录屏数据预处理.py --input video.mp4 --output output_dir/
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))


class ScreenRecordingProcessor:
    """录屏数据处理器"""
    
    def __init__(self, 
                 crop_width: float = 0.75,  # 主播画面占比（左侧75%）
                 auto_detect: bool = True,  # 自动检测裁剪区域
                 crop_top: int = 76,  # 顶部白边像素（仅在不自动检测时使用）
                 crop_bottom: int = 61,  # 底部黑边像素（仅在不自动检测时使用）
                 crop_left: int = 3,  # 左侧边缘像素（仅在不自动检测时使用）
                 comment_position: str = 'right',  # 评论区位置
                 ocr_enabled: bool = True):
        """
        初始化
        
        Args:
            crop_width: 主播画面占视频宽度的比例 (0-1)
            auto_detect: 是否自动检测每个视频的裁剪区域
            crop_top: 顶部需要裁掉的像素数（仅在不自动检测时使用）
            crop_bottom: 底部需要裁掉的像素数（仅在不自动检测时使用）
            crop_left: 左侧需要裁掉的像素数（仅在不自动检测时使用）
            comment_position: 评论区位置 ('right', 'left')
            ocr_enabled: 是否启用OCR识别
        """
        self.crop_width = crop_width
        self.auto_detect = auto_detect
        self.crop_top = crop_top
        self.crop_bottom = crop_bottom
        self.crop_left = crop_left
        self.comment_position = comment_position
        self.ocr_enabled = ocr_enabled
        
        # 检查依赖
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查必要的依赖"""
        # 检查FFmpeg
        try:
            subprocess.run(['ffmpeg', '-version'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("FFmpeg 未安装或不可用")
        
        # 检查PaddleOCR（如果启用OCR）
        if self.ocr_enabled:
            try:
                from paddleocr import PaddleOCR
            except ImportError:
                print("⚠️  PaddleOCR 未安装，OCR功能将被禁用")
                print("   安装: pip install paddleocr")
                self.ocr_enabled = False
    
    def get_video_info(self, video_path: str) -> Dict:
        """
        获取视频信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频信息字典
        """
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,duration,bit_rate',
            '-of', 'json',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        info = json.loads(result.stdout)
        
        stream = info['streams'][0]
        return {
            'width': int(stream['width']),
            'height': int(stream['height']),
            'duration': float(stream.get('duration', 0)),
            'bit_rate': int(stream.get('bit_rate', 0))
        }
    
    def _auto_detect_crop_area(self, video_path: str) -> dict:
        """
        自动检测视频的裁剪区域
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            裁剪参数字典 {top, bottom, left, right}
        """
        import cv2
        import numpy as np
        import tempfile
        
        # 提取一帧用于检测
        temp_frame = os.path.join(tempfile.gettempdir(), 'detect_frame.jpg')
        cmd = [
            'ffmpeg', '-i', video_path,
            '-ss', '60',  # 提取第60秒的帧
            '-vframes', '1',
            '-q:v', '2',
            '-y', temp_frame
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 读取图像
        img = cv2.imread(temp_frame)
        if img is None:
            print("⚠️  自动检测失败，使用默认参数")
            return {
                'top': self.crop_top,
                'bottom': self.crop_bottom,
                'left': self.crop_left
            }
        
        height, width = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 检测上边缘（白色区域）
        top_crop = 0
        row_means = np.mean(gray, axis=1)
        for i in range(int(height * 0.1)):
            if row_means[i] < 180:  # 亮度下降，找到内容区域
                top_crop = i
                break
        
        # 检测下边缘（黑色区域）
        bottom_crop = 0
        for i in range(height - 1, int(height * 0.9), -1):
            if row_means[i] > 70:  # 亮度上升，找到内容区域
                bottom_crop = height - i - 1
                break
        
        # 检测左边缘
        col_means = np.mean(gray, axis=0)
        left_crop = 0
        for i in range(int(width * 0.05)):
            if col_means[i] > 100:
                left_crop = i
                break
        
        # 清理临时文件
        try:
            os.remove(temp_frame)
        except:
            pass
        
        return {
            'top': max(top_crop, 0),
            'bottom': max(bottom_crop, 0),
            'left': max(left_crop, 0)
        }
    
    def crop_video(self, 
                   input_path: str, 
                   output_path: str,
                   dry_run: bool = False) -> bool:
        """
        裁剪视频，去除评论区UI
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            dry_run: 只测试不实际执行
            
        Returns:
            是否成功
        """
        print(f"\n{'='*60}")
        print("📹 视频裁剪")
        print(f"{'='*60}")
        
        # 获取视频信息
        info = self.get_video_info(input_path)
        orig_width = info['width']
        orig_height = info['height']
        
        print(f"原始分辨率: {orig_width}x{orig_height}")
        
        # 自动检测或使用固定参数
        if self.auto_detect:
            print("🔍 自动检测裁剪区域...")
            detected = self._auto_detect_crop_area(input_path)
            crop_top = detected['top']
            crop_bottom = detected['bottom']
            crop_left = detected['left']
            print(f"检测结果: 上={crop_top}px, 下={crop_bottom}px, 左={crop_left}px")
        else:
            crop_top = self.crop_top
            crop_bottom = self.crop_bottom
            crop_left = self.crop_left
            print(f"使用固定参数: 上={crop_top}px, 下={crop_bottom}px, 左={crop_left}px")
        
        # 计算裁剪参数
        if self.comment_position == 'right':
            # 右侧是评论区，保留左侧
            crop_w = int(orig_width * self.crop_width) - crop_left
            crop_h = orig_height - crop_top - crop_bottom
            crop_x = crop_left
            crop_y = crop_top
        elif self.comment_position == 'left':
            # 左侧是评论区，保留右侧
            crop_w = int(orig_width * self.crop_width) - crop_left
            crop_h = orig_height - crop_top - crop_bottom
            crop_x = orig_width - crop_w
            crop_y = crop_top
        else:
            raise ValueError(f"不支持的评论区位置: {self.comment_position}")
        
        print(f"裁剪后分辨率: {crop_w}x{crop_h}")
        print(f"裁剪区域: x={crop_x}, y={crop_y}, w={crop_w}, h={crop_h}")
        
        if dry_run:
            print("🔍 [测试模式] 不实际执行")
            return True
        
        # FFmpeg裁剪命令
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', f'crop={crop_w}:{crop_h}:{crop_x}:{crop_y}',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        print(f"执行裁剪...")
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            print(f"✅ 裁剪完成: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 裁剪失败: {e}")
            print(f"错误信息: {e.stderr.decode()}")
            return False
    
    def extract_comment_area(self, 
                            input_path: str, 
                            output_dir: str,
                            sample_interval: int = 1) -> List[str]:
        """
        提取评论区区域的图片用于OCR
        
        Args:
            input_path: 输入视频路径
            output_dir: 输出目录
            sample_interval: 采样间隔（秒）
            
        Returns:
            提取的图片路径列表
        """
        if not self.ocr_enabled:
            print("⚠️  OCR未启用，跳过评论区提取")
            return []
        
        print(f"\n{'='*60}")
        print("📸 提取评论区图片")
        print(f"{'='*60}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取视频信息
        info = self.get_video_info(input_path)
        orig_width = info['width']
        orig_height = info['height']
        duration = info['duration']
        
        # 计算评论区区域
        if self.comment_position == 'right':
            crop_x = int(orig_width * self.crop_width)
            crop_w = orig_width - crop_x
        else:  # left
            crop_x = 0
            crop_w = int(orig_width * (1 - self.crop_width))
        
        crop_h = orig_height
        crop_y = 0
        
        print(f"评论区域: x={crop_x}, y={crop_y}, w={crop_w}, h={crop_h}")
        print(f"采样间隔: {sample_interval}秒")
        print(f"预计帧数: {int(duration / sample_interval)}")
        
        # 提取图片
        frames = []
        for t in range(0, int(duration), sample_interval):
            output_frame = os.path.join(output_dir, f"comment_{t:06d}.jpg")
            
            cmd = [
                'ffmpeg',
                '-ss', str(t),
                '-i', input_path,
                '-vf', f'crop={crop_w}:{crop_h}:{crop_x}:{crop_y}',
                '-vframes', '1',
                '-q:v', '2',
                '-y',
                output_frame
            ]
            
            try:
                subprocess.run(cmd, 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE, 
                             check=True)
                frames.append(output_frame)
                if len(frames) % 10 == 0:
                    print(f"  已提取 {len(frames)} 帧...")
            except subprocess.CalledProcessError:
                continue
        
        print(f"✅ 完成，共提取 {len(frames)} 帧")
        return frames
    
    def ocr_comments(self, 
                    frame_paths: List[str],
                    output_file: str) -> List[Dict]:
        """
        OCR识别评论区文字
        
        Args:
            frame_paths: 图片路径列表
            output_file: 输出弹幕文件路径
            
        Returns:
            识别的弹幕列表
        """
        if not self.ocr_enabled:
            print("⚠️  OCR未启用")
            return []
        
        print(f"\n{'='*60}")
        print("🔍 OCR识别弹幕")
        print(f"{'='*60}")
        
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
        except ImportError:
            print("❌ PaddleOCR 未安装")
            return []
        
        danmaku_list = []
        seen_texts = set()  # 用于去重
        
        for idx, frame_path in enumerate(frame_paths):
            if idx % 10 == 0:
                print(f"  处理进度: {idx}/{len(frame_paths)}")
            
            try:
                # OCR识别
                result = ocr.ocr(frame_path, cls=True)
                
                if not result or not result[0]:
                    continue
                
                # 提取时间戳（从文件名）
                filename = os.path.basename(frame_path)
                timestamp_sec = int(filename.split('_')[1].split('.')[0])
                
                # 提取文字
                for line in result[0]:
                    text = line[1][0]
                    confidence = line[1][1]
                    
                    # 过滤低置信度和重复文本
                    if confidence < 0.5:
                        continue
                    if text in seen_texts:
                        continue
                    
                    seen_texts.add(text)
                    
                    danmaku_list.append({
                        'timestamp': timestamp_sec,
                        'type': 'chat',
                        'user': 'OCR提取',
                        'content': text,
                        'confidence': confidence,
                        'source': 'ocr'
                    })
            
            except Exception as e:
                print(f"  ⚠️  处理失败: {frame_path} - {e}")
                continue
        
        # 按时间戳排序
        danmaku_list.sort(key=lambda x: x['timestamp'])
        
        # 保存为JSONL格式
        with open(output_file, 'w', encoding='utf-8') as f:
            for danmaku in danmaku_list:
                f.write(json.dumps(danmaku, ensure_ascii=False) + '\n')
        
        print(f"✅ 完成，共识别 {len(danmaku_list)} 条弹幕")
        print(f"   输出: {output_file}")
        
        return danmaku_list
    
    def process(self, 
                input_path: str, 
                output_dir: str,
                extract_danmaku: bool = True,
                dry_run: bool = False) -> Dict:
        """
        完整处理流程
        
        Args:
            input_path: 输入视频路径
            output_dir: 输出目录
            extract_danmaku: 是否提取弹幕
            dry_run: 测试模式
            
        Returns:
            处理结果字典
        """
        print(f"\n{'='*60}")
        print("🚀 录屏数据预处理")
        print(f"{'='*60}")
        print(f"输入视频: {input_path}")
        print(f"输出目录: {output_dir}")
        print(f"{'='*60}\n")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 准备输出路径
        base_name = Path(input_path).stem
        cropped_video = os.path.join(output_dir, f"{base_name}_cropped.mp4")
        danmaku_file = os.path.join(output_dir, f"{base_name}_danmaku.jsonl")
        frames_dir = os.path.join(output_dir, "comment_frames")
        
        result = {
            'input': input_path,
            'cropped_video': None,
            'danmaku_file': None,
            'danmaku_count': 0,
            'success': False
        }
        
        # 步骤1: 裁剪视频
        if self.crop_video(input_path, cropped_video, dry_run):
            result['cropped_video'] = cropped_video
        else:
            return result
        
        # 步骤2: 提取弹幕（如果启用）
        if extract_danmaku and self.ocr_enabled and not dry_run:
            # 提取评论区图片
            frames = self.extract_comment_area(input_path, frames_dir, sample_interval=2)
            
            if frames:
                # OCR识别
                danmaku_list = self.ocr_comments(frames, danmaku_file)
                result['danmaku_file'] = danmaku_file
                result['danmaku_count'] = len(danmaku_list)
        
        result['success'] = True
        return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='录屏数据预处理工具')
    parser.add_argument('--input', '-i', required=True, help='输入视频文件')
    parser.add_argument('--output', '-o', required=True, help='输出目录')
    parser.add_argument('--crop-width', type=float, default=0.75, 
                       help='主播画面占比 (0-1)，默认0.75')
    parser.add_argument('--no-auto-detect', action='store_true',
                       help='禁用自动检测，使用固定参数')
    parser.add_argument('--crop-top', type=int, default=76,
                       help='顶部白边像素，默认76（仅在禁用自动检测时使用）')
    parser.add_argument('--crop-bottom', type=int, default=61,
                       help='底部黑边像素，默认61（仅在禁用自动检测时使用）')
    parser.add_argument('--crop-left', type=int, default=3,
                       help='左侧边缘像素，默认3（仅在禁用自动检测时使用）')
    parser.add_argument('--comment-position', choices=['right', 'left'], 
                       default='right', help='评论区位置，默认right')
    parser.add_argument('--no-ocr', action='store_true', 
                       help='禁用OCR识别')
    parser.add_argument('--no-danmaku', action='store_true',
                       help='不提取弹幕')
    parser.add_argument('--dry-run', action='store_true',
                       help='测试模式，不实际执行')
    
    args = parser.parse_args()
    
    # 创建处理器
    processor = ScreenRecordingProcessor(
        crop_width=args.crop_width,
        auto_detect=not args.no_auto_detect,
        crop_top=args.crop_top,
        crop_bottom=args.crop_bottom,
        crop_left=args.crop_left,
        comment_position=args.comment_position,
        ocr_enabled=not args.no_ocr
    )
    
    # 处理
    result = processor.process(
        args.input,
        args.output,
        extract_danmaku=not args.no_danmaku,
        dry_run=args.dry_run
    )
    
    # 输出结果
    print(f"\n{'='*60}")
    print("✅ 处理完成")
    print(f"{'='*60}")
    print(f"裁剪视频: {result.get('cropped_video', '未生成')}")
    if result.get('danmaku_file'):
        print(f"弹幕文件: {result['danmaku_file']}")
        print(f"弹幕数量: {result['danmaku_count']}")
    print(f"{'='*60}\n")
    
    return 0 if result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())

