#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表情识别模块
使用深度学习检测主播的表情，并标记精彩片段
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class EmotionDetector:
    """
    表情识别器
    用于检测视频中的人脸表情，并识别精彩时刻
    """
    
    # 表情类型定义
    EMOTIONS = {
        0: 'angry',      # 生气
        1: 'disgust',    # 厌恶
        2: 'fear',       # 恐惧
        3: 'happy',      # 开心/大笑
        4: 'sad',        # 悲伤
        5: 'surprise',   # 惊讶
        6: 'neutral'     # 平静
    }
    
    # 中文表情名称
    EMOTIONS_ZH = {
        'angry': '生气',
        'disgust': '厌恶',
        'fear': '恐惧',
        'happy': '开心',
        'sad': '悲伤',
        'surprise': '惊讶',
        'neutral': '平静'
    }
    
    # 精彩表情定义（哪些表情算精彩片段）
    HIGHLIGHT_EMOTIONS = {
        'happy': 5,      # 开心：权重5（最高）
        'surprise': 4,   # 惊讶：权重4
        'fear': 3,       # 恐惧：权重3（游戏惊吓时刻）
        'sad': 2,        # 悲伤：权重2（感动时刻）
    }
    
    def __init__(self, use_gpu=False):
        """
        初始化表情识别器
        
        Args:
            use_gpu: 是否使用GPU加速
        """
        self.use_gpu = use_gpu
        self.face_cascade = None
        self.emotion_model = None
        self.initialized = False
        
    def initialize(self):
        """初始化模型"""
        try:
            # 1. 加载人脸检测器（使用OpenCV的Haar级联）
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self.face_cascade.empty():
                logger.error("无法加载人脸检测模型")
                return False
            
            # 2. 加载表情识别模型
            # 这里使用预训练的表情识别模型
            # 可以使用 FER (Facial Expression Recognition) 库
            try:
                from fer import FER
                self.emotion_model = FER(mtcnn=False)  # 使用OpenCV作为人脸检测器
                logger.info("✅ 表情识别模型加载成功（使用FER库）")
            except ImportError:
                logger.warning("⚠️ FER库未安装，将使用简化版检测")
                logger.info("💡 安装方法: pip install fer")
                # 不使用FER库，只做人脸检测
                self.emotion_model = None
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"初始化表情识别器失败: {e}")
            return False
    
    def detect_emotions_in_frame(self, frame) -> List[Dict]:
        """
        在单帧中检测表情
        
        Args:
            frame: 视频帧（BGR格式）
            
        Returns:
            表情检测结果列表 [{'box': (x,y,w,h), 'emotion': 'happy', 'confidence': 0.95}, ...]
        """
        if not self.initialized:
            if not self.initialize():
                return []
        
        results = []
        
        try:
            if self.emotion_model is not None:
                # 使用FER库进行检测
                emotion_data = self.emotion_model.detect_emotions(frame)
                
                for face_data in emotion_data:
                    box = face_data['box']
                    emotions = face_data['emotions']
                    
                    # 找出置信度最高的表情
                    top_emotion = max(emotions.items(), key=lambda x: x[1])
                    
                    results.append({
                        'box': box,
                        'emotion': top_emotion[0],
                        'confidence': top_emotion[1],
                        'all_emotions': emotions
                    })
            else:
                # 简化版：只检测人脸，不识别表情
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.1, 
                    minNeighbors=5, 
                    minSize=(30, 30)
                )
                
                for (x, y, w, h) in faces:
                    results.append({
                        'box': (x, y, w, h),
                        'emotion': 'neutral',
                        'confidence': 0.5,
                        'all_emotions': {'neutral': 0.5}
                    })
        
        except Exception as e:
            logger.error(f"表情检测失败: {e}")
        
        return results
    
    def analyze_video(self, video_path: str, sample_rate: int = 30) -> List[Tuple[float, str, float]]:
        """
        分析整个视频的表情
        
        Args:
            video_path: 视频文件路径
            sample_rate: 采样率（每隔多少帧分析一次）
            
        Returns:
            [(时间戳, 表情, 置信度), ...]
        """
        if not self.initialized:
            if not self.initialize():
                logger.error("表情识别器未初始化")
                return []
        
        logger.info(f"开始分析视频: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频文件: {video_path}")
            return []
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"视频信息: FPS={fps}, 总帧数={total_frames}")
        
        emotion_timeline = []
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 只分析采样帧
                if frame_count % sample_rate == 0:
                    timestamp = frame_count / fps
                    
                    # 检测当前帧的表情
                    emotions = self.detect_emotions_in_frame(frame)
                    
                    if emotions:
                        # 取置信度最高的表情
                        best_emotion = max(emotions, key=lambda x: x['confidence'])
                        emotion_timeline.append((
                            timestamp,
                            best_emotion['emotion'],
                            best_emotion['confidence']
                        ))
                        
                        if frame_count % (sample_rate * 10) == 0:  # 每10个采样点输出一次
                            logger.debug(f"时间 {timestamp:.1f}s: {best_emotion['emotion']} "
                                       f"(置信度: {best_emotion['confidence']:.2f})")
                
                frame_count += 1
                
                # 进度提示
                if frame_count % (fps * 60) == 0:  # 每分钟输出一次进度
                    progress = (frame_count / total_frames) * 100
                    logger.info(f"分析进度: {progress:.1f}%")
        
        finally:
            cap.release()
        
        logger.info(f"✅ 视频分析完成，共检测到 {len(emotion_timeline)} 个表情数据点")
        return emotion_timeline
    
    def find_highlights_by_emotion(self, emotion_timeline: List[Tuple[float, str, float]],
                                   min_duration: float = 3.0,
                                   merge_gap: float = 2.0) -> List[Tuple[float, float, str, float]]:
        """
        根据表情数据找出精彩片段
        
        Args:
            emotion_timeline: 表情时间线 [(时间戳, 表情, 置信度), ...]
            min_duration: 最小片段时长（秒）
            merge_gap: 合并间隔（秒），小于此间隔的片段会合并
            
        Returns:
            [(开始时间, 结束时间, 主要表情, 平均强度), ...]
        """
        if not emotion_timeline:
            return []
        
        logger.info("开始提取精彩片段...")
        
        # 1. 筛选出精彩表情的时间点
        highlight_moments = []
        for timestamp, emotion, confidence in emotion_timeline:
            if emotion in self.HIGHLIGHT_EMOTIONS and confidence > 0.3:
                weight = self.HIGHLIGHT_EMOTIONS[emotion]
                intensity = confidence * weight
                highlight_moments.append((timestamp, emotion, intensity))
        
        if not highlight_moments:
            logger.warning("未找到任何精彩表情")
            return []
        
        logger.info(f"找到 {len(highlight_moments)} 个精彩表情时刻")
        
        # 2. 将连续的精彩时刻合并成片段
        segments = []
        current_segment = {
            'start': highlight_moments[0][0],
            'end': highlight_moments[0][0],
            'emotions': [highlight_moments[0][1]],
            'intensities': [highlight_moments[0][2]]
        }
        
        for i in range(1, len(highlight_moments)):
            timestamp, emotion, intensity = highlight_moments[i]
            
            # 如果与上一个时刻间隔小于merge_gap，合并到当前片段
            if timestamp - current_segment['end'] <= merge_gap:
                current_segment['end'] = timestamp
                current_segment['emotions'].append(emotion)
                current_segment['intensities'].append(intensity)
            else:
                # 保存当前片段，开始新片段
                if current_segment['end'] - current_segment['start'] >= min_duration:
                    segments.append(current_segment)
                
                current_segment = {
                    'start': timestamp,
                    'end': timestamp,
                    'emotions': [emotion],
                    'intensities': [intensity]
                }
        
        # 添加最后一个片段
        if current_segment['end'] - current_segment['start'] >= min_duration:
            segments.append(current_segment)
        
        # 3. 为每个片段确定主要表情和平均强度
        highlights = []
        for seg in segments:
            # 找出最常见的表情
            emotion_counts = {}
            for e in seg['emotions']:
                emotion_counts[e] = emotion_counts.get(e, 0) + 1
            main_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
            
            # 计算平均强度
            avg_intensity = sum(seg['intensities']) / len(seg['intensities'])
            
            # 扩展时间范围（前后各加1秒）
            start = max(0, seg['start'] - 1.0)
            end = seg['end'] + 1.0
            
            highlights.append((start, end, main_emotion, avg_intensity))
        
        # 4. 按强度排序
        highlights.sort(key=lambda x: x[3], reverse=True)
        
        logger.info(f"✅ 提取了 {len(highlights)} 个精彩片段")
        for i, (start, end, emotion, intensity) in enumerate(highlights[:5]):
            duration = end - start
            logger.info(f"  片段{i+1}: {start:.1f}s-{end:.1f}s ({duration:.1f}秒), "
                       f"表情:{self.EMOTIONS_ZH.get(emotion, emotion)}, 强度:{intensity:.2f}")
        
        return highlights


def analyze_video_emotions(video_path: str, top_n: int = 10) -> List[Tuple[float, float, str]]:
    """
    便捷函数：分析视频并返回Top N精彩片段
    
    Args:
        video_path: 视频路径
        top_n: 返回前N个精彩片段
        
    Returns:
        [(开始时间, 结束时间, 表情类型), ...]
    """
    detector = EmotionDetector()
    
    # 分析视频
    emotion_timeline = detector.analyze_video(video_path, sample_rate=15)  # 每半秒分析一次
    
    if not emotion_timeline:
        logger.warning("未检测到任何表情数据")
        return []
    
    # 提取精彩片段
    highlights = detector.find_highlights_by_emotion(emotion_timeline)
    
    # 返回Top N
    return [(start, end, emotion) for start, end, emotion, _ in highlights[:top_n]]


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("表情识别精彩片段提取器")
    print("=" * 70)
    
    # 示例：分析视频
    # highlights = analyze_video_emotions("path/to/video.mp4", top_n=10)
    # print(f"\n找到 {len(highlights)} 个精彩片段:")
    # for i, (start, end, emotion) in enumerate(highlights):
    #     print(f"{i+1}. {start:.1f}s - {end:.1f}s: {emotion}")

