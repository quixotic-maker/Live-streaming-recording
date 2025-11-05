#!/usr/bin/env python3
"""
音频指纹全视频扫描 - Audio Fingerprint Full Video Scanner
使用Shazamio扫描整个视频，识别所有歌曲

功能:
1. 滑动窗口扫描视频音频
2. 使用Shazamio识别歌曲
3. 合并连续的相同歌曲片段
4. 输出JSON格式的识别结果
"""

import os
import sys
import json
import asyncio
import logging
from typing import List, Dict, Optional
from pathlib import Path
import subprocess
import tempfile
from shazamio import Shazam

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AudioFingerprintScanner:
    """音频指纹扫描器"""
    
    def __init__(self, video_path: str, window_size: int = 15, step_size: int = 10):
        """
        初始化
        
        Args:
            video_path: 视频文件路径
            window_size: 扫描窗口大小（秒）
            step_size: 步进大小（秒）
        """
        self.video_path = video_path
        self.window_size = window_size
        self.step_size = step_size
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 获取视频时长
        self.duration = self._get_video_duration()
        logger.info(f"视频时长: {self.duration:.1f}秒 ({self.duration/60:.1f}分钟)")
        
        # 临时目录
        self.temp_dir = tempfile.mkdtemp(prefix='audio_scan_')
        logger.info(f"临时目录: {self.temp_dir}")
    
    def _get_video_duration(self) -> float:
        """获取视频时长"""
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            self.video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception as e:
            logger.error(f"获取视频时长失败: {e}")
            raise
    
    def _extract_audio_segment(self, start_time: float, duration: float, output_path: str) -> bool:
        """提取音频片段"""
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_time),
            '-t', str(duration),
            '-i', self.video_path,
            '-vn',  # 无视频
            '-acodec', 'libmp3lame',
            '-ar', '44100',
            '-ab', '192k',
            output_path
        ]
        
        try:
            subprocess.run(
                cmd,
                capture_output=True,
                check=True,
                timeout=60
            )
            return True
        except Exception as e:
            logger.warning(f"提取音频片段失败 ({start_time}s): {e}")
            return False
    
    async def _recognize_audio(self, audio_path: str) -> Optional[Dict]:
        """识别音频"""
        try:
            shazam = Shazam()
            result = await shazam.recognize(audio_path)
            
            if result and 'track' in result:
                track = result['track']
                return {
                    'title': track.get('title', 'Unknown'),
                    'artist': track.get('subtitle', 'Unknown'),
                    'confidence': 'high' if result.get('matches') else 'medium'
                }
            return None
        except Exception as e:
            logger.debug(f"识别失败: {e}")
            return None
    
    async def scan(self) -> List[Dict]:
        """扫描整个视频"""
        results = []
        position = 0
        total_windows = int((self.duration - self.window_size) / self.step_size) + 1
        
        logger.info(f"开始扫描: 窗口={self.window_size}s, 步进={self.step_size}s")
        logger.info(f"预计扫描窗口数: {total_windows}")
        
        window_count = 0
        
        while position < self.duration - self.window_size:
            window_count += 1
            
            # 进度显示
            if window_count % 10 == 0:
                progress = (position / self.duration) * 100
                logger.info(f"进度: {progress:.1f}% ({position:.0f}s / {self.duration:.0f}s)")
            
            # 提取音频片段
            audio_file = os.path.join(self.temp_dir, f'segment_{int(position):07d}.mp3')
            
            if self._extract_audio_segment(position, self.window_size, audio_file):
                # 识别
                recognition = await self._recognize_audio(audio_file)
                
                if recognition:
                    results.append({
                        'start': position,
                        'end': position + self.window_size,
                        'title': recognition['title'],
                        'artist': recognition['artist'],
                        'confidence': recognition['confidence']
                    })
                    logger.info(f"✓ {position:.0f}s: {recognition['title']} - {recognition['artist']}")
                
                # 删除临时文件
                try:
                    os.remove(audio_file)
                except:
                    pass
            
            position += self.step_size
        
        logger.info(f"扫描完成: 识别到 {len(results)} 个片段")
        return results
    
    def merge_segments(self, segments: List[Dict]) -> List[Dict]:
        """合并连续的相同歌曲片段"""
        if not segments:
            return []
        
        # 按开始时间排序
        segments.sort(key=lambda x: x['start'])
        
        merged = []
        current = None
        
        for seg in segments:
            if current is None:
                current = {
                    'id': len(merged) + 1,
                    'start': seg['start'],
                    'end': seg['end'],
                    'text': f"{seg['title']} - {seg['artist']}",
                    'song_name': seg['title'],
                    'artist': seg['artist'],
                    'segment_count': 1,
                    'confidence': seg['confidence']
                }
            else:
                # 检查是否是同一首歌（允许较大间隔，避免主播说话导致分割）
                # 修改：step_size * 2 (20秒) → step_size * 6 (60秒)
                same_song = (
                    seg['title'] == current['song_name'] and
                    seg['artist'] == current['artist'] and
                    seg['start'] <= current['end'] + self.step_size * 6
                )
                
                if same_song:
                    # 合并
                    current['end'] = max(current['end'], seg['end'])
                    current['segment_count'] += 1
                    # 如果有high置信度，提升整体置信度
                    if seg['confidence'] == 'high':
                        current['confidence'] = 'high'
                else:
                    # 保存当前，开始新的
                    current['duration'] = current['end'] - current['start']
                    merged.append(current)
                    
                    current = {
                        'id': len(merged) + 1,
                        'start': seg['start'],
                        'end': seg['end'],
                        'text': f"{seg['title']} - {seg['artist']}",
                        'song_name': seg['title'],
                        'artist': seg['artist'],
                        'segment_count': 1,
                        'confidence': seg['confidence']
                    }
        
        # 添加最后一个
        if current:
            current['duration'] = current['end'] - current['start']
            merged.append(current)
        
        # 过滤太短的片段（<15秒）
        merged = [m for m in merged if m['duration'] >= 15]
        
        # 重新编号
        for i, m in enumerate(merged, 1):
            m['id'] = i
        
        logger.info(f"合并后: {len(merged)} 首完整歌曲")
        
        # 统计
        total_duration = sum(m['duration'] for m in merged)
        logger.info(f"总时长: {total_duration:.0f}秒 ({total_duration/60:.1f}分钟)")
        
        return merged
    
    def cleanup(self):
        """清理临时文件"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info(f"已清理临时目录: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"清理临时目录失败: {e}")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='音频指纹全视频扫描')
    parser.add_argument('--video', required=True, help='视频文件路径')
    parser.add_argument('--output', required=True, help='输出JSON文件路径')
    parser.add_argument('--window', type=int, default=15, help='扫描窗口大小（秒）')
    parser.add_argument('--step', type=int, default=10, help='步进大小（秒）')
    
    args = parser.parse_args()
    
    # 检查视频文件
    if not os.path.exists(args.video):
        logger.error(f"视频文件不存在: {args.video}")
        sys.exit(1)
    
    # 创建输出目录
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # 创建扫描器
    scanner = AudioFingerprintScanner(
        video_path=args.video,
        window_size=args.window,
        step_size=args.step
    )
    
    try:
        # 扫描
        segments = await scanner.scan()
        
        # 合并
        merged = scanner.merge_segments(segments)
        
        # 保存结果
        output_data = {'singing': merged}
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 结果已保存: {args.output}")
        logger.info(f"识别到 {len(merged)} 首歌曲")
        
        # 显示结果摘要
        if merged:
            logger.info("\n识别结果摘要:")
            for song in merged[:10]:  # 显示前10首
                logger.info(f"  • {song['text']} ({song['duration']:.0f}秒)")
            if len(merged) > 10:
                logger.info(f"  ... 还有 {len(merged)-10} 首")
        
    finally:
        # 清理
        scanner.cleanup()


if __name__ == '__main__':
    asyncio.run(main())

