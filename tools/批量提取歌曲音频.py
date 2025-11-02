#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量提取歌曲音频

功能：
1. 从歌曲列表JSON读取125首歌曲信息
2. 使用FFmpeg提取音频（MP3/FLAC）
3. 保存到素材库/歌曲站/音频/
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime


class SongAudioExtractor:
    """歌曲音频提取器"""
    
    def __init__(self, video_path: str, song_list_path: str, output_base_dir: str):
        """
        初始化提取器
        
        Args:
            video_path: 原视频路径
            song_list_path: 歌曲列表JSON路径
            output_base_dir: 输出根目录
        """
        self.video_path = video_path
        self.song_list_path = song_list_path
        self.output_base_dir = Path(output_base_dir)
        
        # 验证文件
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        if not os.path.exists(song_list_path):
            raise FileNotFoundError(f"歌曲列表不存在: {song_list_path}")
        
        # 加载歌曲列表
        with open(song_list_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 如果是字典格式（包含songs键），提取songs数组
            if isinstance(data, dict):
                self.songs = data.get("songs", [])
            else:
                self.songs = data
        
        print(f"已加载 {len(self.songs)} 首歌曲")
    
    def extract_mp3(self, start_time: float, duration: float, output_path: str):
        """
        提取MP3音频
        
        Args:
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            output_path: 输出路径
        """
        cmd = [
            'ffmpeg',
            '-i', self.video_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-vn',                          # 不包含视频
            '-acodec', 'libmp3lame',        # MP3编码器
            '-ab', '192k',                  # 比特率192kbps
            '-ar', '44100',                 # 采样率44.1kHz
            '-y',                           # 覆盖输出文件
            output_path
        ]
        
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    def extract_flac(self, start_time: float, duration: float, output_path: str):
        """
        提取FLAC无损音频
        
        Args:
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            output_path: 输出路径
        """
        cmd = [
            'ffmpeg',
            '-i', self.video_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-vn',                          # 不包含视频
            '-acodec', 'flac',              # FLAC编码器
            '-ar', '48000',                 # 采样率48kHz
            '-y',                           # 覆盖输出文件
            output_path
        ]
        
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    def extract_all_mp3(self):
        """提取所有歌曲的MP3"""
        print("\n" + "=" * 70)
        print("提取MP3音频")
        print("=" * 70)
        
        mp3_dir = self.output_base_dir / "歌曲站" / "音频" / "MP3"
        mp3_dir.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        fail_count = 0
        
        for i, song in enumerate(self.songs, 1):
            song_id = song.get("id", f"song_{i:03d}")
            song_name = song.get("name", f"歌曲{i:03d}")
            start_time = song.get("start", 0)
            duration = song.get("duration", 0)
            
            if duration <= 0:
                print(f"[{i}/{len(self.songs)}] ⚠ 跳过: {song_name} (时长无效)")
                fail_count += 1
                continue
            
            output_file = mp3_dir / f"{song_id}_{song_name}.mp3"
            
            print(f"[{i}/{len(self.songs)}] 提取: {song_name} ({duration:.1f}秒)", end="", flush=True)
            
            try:
                self.extract_mp3(start_time, duration, str(output_file))
                
                # 检查文件大小
                file_size_mb = os.path.getsize(output_file) / 1024 / 1024
                print(f" ... ✓ ({file_size_mb:.2f}MB)")
                success_count += 1
                
            except Exception as e:
                print(f" ... ✗ 失败: {e}")
                fail_count += 1
        
        print(f"\nMP3提取完成: {success_count}成功, {fail_count}失败")
        return success_count, fail_count
    
    def extract_all_flac(self):
        """提取所有歌曲的FLAC"""
        print("\n" + "=" * 70)
        print("提取FLAC无损音频")
        print("=" * 70)
        
        flac_dir = self.output_base_dir / "歌曲站" / "音频" / "FLAC"
        flac_dir.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        fail_count = 0
        
        for i, song in enumerate(self.songs, 1):
            song_id = song.get("id", f"song_{i:03d}")
            song_name = song.get("name", f"歌曲{i:03d}")
            start_time = song.get("start", 0)
            duration = song.get("duration", 0)
            
            if duration <= 0:
                print(f"[{i}/{len(self.songs)}] ⚠ 跳过: {song_name} (时长无效)")
                fail_count += 1
                continue
            
            output_file = flac_dir / f"{song_id}_{song_name}.flac"
            
            print(f"[{i}/{len(self.songs)}] 提取: {song_name} ({duration:.1f}秒)", end="", flush=True)
            
            try:
                self.extract_flac(start_time, duration, str(output_file))
                
                # 检查文件大小
                file_size_mb = os.path.getsize(output_file) / 1024 / 1024
                print(f" ... ✓ ({file_size_mb:.2f}MB)")
                success_count += 1
                
            except Exception as e:
                print(f" ... ✗ 失败: {e}")
                fail_count += 1
        
        print(f"\nFLAC提取完成: {success_count}成功, {fail_count}失败")
        return success_count, fail_count
    
    def generate_report(self, mp3_stats: tuple, flac_stats: tuple):
        """
        生成提取报告
        
        Args:
            mp3_stats: MP3统计（成功数，失败数）
            flac_stats: FLAC统计（成功数，失败数）
        """
        report_dir = self.output_base_dir / "歌曲站"
        report_path = report_dir / "音频提取报告.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("歌曲音频提取报告\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"源视频: {self.video_path}\n")
            f.write(f"歌曲列表: {self.song_list_path}\n")
            f.write(f"总歌曲数: {len(self.songs)}\n\n")
            
            f.write("提取统计:\n")
            f.write(f"  MP3: {mp3_stats[0]}成功, {mp3_stats[1]}失败\n")
            f.write(f"  FLAC: {flac_stats[0]}成功, {flac_stats[1]}失败\n\n")
            
            # 计算总大小
            mp3_dir = self.output_base_dir / "歌曲站" / "音频" / "MP3"
            flac_dir = self.output_base_dir / "歌曲站" / "音频" / "FLAC"
            
            mp3_size = sum(f.stat().st_size for f in mp3_dir.glob('*.mp3')) / 1024 / 1024
            flac_size = sum(f.stat().st_size for f in flac_dir.glob('*.flac')) / 1024 / 1024
            
            f.write("文件大小:\n")
            f.write(f"  MP3总大小: {mp3_size:.2f}MB\n")
            f.write(f"  FLAC总大小: {flac_size:.2f}MB\n")
            f.write(f"  总计: {mp3_size + flac_size:.2f}MB\n\n")
            
            f.write("输出目录:\n")
            f.write(f"  MP3: {mp3_dir}\n")
            f.write(f"  FLAC: {flac_dir}\n\n")
            
            f.write("=" * 70 + "\n")
            f.write("提取完成！\n")
            f.write("=" * 70 + "\n")
        
        print(f"\n报告已保存: {report_path}")


