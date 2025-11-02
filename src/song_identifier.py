#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
歌曲识别器
从语音识别结果中识别完整的歌曲片段
"""

import json
import os
from typing import List, Dict, Tuple


class SongIdentifier:
    """歌曲识别器"""
    
    def __init__(self):
        """初始化"""
        # 非歌曲的特征词（说明是在说话，不是唱歌）
        self.non_song_keywords = {
            "谢谢", "感谢", "宝宝", "宝贝", "爱你",
            "欢迎", "点赞", "关注", "礼物", "刷",
            "大家好", "晚上好", "怎么样", "对不对",
            "好不好", "是不是", "可以吗", "行不行"
        }
    
    def is_likely_singing(self, segment: Dict) -> bool:
        """
        判断是否可能是唱歌
        
        更准确的判断标准：
        1. 持续时间较长（>20秒）
        2. 文字内容长（>100字）
        3. 不包含太多互动词汇
        """
        text = segment.get("text", "")
        duration = segment.get("end", 0) - segment.get("start", 0)
        
        # 太短的不可能是唱歌
        if duration < 15 or len(text) < 50:
            return False
        
        # 检查是否包含过多非歌曲词汇
        non_song_count = sum(1 for word in self.non_song_keywords if word in text)
        
        # 如果非歌曲词汇太多（>3个），可能是在说话
        if non_song_count > 3:
            return False
        
        # 如果非歌曲词汇占比太高
        if len(text) > 0 and non_song_count / (len(text) / 10) > 0.3:
            return False
        
        # 其他情况，长时间+长文本 = 可能是唱歌
        return True
    
    def identify_songs(self, segments: List[Dict]) -> List[Dict]:
        """
        识别所有歌曲片段
        
        Args:
            segments: 语音识别结果
            
        Returns:
            歌曲片段列表
        """
        songs = []
        
        for seg in segments:
            if self.is_likely_singing(seg):
                songs.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "duration": seg["end"] - seg["start"],
                    "text": seg["text"]
                })
        
        return songs
    
    def merge_adjacent_songs(self, songs: List[Dict], max_gap: float = 10.0) -> List[Dict]:
        """
        合并相邻的歌曲片段（可能是同一首歌）
        
        Args:
            songs: 歌曲片段列表
            max_gap: 最大间隔（秒）
            
        Returns:
            合并后的歌曲列表
        """
        if not songs:
            return []
        
        # 按开始时间排序
        songs = sorted(songs, key=lambda x: x["start"])
        
        merged = []
        current = songs[0].copy()
        current["texts"] = [current["text"]]
        
        for song in songs[1:]:
            gap = song["start"] - current["end"]
            
            # 间隔很小，可能是同一首歌
            if gap <= max_gap:
                current["end"] = song["end"]
                current["duration"] = current["end"] - current["start"]
                current["texts"].append(song["text"])
            else:
                # 保存当前歌曲
                merged.append(current)
                
                # 开始新歌曲
                current = song.copy()
                current["texts"] = [current["text"]]
        
        # 添加最后一首
        merged.append(current)
        
        return merged
    
    def extract_song_title(self, song: Dict) -> str:
        """
        尝试提取歌名
        
        从歌词中查找"这首歌叫XXX"等模式
        """
        import re
        
        if "texts" in song:
            full_text = " ".join(song["texts"])
        else:
            full_text = song.get("text", "")
        
        # 查找歌名模式
        patterns = [
            r'这首歌叫[《「]?([^》」，。]+)',
            r'歌名[是叫][《「]?([^》」，。]+)',
            r'唱的是[《「]?([^》」，。]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                return match.group(1).strip()
        
        return "未知歌曲"
    
    def generate_song_list(self, songs: List[Dict], output_file: str = "歌曲列表.txt"):
        """
        生成歌曲列表
        
        Args:
            songs: 歌曲列表
            output_file: 输出文件
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("🎤 直播歌曲列表\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"总歌曲数: {len(songs)}\n")
            f.write(f"总时长: {sum(s['duration'] for s in songs)/60:.1f} 分钟\n\n")
            
            for i, song in enumerate(songs, 1):
                start_min = int(song["start"] // 60)
                start_sec = int(song["start"] % 60)
                end_min = int(song["end"] // 60)
                end_sec = int(song["end"] % 60)
                
                title = self.extract_song_title(song)
                
                f.write(f"{i:2d}. 《{title}》\n")
                f.write(f"    时间: {start_min:3d}:{start_sec:02d} - {end_min:3d}:{end_sec:02d} "
                       f"({song['duration']/60:.1f}分钟)\n")
                
                # 显示部分歌词
                if "texts" in song:
                    lyrics_preview = song["texts"][0][:50] + "..."
                else:
                    lyrics_preview = song.get("text", "")[:50] + "..."
                
                f.write(f"    歌词: {lyrics_preview}\n\n")
        
        print(f"✅ 歌曲列表已保存: {output_file}")
    
    def generate_song_library(self, songs: List[Dict], output_dir: str = "歌曲素材库"):
        """
        生成歌曲素材库
        
        为每首歌创建独立的素材文件
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存完整JSON
        json_file = os.path.join(output_dir, "所有歌曲.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_songs": len(songs),
                "total_duration": sum(s["duration"] for s in songs),
                "songs": songs
            }, f, ensure_ascii=False, indent=2)
        
        # 生成歌曲列表
        list_file = os.path.join(output_dir, "歌曲列表.txt")
        self.generate_song_list(songs, list_file)
        
        # 生成FFmpeg剪辑脚本
        script_file = os.path.join(output_dir, "剪辑脚本.sh")
        self.generate_cut_script(songs, script_file)
        
        print(f"✅ 歌曲素材库已生成: {output_dir}/")
    
    def generate_cut_script(self, songs: List[Dict], output_file: str):
        """
        生成FFmpeg剪辑脚本
        
        可以用这个脚本批量提取所有歌曲
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("#!/bin/bash\n")
            f.write("# 批量提取歌曲片段\n\n")
            f.write('VIDEO_FILE="观山_2025-10-30.mp4"  # 修改为实际视频文件路径\n')
            f.write('OUTPUT_DIR="提取的歌曲"\n\n')
            f.write('mkdir -p "$OUTPUT_DIR"\n\n')
            
            for i, song in enumerate(songs, 1):
                title = self.extract_song_title(song)
                # 清理文件名
                safe_title = title.replace('/', '_').replace('\\', '_')
                
                start_time = song["start"]
                duration = song["duration"]
                
                f.write(f'# 歌曲 {i}: {title}\n')
                f.write(f'ffmpeg -i "$VIDEO_FILE" -ss {start_time} -t {duration} ')
                f.write(f'-c copy "$OUTPUT_DIR/{i:02d}_{safe_title}.mp4"\n\n')
        
        # 设置执行权限
        os.chmod(output_file, 0o755)
        print(f"✅ 剪辑脚本已生成: {output_file}")
        print(f"   使用方法: bash {output_file}")


def identify_songs_from_transcript(transcript_file: str, output_dir: str = "歌曲素材库"):
    """
    从语音转录文件识别歌曲
    
    Args:
        transcript_file: 语音转录JSON文件
        output_dir: 输出目录
    """
    print("=" * 70)
    print("🎤 歌曲识别器")
    print("=" * 70)
    
    # 读取转录文件
    with open(transcript_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    segments = data.get("segments", [])
    print(f"\n总语音段数: {len(segments)}")
    
    # 创建识别器
    identifier = SongIdentifier()
    
    # 识别歌曲
    print("\n识别歌曲片段...")
    songs = identifier.identify_songs(segments)
    print(f"初步识别到 {len(songs)} 个歌曲片段")
    
    # 合并相邻歌曲
    print("\n合并连续歌曲...")
    merged_songs = identifier.merge_adjacent_songs(songs, max_gap=10.0)
    print(f"合并后共 {len(merged_songs)} 首歌曲")
    
    # 显示统计
    print("\n歌曲统计:")
    print("-" * 70)
    
    total_duration = sum(s["duration"] for s in merged_songs)
    avg_duration = total_duration / len(merged_songs) if merged_songs else 0
    
    print(f"总歌曲数: {len(merged_songs)}")
    print(f"总时长: {total_duration/60:.1f} 分钟")
    print(f"平均时长: {avg_duration/60:.1f} 分钟/首")
    print()
    
    # 显示前10首歌
    print("前10首歌:")
    print("-" * 70)
    for i, song in enumerate(merged_songs[:10], 1):
        start_min = int(song["start"] // 60)
        start_sec = int(song["start"] % 60)
        duration_min = int(song["duration"] // 60)
        duration_sec = int(song["duration"] % 60)
        
        title = identifier.extract_song_title(song)
        
        print(f"{i:2d}. 《{title}》 {start_min:3d}:{start_sec:02d} "
              f"({duration_min}:{duration_sec:02d})")
    
    if len(merged_songs) > 10:
        print(f"... 还有 {len(merged_songs) - 10} 首歌")
    
    # 生成素材库
    print("\n生成歌曲素材库...")
    identifier.generate_song_library(merged_songs, output_dir)
    
    return merged_songs


if __name__ == "__main__":
    import sys
    
    transcript_file = "speech_analysis_完整转录.json"
    
    if len(sys.argv) > 1:
        transcript_file = sys.argv[1]
    
    if not os.path.exists(transcript_file):
        print(f"❌ 文件不存在: {transcript_file}")
        sys.exit(1)
    
    identify_songs_from_transcript(transcript_file)
    
    print("\n" + "=" * 70)
    print("✅ 歌曲识别完成！")
    print("=" * 70)



