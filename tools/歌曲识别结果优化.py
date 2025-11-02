#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
歌曲识别结果优化工具

功能：
1. 重新识别"existing"（原有歌名）的歌曲
2. 合并重复的歌曲片段
3. 生成优化后的歌曲列表
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List
from collections import defaultdict


class RecognitionResultOptimizer:
    """识别结果优化器"""
    
    def __init__(self, recognition_file: str, song_list_file: str, video_path: str):
        self.recognition_file = recognition_file
        self.song_list_file = song_list_file
        self.video_path = video_path
        
        # 加载数据
        with open(recognition_file, 'r', encoding='utf-8') as f:
            self.recognition_results = json.load(f)
        
        with open(song_list_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.songs = data.get('songs', [])
        
        # 创建song_id到song对象的映射
        self.song_map = {}
        for i, song in enumerate(self.songs, 1):
            song_id = song.get('id', i)
            self.song_map[str(song_id)] = song
    
    async def reidentify_existing(self):
        """重新识别标记为'existing'的歌曲"""
        print("=" * 70)
        print("步骤1：重新识别原有歌名（Whisper转录可能有错误）")
        print("=" * 70)
        print()
        
        # 导入识别器
        from 智能歌曲识别系统 import AudioFingerprint
        fingerprint = AudioFingerprint()
        
        reidentified = 0
        
        for song_id, result in list(self.recognition_results.items()):
            if result.get('source') == 'existing':
                title = result.get('title', '')
                
                print(f"[ID:{song_id}] 重新识别: {title}", end="", flush=True)
                
                # 获取歌曲信息
                song = self.song_map.get(song_id)
                if not song:
                    print(" → ✗ 未找到歌曲信息")
                    continue
                
                # 提取音频片段
                temp_audio = f"/tmp/reidentify_{song_id}.wav"
                try:
                    fingerprint.extract_audio_segment(
                        self.video_path,
                        song.get('start', 0),
                        song.get('duration', 30),
                        temp_audio
                    )
                    
                    # Shazam识别
                    new_result = await fingerprint.recognize_from_file(temp_audio)
                    
                    if new_result:
                        print(f" → ✓ {new_result['title']} - {new_result['artist']}")
                        self.recognition_results[song_id] = new_result
                        reidentified += 1
                    else:
                        print(" → ✗ 未识别")
                    
                    # 清理临时文件
                    if os.path.exists(temp_audio):
                        os.remove(temp_audio)
                    
                except Exception as e:
                    print(f" → ✗ 错误: {e}")
                
                # 延迟
                await asyncio.sleep(0.5)
        
        print()
        print(f"重新识别完成: {reidentified} 首")
        print()
    
    def merge_duplicates(self):
        """合并重复的歌曲片段"""
        print("=" * 70)
        print("步骤2：合并重复的歌曲片段")
        print("=" * 70)
        print()
        
        # 按歌名+歌手分组
        song_groups = defaultdict(list)
        
        for song_id, result in self.recognition_results.items():
            title = result.get('title', '')
            artist = result.get('artist', '')
            
            # 归一化歌名（处理中英文版本）
            key = self._normalize_song_key(title, artist)
            
            song = self.song_map.get(song_id, {})
            song_groups[key].append({
                'id': song_id,
                'title': title,
                'artist': artist,
                'album': result.get('album', ''),
                'start': song.get('start', 0),
                'end': song.get('end', 0),
                'duration': song.get('duration', 0),
                'confidence': result.get('confidence', 0),
                'source': result.get('source', '')
            })
        
        # 合并连续的片段
        merged_songs = []
        duplicate_count = 0
        
        for key, segments in song_groups.items():
            # 按开始时间排序
            segments.sort(key=lambda x: x['start'])
            
            if len(segments) > 1:
                print(f"合并: {segments[0]['title']} - {segments[0]['artist']}")
                print(f"  片段数: {len(segments)}")
                duplicate_count += len(segments) - 1
                
                # 合并为一首完整的歌
                merged = {
                    'title': segments[0]['title'],
                    'artist': segments[0]['artist'],
                    'album': segments[0]['album'],
                    'start': segments[0]['start'],
                    'end': segments[-1]['end'],
                    'duration': sum(s['duration'] for s in segments),
                    'segment_ids': [s['id'] for s in segments],
                    'segment_count': len(segments),
                    'confidence': segments[0]['confidence'],
                    'source': segments[0]['source']
                }
                merged_songs.append(merged)
            else:
                # 单个片段
                segment = segments[0]
                merged_songs.append({
                    'title': segment['title'],
                    'artist': segment['artist'],
                    'album': segment['album'],
                    'start': segment['start'],
                    'end': segment['end'],
                    'duration': segment['duration'],
                    'segment_ids': [segment['id']],
                    'segment_count': 1,
                    'confidence': segment['confidence'],
                    'source': segment['source']
                })
        
        # 按开始时间排序
        merged_songs.sort(key=lambda x: x['start'])
        
        print()
        print(f"合并完成:")
        print(f"  原始片段: {len(self.recognition_results)}")
        print(f"  合并后歌曲: {len(merged_songs)}")
        print(f"  消除重复: {duplicate_count} 个")
        print()
        
        return merged_songs
    
    def _normalize_song_key(self, title: str, artist: str) -> str:
        """归一化歌曲key（处理中英文版本）"""
        # 移除特殊字符
        title = title.lower().strip()
        artist = artist.lower().strip()
        
        # 常见的中英文对照
        mappings = {
            'love confession': '告白气球',
            'a little bit': '一点点',
            'lovers': '老伴',
            'waiting for you': '等你下课',
            'little love song': '小情歌',
            'faulty forecast': '错误的天气预报',
        }
        
        # 检查是否有映射
        for en, zh in mappings.items():
            if en in title:
                title = zh
                break
        
        return f"{title}|{artist}"
    
    def generate_optimized_list(self, merged_songs: List[Dict], output_file: str):
        """生成优化后的歌曲列表"""
        print("=" * 70)
        print("步骤3：生成优化后的歌曲列表")
        print("=" * 70)
        print()
        
        # 生成JSON
        output_data = {
            'total_songs': len(merged_songs),
            'total_duration': sum(s['duration'] for s in merged_songs),
            'generated_at': '2025-10-31',
            'description': '经过Shazam识别和去重后的歌曲列表',
            'songs': merged_songs
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 已保存: {output_file}")
        print()
        
        # 生成TXT报告
        txt_file = output_file.replace('.json', '.txt')
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("优化后的歌曲列表\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"总歌曲数: {len(merged_songs)}\n")
            f.write(f"总时长: {output_data['total_duration']:.1f} 秒 ({output_data['total_duration']/60:.1f} 分钟)\n\n")
            
            f.write("-" * 70 + "\n")
            f.write(f"{'序号':<6} {'歌名':<30} {'歌手':<20} {'时长':<10}\n")
            f.write("-" * 70 + "\n")
            
            for i, song in enumerate(merged_songs, 1):
                f.write(f"{i:<6} {song['title']:<30} {song['artist']:<20} {song['duration']:.1f}秒\n")
            
            f.write("-" * 70 + "\n")
        
        print(f"✓ 已保存: {txt_file}")
        print()
        
        # 统计信息
        print("统计信息:")
        print(f"  唯一歌曲数: {len(merged_songs)}")
        
        # 统计来源
        from collections import Counter
        sources = Counter(s['source'] for s in merged_songs)
        print("\n识别来源:")
        for source, count in sources.items():
            source_names = {
                'shazam': 'Shazam指纹',
                'existing': '原有歌名',
                'danmaku': '弹幕分析',
                'transcript': '文本提取',
                'manual': '人工标注'
            }
            print(f"  {source_names.get(source, source)}: {count} 首")
        
        # 识别率
        recognized = len([s for s in merged_songs if s['source'] != 'unknown'])
        print(f"\n识别率: {recognized}/{len(merged_songs)} ({recognized/len(merged_songs)*100:.1f}%)")
    
    def save_updated_recognition(self):
        """保存更新后的识别结果"""
        backup_file = self.recognition_file + '.backup'
        
        # 备份原文件
        import shutil
        shutil.copy(self.recognition_file, backup_file)
        print(f"✓ 原文件已备份: {backup_file}")
        
        # 保存更新后的结果
        with open(self.recognition_file, 'w', encoding='utf-8') as f:
            json.dump(self.recognition_results, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 已更新: {self.recognition_file}")


async def main():
    """主函数"""
    print("=" * 70)
    print("歌曲识别结果优化工具")
    print("=" * 70)
    print()
    
    # 配置路径
    material_dir = os.path.expanduser("~/shanshan_materials")
    recognition_file = os.path.join(material_dir, "recognition_results.json")
    song_list_file = os.path.join(material_dir, "歌曲素材库/歌曲列表.json")
    video_path = "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4"
    output_file = os.path.join(material_dir, "歌曲列表_优化版.json")
    
    # 检查文件
    if not os.path.exists(recognition_file):
        print(f"❌ 识别结果不存在: {recognition_file}")
        print("请先运行: python3 智能歌曲识别系统.py")
        return
    
    if not os.path.exists(song_list_file):
        print(f"❌ 歌曲列表不存在: {song_list_file}")
        return
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    # 创建优化器
    optimizer = RecognitionResultOptimizer(
        recognition_file,
        song_list_file,
        video_path
    )
    
    # 步骤1：重新识别原有歌名
    await optimizer.reidentify_existing()
    
    # 步骤2：合并重复片段
    merged_songs = optimizer.merge_duplicates()
    
    # 步骤3：生成优化列表
    optimizer.generate_optimized_list(merged_songs, output_file)
    
    # 保存更新后的识别结果
    optimizer.save_updated_recognition()
    
    print()
    print("=" * 70)
    print("✅ 优化完成！")
    print("=" * 70)
    print()
    print("生成的文件:")
    print(f"  - {output_file} (优化后的歌曲列表)")
    print(f"  - {output_file.replace('.json', '.txt')} (文本报告)")
    print(f"  - {recognition_file}.backup (原识别结果备份)")
    print()
    print("下一步:")
    print("  python3 获取网络歌词.py  # 为优化后的歌曲获取歌词")
    print()


if __name__ == "__main__":
    asyncio.run(main())



