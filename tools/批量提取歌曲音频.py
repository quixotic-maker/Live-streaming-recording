#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量提取歌曲音频

功能：
1. 从歌曲列表JSON读取歌曲信息
2. 使用FFmpeg提取音频（MP3/FLAC）
3. 保存到指定输出目录

✨ 支持新的数据格式：
  - recognized_songs_{date}.json: {"1": {"title": "...", "artist": "..."}, ...}
  - singing_素材.json: 用于获取时间信息
"""

import os
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


class SongAudioExtractor:
    """歌曲音频提取器"""
    
    def __init__(self, video_path: str, song_list_path: str, output_base_dir: str, singing_file: str = None):
        """
        初始化提取器
        
        Args:
            video_path: 原视频路径
            song_list_path: 歌曲识别结果JSON路径 (recognized_songs_{date}.json)
            output_base_dir: 输出根目录
            singing_file: singing_素材.json路径（用于获取时间信息）
        """
        self.video_path = video_path
        self.song_list_path = song_list_path
        self.output_base_dir = Path(output_base_dir)
        
        # 验证文件
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        if not os.path.exists(song_list_path):
            raise FileNotFoundError(f"歌曲列表不存在: {song_list_path}")
        
        # 加载歌曲识别结果
        with open(song_list_path, 'r', encoding='utf-8') as f:
            recognized_data = json.load(f)
        
        # ✨ 适配新格式：{"1": {"title": "...", "artist": "..."}, ...}
        if isinstance(recognized_data, dict):
            # 检查是否是新格式（键是数字字符串）
            keys = list(recognized_data.keys())
            if keys and (keys[0].isdigit() or isinstance(keys[0], int)):
                # 新格式
                self.recognized_songs = {
                    k: v for k, v in recognized_data.items() 
                    if isinstance(v, dict) and v.get('title')
                }
                print(f"✓ 加载新格式歌曲数据: {len(self.recognized_songs)} 首")
            elif "songs" in recognized_data:
                # 旧格式（包含songs键）
                self.recognized_songs = {
                    str(i): song for i, song in enumerate(recognized_data["songs"], 1)
                }
                print(f"✓ 加载旧格式歌曲数据: {len(self.recognized_songs)} 首")
            else:
                raise ValueError("无法识别的歌曲数据格式")
        else:
            raise ValueError("歌曲数据必须是字典格式")
        
        # 加载singing_素材.json获取时间信息
        self.singing_segments = {}
        if singing_file and os.path.exists(singing_file):
            with open(singing_file, 'r', encoding='utf-8') as f:
                singing_data = json.load(f)
                segments = singing_data.get('segments', [])
                # 建立索引映射
                for i, seg in enumerate(segments, 1):
                    self.singing_segments[str(i)] = {
                        'start': seg.get('start', seg.get('start_time', 0)),
                        'end': seg.get('end', seg.get('end_time', 0)),
                        'duration': seg.get('duration', 0)
                    }
                print(f"✓ 加载singing时间信息: {len(self.singing_segments)} 个片段")
        else:
            print(f"⚠️  未找到singing_素材.json，将跳过音频提取")
        
        print(f"已加载 {len(self.recognized_songs)} 首歌曲，{len(self.singing_segments)} 个时间片段")
    
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
        """提取所有歌曲的MP3 - 适配新格式"""
        print("\n" + "=" * 70)
        print("提取MP3音频")
        print("=" * 70)
        
        mp3_dir = self.output_base_dir / "MP3"
        mp3_dir.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        total = len(self.recognized_songs)
        
        for idx, (seg_id, song_info) in enumerate(self.recognized_songs.items(), 1):
            # 歌曲名称和艺术家
            title = song_info.get("title", f"未知歌曲{idx}")
            artist = song_info.get("artist", "未知艺术家")
            song_name = f"{title} - {artist}"
            
            # 获取时间信息
            if seg_id not in self.singing_segments:
                print(f"[{idx}/{total}] ⚠ 跳过: {song_name} (无时间信息)")
                skip_count += 1
                continue
            
            time_info = self.singing_segments[seg_id]
            start_time = time_info['start']
            end_time = time_info['end']
            duration = end_time - start_time
            
            if duration <= 0:
                print(f"[{idx}/{total}] ⚠ 跳过: {song_name} (时长无效: {duration:.1f}s)")
                skip_count += 1
                continue
            
            # 安全的文件名（移除特殊字符）
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_artist = "".join(c for c in artist if c.isalnum() or c in (' ', '-', '_')).strip()
            output_file = mp3_dir / f"{safe_title}_{safe_artist}.mp3"
            
            print(f"[{idx}/{total}] 提取: {song_name} ({duration:.1f}秒)", end="", flush=True)
            
            try:
                self.extract_mp3(start_time, duration, str(output_file))
                
                # 检查文件大小
                file_size_mb = os.path.getsize(output_file) / 1024 / 1024
                print(f" ... ✓ ({file_size_mb:.2f}MB)")
                success_count += 1
                
            except Exception as e:
                print(f" ... ✗ 失败: {e}")
                fail_count += 1
        
        print(f"\nMP3提取完成: {success_count}成功, {fail_count}失败, {skip_count}跳过")
        return success_count, fail_count
    
    def extract_all_flac(self):
        """提取所有歌曲的FLAC - 适配新格式"""
        print("\n" + "=" * 70)
        print("提取FLAC无损音频")
        print("=" * 70)
        
        flac_dir = self.output_base_dir / "FLAC"
        flac_dir.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        total = len(self.recognized_songs)
        
        for idx, (seg_id, song_info) in enumerate(self.recognized_songs.items(), 1):
            # 歌曲名称和艺术家
            title = song_info.get("title", f"未知歌曲{idx}")
            artist = song_info.get("artist", "未知艺术家")
            song_name = f"{title} - {artist}"
            
            # 获取时间信息
            if seg_id not in self.singing_segments:
                print(f"[{idx}/{total}] ⚠ 跳过: {song_name} (无时间信息)")
                skip_count += 1
                continue
            
            time_info = self.singing_segments[seg_id]
            start_time = time_info['start']
            end_time = time_info['end']
            duration = end_time - start_time
            
            if duration <= 0:
                print(f"[{idx}/{total}] ⚠ 跳过: {song_name} (时长无效: {duration:.1f}s)")
                skip_count += 1
                continue
            
            # 安全的文件名（移除特殊字符）
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_artist = "".join(c for c in artist if c.isalnum() or c in (' ', '-', '_')).strip()
            output_file = flac_dir / f"{safe_title}_{safe_artist}.flac"
            
            print(f"[{idx}/{total}] 提取: {song_name} ({duration:.1f}秒)", end="", flush=True)
            
            try:
                self.extract_flac(start_time, duration, str(output_file))
                
                # 检查文件大小
                file_size_mb = os.path.getsize(output_file) / 1024 / 1024
                print(f" ... ✓ ({file_size_mb:.2f}MB)")
                success_count += 1
                
            except Exception as e:
                print(f" ... ✗ 失败: {e}")
                fail_count += 1
        
        print(f"\nFLAC提取完成: {success_count}成功, {fail_count}失败, {skip_count}跳过")
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
    """主函数 - 支持命令行参数"""
    parser = argparse.ArgumentParser(description='批量提取歌曲音频')
    parser.add_argument('--video', required=True, help='视频文件路径')
    parser.add_argument('--song_list', required=True, help='歌曲识别结果JSON路径')
    parser.add_argument('--output', required=True, help='输出目录')
    parser.add_argument('--format', default='mp3', choices=['mp3', 'flac'], help='音频格式（默认mp3）')
    parser.add_argument('--singing', help='singing_素材.json路径（用于获取时间信息）')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("批量歌曲音频提取工具")
    print("=" * 70 + "\n")
    
    # 自动查找singing_素材.json
    singing_file = args.singing
    if not singing_file:
        # 尝试从song_list路径推断
        song_list_dir = os.path.dirname(args.song_list)
        potential_singing = os.path.join(song_list_dir, "singing_素材.json")
        if os.path.exists(potential_singing):
            singing_file = potential_singing
            print(f"✓ 自动找到singing_素材.json: {singing_file}")
    
    # 验证文件
    if not os.path.exists(args.video):
        print(f"❌ 错误: 视频文件不存在: {args.video}")
        return 1
    
    if not os.path.exists(args.song_list):
        print(f"❌ 错误: 歌曲列表不存在: {args.song_list}")
        return 1
    
    if not singing_file or not os.path.exists(singing_file):
        print(f"❌ 错误: singing_素材.json不存在")
        print(f"   期待路径: {singing_file or '未指定'}")
        return 1
    
    try:
        # 创建提取器
        extractor = SongAudioExtractor(args.video, args.song_list, args.output, singing_file)
        
        # 检查是否有歌曲
        if not extractor.singing_segments:
            print("❌ 没有可提取的歌曲（singing_segments为空）")
            return 1
        
        start_time = datetime.now()
        
        # 提取音频
        if args.format == 'mp3':
            mp3_stats = extractor.extract_all_mp3()
        else:
            flac_stats = extractor.extract_all_flac()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 显示总结
        print("\n" + "=" * 70)
        print("✓ 音频提取完成！")
        print("=" * 70)
        print(f"总用时: {duration/60:.1f}分钟")
        
        if args.format == 'mp3':
            print(f"MP3: {mp3_stats[0]}成功, {mp3_stats[1]}失败")
            print(f"\n查看结果: {args.output}/MP3/")
        else:
            print(f"FLAC: {flac_stats[0]}成功, {flac_stats[1]}失败")
            print(f"\n查看结果: {args.output}/FLAC/")
        
        print()
        return 0
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

