#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量提取歌曲视频 - 每首歌一个独立MP4文件

功能：
1. 从singing_素材.json读取歌曲时间段
2. 从recognized_songs_*.json读取歌曲名称
3. 从原视频提取每首歌的片段，生成独立MP4
4. 可选：添加歌词字幕
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class SongVideoExtractor:
    """歌曲视频提取器"""
    
    def __init__(self, video_path: str, singing_file: str, song_list: str, output_dir: str):
        self.video_path = video_path
        self.singing_file = singing_file
        self.song_list = song_list
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载数据
        self.singing_segments = self._load_singing_segments()
        self.recognized_songs = self._load_recognized_songs()
        
        print(f"✓ 加载了 {len(self.singing_segments)} 个唱歌片段")
        print(f"✓ 识别了 {len(self.recognized_songs)} 首歌曲")
    
    def _load_singing_segments(self) -> Dict:
        """加载唱歌片段数据"""
        with open(self.singing_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # singing_素材.json 格式: {"segments": [...]}
        if 'segments' in data:
            return {str(i+1): seg for i, seg in enumerate(data['segments'])}
        else:
            # 旧格式可能是 {"materials": [...]}
            return {str(i+1): seg for i, seg in enumerate(data.get('materials', []))}
    
    def _load_recognized_songs(self) -> Dict:
        """加载识别的歌曲数据"""
        with open(self.song_list, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # recognized_songs_*.json 格式: {"1": {"title": "...", "artist": "..."}, ...}
        if isinstance(data, dict):
            return data
        else:
            # 旧格式可能是 {"songs": [...]}
            songs = data.get('songs', [])
            return {str(i+1): song for i, song in enumerate(songs)}
    
    def extract_all(self, add_subtitle: bool = False, lyrics_dir: Optional[str] = None) -> List[str]:
        """
        提取所有歌曲视频
        
        Args:
            add_subtitle: 是否添加歌词字幕
            lyrics_dir: 歌词目录
        
        Returns:
            生成的视频文件列表
        """
        output_files = []
        
        print()
        print("=" * 70)
        print("开始提取歌曲视频")
        print("=" * 70)
        print()
        
        success_count = 0
        fail_count = 0
        
        # 遍历所有歌曲
        for seg_id, song_info in self.recognized_songs.items():
            # 获取歌曲信息
            title = song_info.get('title', f'未知歌曲{seg_id}')
            artist = song_info.get('artist', '')
            
            # 跳过未识别歌曲
            if title.startswith('未知'):
                print(f"[{seg_id}] 跳过未识别歌曲")
                continue
            
            # 获取时间信息
            if seg_id not in self.singing_segments:
                print(f"[{seg_id}] {title} - ⚠ 未找到时间信息，跳过")
                fail_count += 1
                continue
            
            segment = self.singing_segments[seg_id]
            start = segment.get('start', 0)
            duration = segment.get('duration', 0)
            
            if duration <= 0:
                print(f"[{seg_id}] {title} - ⚠ 时长无效，跳过")
                fail_count += 1
                continue
            
            print(f"[{seg_id}] {title} - {artist}")
            print(f"  时间: {start:.1f}s ~ {start+duration:.1f}s (时长: {duration:.1f}s)")
            
            # 生成安全文件名
            safe_title = self._sanitize_filename(title)
            safe_artist = self._sanitize_filename(artist) if artist else ''
            
            if safe_artist:
                filename = f"{safe_title}_{safe_artist}.mp4"
            else:
                filename = f"{safe_title}.mp4"
            
            output_path = self.output_dir / filename
            
            # 提取视频
            success = self._extract_video(start, duration, str(output_path))
            
            if success:
                print(f"  ✓ 视频: {filename}")
                output_files.append(str(output_path))
                success_count += 1
                
                # 添加字幕（如果需要）
                if add_subtitle and lyrics_dir:
                    self._add_subtitle(
                        str(output_path),
                        title,
                        lyrics_dir,
                        start
                    )
            else:
                print(f"  ✗ 提取失败")
                fail_count += 1
            
            print()
        
        # 完成
        print("=" * 70)
        print("✅ 歌曲视频提取完成！")
        print("=" * 70)
        print()
        print(f"输出目录: {self.output_dir}")
        print(f"  成功: {success_count} 首")
        print(f"  失败: {fail_count} 首")
        print()
        
        return output_files
    
    def _extract_video(self, start: float, duration: float, output_path: str) -> bool:
        """
        提取视频片段
        
        Args:
            start: 开始时间（秒）
            duration: 时长（秒）
            output_path: 输出路径
        
        Returns:
            是否成功
        """
        try:
            cmd = [
                'ffmpeg',
                '-ss', str(start),
                '-i', self.video_path,
                '-t', str(duration),
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=600
            )
            
            success = result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0
            
            return success
            
        except Exception as e:
            print(f"  错误: {e}")
            return False
    
    def _add_subtitle(self, video_path: str, song_title: str, lyrics_dir: str, video_start: float):
        """
        添加歌词字幕（可选）
        
        Args:
            video_path: 视频路径
            song_title: 歌曲标题
            lyrics_dir: 歌词目录
            video_start: 视频在原录播中的起始时间
        """
        try:
            # 查找歌词文件
            safe_title = self._sanitize_filename(song_title)
            
            # 尝试多种文件名格式
            possible_names = [
                f"{safe_title}.ass",
                f"{safe_title}.srt",
                f"{song_title}.ass",
                f"{song_title}.srt"
            ]
            
            subtitle_file = None
            for name in possible_names:
                path = os.path.join(lyrics_dir, name)
                if os.path.exists(path):
                    subtitle_file = path
                    break
            
            if not subtitle_file:
                print(f"  ⚠ 未找到歌词文件，跳过字幕")
                return
            
            # 生成带字幕的视频
            output_with_sub = video_path.replace('.mp4', '_字幕版.mp4')
            
            # 调整字幕时间轴（歌词是从0开始，需要减去video_start）
            # 这里简化处理，实际需要修改字幕文件的时间戳
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"subtitles={subtitle_file}",
                '-c:a', 'copy',
                '-y',
                output_with_sub
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=600
            )
            
            if result.returncode == 0:
                print(f"  ✓ 字幕版: {os.path.basename(output_with_sub)}")
            
        except Exception as e:
            print(f"  ⚠ 添加字幕失败: {e}")
    
    def _sanitize_filename(self, name: str) -> str:
        """生成安全的文件名"""
        # 移除非法字符
        illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        safe_name = name
        for char in illegal_chars:
            safe_name = safe_name.replace(char, '_')
        
        # 移除多余空格
        safe_name = ' '.join(safe_name.split())
        
        # 限制长度
        if len(safe_name) > 100:
            safe_name = safe_name[:100]
        
        return safe_name


def main():
    parser = argparse.ArgumentParser(description='批量提取歌曲视频')
    parser.add_argument('--video', required=True, help='原始视频路径')
    parser.add_argument('--singing', required=True, help='singing_素材.json路径')
    parser.add_argument('--song_list', required=True, help='recognized_songs_*.json路径')
    parser.add_argument('--output', required=True, help='输出目录')
    parser.add_argument('--add_subtitle', action='store_true', help='添加歌词字幕')
    parser.add_argument('--lyrics_dir', help='歌词目录（用于字幕）')
    
    args = parser.parse_args()
    
    # 检查文件
    if not os.path.exists(args.video):
        print(f"❌ 视频文件不存在: {args.video}")
        return 1
    
    if not os.path.exists(args.singing):
        print(f"❌ singing_素材.json不存在: {args.singing}")
        return 1
    
    if not os.path.exists(args.song_list):
        print(f"❌ 歌曲列表不存在: {args.song_list}")
        return 1
    
    if args.add_subtitle and not args.lyrics_dir:
        print("❌ 添加字幕需要指定 --lyrics_dir")
        return 1
    
    # 创建提取器
    extractor = SongVideoExtractor(
        video_path=args.video,
        singing_file=args.singing,
        song_list=args.song_list,
        output_dir=args.output
    )
    
    # 提取视频
    output_files = extractor.extract_all(
        add_subtitle=args.add_subtitle,
        lyrics_dir=args.lyrics_dir
    )
    
    print(f"💡 提示: 生成了 {len(output_files)} 个视频文件")
    print(f"    每首歌都是一个独立的MP4文件")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

