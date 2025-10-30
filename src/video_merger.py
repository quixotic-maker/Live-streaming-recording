#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频合并模块
自动合并分段录制的视频文件
"""

import os
import glob
import subprocess
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def find_segmented_videos(directory: str, anchor_name: str, date_pattern: str) -> List[str]:
    """
    查找某个主播某天的所有分段视频
    
    Args:
        directory: 视频所在目录
        anchor_name: 主播名称
        date_pattern: 日期模式，如 "2025-10-30_19-01-00"
    
    Returns:
        排序后的视频文件路径列表
    """
    # 匹配模式：主播名_日期_XXX.ts
    pattern = os.path.join(directory, f"{anchor_name}_{date_pattern}_*.ts")
    files = glob.glob(pattern)
    
    # 按文件名排序，确保顺序正确
    files.sort()
    
    logger.info(f"找到 {len(files)} 个分段视频文件")
    return files


def merge_videos_ffmpeg(video_files: List[str], output_path: str, delete_source: bool = False) -> bool:
    """
    使用FFmpeg合并视频文件
    
    Args:
        video_files: 要合并的视频文件列表
        output_path: 输出文件路径
        delete_source: 是否删除源文件
    
    Returns:
        是否成功
    """
    if not video_files:
        logger.warning("没有视频文件需要合并")
        return False
    
    if len(video_files) == 1:
        logger.info("只有一个视频文件，无需合并")
        return True
    
    try:
        # 创建临时文件列表
        temp_list_file = output_path + ".filelist.txt"
        with open(temp_list_file, 'w', encoding='utf-8') as f:
            for video_file in video_files:
                # FFmpeg concat 格式要求
                f.write(f"file '{os.path.abspath(video_file)}'\n")
        
        logger.info(f"开始合并 {len(video_files)} 个视频文件...")
        
        # 使用FFmpeg的concat协议合并视频（速度快，无需重新编码）
        ffmpeg_command = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', temp_list_file,
            '-c', 'copy',  # 直接复制流，不重新编码
            '-y',  # 覆盖输出文件
            output_path
        ]
        
        result = subprocess.run(
            ffmpeg_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8'
        )
        
        # 删除临时文件列表
        if os.path.exists(temp_list_file):
            os.remove(temp_list_file)
        
        if result.returncode == 0:
            logger.info(f"✅ 视频合并成功: {output_path}")
            
            # 如果需要，删除源文件
            if delete_source:
                for video_file in video_files:
                    try:
                        os.remove(video_file)
                        logger.debug(f"已删除源文件: {video_file}")
                    except Exception as e:
                        logger.warning(f"删除源文件失败: {video_file}, 错误: {e}")
            
            return True
        else:
            logger.error(f"❌ 视频合并失败: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"合并视频时发生错误: {e}")
        return False


def auto_merge_daily_videos(base_directory: str, anchor_name: str, 
                            date_str: str = None, delete_source: bool = False) -> str:
    """
    自动合并某天录制的所有视频
    
    Args:
        base_directory: 视频基础目录
        anchor_name: 主播名称
        date_str: 日期字符串，如 "2025-10-30"，不指定则为今天
        delete_source: 是否删除源分段文件
    
    Returns:
        合并后的视频路径，失败返回None
    """
    from datetime import datetime
    
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # 查找该主播该日期的所有视频文件
    # 模式：主播名_2025-10-30*.ts
    pattern = os.path.join(base_directory, f"{anchor_name}_{date_str}*.ts")
    all_files = glob.glob(pattern)
    
    if not all_files:
        logger.warning(f"未找到 {anchor_name} 在 {date_str} 的视频文件")
        return None
    
    # 按文件名排序
    all_files.sort()
    
    # 生成输出文件名
    output_filename = f"{anchor_name}_{date_str}_完整录制.ts"
    output_path = os.path.join(base_directory, output_filename)
    
    logger.info(f"准备合并 {len(all_files)} 个视频文件为: {output_filename}")
    
    # 执行合并
    success = merge_videos_ffmpeg(all_files, output_path, delete_source)
    
    if success:
        return output_path
    else:
        return None


def merge_by_session(base_directory: str, anchor_name: str, 
                     start_time_pattern: str, delete_source: bool = False) -> str:
    """
    根据录制会话合并视频（适用于同一次直播的多个分段）
    
    Args:
        base_directory: 视频基础目录
        anchor_name: 主播名称
        start_time_pattern: 开始时间模式，如 "2025-10-30_19-01-00"
        delete_source: 是否删除源分段文件
    
    Returns:
        合并后的视频路径
    """
    # 查找同一会话的所有分段
    pattern = os.path.join(base_directory, f"{anchor_name}_{start_time_pattern}_*.ts")
    video_files = glob.glob(pattern)
    
    if not video_files:
        logger.warning(f"未找到匹配的视频文件: {pattern}")
        return None
    
    video_files.sort()
    
    # 生成输出文件名（移除分段序号）
    output_filename = f"{anchor_name}_{start_time_pattern}_完整.ts"
    output_path = os.path.join(base_directory, output_filename)
    
    success = merge_videos_ffmpeg(video_files, output_path, delete_source)
    
    return output_path if success else None


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 示例用法
    # auto_merge_daily_videos("/path/to/videos", "主播名", "2025-10-30", delete_source=False)

