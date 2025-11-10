#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
弹幕录制管理器

功能：
- 与视频录制同步启动/停止弹幕录制
- 管理弹幕录制线程
- 确保弹幕文件与视频文件对应
"""

import os
import threading
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DanmakuRecordManager:
    """弹幕录制管理器"""
    
    def __init__(self):
        """初始化"""
        self.recording_sessions: Dict[str, any] = {}  # {anchor_name: recorder}
        self.lock = threading.Lock()
    
    def start_recording(
        self,
        platform: str,
        record_url: str,
        anchor_name: str,
        save_file_path: str
    ) -> bool:
        """
        启动弹幕录制
        
        Args:
            platform: 平台名称
            record_url: 直播URL
            anchor_name: 主播名称
            save_file_path: 视频保存路径
        
        Returns:
            是否成功启动
        """
        # 只支持抖音平台
        if platform != '抖音直播':
            logger.debug(f"{anchor_name} - {platform} 不支持弹幕录制")
            return False
        
        with self.lock:
            # 如果已经在录制，先停止
            if anchor_name in self.recording_sessions:
                logger.warning(f"{anchor_name} 已在录制弹幕，先停止旧录制")
                self.stop_recording(anchor_name)
            
            try:
                # 动态导入（避免循环依赖）
                from src.danmaku_douyin import DouyinDanmakuRecorder
                
                # 确定弹幕输出目录
                video_dir = os.path.dirname(save_file_path)
                video_name = Path(save_file_path).stem  # 不含扩展名
                
                # 弹幕文件使用与视频相同的基础名称
                danmaku_dir = os.path.join(video_dir, 'danmaku_data')
                os.makedirs(danmaku_dir, exist_ok=True)
                
                output_dir = danmaku_dir
                base_filename = video_name
                
                # 创建录制器
                recorder = DouyinDanmakuRecorder(
                    room_url=record_url,
                    output_dir=output_dir,
                    base_filename=base_filename
                )
                
                # 启动录制（异步）
                success = recorder.start_recording()
                
                if success:
                    self.recording_sessions[anchor_name] = recorder
                    logger.info(f"✅ {anchor_name} 弹幕录制已启动")
                    logger.info(f"   弹幕保存位置: {output_dir}/{base_filename}_danmaku.jsonl")
                    return True
                else:
                    logger.error(f"❌ {anchor_name} 弹幕录制启动失败")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ {anchor_name} 启动弹幕录制失败: {e}")
                return False
    
    def stop_recording(self, anchor_name: str) -> bool:
        """
        停止弹幕录制
        
        Args:
            anchor_name: 主播名称
        
        Returns:
            是否成功停止
        """
        with self.lock:
            if anchor_name not in self.recording_sessions:
                logger.debug(f"{anchor_name} 没有进行中的弹幕录制")
                return False
            
            try:
                recorder = self.recording_sessions[anchor_name]
                recorder.stop_recording()
                del self.recording_sessions[anchor_name]
                logger.info(f"✅ {anchor_name} 弹幕录制已停止")
                return True
            except Exception as e:
                logger.error(f"❌ {anchor_name} 停止弹幕录制失败: {e}")
                return False
    
    def is_recording(self, anchor_name: str) -> bool:
        """
        检查是否正在录制弹幕
        
        Args:
            anchor_name: 主播名称
        
        Returns:
            是否正在录制
        """
        with self.lock:
            return anchor_name in self.recording_sessions
    
    def stop_all(self):
        """停止所有弹幕录制"""
        with self.lock:
            anchor_names = list(self.recording_sessions.keys())
            for anchor_name in anchor_names:
                try:
                    self.stop_recording(anchor_name)
                except Exception as e:
                    logger.error(f"停止 {anchor_name} 弹幕录制失败: {e}")


# 全局单例
_danmaku_manager = None


def get_danmaku_manager() -> DanmakuRecordManager:
    """获取全局弹幕录制管理器"""
    global _danmaku_manager
    if _danmaku_manager is None:
        _danmaku_manager = DanmakuRecordManager()
    return _danmaku_manager


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n=== 弹幕录制管理器 ===\n")
    print("功能:")
    print("  • 与视频录制同步")
    print("  • 自动管理录制线程")
    print("  • 文件名自动对应")
    print()





















