#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量提取关键帧截图工具

功能：
1. 固定间隔截图（每N秒）
2. 场景变化检测截图
3. 基于素材时间点截图（歌曲、礼物、精彩时刻）
4. 自动分类保存和生成索引
"""

import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime


class KeyFrameExtractor:
    """关键帧提取器"""
    
    def __init__(self, video_path: str, output_dir: str, quality: int = 95, 
                 format: str = 'png'):
        """
        初始化提取器
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            quality: JPEG质量（1-100，默认95）或PNG压缩（0-9，默认3）
            format: 输出格式 'png'（推荐，无损） 或 'jpg'（默认png）
        """
        self.video_path = video_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.quality = quality
        self.format = format.lower()
        
        # 打开视频
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        # 视频信息
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"视频信息:")
        print(f"  分辨率: {self.width}x{self.height}")
        print(f"  帧率: {self.fps:.2f} fps")
        print(f"  总帧数: {self.total_frames}")
        print(f"  时长: {self.duration/60:.1f} 分钟")
    
    def extract_by_interval(self, interval: int = 30, quality: int = None) -> List[Dict]:
        """
        按固定间隔提取截图
        
        Args:
            interval: 间隔秒数
            quality: JPEG质量 (0-100)
            
        Returns:
            截图信息列表
        """
        print(f"\n[模式1] 固定间隔截图 (每{interval}秒)")
        print("-" * 70)
        
        output_subdir = self.output_dir / "固定间隔"
        output_subdir.mkdir(exist_ok=True)
        
        screenshots = []
        frame_interval = int(interval * self.fps)
        
        for frame_num in range(0, self.total_frames, frame_interval):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = self.cap.read()
            
            if not ret:
                break
            
            timestamp = frame_num / self.fps
            
            # 使用指定格式
            ext = 'png' if self.format == 'png' else 'jpg'
            filename = f"screenshot_{int(timestamp):06d}s.{ext}"
            filepath = output_subdir / filename
            
            # 锐化处理（可选，提升清晰度）
            sharpened_frame = self._sharpen_frame(frame)
            
            # 保存截图
            self._save_image(str(filepath), sharpened_frame, quality or self.quality)
            
            screenshots.append({
                "time": timestamp,
                "frame": frame_num,
                "file": str(filepath),
                "type": "interval"
            })
            
            if len(screenshots) % 10 == 0:
                print(f"  已提取 {len(screenshots)} 张...")
        
        print(f"✓ 完成，共 {len(screenshots)} 张")
        return screenshots
    
    def extract_scene_changes(self, threshold: float = 30.0, min_interval: int = 5,
                               quality: int = 95) -> List[Dict]:
        """
        基于场景变化检测提取截图
        
        Args:
            threshold: 场景变化阈值（越小越敏感）
            min_interval: 最小间隔秒数（避免过密）
            quality: JPEG质量
            
        Returns:
            截图信息列表
        """
        print(f"\n[模式2] 场景变化检测 (阈值={threshold:.1f})")
        print("-" * 70)
        
        output_subdir = self.output_dir / "场景变化"
        output_subdir.mkdir(exist_ok=True)
        
        screenshots = []
        prev_frame = None
        last_screenshot_time = -min_interval
        
        frame_num = 0
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            timestamp = frame_num / self.fps
            
            # 计算与上一帧的差异
            if prev_frame is not None:
                diff = cv2.absdiff(
                    cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                    cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                )
                diff_score = np.mean(diff)
                
                # 场景变化检测
                if (diff_score > threshold and 
                    timestamp - last_screenshot_time >= min_interval):
                    
                    ext = 'png' if self.format == 'png' else 'jpg'
                    filename = f"scene_{int(timestamp):06d}s_diff{diff_score:.1f}.{ext}"
                    filepath = output_subdir / filename
                    
                    # 锐化并保存
                    sharpened_frame = self._sharpen_frame(frame)
                    self._save_image(str(filepath), sharpened_frame, quality or self.quality)
                    
                    screenshots.append({
                        "time": timestamp,
                        "frame": frame_num,
                        "file": str(filepath),
                        "type": "scene_change",
                        "diff_score": float(diff_score)
                    })
                    
                    last_screenshot_time = timestamp
                    
                    if len(screenshots) % 10 == 0:
                        print(f"  已提取 {len(screenshots)} 张...")
            
            prev_frame = frame.copy()
            frame_num += 1
        
        print(f"✓ 完成，共 {len(screenshots)} 张")
        return screenshots
    
    def extract_from_timestamps(self, timestamps: List[Dict], 
                                 category: str = "素材",
                                 quality: int = 95) -> List[Dict]:
        """
        根据时间点列表提取截图
        
        Args:
            timestamps: 时间点列表 [{"time": 10.5, "label": "歌曲1"}]
            category: 分类名称
            quality: JPEG质量
            
        Returns:
            截图信息列表
        """
        print(f"\n[模式3] 素材时间点截图 ({category})")
        print("-" * 70)
        
        output_subdir = self.output_dir / category
        output_subdir.mkdir(exist_ok=True)
        
        screenshots = []
        
        for i, item in enumerate(timestamps):
            timestamp = item["time"]
            label = item.get("label", f"item_{i}")
            
            # 定位到指定时间
            frame_num = int(timestamp * self.fps)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = self.cap.read()
            
            if not ret:
                print(f"  ⚠ 无法读取时间点 {timestamp}s")
                continue
            
            # 清理文件名
            safe_label = "".join(c if c.isalnum() or c in "._- " else "_" for c in label)
            ext = 'png' if self.format == 'png' else 'jpg'
            filename = f"{int(timestamp):06d}s_{safe_label}.{ext}"
            filepath = output_subdir / filename
            
            # 锐化并保存
            sharpened_frame = self._sharpen_frame(frame)
            self._save_image(str(filepath), sharpened_frame, quality or self.quality)
            
            screenshots.append({
                "time": timestamp,
                "frame": frame_num,
                "file": str(filepath),
                "type": "material",
                "label": label,
                "category": category
            })
            
            if (i + 1) % 10 == 0:
                print(f"  已提取 {i + 1}/{len(timestamps)} 张...")
        
        print(f"✓ 完成，共 {len(screenshots)} 张")
        return screenshots
    
    def generate_thumbnail_grid(self, screenshots: List[Dict], 
                                 output_file: str = "preview_grid.jpg",
                                 grid_size: Tuple[int, int] = (4, 3),
                                 thumb_size: Tuple[int, int] = (320, 180)):
        """
        生成缩略图网格预览
        
        Args:
            screenshots: 截图列表
            output_file: 输出文件名
            grid_size: 网格大小 (列, 行)
            thumb_size: 单个缩略图大小
        """
        print(f"\n生成预览网格...")
        
        cols, rows = grid_size
        per_page = cols * rows
        
        for page, start_idx in enumerate(range(0, len(screenshots), per_page)):
            page_screenshots = screenshots[start_idx:start_idx + per_page]
            
            # 创建空白画布
            canvas_width = cols * thumb_size[0]
            canvas_height = rows * thumb_size[1]
            canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
            
            for idx, screenshot in enumerate(page_screenshots):
                row = idx // cols
                col = idx % cols
                
                # 读取图片
                img = cv2.imread(screenshot["file"])
                if img is None:
                    continue
                
                # 调整大小
                thumb = cv2.resize(img, thumb_size)
                
                # 添加时间戳文本
                time_str = f"{int(screenshot['time']//60):02d}:{int(screenshot['time']%60):02d}"
                cv2.putText(thumb, time_str, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(thumb, time_str, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
                
                # 放置到画布
                y_start = row * thumb_size[1]
                x_start = col * thumb_size[0]
                canvas[y_start:y_start+thumb_size[1], 
                       x_start:x_start+thumb_size[0]] = thumb
            
            # 保存
            if len(screenshots) > per_page:
                page_file = self.output_dir / f"preview_grid_page{page+1}.jpg"
            else:
                page_file = self.output_dir / output_file
            
            cv2.imwrite(str(page_file), canvas, [cv2.IMWRITE_JPEG_QUALITY, 85])
            print(f"  ✓ 保存预览: {page_file}")
    
    def save_index(self, all_screenshots: List[Dict], index_file: str = "截图索引.json"):
        """
        保存截图索引
        
        Args:
            all_screenshots: 所有截图列表
            index_file: 索引文件名
        """
        index_path = self.output_dir / index_file
        
        index_data = {
            "video_path": self.video_path,
            "video_duration": self.duration,
            "total_screenshots": len(all_screenshots),
            "extract_time": datetime.now().isoformat(),
            "screenshots": sorted(all_screenshots, key=lambda x: x["time"])
        }
        
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 索引已保存: {index_path}")
        
        # 也生成文本版
        txt_path = self.output_dir / "截图索引.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("关键帧截图索引\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"视频: {self.video_path}\n")
            f.write(f"总截图数: {len(all_screenshots)}\n")
            f.write(f"提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 按类型分组
            by_type = {}
            for screenshot in all_screenshots:
                t = screenshot.get("type", "unknown")
                by_type.setdefault(t, []).append(screenshot)
            
            f.write("分类统计:\n")
            f.write("-" * 70 + "\n")
            for t, items in by_type.items():
                f.write(f"  {t}: {len(items)} 张\n")
            
            f.write("\n详细列表:\n")
            f.write("-" * 70 + "\n")
            for i, screenshot in enumerate(sorted(all_screenshots, key=lambda x: x["time"]), 1):
                time_str = f"{int(screenshot['time']//60):02d}:{int(screenshot['time']%60):02d}"
                f.write(f"{i:4d}. {time_str} - {screenshot.get('type', '?')} - {Path(screenshot['file']).name}\n")
        
        print(f"✓ 文本索引: {txt_path}")
    
    def _sharpen_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        锐化处理，提升图片清晰度
        
        Args:
            frame: 输入帧
        
        Returns:
            锐化后的帧
        """
        # 锐化核
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(frame, -1, kernel)
        return sharpened
    
    def _save_image(self, filepath: str, frame: np.ndarray, quality: int):
        """
        保存图片（支持PNG和JPEG）
        
        Args:
            filepath: 输出文件路径
            frame: 图片帧
            quality: 质量参数
        """
        if self.format == 'png':
            # PNG格式：无损压缩，quality为压缩级别0-9
            # 0=无压缩（最快），9=最大压缩（最慢）
            # 默认3是一个不错的平衡点
            png_compression = min(9, max(0, 9 - quality // 10))  # 质量95 → 压缩0
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_PNG_COMPRESSION, png_compression])
        else:
            # JPEG格式：有损压缩，quality为1-100
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    
    def close(self):
        """释放资源"""
        self.cap.release()


