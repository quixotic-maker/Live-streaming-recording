#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整理歌曲素材
从素材库中的"未分类"提取歌曲（因为94%都是唱歌）
"""

import json
import os
import re


def extract_song_title_from_text(text: str) -> str:
    """从文字中提取歌名"""
    # 查找歌名模式
    patterns = [
        r'这首歌叫[《「]?([^》」，。|]+)',
        r'歌名[是叫][《「]?([^》」，。|]+)',
        r'唱的是[《「]?([^》」，。|]+)',
        r'点歌[《「]?([^》」，。|]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            title = match.group(1).strip()
            # 清理标题
            title = title.replace('我是你的', '')
            title = title.replace('叫', '')
            return title[:20]  # 限制长度
    
    return None


def organize_songs():
    """整理歌曲素材"""
    
    print("=" * 70)
    print("🎤 整理歌曲素材")
    print("=" * 70)
    
    # 读取未分类素材（大部分是唱歌）
    base_dir = os.path.expanduser("~/shanshan_materials/素材库_最新")
    unknown_file = os.path.join(base_dir, "unknown_素材.json")
    
    if not os.path.exists(unknown_file):
        print(f"❌ 文件不存在: {unknown_file}")
        return
    
    with open(unknown_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    segments = data.get("segments", [])
    print(f"\n找到 {len(segments)} 个片段")
    
    # 筛选出真正的歌曲（排除太短的）
    songs = []
    for seg in segments:
        duration = seg["duration"]
        text = seg["text"]
        
        # 歌曲特征：持续时间较长
        if duration > 60:  # 超过1分钟
            songs.append(seg)
        elif duration > 20 and len(text) > 50:  # 或者超过20秒且有足够文字
            songs.append(seg)
    
    print(f"筛选出 {len(songs)} 首可能的歌曲\n")
    
    # 提取歌名
    print("识别歌名...")
    for i, song in enumerate(songs):
        title = extract_song_title_from_text(song["text"])
        if title:
            song["title"] = title
            print(f"  发现歌名: {title}")
        else:
            song["title"] = f"未知歌曲{i+1}"
    
    # 统计
    print("\n歌曲统计:")
    print("-" * 70)
    
    total_duration = sum(s["duration"] for s in songs)
    print(f"总歌曲数: {len(songs)}")
    print(f"总时长: {total_duration/60:.1f} 分钟")
    print(f"平均时长: {total_duration/len(songs)/60:.1f} 分钟/首" if songs else 0)
    
    # 显示所有歌曲
    print("\n歌曲列表:")
    print("-" * 70)
    
    for i, song in enumerate(songs, 1):
        start_min = int(song["start"] // 60)
        start_sec = int(song["start"] % 60)
        end_min = int(song["end"] // 60)
        end_sec = int(song["end"] % 60)
        dur_min = int(song["duration"] // 60)
        dur_sec = int(song["duration"] % 60)
        
        print(f"{i:2d}. 《{song['title']}》")
        print(f"    {start_min:3d}:{start_sec:02d} - {end_min:3d}:{end_sec:02d} "
              f"({dur_min}:{dur_sec:02d})")
        
        # 显示歌词片段
        lyrics = song["text"].split('|')[0][:60]
        print(f"    {lyrics}...")
        print()
    
    # 保存到新文件
    output_dir = os.path.expanduser("~/shanshan_materials/歌曲素材库")
    os.makedirs(output_dir, exist_ok=True)
    
    # JSON格式
    json_file = os.path.join(output_dir, "歌曲列表.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_songs": len(songs),
            "total_duration": total_duration,
            "songs": songs
        }, f, ensure_ascii=False, indent=2)
    
    # 文本格式
    txt_file = os.path.join(output_dir, "歌曲列表.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("🎤 直播歌曲列表\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"总歌曲数: {len(songs)}\n")
        f.write(f"总时长: {total_duration/60:.1f} 分钟\n")
        f.write(f"平均时长: {total_duration/len(songs)/60:.1f} 分钟/首\n\n" if songs else "\n")
        
        for i, song in enumerate(songs, 1):
            start_min = int(song["start"] // 60)
            start_sec = int(song["start"] % 60)
            end_min = int(song["end"] // 60)
            end_sec = int(song["end"] % 60)
            dur_min = int(song["duration"] // 60)
            dur_sec = int(song["duration"] % 60)
            
            f.write(f"{i:2d}. 《{song['title']}》\n")
            f.write(f"    时间: {start_min:3d}:{start_sec:02d} - {end_min:3d}:{end_sec:02d} "
                   f"({dur_min}:{dur_sec:02d})\n")
            
            lyrics = song["text"].split('|')[0][:80]
            f.write(f"    歌词: {lyrics}...\n\n")
    
    # FFmpeg剪辑脚本
    script_file = os.path.join(output_dir, "提取歌曲.sh")
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write("#!/bin/bash\n")
        f.write("# 批量提取歌曲片段\n\n")
        f.write('VIDEO_FILE="/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4"\n')
        f.write('OUTPUT_DIR="提取的歌曲"\n\n')
        f.write('mkdir -p "$OUTPUT_DIR"\n\n')
        
        for i, song in enumerate(songs, 1):
            title = song["title"].replace('/', '_').replace('\\', '_')
            start_time = song["start"]
            duration = song["duration"]
            
            f.write(f'# {i}. {title}\n')
            f.write(f'echo "提取: {title}..."\n')
            f.write(f'ffmpeg -i "$VIDEO_FILE" -ss {start_time} -t {duration} ')
            f.write(f'-c copy -y "$OUTPUT_DIR/{i:02d}_{title}.mp4" 2>/dev/null\n\n')
        
        f.write('echo "✅ 完成！"\n')
        f.write('echo "歌曲已保存到: $OUTPUT_DIR/"\n')
    
    os.chmod(script_file, 0o755)
    
    # 生成剪映草稿脚本（伪代码）
    draft_file = os.path.join(output_dir, "生成剪映草稿_说明.txt")
    with open(draft_file, 'w', encoding='utf-8') as f:
        f.write("生成剪映草稿的思路\n")
        f.write("=" * 70 + "\n\n")
        f.write("方案1：精选集锦（推荐）\n")
        f.write("-" * 70 + "\n")
        f.write("1. 选择最受欢迎的5-6首歌（根据时长和位置）\n")
        f.write("2. 每首歌取高潮部分30-40秒\n")
        f.write("3. 添加转场效果\n")
        f.write("4. 总时长：3-4分钟\n\n")
        
        f.write("推荐歌曲（按直播顺序）:\n")
        for i, song in enumerate(songs[:10], 1):
            f.write(f"  {i}. 《{song['title']}》 "
                   f"({int(song['duration']//60)}:{int(song['duration']%60):02d})\n")
        
        f.write("\n\n方案2：完整歌曲合集\n")
        f.write("-" * 70 + "\n")
        f.write("1. 选择5首完整歌曲\n")
        f.write("2. 添加歌名字幕\n")
        f.write("3. 添加背景效果\n")
        f.write(f"4. 总时长：约{sum(s['duration'] for s in songs[:5])/60:.0f}分钟\n")
    
    print(f"\n✅ 歌曲素材库已生成: {output_dir}/")
    print(f"   - 歌曲列表: {txt_file}")
    print(f"   - JSON数据: {json_file}")
    print(f"   - 提取脚本: {script_file}")
    print(f"   - 使用方法: bash {script_file}")
    
    return songs


if __name__ == "__main__":
    songs = organize_songs()
    
    print("\n" + "=" * 70)
    print("✅ 整理完成！")
    print("=" * 70)

