#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
升级检测系统

功能：
- 从弹幕数据中检测升级事件
- 从语音识别中检测升级事件
- 从视觉特效中检测升级事件（可选）
- 生成升级视频片段（完整版、精简版、短视频版）
"""

import os
import json
import re
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class UpgradeDetector:
    """
    升级检测器 - 三重检测
    
    检测源：
    1. 弹幕数据（主要）
    2. 语音识别（辅助）
    3. 视觉特效（可选）
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 配置参数
        self.min_level = self.config.get('min_level', 16)  # 最小等级
        self.before_seconds = self.config.get('before_seconds', 5)  # 升级前几秒
        self.after_seconds = self.config.get('after_seconds', 10)  # 升级后几秒
        
        # 升级关键词（中文）
        self.upgrade_keywords_zh = [
            '升级', '升到', '升至', '达到', '到达',
            '恭喜', '成为', '粉丝团', '等级'
        ]
        
        # 升级关键词（英文）
        self.upgrade_keywords_en = [
            'level', 'lv', 'upgrade', 'reach', 'achieve'
        ]
        
        # 升级正则模式
        self.upgrade_patterns = [
            r'升到\s*(\d+)\s*级',
            r'升至\s*(\d+)\s*级',
            r'达到\s*(\d+)\s*级',
            r'到达\s*(\d+)\s*级',
            r'lv\s*(\d+)',
            r'level\s*(\d+)',
            r'(\d+)\s*级.*粉丝',
            r'粉丝.*(\d+)\s*级',
            r'恭喜.*(\d+)\s*级'
        ]
    
    def detect_from_danmaku(self, danmaku_file: str) -> List[Dict]:
        """
        从弹幕数据中检测升级事件
        
        Args:
            danmaku_file: 弹幕JSONL文件路径
        
        Returns:
            升级事件列表
        """
        if not os.path.exists(danmaku_file):
            logger.warning(f"弹幕文件不存在: {danmaku_file}")
            return []
        
        upgrades = []
        
        try:
            with open(danmaku_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    msg = json.loads(line)
                    
                    # 只处理聊天消息和成员消息
                    if msg.get('type') not in ['chat', 'member']:
                        continue
                    
                    # 检测升级
                    upgrade_info = self._detect_upgrade_from_text(
                        msg.get('content', ''),
                        msg.get('timestamp', 0),
                        msg.get('user', 'Unknown')
                    )
                    
                    if upgrade_info:
                        upgrades.append(upgrade_info)
            
            logger.info(f"从弹幕检测到 {len(upgrades)} 个升级事件")
            return upgrades
            
        except Exception as e:
            logger.error(f"从弹幕检测升级失败: {e}")
            return []
    
    def detect_from_transcript(self, transcript_file: str) -> List[Dict]:
        """
        从语音识别结果中检测升级事件
        
        Args:
            transcript_file: Whisper转文字JSON文件
        
        Returns:
            升级事件列表
        """
        if not os.path.exists(transcript_file):
            logger.warning(f"转文字文件不存在: {transcript_file}")
            return []
        
        upgrades = []
        
        try:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 处理Whisper的segments
            segments = data.get('segments', [])
            
            for segment in segments:
                text = segment.get('text', '')
                start = segment.get('start', 0)
                
                upgrade_info = self._detect_upgrade_from_text(
                    text,
                    start,
                    speaker='主播'
                )
                
                if upgrade_info:
                    upgrade_info['source'] = 'speech'
                    upgrades.append(upgrade_info)
            
            logger.info(f"从语音识别检测到 {len(upgrades)} 个升级事件")
            return upgrades
            
        except Exception as e:
            logger.error(f"从语音识别检测升级失败: {e}")
            return []
    
    def _detect_upgrade_from_text(
        self,
        text: str,
        timestamp: float,
        speaker: str = 'Unknown'
    ) -> Optional[Dict]:
        """
        从文本中检测升级
        
        Args:
            text: 文本内容
            timestamp: 时间戳
            speaker: 说话人
        
        Returns:
            升级信息或None
        """
        if not text:
            return None
        
        text_lower = text.lower()
        
        # 快速关键词过滤
        has_keyword = any(
            kw in text_lower
            for kw in self.upgrade_keywords_zh + self.upgrade_keywords_en
        )
        
        if not has_keyword:
            return None
        
        # 正则提取等级
        for pattern in self.upgrade_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                level = int(match.group(1))
                
                # 等级过滤
                if level < self.min_level:
                    continue
                
                return {
                    'timestamp': timestamp,
                    'time': datetime.fromtimestamp(timestamp).isoformat() if timestamp > 0 else '',
                    'user': speaker,
                    'level': level,
                    'original_text': text,
                    'source': 'danmaku'
                }
        
        return None
    
    def merge_detections(
        self,
        danmaku_upgrades: List[Dict],
        speech_upgrades: List[Dict],
        time_threshold: float = 10.0
    ) -> List[Dict]:
        """
        合并不同来源的检测结果
        
        Args:
            danmaku_upgrades: 弹幕检测结果
            speech_upgrades: 语音检测结果
            time_threshold: 时间阈值（秒）
        
        Returns:
            合并后的升级事件列表
        """
        if not danmaku_upgrades and not speech_upgrades:
            return []
        
        # 以弹幕检测为主
        merged = list(danmaku_upgrades)
        
        # 添加语音检测中的新事件
        for speech_upgrade in speech_upgrades:
            # 检查是否与已有事件重复
            is_duplicate = False
            
            for existing in merged:
                time_diff = abs(speech_upgrade['timestamp'] - existing['timestamp'])
                level_match = speech_upgrade['level'] == existing['level']
                
                if time_diff < time_threshold and level_match:
                    # 重复事件，标记为多源验证
                    existing['verified'] = True
                    existing['sources'] = existing.get('sources', [existing['source']])
                    existing['sources'].append(speech_upgrade['source'])
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                merged.append(speech_upgrade)
        
        # 按时间排序
        merged.sort(key=lambda x: x['timestamp'])
        
        # 添加序号
        for i, upgrade in enumerate(merged, 1):
            upgrade['id'] = i
        
        logger.info(f"合并后共 {len(merged)} 个升级事件")
        logger.info(f"  其中 {sum(1 for u in merged if u.get('verified'))} 个经过多源验证")
        
        return merged
    
    def extract_video_clip(
        self,
        video_path: str,
        timestamp: float,
        output_path: str,
        version: str = 'full'
    ) -> bool:
        """
        提取视频片段
        
        Args:
            video_path: 原始视频路径
            timestamp: 升级时间戳（秒）
            output_path: 输出路径
            version: 版本
                - 'full': 完整版（前5秒+后10秒）
                - 'short': 精简版（前3秒+后5秒）
                - 'ultra': 短视频版（前2秒+后3秒）
        
        Returns:
            是否成功
        """
        if not os.path.exists(video_path):
            logger.error(f"视频文件不存在: {video_path}")
            return False
        
        # 确定时间范围
        if version == 'full':
            before = self.before_seconds
            after = self.after_seconds
        elif version == 'short':
            before = 3
            after = 5
        else:  # ultra
            before = 2
            after = 3
        
        start_time = max(0, timestamp - before)
        duration = before + after
        
        # 创建输出目录
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # FFmpeg命令
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', video_path,
            '-t', str(duration),
            '-c', 'copy',  # 快速模式，不重新编码
            '-y',
            output_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                timeout=300
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"✅ 视频片段提取成功: {os.path.basename(output_path)}")
                return True
            else:
                logger.error(f"❌ 视频片段提取失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ 视频片段提取超时")
            return False
        except Exception as e:
            logger.error(f"❌ 视频片段提取出错: {e}")
            return False
    
    def generate_upgrade_videos(
        self,
        video_path: str,
        upgrades: List[Dict],
        output_dir: str
    ) -> Dict:
        """
        批量生成升级视频
        
        Args:
            video_path: 原始视频路径
            upgrades: 升级事件列表
            output_dir: 输出目录
        
        Returns:
            生成结果统计
        """
        os.makedirs(output_dir, exist_ok=True)
        
        stats = {
            'total': len(upgrades),
            'success': 0,
            'failed': 0,
            'generated_files': []
        }
        
        for upgrade in upgrades:
            user = upgrade.get('user', 'Unknown')
            level = upgrade.get('level', 0)
            timestamp = upgrade.get('timestamp', 0)
            upgrade_id = upgrade.get('id', 0)
            
            # 清理用户名（去除特殊字符）
            safe_user = re.sub(r'[^\w\-]', '_', user)
            
            # 生成三个版本
            versions = {
                'full': f"{upgrade_id:02d}_{safe_user}_{level}级_完整版.mp4",
                'short': f"{upgrade_id:02d}_{safe_user}_{level}级_精简版.mp4",
                'ultra': f"{upgrade_id:02d}_{safe_user}_{level}级_短视频.mp4"
            }
            
            success_count = 0
            
            for version, filename in versions.items():
                output_path = os.path.join(output_dir, filename)
                
                if self.extract_video_clip(video_path, timestamp, output_path, version):
                    success_count += 1
                    stats['generated_files'].append(filename)
            
            if success_count > 0:
                stats['success'] += 1
            else:
                stats['failed'] += 1
        
        logger.info(f"\n升级视频生成完成:")
        logger.info(f"  总计: {stats['total']} 个升级事件")
        logger.info(f"  成功: {stats['success']} 个")
        logger.info(f"  失败: {stats['failed']} 个")
        logger.info(f"  生成文件: {len(stats['generated_files'])} 个")
        
        return stats
    
    def save_upgrade_metadata(
        self,
        upgrades: List[Dict],
        output_path: str
    ):
        """保存升级元数据"""
        try:
            metadata = {
                'total_upgrades': len(upgrades),
                'detection_time': datetime.now().isoformat(),
                'upgrades': upgrades
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 升级元数据已保存: {output_path}")
            
        except Exception as e:
            logger.error(f"保存升级元数据失败: {e}")


def process_upgrade_detection(
    video_path: str,
    danmaku_file: str,
    transcript_file: str,
    output_dir: str
) -> Dict:
    """
    完整的升级检测流程
    
    Args:
        video_path: 视频文件路径
        danmaku_file: 弹幕文件路径
        transcript_file: 转文字文件路径
        output_dir: 输出目录
    
    Returns:
        处理结果
    """
    logger.info("="*80)
    logger.info("开始升级检测")
    logger.info("="*80)
    
    # 创建检测器
    detector = UpgradeDetector({
        'min_level': 16,
        'before_seconds': 5,
        'after_seconds': 10
    })
    
    # 1. 从弹幕检测
    logger.info("\n步骤1: 从弹幕数据检测...")
    danmaku_upgrades = detector.detect_from_danmaku(danmaku_file)
    
    # 2. 从语音识别检测
    logger.info("\n步骤2: 从语音识别检测...")
    speech_upgrades = detector.detect_from_transcript(transcript_file)
    
    # 3. 合并结果
    logger.info("\n步骤3: 合并检测结果...")
    all_upgrades = detector.merge_detections(danmaku_upgrades, speech_upgrades)
    
    if not all_upgrades:
        logger.warning("未检测到任何升级事件")
        return {'upgrades': [], 'videos': []}
    
    # 4. 生成视频片段
    logger.info(f"\n步骤4: 生成升级视频片段...")
    video_stats = detector.generate_upgrade_videos(
        video_path,
        all_upgrades,
        os.path.join(output_dir, 'upgrade_videos')
    )
    
    # 5. 保存元数据
    logger.info("\n步骤5: 保存元数据...")
    detector.save_upgrade_metadata(
        all_upgrades,
        os.path.join(output_dir, 'upgrades_metadata.json')
    )
    
    logger.info("\n" + "="*80)
    logger.info("升级检测完成！")
    logger.info("="*80)
    
    return {
        'upgrades': all_upgrades,
        'videos': video_stats
    }


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n=== 升级检测系统 ===\n")
    print("功能：")
    print("  • 从弹幕数据检测升级事件")
    print("  • 从语音识别检测升级事件")
    print("  • 多源验证")
    print("  • 自动生成升级视频（完整版、精简版、短视频版）")
    print()
    print("使用方法:")
    print("  from src.upgrade_detector import process_upgrade_detection")
    print("  ")
    print("  process_upgrade_detection(")
    print("      video_path='录播.mp4',")
    print("      danmaku_file='弹幕.jsonl',")
    print("      transcript_file='转文字.json',")
    print("      output_dir='./output'")
    print("  )")
    print()