def load_material_timestamps(material_dir: str) -> Dict[str, List[Dict]]:
    """
    从素材库加载时间点
    
    Args:
        material_dir: 素材目录
        
    Returns:
        分类时间点字典
    """
    material_dir = Path(material_dir)
    timestamps = {}
    
    # 歌曲
    song_file = material_dir / "歌曲素材库" / "歌曲列表.json"
    if song_file.exists():
        with open(song_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        timestamps["歌曲"] = [
            {"time": song["start"], "label": song.get("title", f"歌曲{i}")}
            for i, song in enumerate(data.get("songs", []), 1)
        ]
    
    # 礼物感谢
    gift_file = material_dir / "素材库_最新" / "gift_素材.json"
    if gift_file.exists():
        with open(gift_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        segments = data.get("segments", []) if isinstance(data, dict) else data
        timestamps["礼物感谢"] = [
            {"time": seg["start"], "label": f"感谢_{i}"}
            for i, seg in enumerate(segments[:50], 1)  # 限制50个
        ]
    
    return timestamps


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='批量提取关键帧截图工具')
    parser.add_argument('--video', type=str, help='视频文件路径')
    parser.add_argument('--output', type=str, help='输出目录')
    parser.add_argument('--material_dir', type=str, help='素材目录（用于模式3）')
    parser.add_argument('--mode', type=str, default='4', 
                       help='提取模式: 1=固定间隔, 2=场景变化, 3=素材时间点, 4=全部 (默认4-混合模式)')
    parser.add_argument('--interval', type=int, default=10, help='固定间隔（秒，默认10，提升到10获得更多关键帧）')
    parser.add_argument('--quality', type=int, default=95, help='图片质量（1-100，默认95）')
    parser.add_argument('--format', type=str, default='png', choices=['png', 'jpg'],
                       help='输出格式: png=无损（推荐），jpg=有损（默认png）')
    args = parser.parse_args()
    
    print("=" * 70)
    print("批量提取关键帧截图工具")
    print("=" * 70)
    
    # 配置（优先使用命令行参数）
    video_path = args.video or "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4"
    output_dir = args.output or os.path.expanduser("~/shanshan_materials/关键帧截图")
    material_dir = args.material_dir or os.path.expanduser("~/shanshan_materials")
    
    # 验证视频文件
    if not os.path.exists(video_path):
        print(f"错误: 视频文件不存在: {video_path}")
        print("\n请使用 --video 参数指定正确的视频路径")
        return
    
    print(f"\n视频文件: {video_path}")
    print(f"输出目录: {output_dir}")
    print(f"提取模式: {args.mode}")
    print(f"输出格式: {args.format.upper()}")
    print(f"固定间隔: {args.interval}秒\n")
    
    # 创建提取器
    extractor = KeyFrameExtractor(video_path, output_dir, quality=args.quality, format=args.format)
    
    all_screenshots = []
    
    # 使用命令行参数指定的模式
    choice = args.mode
    
    try:
        
        if choice in ["1", "4"]:
            screenshots = extractor.extract_by_interval(interval=args.interval)
            all_screenshots.extend(screenshots)
        
        if choice in ["2", "4"]:
            # 重置视频位置
            extractor.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            screenshots = extractor.extract_scene_changes(threshold=30.0, min_interval=10)
            all_screenshots.extend(screenshots)
        
        if choice in ["3", "4"]:
            # 加载素材时间点
            material_timestamps = load_material_timestamps(material_dir)
            
            for category, timestamps in material_timestamps.items():
                if timestamps:
                    screenshots = extractor.extract_from_timestamps(timestamps, category)
                    all_screenshots.extend(screenshots)
        
        # 生成预览和索引
        if all_screenshots:
            print(f"\n总共提取了 {len(all_screenshots)} 张截图")
            
            # 生成缩略图网格
            extractor.generate_thumbnail_grid(all_screenshots)
            
            # 保存索引
            extractor.save_index(all_screenshots)
            
            print("\n" + "=" * 70)
            print("✅ 截图提取完成！")
            print("=" * 70)
            print(f"\n输出目录: {output_dir}")
            print(f"  - 固定间隔/")
            print(f"  - 场景变化/")
            print(f"  - 歌曲/")
            print(f"  - 礼物感谢/")
            print(f"  - preview_grid.jpg (预览)")
            print(f"  - 截图索引.json")
            print(f"  - 截图索引.txt")
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
    finally:
        extractor.close()


if __name__ == "__main__":
    main()