def main():
    """主函数"""
    
    print("\n" + "=" * 70)
    print("批量歌曲音频提取工具")
    print("=" * 70 + "\n")
    
    # 配置参数
    video_path = "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4"
    song_list_path = os.path.expanduser("~/shanshan_materials/歌曲素材库/歌曲列表.json")
    output_dir = os.path.expanduser("~/shanshan_materials")
    
    # 验证文件
    if not os.path.exists(video_path):
        print(f"错误: 视频文件不存在: {video_path}")
        return
    
    if not os.path.exists(song_list_path):
        print(f"错误: 歌曲列表不存在: {song_list_path}")
        print("\n请先运行 '整理歌曲素材.py' 生成歌曲列表")
        return
    
    # 创建提取器
    extractor = SongAudioExtractor(video_path, song_list_path, output_dir)
    
    # 询问提取格式
    print("选择提取格式:")
    print("  1. 仅MP3（192kbps，节省空间）")
    print("  2. 仅FLAC（无损，高质量）")
    print("  3. 同时提取MP3和FLAC")
    
    choice = input("\n请选择 (1/2/3，默认1): ").strip() or "1"
    
    mp3_stats = (0, 0)
    flac_stats = (0, 0)
    
    start_time = datetime.now()
    
    if choice in ["1", "3"]:
        mp3_stats = extractor.extract_all_mp3()
    
    if choice in ["2", "3"]:
        flac_stats = extractor.extract_all_flac()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # 生成报告
    extractor.generate_report(mp3_stats, flac_stats)
    
    # 显示总结
    print("\n" + "=" * 70)
    print("✓ 音频提取完成！")
    print("=" * 70)
    print(f"总用时: {duration/60:.1f}分钟")
    
    if choice in ["1", "3"]:
        print(f"MP3: {mp3_stats[0]}成功, {mp3_stats[1]}失败")
    if choice in ["2", "3"]:
        print(f"FLAC: {flac_stats[0]}成功, {flac_stats[1]}失败")
    
    print("\n查看结果:")
    if choice in ["1", "3"]:
        print(f"  MP3文件: {output_dir}/歌曲站/音频/MP3/")
    if choice in ["2", "3"]:
        print(f"  FLAC文件: {output_dir}/歌曲站/音频/FLAC/")
    print(f"  提取报告: {output_dir}/歌曲站/音频提取报告.txt")
    print()


if __name__ == "__main__":
    main()

