#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表情包生成器 - 从视频生成多规格GIF和高清图片

功能：
1. 从视频提取帧序列
2. 生成多规格GIF（240x240, 300x300, 512x512）
3. 生成高清静态图
4. 压缩优化到指定大小
5. 添加元数据
"""

import cv2
import numpy as np
from PIL import Image, ImageSequence
import imageio
import os
import json
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmojiGenerator:
    """
    表情包生成器
    
    功能：
    - 从视频片段生成GIF动图
    - 生成多种规格（适配不同平台）
    - 压缩优化文件大小
    - 生成高清静态图
    """
    
    # 抖音表情包推荐规格
    DOUYIN_SPECS = {
        "small": (240, 240),      # 小尺寸，快速加载
        "medium": (300, 300),     # 中等尺寸，常用
        "large": (512, 512)       # 大尺寸，高清
    }
    
    # 通用表情包规格
    GENERAL_SPECS = {
        "normal": (480, 480),
        "large": (720, 720),
        "xlarge": (1080, 1080)
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化表情包生成器
        
        Args:
            config: 配置参数字典
        """
        default_config = {
            "default_fps": 15,              # 默认GIF帧率
            "max_size_kb": 1000,            # 最大文件大小（KB）
            "quality": 85,                  # 图片质量（1-100）
            "optimize": True,               # 是否优化
            "loop": 0,                      # 循环次数（0=无限循环）
            "resize_method": "lanczos",     # 缩放方法
            "hd_size": (1920, 1080)        # 高清图片尺寸
        }
        
        self.config = {**default_config, **(config or {})}
        logger.info(f"EmojiGenerator initialized with config: {self.config}")
    
    def extract_frames(
        self,
        video_path: str,
        start: float,
        end: float,
        fps: Optional[int] = None
    ) -> List[np.ndarray]:
        """
        从视频提取帧序列
        
        Args:
            video_path: 视频路径
            start: 开始时间（秒）
            end: 结束时间（秒）
            fps: 目标帧率，None使用默认值
        
        Returns:
            帧列表（numpy数组）
        """
        if fps is None:
            fps = self.config["default_fps"]
        
        logger.info(f"提取帧: {start:.2f}s - {end:.2f}s, fps={fps}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        
        # 计算需要提取的帧
        start_frame = int(start * video_fps)
        end_frame = int(end * video_fps)
        total_frames = end_frame - start_frame
        
        # 计算采样间隔
        sample_interval = int(video_fps / fps)
        if sample_interval < 1:
            sample_interval = 1
        
        frames = []
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        frame_idx = 0
        while frame_idx < total_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 按采样间隔提取帧
            if frame_idx % sample_interval == 0:
                # OpenCV读取的是BGR，转换为RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
            
            frame_idx += 1
        
        cap.release()
        
        logger.info(f"提取完成: 共 {len(frames)} 帧")
        
        return frames
    
    def create_gif(
        self,
        frames: List[np.ndarray],
        output_path: str,
        size: Tuple[int, int],
        max_size_kb: Optional[int] = None,
        fps: Optional[int] = None
    ) -> Dict:
        """
        创建GIF文件
        
        Args:
            frames: 帧列表
            output_path: 输出路径
            size: 目标尺寸 (width, height)
            max_size_kb: 最大文件大小（KB），None使用配置值
            fps: 帧率，None使用配置值
        
        Returns:
            生成信息：
            {
                "path": "output.gif",
                "size": (240, 240),
                "frames": 30,
                "duration": 2.0,
                "file_size_kb": 450,
                "fps": 15
            }
        """
        if not frames:
            raise ValueError("帧列表为空")
        
        if fps is None:
            fps = self.config["default_fps"]
        
        if max_size_kb is None:
            max_size_kb = self.config["max_size_kb"]
        
        logger.info(f"创建GIF: {size}, {len(frames)}帧, {fps}fps")
        
        # 调整帧尺寸
        resized_frames = self._resize_frames(frames, size)
        
        # 转换为PIL Image
        pil_frames = [Image.fromarray(frame) for frame in resized_frames]
        
        # 计算每帧持续时间（毫秒）
        duration_ms = int(1000 / fps)
        
        # 保存GIF
        pil_frames[0].save(
            output_path,
            save_all=True,
            append_images=pil_frames[1:],
            duration=duration_ms,
            loop=self.config["loop"],
            optimize=self.config["optimize"]
        )
        
        # 检查文件大小
        file_size_kb = os.path.getsize(output_path) / 1024
        
        # 如果超过最大大小，尝试压缩
        if file_size_kb > max_size_kb:
            logger.info(f"文件过大({file_size_kb:.0f}KB)，尝试压缩...")
            self._optimize_gif(output_path, max_size_kb)
            file_size_kb = os.path.getsize(output_path) / 1024
        
        result = {
            "path": output_path,
            "size": size,
            "frames": len(frames),
            "duration": len(frames) / fps,
            "file_size_kb": round(file_size_kb, 2),
            "fps": fps
        }
        
        logger.info(f"GIF创建完成: {file_size_kb:.2f}KB")
        
        return result
    
    def create_static_image(
        self,
        frame: np.ndarray,
        output_path: str,
        size: Optional[Tuple[int, int]] = None
    ) -> Dict:
        """
        创建高清静态图
        
        Args:
            frame: 单帧图像
            output_path: 输出路径
            size: 目标尺寸，None使用配置值
        
        Returns:
            生成信息
        """
        if size is None:
            size = self.config["hd_size"]
        
        logger.info(f"创建静态图: {size}")
        
        # 调整尺寸
        resized = self._resize_frame(frame, size)
        
        # 保存为PNG（无损）
        img = Image.fromarray(resized)
        img.save(output_path, "PNG", quality=self.config["quality"], optimize=True)
        
        file_size_kb = os.path.getsize(output_path) / 1024
        
        result = {
            "path": output_path,
            "size": size,
            "file_size_kb": round(file_size_kb, 2)
        }
        
        logger.info(f"静态图创建完成: {file_size_kb:.2f}KB")
        
        return result
    
    def generate_multi_specs(
        self,
        video_path: str,
        start: float,
        end: float,
        output_dir: str,
        base_name: str,
        specs: Optional[Dict[str, Tuple[int, int]]] = None,
        include_static: bool = True
    ) -> Dict:
        """
        生成多规格表情包
        
        Args:
            video_path: 视频路径
            start: 开始时间（秒）
            end: 结束时间（秒）
            output_dir: 输出目录
            base_name: 基础文件名（如"emoji_001"）
            specs: 规格字典，None使用抖音规格
            include_static: 是否生成静态图
        
        Returns:
            生成结果字典
        """
        logger.info(f"生成多规格表情包: {base_name}")
        
        # 确保输出目录存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 使用默认规格
        if specs is None:
            specs = self.DOUYIN_SPECS
        
        # 提取帧序列
        frames = self.extract_frames(video_path, start, end)
        
        if not frames:
            raise ValueError("未提取到任何帧")
        
        results = {
            "source": {
                "video_path": video_path,
                "start": start,
                "end": end,
                "duration": end - start,
                "frames_extracted": len(frames)
            },
            "gifs": {},
            "static": None
        }
        
        # 生成各种规格的GIF
        for spec_name, size in specs.items():
            output_path = os.path.join(
                output_dir,
                f"{base_name}_{size[0]}x{size[1]}.gif"
            )
            
            try:
                gif_info = self.create_gif(frames, output_path, size)
                results["gifs"][spec_name] = gif_info
            except Exception as e:
                logger.error(f"生成{spec_name}规格GIF失败: {e}")
        
        # 生成高清静态图
        if include_static and frames:
            # 使用中间帧或最佳帧
            best_frame_idx = len(frames) // 2
            best_frame = frames[best_frame_idx]
            
            output_path = os.path.join(output_dir, f"{base_name}_hd.png")
            
            try:
                static_info = self.create_static_image(best_frame, output_path)
                results["static"] = static_info
            except Exception as e:
                logger.error(f"生成静态图失败: {e}")
        
        # 保存元数据
        metadata_path = os.path.join(output_dir, f"{base_name}_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"多规格表情包生成完成: {len(results['gifs'])}个GIF")
        
        return results
    
    def _resize_frames(
        self,
        frames: List[np.ndarray],
        size: Tuple[int, int]
    ) -> List[np.ndarray]:
        """
        批量调整帧尺寸
        
        Args:
            frames: 帧列表
            size: 目标尺寸
        
        Returns:
            调整后的帧列表
        """
        return [self._resize_frame(frame, size) for frame in frames]
    
    def _resize_frame(
        self,
        frame: np.ndarray,
        size: Tuple[int, int]
    ) -> np.ndarray:
        """
        调整单帧尺寸（保持纵横比，裁剪中心）
        
        Args:
            frame: 输入帧
            size: 目标尺寸 (width, height)
        
        Returns:
            调整后的帧
        """
        target_w, target_h = size
        h, w = frame.shape[:2]
        
        # 计算缩放比例（保持纵横比，覆盖目标尺寸）
        scale = max(target_w / w, target_h / h)
        
        # 缩放
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # 使用PIL进行高质量缩放
        img = Image.fromarray(frame)
        
        # 选择缩放方法
        if self.config["resize_method"] == "lanczos":
            resample = Image.LANCZOS
        elif self.config["resize_method"] == "bicubic":
            resample = Image.BICUBIC
        else:
            resample = Image.BILINEAR
        
        img_resized = img.resize((new_w, new_h), resample)
        
        # 裁剪中心区域
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        right = left + target_w
        bottom = top + target_h
        
        img_cropped = img_resized.crop((left, top, right, bottom))
        
        return np.array(img_cropped)
    
    def _optimize_gif(
        self,
        gif_path: str,
        target_size_kb: int,
        max_iterations: int = 5
    ):
        """
        优化GIF文件大小
        
        策略：
        1. 减少颜色数量
        2. 降低帧率
        3. 减少帧数
        
        Args:
            gif_path: GIF文件路径
            target_size_kb: 目标大小（KB）
            max_iterations: 最大迭代次数
        """
        for iteration in range(max_iterations):
            current_size_kb = os.path.getsize(gif_path) / 1024
            
            if current_size_kb <= target_size_kb:
                logger.info(f"优化完成: {current_size_kb:.2f}KB")
                return
            
            logger.info(f"优化迭代{iteration+1}: {current_size_kb:.2f}KB -> 目标{target_size_kb}KB")
            
            # 读取GIF
            gif = Image.open(gif_path)
            frames = []
            durations = []
            
            try:
                while True:
                    frames.append(gif.copy())
                    durations.append(gif.info.get('duration', 100))
                    gif.seek(gif.tell() + 1)
            except EOFError:
                pass
            
            # 策略1: 减少颜色（从256逐步降到64）
            colors = max(64, 256 - iteration * 32)
            
            # 策略2: 跳帧（如果帧数较多）
            if len(frames) > 20 and iteration > 2:
                frames = frames[::2]  # 每隔一帧取一帧
                durations = [d * 2 for d in durations[::2]]
            
            # 转换颜色模式并保存
            quantized_frames = []
            for frame in frames:
                # 转换为P模式（256色）
                if frame.mode != 'P':
                    frame_p = frame.convert('P', palette=Image.ADAPTIVE, colors=colors)
                else:
                    frame_p = frame
                quantized_frames.append(frame_p)
            
            # 保存优化后的GIF
            quantized_frames[0].save(
                gif_path,
                save_all=True,
                append_images=quantized_frames[1:],
                duration=durations,
                loop=0,
                optimize=True
            )
        
        # 最后检查
        final_size_kb = os.path.getsize(gif_path) / 1024
        logger.warning(f"优化达到最大迭代次数，最终大小: {final_size_kb:.2f}KB")
    
    def batch_generate(
        self,
        tasks: List[Dict],
        output_base_dir: str
    ) -> List[Dict]:
        """
        批量生成表情包
        
        Args:
            tasks: 任务列表，每个任务包含：
                {
                    "video_path": "...",
                    "start": 125.5,
                    "end": 128.5,
                    "name": "emoji_001",
                    "category": "hand_dance"
                }
            output_base_dir: 输出根目录
        
        Returns:
            结果列表
        """
        logger.info(f"批量生成: {len(tasks)}个任务")
        
        results = []
        
        for i, task in enumerate(tasks, 1):
            logger.info(f"处理任务 {i}/{len(tasks)}: {task.get('name', 'unnamed')}")
            
            try:
                # 确定输出目录
                category = task.get("category", "uncategorized")
                output_dir = os.path.join(output_base_dir, category)
                
                # 生成表情包
                result = self.generate_multi_specs(
                    video_path=task["video_path"],
                    start=task["start"],
                    end=task["end"],
                    output_dir=output_dir,
                    base_name=task.get("name", f"emoji_{i:03d}")
                )
                
                result["task_info"] = task
                result["success"] = True
                results.append(result)
                
            except Exception as e:
                logger.error(f"任务失败: {e}")
                results.append({
                    "task_info": task,
                    "success": False,
                    "error": str(e)
                })
        
        # 生成批量报告
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"批量生成完成: {success_count}/{len(tasks)} 成功")
        
        return results


# ============================================================
# 主函数 - 示例用法
# ============================================================

def main():
    """示例：如何使用表情包生成器"""
    
    print("=" * 60)
    print("表情包生成器 - 示例")
    print("=" * 60)
    
    # 示例视频路径
    video_path = "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4"
    
    if not os.path.exists(video_path):
        print(f"错误: 视频文件不存在: {video_path}")
        return
    
    # 创建生成器
    generator = EmojiGenerator()
    
    # ========== 示例1: 生成单个GIF ==========
    print("\n[示例1] 生成单个GIF")
    print("-" * 60)
    
    frames = generator.extract_frames(video_path, 125.5, 128.5)
    
    gif_info = generator.create_gif(
        frames=frames,
        output_path="test_emoji.gif",
        size=(300, 300)
    )
    
    print(f"GIF生成完成:")
    print(f"  路径: {gif_info['path']}")
    print(f"  尺寸: {gif_info['size']}")
    print(f"  帧数: {gif_info['frames']}")
    print(f"  时长: {gif_info['duration']:.2f}秒")
    print(f"  文件大小: {gif_info['file_size_kb']}KB")
    
    # ========== 示例2: 生成多规格表情包 ==========
    print("\n[示例2] 生成多规格表情包")
    print("-" * 60)
    
    result = generator.generate_multi_specs(
        video_path=video_path,
        start=132.5,
        end=135.0,
        output_dir="temp_emojis",
        base_name="emoji_001"
    )
    
    print(f"多规格生成完成:")
    print(f"  来源: {result['source']['video_path']}")
    print(f"  时间: {result['source']['start']:.2f}s - {result['source']['end']:.2f}s")
    print(f"  提取帧数: {result['source']['frames_extracted']}")
    print(f"\nGIF规格:")
    for spec_name, gif_info in result['gifs'].items():
        print(f"  {spec_name}: {gif_info['size']}, {gif_info['file_size_kb']}KB")
    
    if result['static']:
        print(f"\n静态图: {result['static']['size']}, {result['static']['file_size_kb']}KB")
    
    # ========== 示例3: 批量生成 ==========
    print("\n[示例3] 批量生成")
    print("-" * 60)
    
    tasks = [
        {
            "video_path": video_path,
            "start": 125.5,
            "end": 128.5,
            "name": "emoji_001",
            "category": "hand_dance"
        },
        {
            "video_path": video_path,
            "start": 132.5,
            "end": 135.0,
            "name": "emoji_002",
            "category": "thank"
        }
    ]
    
    batch_results = generator.batch_generate(tasks, "batch_output")
    
    print(f"批量生成完成: {len(batch_results)}个任务")
    for i, result in enumerate(batch_results, 1):
        status = "✓" if result.get("success") else "✗"
        name = result['task_info'].get('name', 'unknown')
        print(f"  {status} {i}. {name}")
    
    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    main()



