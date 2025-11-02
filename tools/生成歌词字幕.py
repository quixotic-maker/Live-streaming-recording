#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
歌词字幕生成工具

功能：
1. 从Whisper转录结果提取歌词
2. 生成SRT/ASS字幕文件
3. 字幕烧录到视频
4. 支持歌词样式自定义
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime, timedelta


class SubtitleGenerator:
    """字幕生成器"""
    
    def __init__(self):
        """初始化生成器"""
        pass
    
    def load_transcript(self, transcript_file: str) -> List[Dict]:
        """
        加载语音转录结果
        
        Args:
            transcript_file: 转录JSON文件
            
        Returns:
            片段列表
        """
        with open(transcript_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get("segments", [])
    
    def load_songs(self, song_file: str) -> List[Dict]:
        """
        加载歌曲列表
        
        Args:
            song_file: 歌曲JSON文件
            
        Returns:
            歌曲列表
        """
        with open(song_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get("songs", [])
    
    def extract_lyrics_for_song(self, song: Dict, all_segments: List[Dict]) -> List[Dict]:
        """
        提取单首歌曲的歌词
        
        Args:
            song: 歌曲信息
            all_segments: 所有语音片段
            
        Returns:
            歌词片段列表
        """
        song_start = song["start"]
        song_end = song["end"]
        
        lyrics = []
        
        for seg in all_segments:
            # 判断是否在歌曲时间范围内
            if seg["start"] >= song_start and seg["end"] <= song_end:
                lyrics.append({
                    "start": seg["start"] - song_start,  # 相对时间
                    "end": seg["end"] - song_start,
                    "text": seg["text"].strip()
                })
        
        return lyrics
    
    def format_timestamp_srt(self, seconds: float) -> str:
        """
        格式化SRT时间戳
        
        Args:
            seconds: 秒数
            
        Returns:
            SRT格式时间戳 (00:00:00,000)
        """
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = int(td.total_seconds() % 60)
        millis = int((td.total_seconds() % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def format_timestamp_ass(self, seconds: float) -> str:
        """
        格式化ASS时间戳
        
        Args:
            seconds: 秒数
            
        Returns:
            ASS格式时间戳 (0:00:00.00)
        """
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = int(td.total_seconds() % 60)
        centisecs = int((td.total_seconds() % 1) * 100)
        
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
    
    def generate_srt(self, lyrics: List[Dict], output_file: str):
        """
        生成SRT字幕文件
        
        Args:
            lyrics: 歌词片段列表
            output_file: 输出文件
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, lyric in enumerate(lyrics, 1):
                f.write(f"{i}\n")
                f.write(f"{self.format_timestamp_srt(lyric['start'])} --> "
                       f"{self.format_timestamp_srt(lyric['end'])}\n")
                f.write(f"{lyric['text']}\n\n")
    
    def generate_ass(self, lyrics: List[Dict], output_file: str,
                     style: Dict = None):
        """
        生成ASS字幕文件（支持样式）
        
        Args:
            lyrics: 歌词片段列表
            output_file: 输出文件
            style: 字幕样式配置
        """
        if style is None:
            style = {
                "font": "Arial",
                "font_size": 24,
                "color": "&H00FFFFFF",  # 白色
                "bold": False,
                "outline": 2,
                "shadow": 1
            }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # ASS文件头
            f.write("[Script Info]\n")
            f.write("Title: 歌词字幕\n")
            f.write("ScriptType: v4.00+\n")
            f.write("WrapStyle: 0\n")
            f.write("ScaledBorderAndShadow: yes\n")
            f.write("PlayResX: 1920\n")
            f.write("PlayResY: 1080\n\n")
            
            # 样式定义
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                   "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
                   "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
                   "Alignment, MarginL, MarginR, MarginV, Encoding\n")
            
            bold = "-1" if style["bold"] else "0"
            f.write(f"Style: Default,{style['font']},{style['font_size']},"
                   f"{style['color']},&H000000FF,&H00000000,&H00000000,"
                   f"{bold},0,0,0,100,100,0,0,1,{style['outline']},{style['shadow']},"
                   f"2,10,10,10,1\n\n")
            
            # 事件（字幕内容）
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            for lyric in lyrics:
                start = self.format_timestamp_ass(lyric["start"])
                end = self.format_timestamp_ass(lyric["end"])
                text = lyric["text"].replace("\n", "\\N")
                
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")
    
    def burn_subtitles(self, video_file: str, subtitle_file: str,
                       output_file: str) -> bool:
        """
        将字幕烧录到视频
        
        Args:
            video_file: 视频文件
            subtitle_file: 字幕文件
            output_file: 输出文件
            
        Returns:
            是否成功
        """
        print(f"烧录字幕到视频...")
        
        # 判断字幕类型
        if subtitle_file.endswith('.srt'):
            subtitle_filter = f"subtitles={subtitle_file}"
        elif subtitle_file.endswith('.ass'):
            subtitle_filter = f"ass={subtitle_file}"
        else:
            print("不支持的字幕格式")
            return False
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_file,
            "-vf", subtitle_filter,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "copy",
            output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            print(f"✓ 字幕烧录完成: {output_file}")
            return True
        else:
            print(f"✗ 字幕烧录失败")
            return False


def main():
    """主函数"""
    print("=" * 70)
    print("歌词字幕生成工具")
    print("=" * 70)
    
    # 配置
    material_dir = os.path.expanduser("~/shanshan_materials")
    transcript_file = "speech_analysis_完整转录.json"
    song_file = os.path.join(material_dir, "歌曲素材库/歌曲列表.json")
    output_dir = os.path.join(material_dir, "歌词字幕")
    
    # 验证文件
    if not os.path.exists(transcript_file):
        print(f"错误: 转录文件不存在: {transcript_file}")
        return
    
    if not os.path.exists(song_file):
        print(f"错误: 歌曲列表不存在: {song_file}")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n转录文件: {transcript_file}")
    print(f"歌曲列表: {song_file}")
    print(f"输出目录: {output_dir}\n")
    
    try:
        # 创建生成器
        generator = SubtitleGenerator()
        
        # 加载数据
        print("加载数据...")
        all_segments = generator.load_transcript(transcript_file)
        songs = generator.load_songs(song_file)
        
        print(f"  转录片段: {len(all_segments)} 个")
        print(f"  歌曲数量: {len(songs)} 首")
        
        # 为每首歌生成字幕
        print("\n生成字幕文件...")
        print("-" * 70)
        
        generated_count = 0
        
        for i, song in enumerate(songs[:50], 1):  # 限制50首
            title = song.get("title", f"歌曲{i}")
            print(f"\n[{i}/{min(len(songs), 50)}] {title}")
            
            # 提取歌词
            lyrics = generator.extract_lyrics_for_song(song, all_segments)
            
            if not lyrics:
                print(f"  ⚠ 未找到歌词")
                continue
            
            print(f"  歌词行数: {len(lyrics)}")
            
            # 清理文件名
            safe_title = "".join(
                c if c.isalnum() or c in " ._-" else "_"
                for c in title
            )
            
            # 生成SRT
            srt_file = os.path.join(output_dir, f"{i:02d}_{safe_title}.srt")
            generator.generate_srt(lyrics, srt_file)
            print(f"  ✓ SRT: {Path(srt_file).name}")
            
            # 生成ASS
            ass_file = os.path.join(output_dir, f"{i:02d}_{safe_title}.ass")
            generator.generate_ass(lyrics, ass_file)
            print(f"  ✓ ASS: {Path(ass_file).name}")
            
            generated_count += 1
        
        # 生成总结
        summary_file = os.path.join(output_dir, "字幕生成报告.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("歌词字幕生成报告\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总歌曲数: {len(songs)}\n")
            f.write(f"生成字幕: {generated_count} 首\n\n")
            
            f.write("使用说明:\n")
            f.write("-" * 70 + "\n")
            f.write("1. SRT格式 - 通用字幕格式，支持大多数播放器\n")
            f.write("2. ASS格式 - 高级字幕格式，支持样式和特效\n")
            f.write("3. 可用于视频编辑软件导入\n")
            f.write("4. 可使用 ffmpeg 烧录到视频\n\n")
            
            f.write("烧录字幕示例命令:\n")
            f.write("-" * 70 + "\n")
            f.write("ffmpeg -i input.mp4 -vf subtitles=歌词.srt -c:a copy output.mp4\n")
        
        print("\n" + "=" * 70)
        print("✅ 字幕生成完成！")
        print("=" * 70)
        print(f"\n输出目录: {output_dir}")
        print(f"  生成字幕: {generated_count} 首歌曲")
        print(f"  格式: SRT + ASS")
        print(f"  报告: {Path(summary_file).name}")
        
        print("\n💡 使用提示:")
        print("  - 在播放器中加载字幕文件")
        print("  - 导入到视频编辑软件")
        print("  - 使用 ffmpeg 烧录到视频")
    
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()



