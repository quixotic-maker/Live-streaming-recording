#!/usr/bin/env python3
"""
段边界优化器 - Segment Boundary Fixer
通过视频分析优化片段起止点，避免截断完整动作

功能:
1. 动作检测: 检测视频中的运动/手势
2. 边界扩展: 将边界扩展到动作开始/结束点
3. 场景分析: 检测场景切换避免跨场景
"""

import cv2
import numpy as np
import json
import os
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SegmentBoundaryFixer:
    """段边界优化器"""
    
    def __init__(self, video_path: str, motion_threshold: float = 5.0):
        """
        初始化
        
        Args:
            video_path: 视频文件路径
            motion_threshold: 运动阈值（像素差异）
        """
        self.video_path = video_path
        self.motion_threshold = motion_threshold
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps
        
        logger.info(f"视频: {os.path.basename(video_path)}")
        logger.info(f"  时长: {self.duration:.1f}秒")
        logger.info(f"  帧率: {self.fps:.1f} FPS")
        logger.info(f"  总帧数: {self.total_frames}")
    
    def _calculate_motion(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """
        计算两帧之间的运动量
        
        Args:
            frame1: 第一帧
            frame2: 第二帧
        
        Returns:
            运动量（0-100）
        """
        # 转灰度
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # 计算差异
        diff = cv2.absdiff(gray1, gray2)
        
        # 计算平均差异
        motion = np.mean(diff)
        
        return motion
    
    def find_motion_boundaries(self, start_time: float, end_time: float,
                              extend_before: float = 2.0,
                              extend_after: float = 2.0) -> Tuple[float, float]:
        """
        查找动作边界
        
        Args:
            start_time: 原始开始时间（秒）
            end_time: 原始结束时间（秒）
            extend_before: 向前扩展搜索范围（秒）
            extend_after: 向后扩展搜索范围（秒）
        
        Returns:
            (优化后的开始时间, 优化后的结束时间)
        """
        # 转换为帧号
        start_frame = int(start_time * self.fps)
        end_frame = int(end_time * self.fps)
        
        # 扩展搜索范围
        search_start = max(0, start_frame - int(extend_before * self.fps))
        search_end = min(self.total_frames - 1, end_frame + int(extend_after * self.fps))
        
        # 查找开始边界（动作开始点）
        new_start_frame = self._find_action_start(search_start, start_frame)
        
        # 查找结束边界（动作结束点）
        new_end_frame = self._find_action_end(end_frame, search_end)
        
        # 转换回时间
        new_start_time = new_start_frame / self.fps
        new_end_time = new_end_frame / self.fps
        
        logger.debug(f"边界优化: {start_time:.1f}-{end_time:.1f}s → {new_start_time:.1f}-{new_end_time:.1f}s")
        
        return new_start_time, new_end_time
    
    def _find_action_start(self, search_start: int, original_start: int) -> int:
        """查找动作开始点（向前搜索）"""
        # 从original_start向前搜索到search_start
        # 找到运动量从低到高的转折点
        
        prev_frame = None
        motion_scores = []
        
        for frame_idx in range(original_start, search_start - 1, -1):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self.cap.read()
            
            if not ret:
                break
            
            if prev_frame is not None:
                motion = self._calculate_motion(prev_frame, frame)
                motion_scores.append((frame_idx, motion))
            
            prev_frame = frame
        
        # 找到运动量开始上升的点
        if motion_scores:
            motion_scores.reverse()  # 反转为时间正序
            
            # 查找第一个运动量超过阈值的点
            for frame_idx, motion in motion_scores:
                if motion > self.motion_threshold:
                    return frame_idx
        
        return search_start
    
    def _find_action_end(self, original_end: int, search_end: int) -> int:
        """查找动作结束点（向后搜索）"""
        # 从original_end向后搜索到search_end
        # 找到运动量从高到低的转折点
        
        prev_frame = None
        motion_scores = []
        
        for frame_idx in range(original_end, search_end + 1):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self.cap.read()
            
            if not ret:
                break
            
            if prev_frame is not None:
                motion = self._calculate_motion(prev_frame, frame)
                motion_scores.append((frame_idx, motion))
            
            prev_frame = frame
        
        # 找到运动量开始下降的点
        if motion_scores:
            # 查找最后一个运动量超过阈值的点
            last_motion_frame = original_end
            for frame_idx, motion in motion_scores:
                if motion > self.motion_threshold:
                    last_motion_frame = frame_idx
                else:
                    # 连续低运动量，说明动作结束
                    break
            
            return last_motion_frame
        
        return search_end
    
    def fix_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        优化所有片段的边界
        
        Args:
            segments: 片段列表，每个片段包含start和end字段
        
        Returns:
            优化后的片段列表
        """
        fixed_segments = []
        
        for i, seg in enumerate(segments):
            # 获取原始时间（兼容start_time和start）
            start = seg.get('start_time', seg.get('start', 0))
            end = seg.get('end_time', seg.get('end', 0))
            
            logger.info(f"处理片段 {i+1}/{len(segments)}: {start:.1f}-{end:.1f}s")
            
            # 优化边界
            new_start, new_end = self.find_motion_boundaries(start, end)
            
            # 创建新片段
            new_seg = seg.copy()
            
            # 更新时间字段（保持原有字段名）
            if 'start_time' in seg:
                new_seg['start_time'] = new_start
                new_seg['end_time'] = new_end
            else:
                new_seg['start'] = new_start
                new_seg['end'] = new_end
            
            # 更新时长
            new_seg['duration'] = new_end - new_start
            
            # 记录原始时间
            new_seg['original_start'] = start
            new_seg['original_end'] = end
            
            fixed_segments.append(new_seg)
        
        return fixed_segments
    
    def __del__(self):
        """释放资源"""
        if hasattr(self, 'cap'):
            self.cap.release()


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='优化视频片段边界')
    parser.add_argument('--video', required=True, help='视频文件路径')
    parser.add_argument('--segments', required=True, help='片段JSON文件路径')
    parser.add_argument('--output', help='输出文件路径（默认覆盖原文件）')
    parser.add_argument('--motion-threshold', type=float, default=5.0,
                       help='运动阈值（默认5.0）')
    parser.add_argument('--extend-before', type=float, default=2.0,
                       help='向前扩展秒数（默认2.0）')
    parser.add_argument('--extend-after', type=float, default=2.0,
                       help='向后扩展秒数（默认2.0）')
    
    args = parser.parse_args()
    
    # 读取片段
    with open(args.segments, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    segments = data.get('segments', data if isinstance(data, list) else [])
    
    if not segments:
        logger.error("未找到片段数据")
        return
    
    logger.info(f"读取到 {len(segments)} 个片段")
    
    # 创建优化器
    fixer = SegmentBoundaryFixer(args.video, motion_threshold=args.motion_threshold)
    
    # 优化边界
    fixed_segments = fixer.fix_segments(segments)
    
    # 保存结果
    output_file = args.output or args.segments
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({'segments': fixed_segments}, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ 已保存优化结果: {output_file}")
    
    # 统计
    total_extend = sum([
        (seg['duration'] - seg.get('original_end', seg.get('end', 0)) +
         seg.get('original_start', seg.get('start', 0)))
        for seg in fixed_segments
    ])
    
    logger.info(f"总计扩展时长: {total_extend:.1f}秒")


if __name__ == '__main__':
    main()

