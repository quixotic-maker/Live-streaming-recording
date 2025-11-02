#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成剪映草稿 - 歌曲集锦版

功能：
1. 基于歌曲列表生成剪映草稿
2. 自动添加歌名字幕
3. 可选择完整版或精选版
"""

import os
import sys
import json
from pathlib import Path

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jianying_draft import JianYingDraft


def load_songs(song_file: str) -> list:
    """加载歌曲列表"""
    with open(song_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("songs", [])


def generate_song_collection_draft(video_path: str, songs: list,
                                   output_dir: str, mode: str = "selected"):
    """
    生成歌曲集锦草稿
    
    Args:
        video_path: 视频文件路径
        songs: 歌曲列表
        output_dir: 输出目录
        mode: 模式 ("selected" = 精选10首, "full" = 全部歌曲)
    """
    
    print(f"\n生成模式: {mode}")
    print("-" * 70)
    
    # 选择歌曲
    if mode == "selected":
        # 精选：选择时长适中的歌曲（60-180秒）
        selected_songs = [
            s for s in songs
            if 60 <= s.get("duration", 0) <= 180
        ][:10]
        draft_name = f"歌曲集锦_精选{len(selected_songs)}首"
    else:
        selected_songs = songs
        draft_name = f"歌曲集锦_完整{len(selected_songs)}首"
    
    print(f"选中歌曲: {len(selected_songs)} 首\n")
    
    # 创建草稿
    draft = JianYingDraft(
        project_name=draft_name,
        output_dir=output_dir
    )
    
    # 添加视频素材
    video_material_id = draft.add_video_material(video_path)
    
    # 添加每首歌的片段和字幕
    for i, song in enumerate(selected_songs, 1):
        title = song.get("title", f"歌曲{i}")
        start = song["start"]
        duration = song["duration"]
        
        print(f"[{i}/{len(selected_songs)}] {title} ({duration:.0f}秒)")
        
        # 添加视频片段
        draft.add_video_segment(
            material_id=video_material_id,
            duration=duration,
            track_index=0
        )
        
        # 添加歌名字幕（显示在开头5秒）
        draft.add_text_segment(
            text=f"♪ {title} ♪",
            start=sum(s["duration"] for s in selected_songs[:i-1]),
            duration=min(5.0, duration),
            style={
                "font": "默认",
                "font_size": 32.0,
                "color": [255, 255, 0],  # 黄色
                "bold": True
            }
        )
    
    # 保存草稿
    draft_path = draft.save(draft_name)
    
    total_duration = draft.get_total_duration()
    print(f"\n总时长: {total_duration/60:.1f} 分钟")
    print(f"草稿路径: {draft_path}")
    
    return draft_path


def main():
    """主函数"""
    print("=" * 70)
    print("剪映草稿生成器 - 歌曲集锦")
    print("=" * 70)
    
    # 配置
    video_path = "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4"
    material_dir = os.path.expanduser("~/shanshan_materials")
    song_file = os.path.join(material_dir, "歌曲素材库/歌曲列表.json")
    output_dir = os.path.join(material_dir, "剪映草稿")
    
    # 验证文件
    if not os.path.exists(video_path):
        print(f"错误: 视频文件不存在: {video_path}")
        return
    
    if not os.path.exists(song_file):
        print(f"错误: 歌曲列表不存在: {song_file}")
        return
    
    print(f"\n视频文件: {video_path}")
    print(f"歌曲列表: {song_file}")
    print(f"输出目录: {output_dir}\n")
    
    # 加载歌曲
    songs = load_songs(song_file)
    print(f"总歌曲数: {len(songs)}")
    
    # 选择模式
    print("\n请选择生成模式:")
    print("  1. 精选10首（时长1-3分钟的歌曲）")
    print("  2. 全部歌曲")
    
    try:
        choice = input("\n选择 (1-2, 默认1): ").strip() or "1"
        
        if choice == "1":
            mode = "selected"
        elif choice == "2":
            mode = "full"
        else:
            print("无效选择")
            return
        
        # 生成草稿
        draft_path = generate_song_collection_draft(
            video_path, songs, output_dir, mode
        )
        
        print("\n" + "=" * 70)
        print("✅ 剪映草稿生成完成！")
        print("=" * 70)
        print("\n使用方法:")
        print(f"1. 打开剪映专业版")
        print(f"2. 导入草稿目录: {draft_path}")
        print(f"3. 可直接编辑或导出视频")
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()



