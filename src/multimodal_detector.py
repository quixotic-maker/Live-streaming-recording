#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态精彩片段检测器
结合语音识别、礼物特效检测、表情识别、时间规律等多个维度
针对特定主播进行定制化分析
"""

import cv2
import numpy as np
import json
import logging
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class MultimodalDetector:
    """
    多模态精彩片段检测器
    
    检测维度：
    1. 语音对话 - 识别特定话语
    2. 礼物特效 - 检测画面中的礼物动画
    3. 表情识别 - 检测主播表情
    4. 时间规律 - 开播初期权重加倍
    5. 弹幕爆发 - 观众互动高峰（如果有弹幕数据）
    """
    
    def __init__(self, anchor_name: str = "default"):
        """
        初始化检测器
        
        Args:
            anchor_name: 主播名称，用于加载个性化配置
        """
        self.anchor_name = anchor_name
        self.config = self._load_anchor_config(anchor_name)
        
        # 关键词触发器
        self.trigger_keywords = self.config.get('trigger_keywords', [])
        
        # 时间窗口配置
        self.high_density_duration = self.config.get('high_density_duration', 1200)  # 前20分钟
        
        # 礼物特效模板（颜色特征）
        self.gift_color_ranges = [
            # 金色礼物（高级礼物）
            {'lower': np.array([15, 100, 100]), 'upper': np.array([30, 255, 255]), 'weight': 5},
            # 粉色礼物
            {'lower': np.array([140, 50, 50]), 'upper': np.array([170, 255, 255]), 'weight': 3},
            # 紫色礼物
            {'lower': np.array([120, 50, 50]), 'upper': np.array([140, 255, 255]), 'weight': 3},
        ]
    
    def _load_anchor_config(self, anchor_name: str) -> Dict:
        """
        加载主播个性化配置
        
        Args:
            anchor_name: 主播名称
            
        Returns:
            配置字典
        """
        config_path = Path(f"config/anchors/{anchor_name}.json")
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载主播配置失败: {e}")
        
        # 返回默认配置
        return {
            'trigger_keywords': [
                # 这些是示例，需要根据实际主播调整
                '哈哈哈',
                '我的天',
                '卧槽',
                '笑死',
                '太好笑了',
                '可爱',
                '萌',
                '宝宝',
            ],
            'high_density_duration': 1200,  # 前20分钟
            'time_decay_factor': 0.5,  # 时间衰减因子
        }
    
    def analyze_audio_transcript(self, video_path: str, 
                                 transcript_file: Optional[str] = None) -> List[Tuple[float, str, float]]:
        """
        分析视频中的语音对话，识别触发关键词的时刻
        
        Args:
            video_path: 视频路径
            transcript_file: 字幕文件路径（如果已有）
            
        Returns:
            [(时间戳, 关键词, 权重), ...]
        """
        keyword_moments = []
        
        # 如果提供了字幕文件，直接解析
        if transcript_file and Path(transcript_file).exists():
            keyword_moments = self._parse_subtitle_file(transcript_file)
            logger.info(f"从字幕文件中找到 {len(keyword_moments)} 个关键词时刻")
            return keyword_moments
        
        # 否则进行语音识别
        logger.info("开始语音识别...")
        try:
            # 使用Whisper进行语音识别
            transcript_data = self._transcribe_audio(video_path)
            keyword_moments = self._extract_keywords_from_transcript(transcript_data)
            
            # 保存转录结果供后续使用
            self._save_transcript(video_path, transcript_data)
            
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            logger.info("💡 提示: 安装 openai-whisper 以启用语音识别")
            logger.info("   pip install openai-whisper")
        
        return keyword_moments
    
    def _transcribe_audio(self, video_path: str) -> List[Dict]:
        """
        使用Whisper进行语音识别
        
        Args:
            video_path: 视频路径
            
        Returns:
            [{'start': 0.0, 'end': 5.2, 'text': '哈哈哈'}, ...]
        """
        try:
            import whisper
            
            logger.info("正在加载Whisper模型...")
            model = whisper.load_model("base")  # 可选: tiny, base, small, medium, large
            
            logger.info("正在转录音频...")
            result = model.transcribe(
                video_path,
                language='zh',  # 中文
                verbose=False,
                word_timestamps=True  # 获取词级时间戳
            )
            
            # 提取带时间戳的文本段落
            segments = []
            for segment in result['segments']:
                segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'].strip()
                })
            
            logger.info(f"✅ 语音识别完成，共 {len(segments)} 个片段")
            return segments
            
        except ImportError:
            logger.warning("⚠️ Whisper未安装，无法进行语音识别")
            logger.info("安装方法: pip install openai-whisper")
            return []
        except Exception as e:
            logger.error(f"语音识别过程出错: {e}")
            return []
    
    def _extract_keywords_from_transcript(self, transcript_data: List[Dict]) -> List[Tuple[float, str, float]]:
        """
        从转录文本中提取关键词时刻
        
        Args:
            transcript_data: 转录数据
            
        Returns:
            [(时间戳, 关键词, 权重), ...]
        """
        keyword_moments = []
        
        for segment in transcript_data:
            text = segment['text']
            timestamp = segment['start']
            
            # 检查是否包含触发关键词
            for keyword in self.trigger_keywords:
                if keyword in text:
                    # 根据关键词设置权重
                    weight = self._calculate_keyword_weight(keyword, text)
                    keyword_moments.append((timestamp, keyword, weight))
                    logger.debug(f"发现关键词 '{keyword}' 在 {timestamp:.1f}秒")
        
        return keyword_moments
    
    def _calculate_keyword_weight(self, keyword: str, full_text: str) -> float:
        """
        计算关键词权重
        
        Args:
            keyword: 触发的关键词
            full_text: 完整文本
            
        Returns:
            权重值
        """
        # 基础权重
        base_weight = 3.0
        
        # 重复出现加权
        count = full_text.count(keyword)
        if count > 1:
            base_weight *= (1 + count * 0.5)
        
        # 特定关键词加权
        high_weight_keywords = ['哈哈哈', '笑死', '太好笑了']
        if keyword in high_weight_keywords:
            base_weight *= 1.5
        
        return min(base_weight, 10.0)  # 最高10分
    
    def detect_gift_effects(self, video_path: str, 
                           sample_rate: int = 5) -> List[Tuple[float, float]]:
        """
        检测视频中的礼物特效
        
        通过颜色特征和画面变化检测礼物动画
        
        Args:
            video_path: 视频路径
            sample_rate: 检测间隔（帧）
            
        Returns:
            [(时间戳, 强度), ...]
        """
        logger.info("开始检测礼物特效...")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频: {video_path}")
            return []
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        gift_moments = []
        frame_count = 0
        
        try:
            prev_frame = None
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % sample_rate == 0:
                    timestamp = frame_count / fps
                    
                    # 检测礼物特效
                    gift_intensity = self._detect_gift_in_frame(frame, prev_frame)
                    
                    if gift_intensity > 0.3:  # 阈值
                        gift_moments.append((timestamp, gift_intensity))
                        logger.debug(f"检测到礼物特效在 {timestamp:.1f}秒 (强度: {gift_intensity:.2f})")
                    
                    prev_frame = frame.copy()
                
                frame_count += 1
                
                # 进度提示
                if frame_count % (fps * 60) == 0:
                    progress = (frame_count / int(cap.get(cv2.CAP_PROP_FRAME_COUNT))) * 100
                    logger.info(f"礼物检测进度: {progress:.1f}%")
        
        finally:
            cap.release()
        
        logger.info(f"✅ 检测到 {len(gift_moments)} 个礼物特效")
        return gift_moments
    
    def _detect_gift_in_frame(self, frame, prev_frame=None) -> float:
        """
        在单帧中检测礼物特效
        
        Args:
            frame: 当前帧
            prev_frame: 前一帧（用于运动检测）
            
        Returns:
            礼物强度 (0-1)
        """
        # 转换为HSV色彩空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        max_intensity = 0.0
        
        # 检测特定颜色区域（礼物通常有鲜艳的颜色）
        for color_range in self.gift_color_ranges:
            # 创建颜色掩码
            mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
            
            # 计算颜色区域占比
            color_ratio = np.count_nonzero(mask) / (frame.shape[0] * frame.shape[1])
            
            # 如果颜色占比超过一定阈值，认为可能是礼物特效
            if color_ratio > 0.05:  # 超过5%的画面
                intensity = color_ratio * color_range['weight']
                max_intensity = max(max_intensity, intensity)
        
        # 如果有前一帧，检测画面变化（礼物动画会造成剧烈变化）
        if prev_frame is not None:
            diff = cv2.absdiff(frame, prev_frame)
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            motion_score = np.mean(diff_gray) / 255.0
            
            # 如果画面变化剧烈，加权
            if motion_score > 0.1:
                max_intensity *= 1.5
        
        return min(max_intensity, 1.0)
    
    def calculate_time_weight(self, timestamp: float, video_duration: float) -> float:
        """
        根据时间位置计算权重
        
        前20分钟：权重 x2
        之后逐渐衰减
        
        Args:
            timestamp: 当前时间戳（秒）
            video_duration: 视频总时长（秒）
            
        Returns:
            时间权重
        """
        if timestamp <= self.high_density_duration:
            # 前20分钟，权重翻倍
            return 2.0
        else:
            # 之后逐渐衰减
            elapsed = timestamp - self.high_density_duration
            decay = self.config.get('time_decay_factor', 0.5)
            return 1.0 + (1.0 - decay) * np.exp(-elapsed / video_duration)
    
    def fusion_analysis(self, 
                       video_path: str,
                       emotion_timeline: Optional[List] = None,
                       transcript_file: Optional[str] = None,
                       barrage_data: Optional[List] = None) -> List[Tuple[float, float, Dict]]:
        """
        多模态融合分析
        
        综合考虑：
        1. 语音关键词
        2. 礼物特效
        3. 表情识别（如果提供）
        4. 时间规律
        5. 弹幕数据（如果提供）
        
        Args:
            video_path: 视频路径
            emotion_timeline: 表情时间线（可选）
            transcript_file: 字幕文件（可选）
            barrage_data: 弹幕数据（可选）
            
        Returns:
            [(开始时间, 结束时间, 详情), ...]
        """
        logger.info("="*70)
        logger.info("开始多模态融合分析")
        logger.info("="*70)
        
        # 获取视频时长
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        video_duration = frame_count / fps
        cap.release()
        
        logger.info(f"视频时长: {video_duration/60:.1f}分钟")
        
        # 1. 语音关键词分析
        keyword_moments = self.analyze_audio_transcript(video_path, transcript_file)
        logger.info(f"✅ 找到 {len(keyword_moments)} 个关键词时刻")
        
        # 2. 礼物特效检测
        gift_moments = self.detect_gift_effects(video_path)
        logger.info(f"✅ 找到 {len(gift_moments)} 个礼物特效")
        
        # 3. 融合所有数据
        score_timeline = defaultdict(float)
        detail_timeline = defaultdict(lambda: {'sources': []})
        
        # 添加关键词得分
        for timestamp, keyword, weight in keyword_moments:
            time_weight = self.calculate_time_weight(timestamp, video_duration)
            score = weight * time_weight
            score_timeline[int(timestamp)] += score
            detail_timeline[int(timestamp)]['sources'].append(f'关键词:{keyword}({score:.1f})')
        
        # 添加礼物得分
        for timestamp, intensity in gift_moments:
            time_weight = self.calculate_time_weight(timestamp, video_duration)
            score = intensity * 5.0 * time_weight  # 礼物权重5
            score_timeline[int(timestamp)] += score
            detail_timeline[int(timestamp)]['sources'].append(f'礼物({score:.1f})')
        
        # 添加表情得分（如果提供）
        if emotion_timeline:
            logger.info("融合表情识别数据...")
            for timestamp, emotion, confidence in emotion_timeline:
                if emotion in ['happy', 'surprise', 'fear']:
                    time_weight = self.calculate_time_weight(timestamp, video_duration)
                    score = confidence * 3.0 * time_weight
                    score_timeline[int(timestamp)] += score
                    detail_timeline[int(timestamp)]['sources'].append(f'表情:{emotion}({score:.1f})')
        
        # 添加弹幕得分（如果提供）
        if barrage_data:
            logger.info("融合弹幕数据...")
            for timestamp, count in barrage_data:
                time_weight = self.calculate_time_weight(timestamp, video_duration)
                score = (count / 10.0) * time_weight  # 每10条弹幕得1分
                score_timeline[int(timestamp)] += score
                detail_timeline[int(timestamp)]['sources'].append(f'弹幕:{count}条({score:.1f})')
        
        # 4. 提取高分时刻
        highlights = []
        sorted_times = sorted(score_timeline.items(), key=lambda x: x[1], reverse=True)
        
        logger.info(f"\n得分最高的前10个时刻:")
        for i, (timestamp, score) in enumerate(sorted_times[:10]):
            sources = ', '.join(detail_timeline[timestamp]['sources'])
            logger.info(f"  {i+1}. {timestamp//60:02d}:{timestamp%60:02d} - 得分:{score:.1f} - 来源:[{sources}]")
            
            # 扩展时间范围（前后各2秒）
            start = max(0, timestamp - 2)
            end = min(video_duration, timestamp + 5)
            
            highlights.append((
                float(start),
                float(end),
                {
                    'score': score,
                    'sources': detail_timeline[timestamp]['sources'],
                    'time_weight': self.calculate_time_weight(timestamp, video_duration)
                }
            ))
        
        logger.info(f"\n✅ 融合分析完成，提取 {len(highlights)} 个精彩片段")
        return highlights
    
    def _parse_subtitle_file(self, subtitle_file: str) -> List[Tuple[float, str, float]]:
        """解析SRT字幕文件"""
        # TODO: 实现SRT解析
        return []
    
    def _save_transcript(self, video_path: str, transcript_data: List[Dict]):
        """保存转录结果"""
        output_path = Path(video_path).with_suffix('.transcript.json')
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)
            logger.info(f"转录结果已保存: {output_path}")
        except Exception as e:
            logger.warning(f"保存转录结果失败: {e}")


def create_anchor_config(anchor_name: str, trigger_keywords: List[str]):
    """
    创建主播个性化配置文件
    
    Args:
        anchor_name: 主播名称
        trigger_keywords: 触发关键词列表
    """
    config_dir = Path("config/anchors")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    config = {
        'trigger_keywords': trigger_keywords,
        'high_density_duration': 1200,  # 前20分钟
        'time_decay_factor': 0.5,
    }
    
    config_path = config_dir / f"{anchor_name}.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ 主播配置已创建: {config_path}")


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("多模态精彩片段检测器")
    print("=" * 70)
    
    # 示例：创建主播配置
    # create_anchor_config(
    #     "某主播",
    #     trigger_keywords=['哈哈哈', '我的天', '笑死', '太可爱了', '宝宝']
    # )
    
    # 示例：使用检测器
    # detector = MultimodalDetector("某主播")
    # highlights = detector.fusion_analysis("video.mp4")

