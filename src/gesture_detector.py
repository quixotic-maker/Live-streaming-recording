#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手势/表情检测器 - 三种检测方案

方案A: MotionDetector - 运动检测（快速，适合手势舞）
方案B: PoseDetector - 姿态估计（准确，识别具体手势）
方案C: MultimodalDetector - 多模态融合（推荐，平衡方案）
"""

import cv2
import numpy as np
import json
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# 方案A: 运动检测器（快速粗筛）
# ============================================================

class MotionDetector:
    """
    运动检测器 - 检测手势舞和大幅度动作
    
    使用场景：
    - 前30-60分钟唱歌片段
    - 快速找出所有手势舞候选片段
    
    优点：
    - 速度快，不需要深度学习
    - 可处理长视频（4小时）
    - CPU友好
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化运动检测器
        
        Args:
            config: 配置参数字典
        """
        default_config = {
            "sample_interval": 5,          # 采样间隔（秒）
            "analysis_frames": 10,         # 分析帧数（每个采样点）
            "roi_top": 0.0,                # ROI上边界（比例）
            "roi_bottom": 0.5,             # ROI下边界（上半身）
            "roi_left": 0.2,               # ROI左边界
            "roi_right": 0.8,              # ROI右边界
            "motion_threshold": 0.15,      # 运动强度阈值
            "merge_gap": 3.0,              # 合并间隔（秒）
            "min_duration": 2.0,           # 最小持续时间（秒）
            "max_duration": 10.0           # 最大持续时间（秒）
        }
        
        self.config = {**default_config, **(config or {})}
        logger.info(f"MotionDetector initialized with config: {self.config}")
    
    def detect_dance_moments(
        self, 
        video_path: str, 
        start_time: float = 0, 
        end_time: Optional[float] = None
    ) -> List[Dict]:
        """
        检测手势舞时刻
        
        Args:
            video_path: 视频路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒），None表示到视频结尾
        
        Returns:
            检测结果列表，每个元素包含：
            {
                "start": 125.5,
                "end": 128.5,
                "peak": 126.8,
                "motion_score": 0.23,
                "confidence": 0.85
            }
        """
        logger.info(f"开始检测手势舞: {video_path} ({start_time}s - {end_time}s)")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        if end_time is None or end_time > duration:
            end_time = duration
        
        logger.info(f"视频信息: {fps:.2f}fps, {total_frames}帧, {duration:.2f}秒")
        
        # 采样点列表
        sample_times = np.arange(start_time, end_time, self.config["sample_interval"])
        logger.info(f"将分析 {len(sample_times)} 个采样点")
        
        motion_scores = []
        
        for i, time in enumerate(sample_times):
            if i % 50 == 0:
                logger.info(f"进度: {i}/{len(sample_times)} ({i/len(sample_times)*100:.1f}%)")
            
            score = self._analyze_motion_at_time(cap, time, fps)
            motion_scores.append({
                "time": time,
                "score": score
            })
        
        cap.release()
        
        # 找出候选片段
        candidates = self._find_motion_peaks(motion_scores)
        
        # 合并相邻片段
        merged = self._merge_candidates(candidates)
        
        logger.info(f"检测完成: 找到 {len(merged)} 个手势舞候选片段")
        
        return merged
    
    def _analyze_motion_at_time(
        self, 
        cap: cv2.VideoCapture, 
        time: float, 
        fps: float
    ) -> float:
        """
        分析指定时间点的运动强度
        
        Args:
            cap: 视频捕获对象
            time: 时间点（秒）
            fps: 帧率
        
        Returns:
            运动强度得分 (0-1)
        """
        frame_idx = int(time * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        
        frames = []
        for _ in range(self.config["analysis_frames"]):
            ret, frame = cap.read()
            if not ret:
                break
            
            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 提取ROI（上半身区域）
            h, w = gray.shape
            y1 = int(h * self.config["roi_top"])
            y2 = int(h * self.config["roi_bottom"])
            x1 = int(w * self.config["roi_left"])
            x2 = int(w * self.config["roi_right"])
            
            roi = gray[y1:y2, x1:x2]
            frames.append(roi)
        
        if len(frames) < 2:
            return 0.0
        
        # 计算相邻帧差
        total_diff = 0
        for i in range(len(frames) - 1):
            diff = cv2.absdiff(frames[i], frames[i + 1])
            total_diff += np.sum(diff)
        
        # 归一化
        roi_area = (y2 - y1) * (x2 - x1) * 255
        motion_score = total_diff / (len(frames) - 1) / roi_area
        
        return min(motion_score, 1.0)
    
    def _find_motion_peaks(
        self, 
        motion_scores: List[Dict]
    ) -> List[Dict]:
        """
        找出运动强度峰值
        
        Args:
            motion_scores: 运动得分列表
        
        Returns:
            候选片段列表
        """
        threshold = self.config["motion_threshold"]
        candidates = []
        
        for i, item in enumerate(motion_scores):
            if item["score"] > threshold:
                # 向前后扩展，找到峰值
                start_idx = i
                end_idx = i
                peak_idx = i
                peak_score = item["score"]
                
                # 向前扫描
                for j in range(i - 1, -1, -1):
                    if motion_scores[j]["score"] > threshold * 0.5:
                        start_idx = j
                        if motion_scores[j]["score"] > peak_score:
                            peak_score = motion_scores[j]["score"]
                            peak_idx = j
                    else:
                        break
                
                # 向后扫描
                for j in range(i + 1, len(motion_scores)):
                    if motion_scores[j]["score"] > threshold * 0.5:
                        end_idx = j
                        if motion_scores[j]["score"] > peak_score:
                            peak_score = motion_scores[j]["score"]
                            peak_idx = j
                    else:
                        break
                
                duration = motion_scores[end_idx]["time"] - motion_scores[start_idx]["time"]
                
                # 检查时长是否合理
                if (self.config["min_duration"] <= duration <= self.config["max_duration"]):
                    candidates.append({
                        "start": motion_scores[start_idx]["time"],
                        "end": motion_scores[end_idx]["time"],
                        "peak": motion_scores[peak_idx]["time"],
                        "motion_score": peak_score,
                        "confidence": min(peak_score / threshold, 1.0)
                    })
        
        return candidates
    
    def _merge_candidates(
        self, 
        candidates: List[Dict]
    ) -> List[Dict]:
        """
        合并相邻的候选片段
        
        Args:
            candidates: 候选片段列表
        
        Returns:
            合并后的片段列表
        """
        if not candidates:
            return []
        
        # 按开始时间排序
        sorted_candidates = sorted(candidates, key=lambda x: x["start"])
        
        merged = []
        current = sorted_candidates[0].copy()
        
        for next_item in sorted_candidates[1:]:
            # 如果间隔小于merge_gap，合并
            if next_item["start"] - current["end"] <= self.config["merge_gap"]:
                # 更新结束时间
                current["end"] = next_item["end"]
                # 保留更高的得分
                if next_item["motion_score"] > current["motion_score"]:
                    current["peak"] = next_item["peak"]
                    current["motion_score"] = next_item["motion_score"]
                    current["confidence"] = next_item["confidence"]
            else:
                # 保存当前片段，开始新片段
                merged.append(current)
                current = next_item.copy()
        
        # 添加最后一个片段
        merged.append(current)
        
        return merged


# ============================================================
# 方案B: 姿态估计器（精确识别）
# ============================================================

class PoseDetector:
    """
    姿态估计器 - 识别具体手势类型
    
    使用场景：
    - 对方案A找到的候选片段进行精确分析
    - 识别具体手势类型（比心、挥手、招手等）
    
    优点：
    - 能识别具体动作类型
    - 准确率高
    
    缺点：
    - 较慢，需要更多计算资源
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化姿态估计器
        
        Args:
            config: 配置参数字典
        """
        default_config = {
            "min_detection_confidence": 0.5,
            "min_tracking_confidence": 0.5,
            "sample_fps": 15,                   # 采样帧率
            "gesture_duration": 0.5,            # 手势最小持续时间
            "hand_distance_threshold": 0.05     # 比心判定阈值
        }
        
        self.config = {**default_config, **(config or {})}
        
        # 尝试导入MediaPipe
        try:
            import mediapipe as mp
            self.mp_hands = mp.solutions.hands
            self.mp_pose = mp.solutions.pose
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=self.config["min_detection_confidence"],
                min_tracking_confidence=self.config["min_tracking_confidence"]
            )
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                min_detection_confidence=self.config["min_detection_confidence"],
                min_tracking_confidence=self.config["min_tracking_confidence"]
            )
            self.available = True
            logger.info("MediaPipe initialized successfully")
        except ImportError:
            logger.warning("MediaPipe not available, PoseDetector will not work")
            self.available = False
    
    def identify_gesture(
        self, 
        video_path: str, 
        start: float, 
        end: float
    ) -> Dict:
        """
        识别具体手势类型
        
        Args:
            video_path: 视频路径
            start: 开始时间（秒）
            end: 结束时间（秒）
        
        Returns:
            识别结果：
            {
                "gesture_type": "heart",  # heart/wave/thank/dance/unknown
                "confidence": 0.92,
                "frames_detected": 28,
                "total_frames": 30,
                "best_frame": 126.8,
                "hand_positions": [...]
            }
        """
        if not self.available:
            logger.warning("MediaPipe not available, returning unknown")
            return {
                "gesture_type": "unknown",
                "confidence": 0.0,
                "frames_detected": 0,
                "total_frames": 0,
                "best_frame": start,
                "hand_positions": []
            }
        
        logger.info(f"识别手势: {start:.2f}s - {end:.2f}s")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # 设置起始帧
        start_frame = int(start * fps)
        end_frame = int(end * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # 采样参数
        sample_interval = int(fps / self.config["sample_fps"])
        
        gesture_detections = []
        frame_idx = start_frame
        
        while frame_idx < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 只处理采样帧
            if (frame_idx - start_frame) % sample_interval == 0:
                # 转换为RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 检测手部
                hand_results = self.hands.process(frame_rgb)
                
                # 检测身体
                pose_results = self.pose.process(frame_rgb)
                
                # 分析手势
                gesture = self._analyze_frame(hand_results, pose_results)
                if gesture:
                    gesture["time"] = frame_idx / fps
                    gesture_detections.append(gesture)
            
            frame_idx += 1
        
        cap.release()
        
        # 统计手势类型
        result = self._summarize_gestures(gesture_detections, start, end)
        
        logger.info(f"识别结果: {result['gesture_type']}, 置信度: {result['confidence']:.2f}")
        
        return result
    
    def _analyze_frame(
        self, 
        hand_results, 
        pose_results
    ) -> Optional[Dict]:
        """
        分析单帧的手势
        
        Args:
            hand_results: MediaPipe手部检测结果
            pose_results: MediaPipe姿态检测结果
        
        Returns:
            手势信息字典或None
        """
        if not hand_results.multi_hand_landmarks:
            return None
        
        gesture_info = {
            "gesture_type": "unknown",
            "confidence": 0.0,
            "hand_count": len(hand_results.multi_hand_landmarks)
        }
        
        # 检测比心手势
        if len(hand_results.multi_hand_landmarks) == 2:
            heart_conf = self._detect_heart_gesture(hand_results.multi_hand_landmarks)
            if heart_conf > 0.5:
                gesture_info["gesture_type"] = "heart"
                gesture_info["confidence"] = heart_conf
                return gesture_info
        
        # 检测挥手
        if pose_results.pose_landmarks:
            wave_conf = self._detect_wave_gesture(
                hand_results.multi_hand_landmarks,
                pose_results.pose_landmarks
            )
            if wave_conf > 0.5:
                gesture_info["gesture_type"] = "wave"
                gesture_info["confidence"] = wave_conf
                return gesture_info
        
        # 默认标记为舞蹈动作
        if len(hand_results.multi_hand_landmarks) > 0:
            gesture_info["gesture_type"] = "dance"
            gesture_info["confidence"] = 0.6
        
        return gesture_info
    
    def _detect_heart_gesture(
        self, 
        hand_landmarks_list
    ) -> float:
        """
        检测比心手势
        
        Args:
            hand_landmarks_list: 双手关键点列表
        
        Returns:
            置信度 (0-1)
        """
        if len(hand_landmarks_list) != 2:
            return 0.0
        
        # 获取食指尖和拇指尖的位置
        left_hand = hand_landmarks_list[0].landmark
        right_hand = hand_landmarks_list[1].landmark
        
        # 食指尖: landmark 8, 拇指尖: landmark 4
        left_index = np.array([left_hand[8].x, left_hand[8].y])
        left_thumb = np.array([left_hand[4].x, left_hand[4].y])
        right_index = np.array([right_hand[8].x, right_hand[8].y])
        right_thumb = np.array([right_hand[4].x, right_hand[4].y])
        
        # 计算距离
        index_dist = np.linalg.norm(left_index - right_index)
        thumb_dist = np.linalg.norm(left_thumb - right_thumb)
        
        # 比心特征：食指尖和拇指尖都很接近
        threshold = self.config["hand_distance_threshold"]
        
        if index_dist < threshold and thumb_dist < threshold:
            # 计算置信度
            confidence = 1.0 - (index_dist + thumb_dist) / (2 * threshold)
            return min(confidence, 1.0)
        
        return 0.0
    
    def _detect_wave_gesture(
        self, 
        hand_landmarks_list, 
        pose_landmarks
    ) -> float:
        """
        检测挥手手势
        
        Args:
            hand_landmarks_list: 手部关键点列表
            pose_landmarks: 身体关键点
        
        Returns:
            置信度 (0-1)
        """
        if not hand_landmarks_list:
            return 0.0
        
        # 获取肩膀高度
        left_shoulder = pose_landmarks.landmark[11]
        right_shoulder = pose_landmarks.landmark[12]
        shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        
        # 检查手部是否高于肩膀
        for hand_landmarks in hand_landmarks_list:
            wrist = hand_landmarks.landmark[0]
            
            if wrist.y < shoulder_y:
                # 手在肩膀上方，判定为挥手
                height_diff = shoulder_y - wrist.y
                confidence = min(height_diff * 2, 1.0)
                return confidence
        
        return 0.0
    
    def _summarize_gestures(
        self, 
        gesture_detections: List[Dict],
        start: float,
        end: float
    ) -> Dict:
        """
        统计手势类型
        
        Args:
            gesture_detections: 检测结果列表
            start: 开始时间
            end: 结束时间
        
        Returns:
            汇总结果
        """
        if not gesture_detections:
            return {
                "gesture_type": "unknown",
                "confidence": 0.0,
                "frames_detected": 0,
                "total_frames": 0,
                "best_frame": start,
                "hand_positions": []
            }
        
        # 统计各类型出现次数
        type_counts = {}
        type_confidences = {}
        
        for detection in gesture_detections:
            g_type = detection["gesture_type"]
            type_counts[g_type] = type_counts.get(g_type, 0) + 1
            
            if g_type not in type_confidences:
                type_confidences[g_type] = []
            type_confidences[g_type].append(detection["confidence"])
        
        # 找出主要手势类型
        main_type = max(type_counts, key=type_counts.get)
        main_count = type_counts[main_type]
        avg_confidence = np.mean(type_confidences[main_type])
        
        # 找出最佳帧
        best_detection = max(
            [d for d in gesture_detections if d["gesture_type"] == main_type],
            key=lambda x: x["confidence"]
        )
        
        return {
            "gesture_type": main_type,
            "confidence": avg_confidence,
            "frames_detected": main_count,
            "total_frames": len(gesture_detections),
            "best_frame": best_detection["time"],
            "hand_positions": []
        }


# ============================================================
# 方案C: 多模态检测器（推荐方案）
# ============================================================

class MultimodalDetector:
    """
    多模态检测器 - 语音+视觉联合分析
    
    使用场景：
    - 分析感谢时刻（基于"谢谢"关键词）
    - 综合表情、手势、特效多个维度
    
    优点：
    - 精准定位
    - 处理快
    - 准确率高
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化多模态检测器
        
        Args:
            config: 配置参数字典
        """
        default_config = {
            "time_window": 3.0,             # 前后时间窗口（秒）
            "emotion_weight": 0.3,          # 表情权重
            "gesture_weight": 0.4,          # 手势权重
            "effect_weight": 0.2,           # 特效权重
            "keyword_weight": 0.1,          # 关键词权重
            "recommend_threshold": 0.7,     # 推荐阈值
            "sample_fps": 10                # 采样帧率
        }
        
        self.config = {**default_config, **(config or {})}
        
        # 初始化表情检测器（如果可用）
        try:
            from .emotion_detector import EmotionDetector
            self.emotion_detector = EmotionDetector()
            logger.info("EmotionDetector loaded")
        except:
            self.emotion_detector = None
            logger.warning("EmotionDetector not available")
        
        logger.info(f"MultimodalDetector initialized with config: {self.config}")
    
    def analyze_thank_moment(
        self, 
        video_path: str, 
        time: float, 
        keyword: str
    ) -> Dict:
        """
        分析感谢时刻（时间点±3秒）
        
        Args:
            video_path: 视频路径
            time: 关键词出现时间（秒）
            keyword: 关键词（如"谢谢"）
        
        Returns:
            分析结果：
            {
                "keyword": "谢谢",
                "source_time": 132.5,
                "best_moment": {
                    "start": 132.2,
                    "end": 134.0,
                    "score": 0.87
                },
                "features": {
                    "has_smile": true,
                    "smile_confidence": 0.92,
                    "has_gesture": true,
                    "gesture_type": "wave",
                    "gesture_confidence": 0.85,
                    "has_effect": true,
                    "effect_intensity": 0.73
                },
                "recommended": true
            }
        """
        logger.info(f"分析感谢时刻: {time:.2f}s, 关键词: {keyword}")
        
        window = self.config["time_window"]
        start_time = max(0, time - window)
        end_time = time + window
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # 分析时间窗口内的帧
        frame_scores = []
        current_time = start_time
        sample_interval = 1.0 / self.config["sample_fps"]
        
        while current_time <= end_time:
            frame_idx = int(current_time * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            
            ret, frame = cap.read()
            if not ret:
                break
            
            # 多维度分析
            score_dict = self._analyze_frame_multimodal(frame, current_time, time)
            score_dict["time"] = current_time
            frame_scores.append(score_dict)
            
            current_time += sample_interval
        
        cap.release()
        
        # 找出最佳时刻
        best_moment = self._find_best_moment(frame_scores, start_time, end_time)
        
        # 汇总特征
        features = self._summarize_features(frame_scores)
        
        # 判断是否推荐
        recommended = best_moment["score"] >= self.config["recommend_threshold"]
        
        result = {
            "keyword": keyword,
            "source_time": time,
            "best_moment": best_moment,
            "features": features,
            "recommended": recommended
        }
        
        logger.info(f"分析结果: score={best_moment['score']:.2f}, recommended={recommended}")
        
        return result
    
    def _analyze_frame_multimodal(
        self, 
        frame: np.ndarray, 
        current_time: float,
        keyword_time: float
    ) -> Dict:
        """
        多维度分析单帧
        
        Args:
            frame: 视频帧
            current_time: 当前时间
            keyword_time: 关键词时间
        
        Returns:
            各维度得分
        """
        scores = {
            "emotion_score": 0.0,
            "gesture_score": 0.0,
            "effect_score": 0.0,
            "keyword_score": 0.0
        }
        
        # 维度1: 表情检测
        if self.emotion_detector:
            emotion_result = self.emotion_detector.detect_emotion_single_frame(frame)
            if emotion_result and emotion_result.get("dominant_emotion") in ["happy", "surprise"]:
                scores["emotion_score"] = emotion_result.get("confidence", 0.0)
        
        # 维度2: 手势检测（简化版，检测手部区域运动）
        scores["gesture_score"] = self._detect_gesture_simple(frame)
        
        # 维度3: 特效检测
        scores["effect_score"] = self._detect_gift_effect(frame)
        
        # 维度4: 时间匹配
        time_diff = abs(current_time - keyword_time)
        scores["keyword_score"] = max(0, 1.0 - time_diff / self.config["time_window"])
        
        # 计算综合得分
        total_score = (
            scores["emotion_score"] * self.config["emotion_weight"] +
            scores["gesture_score"] * self.config["gesture_weight"] +
            scores["effect_score"] * self.config["effect_weight"] +
            scores["keyword_score"] * self.config["keyword_weight"]
        )
        
        scores["total_score"] = total_score
        
        return scores
    
    def _detect_gesture_simple(self, frame: np.ndarray) -> float:
        """
        简化的手势检测（检测上半身区域的活动）
        
        Args:
            frame: 视频帧
        
        Returns:
            手势得分 (0-1)
        """
        # 提取上半身区域
        h, w = frame.shape[:2]
        upper_body = frame[0:int(h*0.5), int(w*0.2):int(w*0.8)]
        
        # 检测边缘（手部轮廓通常边缘明显）
        gray = cv2.cvtColor(upper_body, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        
        # 计算边缘密度
        edge_density = np.sum(edges > 0) / edges.size
        
        # 归一化到0-1
        gesture_score = min(edge_density * 10, 1.0)
        
        return gesture_score
    
    def _detect_gift_effect(self, frame: np.ndarray) -> float:
        """
        检测礼物特效
        
        礼物特效通常特征：
        - 高饱和度（彩色）
        - 高亮度
        - 突然出现
        
        Args:
            frame: 视频帧
        
        Returns:
            特效强度 (0-1)
        """
        # 转换为HSV色彩空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 检测高饱和度像素（S > 200）
        high_saturation = np.sum(hsv[:, :, 1] > 200)
        
        # 检测高亮度像素（V > 200）
        high_value = np.sum(hsv[:, :, 2] > 200)
        
        # 检测金色（H: 20-40）和粉色（H: 150-170）
        gold_mask = (hsv[:, :, 0] >= 20) & (hsv[:, :, 0] <= 40) & (hsv[:, :, 1] > 150)
        pink_mask = (hsv[:, :, 0] >= 150) & (hsv[:, :, 0] <= 170) & (hsv[:, :, 1] > 150)
        
        colored_pixels = np.sum(gold_mask | pink_mask)
        
        # 计算特效强度
        total_pixels = frame.shape[0] * frame.shape[1]
        effect_ratio = (high_saturation + high_value + colored_pixels * 2) / (total_pixels * 4)
        
        effect_score = min(effect_ratio, 1.0)
        
        return effect_score
    
    def _find_best_moment(
        self, 
        frame_scores: List[Dict],
        start_time: float,
        end_time: float
    ) -> Dict:
        """
        找出最佳时刻
        
        Args:
            frame_scores: 帧得分列表
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            最佳时刻信息
        """
        if not frame_scores:
            return {
                "start": start_time,
                "end": end_time,
                "score": 0.0
            }
        
        # 找出得分最高的帧
        best_frame = max(frame_scores, key=lambda x: x["total_score"])
        best_time = best_frame["time"]
        best_score = best_frame["total_score"]
        
        # 以最佳帧为中心，扩展1-2秒作为表情包片段
        moment_start = max(start_time, best_time - 1.0)
        moment_end = min(end_time, best_time + 1.0)
        
        return {
            "start": moment_start,
            "end": moment_end,
            "peak": best_time,
            "score": best_score
        }
    
    def _summarize_features(self, frame_scores: List[Dict]) -> Dict:
        """
        汇总特征
        
        Args:
            frame_scores: 帧得分列表
        
        Returns:
            特征汇总
        """
        if not frame_scores:
            return {
                "has_smile": False,
                "smile_confidence": 0.0,
                "has_gesture": False,
                "gesture_confidence": 0.0,
                "has_effect": False,
                "effect_intensity": 0.0
            }
        
        # 计算各维度平均分
        avg_emotion = np.mean([s["emotion_score"] for s in frame_scores])
        avg_gesture = np.mean([s["gesture_score"] for s in frame_scores])
        avg_effect = np.mean([s["effect_score"] for s in frame_scores])
        
        return {
            "has_smile": avg_emotion > 0.5,
            "smile_confidence": avg_emotion,
            "has_gesture": avg_gesture > 0.3,
            "gesture_confidence": avg_gesture,
            "has_effect": avg_effect > 0.3,
            "effect_intensity": avg_effect
        }


# ============================================================
# 主函数 - 示例用法
# ============================================================

def main():
    """示例：如何使用三种检测方案"""
    
    print("=" * 60)
    print("手势/表情检测器 - 示例")
    print("=" * 60)
    
    # 示例视频路径（需要替换为实际路径）
    video_path = "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4"
    
    if not os.path.exists(video_path):
        print(f"错误: 视频文件不存在: {video_path}")
        return
    
    # ========== 方案A: 运动检测 ==========
    print("\n[方案A] 运动检测 - 查找手势舞")
    print("-" * 60)
    
    motion_detector = MotionDetector()
    dance_moments = motion_detector.detect_dance_moments(
        video_path,
        start_time=0,
        end_time=3600  # 前60分钟
    )
    
    print(f"找到 {len(dance_moments)} 个手势舞候选片段:")
    for i, moment in enumerate(dance_moments[:5], 1):  # 只显示前5个
        print(f"  {i}. {moment['start']:.2f}s - {moment['end']:.2f}s, "
              f"得分: {moment['motion_score']:.3f}")
    
    # ========== 方案B: 姿态估计 ==========
    print("\n[方案B] 姿态估计 - 识别具体手势")
    print("-" * 60)
    
    pose_detector = PoseDetector()
    
    if dance_moments and pose_detector.available:
        # 对第一个候选片段进行精确识别
        first_moment = dance_moments[0]
        gesture_result = pose_detector.identify_gesture(
            video_path,
            first_moment["start"],
            first_moment["end"]
        )
        
        print(f"手势类型: {gesture_result['gesture_type']}")
        print(f"置信度: {gesture_result['confidence']:.2f}")
        print(f"检测帧数: {gesture_result['frames_detected']}/{gesture_result['total_frames']}")
    
    # ========== 方案C: 多模态检测 ==========
    print("\n[方案C] 多模态检测 - 分析感谢时刻")
    print("-" * 60)
    
    multimodal_detector = MultimodalDetector()
    
    # 示例：分析一个"谢谢"时刻
    thank_result = multimodal_detector.analyze_thank_moment(
        video_path,
        time=132.5,  # 假设这是一个关键词时刻
        keyword="谢谢"
    )
    
    print(f"关键词: {thank_result['keyword']}")
    print(f"最佳时刻: {thank_result['best_moment']['start']:.2f}s - "
          f"{thank_result['best_moment']['end']:.2f}s")
    print(f"综合得分: {thank_result['best_moment']['score']:.2f}")
    print(f"是否推荐: {thank_result['recommended']}")
    print(f"特征:")
    for key, value in thank_result['features'].items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    main()



