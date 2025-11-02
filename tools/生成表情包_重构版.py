#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表情包生成系统 - 重构版

特点：
1. 使用FFmpeg + gifsicle生成高质量GIF
2. 完善的错误处理和验证
3. 标准化的目录结构
4. 详细的进度报告
"""

import os
import sys
import json
import subprocess
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


class OptimizedGIFGenerator:
    """优化的GIF生成器（使用FFmpeg + gifsicle）"""
    
    def __init__(self, config=None):
        self.config = config or {
            "target_size_kb": 800,
            "max_colors": 256,
            "fps": 20,
            "quality": 90
        }
    
    def extract_frames(self, video_path, start, end, target_fps=20):
        """从视频提取帧"""
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        start_frame = int(start * video_fps)
        end_frame = int(end * video_fps)
        
        # 计算采样间隔
        frame_interval = max(1, int(video_fps / target_fps))
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        current_frame = start_frame
        while current_frame < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            
            if (current_frame - start_frame) % frame_interval == 0:
                frames.append(frame)
            
            current_frame += 1
        
        cap.release()
        
        return frames
    
    def create_gif_with_ffmpeg(self, frames, output_path, width, height):
        """
        使用FFmpeg创建高质量GIF
        
        FFmpeg的palette方法可以生成256色的高质量调色板
        """
        import tempfile
        
        # 创建临时目录存放帧
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. 保存帧为PNG序列
            for i, frame in enumerate(frames):
                # 调整大小
                resized = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
                frame_path = os.path.join(temp_dir, f"frame_{i:04d}.png")
                cv2.imwrite(frame_path, resized)
            
            # 2. 使用FFmpeg生成GIF（两步法：先生成调色板，再应用）
            palette_path = os.path.join(temp_dir, "palette.png")
            temp_gif = os.path.join(temp_dir, "output.gif")
            
            # 生成调色板
            cmd_palette = [
                'ffmpeg', '-y',
                '-framerate', str(self.config["fps"]),
                '-i', os.path.join(temp_dir, 'frame_%04d.png'),
                '-vf', f'palettegen=max_colors={self.config["max_colors"]}:stats_mode=full',
                palette_path
            ]
            
            subprocess.run(cmd_palette, check=True, capture_output=True)
            
            # 使用调色板生成GIF
            cmd_gif = [
                'ffmpeg', '-y',
                '-framerate', str(self.config["fps"]),
                '-i', os.path.join(temp_dir, 'frame_%04d.png'),
                '-i', palette_path,
                '-lavfi', 'paletteuse=dither=sierra2_4a',
                '-loop', '0',
                temp_gif
            ]
            
            subprocess.run(cmd_gif, check=True, capture_output=True)
            
            # 3. 使用gifsicle优化（如果可用）
            if self._check_gifsicle():
                self._optimize_with_gifsicle(temp_gif, output_path)
            else:
                # gifsicle不可用，直接复制
                import shutil
                shutil.copy(temp_gif, output_path)
    
    def _check_gifsicle(self):
        """检查gifsicle是否可用"""
        try:
            subprocess.run(['gifsicle', '--version'], 
                          capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _optimize_with_gifsicle(self, input_path, output_path):
        """使用gifsicle优化GIF"""
        target_kb = self.config["target_size_kb"]
        
        # 尝试不同的优化级别
        optimizations = [
            {'lossy': 20, 'colors': 256},  # 温和优化
            {'lossy': 30, 'colors': 224},  # 中等优化
            {'lossy': 40, 'colors': 192},  # 较强优化
            {'lossy': 50, 'colors': 160},  # 强优化
        ]
        
        for opt in optimizations:
            cmd = [
                'gifsicle',
                '--optimize=3',
                f'--lossy={opt["lossy"]}',
                f'--colors={opt["colors"]}',
                '--careful',
                input_path,
                '-o', output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # 检查文件大小
            size_kb = os.path.getsize(output_path) / 1024
            
            if size_kb <= target_kb:
                # 满足要求
                return
        
        # 如果都不满足，使用最强优化的结果
    
    def generate_multi_size(self, frames, output_dir, base_name):
        """生成多种尺寸的GIF"""
        sizes = {
            "240x240": (240, 240),
            "300x300": (300, 300),
            "512x512": (512, 512)
        }
        
        results = {}
        
        for size_name, (width, height) in sizes.items():
            output_path = os.path.join(output_dir, f"{base_name}_{size_name}.gif")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            try:
                self.create_gif_with_ffmpeg(frames, output_path, width, height)
                
                # 验证文件
                if os.path.exists(output_path):
                    size_kb = os.path.getsize(output_path) / 1024
                    results[size_name] = {
                        "path": output_path,
                        "size_kb": size_kb,
                        "colors": self.config["max_colors"]
                    }
                else:
                    results[size_name] = {"error": "文件未生成"}
                    
            except Exception as e:
                results[size_name] = {"error": str(e)}
        
        return results
    
    def create_static_image(self, frames, output_path):
        """创建高清静态图"""
        # 选择中间帧
        best_frame = frames[len(frames) // 2]
        
        # 调整到合适的大小
        h, w = best_frame.shape[:2]
        max_size = 1920
        if w > max_size or h > max_size:
            scale = max_size / max(w, h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            best_frame = cv2.resize(best_frame, (new_w, new_h), 
                                   interpolation=cv2.INTER_AREA)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, best_frame, 
                   [cv2.IMWRITE_PNG_COMPRESSION, 9])
        
        return output_path


class EmojiDetector:
    """表情包检测器（基于已有分类数据）"""
    
    def __init__(self, date="2025-10-30"):
        self.date = date
        self.base_dir = os.path.expanduser("~/shanshan_materials")
        
        # 加载分类数据
        classified_dir = os.path.join(self.base_dir, "03_内容分类", date)
        
        with open(os.path.join(classified_dir, "gift_素材.json"), 'r', encoding='utf-8') as f:
            gift_data = json.load(f)
            self.gift_segments = gift_data.get("segments", []) if isinstance(gift_data, dict) else gift_data
        
        with open(os.path.join(classified_dir, "chat_素材.json"), 'r', encoding='utf-8') as f:
            chat_data = json.load(f)
            self.chat_segments = chat_data.get("segments", []) if isinstance(chat_data, dict) else chat_data
    
    def detect_thank_moments(self, max_count=50):
        """检测感谢表情"""
        candidates = []
        
        for seg in self.gift_segments[:200]:
            text = seg.get("text", "")
            
            if "谢谢" in text or "感谢" in text:
                # 只取前2秒
                candidates.append({
                    "start": seg["start"],
                    "end": min(seg["start"] + 2.0, seg["end"]),
                    "text": text,
                    "type": "thank"
                })
                
                if len(candidates) >= max_count:
                    break
        
        return candidates
    
    def detect_cute_moments(self, max_count=50):
        """检测可爱表情"""
        cute_keywords = [
            "哈哈", "嘿嘿", "嘻嘻", "呵呵",
            "哎呀", "哇", "呀",
            "爱你", "亲亲", "么么", "抱抱", "比心",
            "开心", "高兴",
            "宝宝", "宝贝", "乖"
        ]
        
        candidates = []
        
        for seg in self.chat_segments[:500]:
            text = seg.get("text", "")
            
            # 检查关键词
            matches = [kw for kw in cute_keywords if kw in text]
            
            if len(matches) >= 1:
                candidates.append({
                    "start": seg["start"],
                    "end": min(seg["start"] + 2.5, seg["end"]),
                    "text": text,
                    "keywords": matches,
                    "type": "cute"
                })
                
                if len(candidates) >= max_count:
                    break
        
        return candidates
    
    def detect_dance_moments(self, max_count=30):
        """检测手势舞（简单策略：前60分钟均匀采样）"""
        candidates = []
        
        # 在前60分钟，每2分钟取一个2秒片段
        for i in range(0, 3600, 120):  # 60分钟
            candidates.append({
                "start": i,
                "end": i + 2.0,
                "text": "手势舞片段",
                "type": "dance"
            })
            
            if len(candidates) >= max_count:
                break
        
        return candidates


class EmojiGenerationPipeline:
    """表情包生成流水线"""
    
    def __init__(self, video_path, date="2025-10-30"):
        self.video_path = video_path
        self.date = date
        self.base_dir = os.path.expanduser("~/shanshan_materials")
        
        # 输出目录（标准化）
        self.output_dir = os.path.join(
            self.base_dir,
            "04_素材生成",
            date,
            "emojis"
        )
        
        # 创建子目录
        self.gifs_dir = os.path.join(self.output_dir, "gifs")
        self.images_dir = os.path.join(self.output_dir, "images")
        self.metadata_dir = os.path.join(self.output_dir, "metadata")
        
        for d in [self.gifs_dir, self.images_dir, self.metadata_dir]:
            os.makedirs(d, exist_ok=True)
        
        # 初始化组件
        self.gif_generator = OptimizedGIFGenerator()
        self.detector = EmojiDetector(date)
    
    def run(self):
        """运行完整流程"""
        print("\n" + "="*80)
        print("表情包生成系统 - 重构版")
        print("="*80)
        print(f"\n视频: {self.video_path}")
        print(f"日期: {self.date}")
        print(f"输出: {self.output_dir}")
        print()
        
        # 步骤1: 检测候选
        print("[步骤1] 检测表情包候选...")
        print("-" * 80)
        
        thank_moments = self.detector.detect_thank_moments(max_count=50)
        cute_moments = self.detector.detect_cute_moments(max_count=50)
        dance_moments = self.detector.detect_dance_moments(max_count=30)
        
        print(f"✓ 感谢表情: {len(thank_moments)}个")
        print(f"✓ 可爱表情: {len(cute_moments)}个")
        print(f"✓ 手势舞: {len(dance_moments)}个")
        print(f"✓ 总计: {len(thank_moments) + len(cute_moments) + len(dance_moments)}个")
        print()
        
        # 步骤2: 生成表情包
        print("[步骤2] 生成表情包...")
        print("-" * 80)
        
        all_moments = {
            "thank": thank_moments,
            "cute": cute_moments,
            "dance": dance_moments
        }
        
        results = {
            "thank": [],
            "cute": [],
            "dance": []
        }
        
        total_count = sum(len(moments) for moments in all_moments.values())
        current = 0
        
        for emoji_type, moments in all_moments.items():
            print(f"\n生成 {emoji_type} 类型...")
            
            for i, moment in enumerate(moments, 1):
                current += 1
                base_name = f"emoji_{emoji_type}_{i:03d}"
                
                print(f"[{current}/{total_count}] {base_name}...", end="", flush=True)
                
                try:
                    # 提取帧
                    frames = self.gif_generator.extract_frames(
                        self.video_path,
                        moment["start"],
                        moment["end"]
                    )
                    
                    if len(frames) == 0:
                        print(" ✗ 无法提取帧")
                        continue
                    
                    # 生成多尺寸GIF
                    type_gifs_dir = os.path.join(self.gifs_dir, emoji_type)
                    gif_results = self.gif_generator.generate_multi_size(
                        frames,
                        type_gifs_dir,
                        base_name
                    )
                    
                    # 生成静态图
                    type_images_dir = os.path.join(self.images_dir, emoji_type)
                    image_path = os.path.join(type_images_dir, f"{base_name}_hd.png")
                    self.gif_generator.create_static_image(frames, image_path)
                    
                    # 保存元数据
                    metadata = {
                        "name": base_name,
                        "type": emoji_type,
                        "source": {
                            "video": self.video_path,
                            "start": moment["start"],
                            "end": moment["end"],
                            "text": moment.get("text", "")
                        },
                        "generated": {
                            "gifs": gif_results,
                            "image": image_path,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    
                    metadata_path = os.path.join(
                        self.metadata_dir,
                        emoji_type,
                        f"{base_name}_metadata.json"
                    )
                    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
                    
                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
                    
                    results[emoji_type].append(metadata)
                    
                    # 显示文件大小
                    sizes = [r.get("size_kb", 0) for r in gif_results.values() 
                            if "size_kb" in r]
                    if sizes:
                        avg_size = sum(sizes) / len(sizes)
                        print(f" ✓ (平均 {avg_size:.0f}KB)")
                    else:
                        print(" ✓")
                    
                except Exception as e:
                    print(f" ✗ {e}")
                    import traceback
                    traceback.print_exc()
        
        # 步骤3: 生成总索引
        print("\n[步骤3] 生成索引...")
        print("-" * 80)
        
        index_path = os.path.join(self.output_dir, "index.json")
        
        index_data = {
            "date": self.date,
            "video": self.video_path,
            "generated_at": datetime.now().isoformat(),
            "statistics": {
                "thank": len(results["thank"]),
                "cute": len(results["cute"]),
                "dance": len(results["dance"]),
                "total": len(results["thank"]) + len(results["cute"]) + len(results["dance"])
            },
            "emojis": results
        }
        
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 索引已保存: {index_path}")
        
        # 生成报告
        report_path = os.path.join(self.output_dir, "generation_report.txt")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("表情包生成报告\n")
            f.write("="*80 + "\n\n")
            f.write(f"日期: {self.date}\n")
            f.write(f"视频: {self.video_path}\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("统计信息:\n")
            f.write(f"  感谢表情: {len(results['thank'])}个\n")
            f.write(f"  可爱表情: {len(results['cute'])}个\n")
            f.write(f"  手势舞: {len(results['dance'])}个\n")
            f.write(f"  总计: {index_data['statistics']['total']}个\n\n")
            f.write(f"输出目录: {self.output_dir}\n")
            f.write(f"  - GIF动图: {self.gifs_dir}\n")
            f.write(f"  - 静态图: {self.images_dir}\n")
            f.write(f"  - 元数据: {self.metadata_dir}\n")
        
        print(f"✓ 报告已保存: {report_path}")
        
        # 完成
        print("\n" + "="*80)
        print("✅ 表情包生成完成！")
        print("="*80)
        print(f"\n📊 统计:")
        print(f"  感谢表情: {len(results['thank'])}个")
        print(f"  可爱表情: {len(results['cute'])}个")
        print(f"  手势舞: {len(results['dance'])}个")
        print(f"  总计: {index_data['statistics']['total']}个")
        print(f"\n📁 输出目录: {self.output_dir}")
        print(f"\n下一步:")
        print(f"  1. 查看GIF: ls -lh {self.gifs_dir}/")
        print(f"  2. 查看索引: cat {index_path}")
        print(f"  3. 查看报告: cat {report_path}")
        print()


def main():
    # 配置
    video_path = "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4"
    date = "2025-10-30"
    
    # 检查视频
    if not os.path.exists(video_path):
        print(f"✗ 视频不存在: {video_path}")
        return
    
    # 确认
    print()
    print("准备生成表情包（重构版）")
    print(f"视频: {video_path}")
    print(f"日期: {date}")
    print()
    choice = input("确认开始？[y/N]: ").strip().lower()
    
    if choice != 'y':
        print("已取消")
        return
    
    # 运行
    pipeline = EmojiGenerationPipeline(video_path, date)
    pipeline.run()


if __name__ == "__main__":
    main()



