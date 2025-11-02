#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成剪映草稿 - 完整视频分段版

功能：
1. 基于内容分类生成分段草稿
2. 自动标记唱歌、礼物、闲聊片段
3. 添加章节字幕标记
"""

import os
import sys
import json
from pathlib import Path

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jianying_draft import JianYingDraft


def load_materials(material_dir: str) -> dict:
    """加载所有素材"""
    materials = {}
    
    # 加载唱歌
    singing_file = Path(material_dir) / "素材库_最新" / "singing_素材.json"
    if singing_file.exists():
        with open(singing_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        materials["singing"] = data.get("segments", [])
    
    # 加载礼物
    gift_file = Path(material_dir) / "素材库_最新" / "gift_素材.json"
    if gift_file.exists():
        with open(gift_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        materials["gift"] = data.get("segments", [])
    
    # 加载闲聊
    chat_file = Path(material_dir) / "素材库_最新" / "chat_素材.json"
    if chat_file.exists():
        with open(chat_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        materials["chat"] = data.get("segments", [])
    
    return materials


def merge_timeline(materials: dict) -> list:
    """合并所有素材到时间线"""
    timeline = []
    
    for category, segments in materials.items():
        for seg in segments:
            timeline.append({
                "start": seg["start"],
                "end": seg["end"],
                "duration": seg["duration"],
                "category": category,
                "text": seg.get("text", "")
            })
    
    # 按时间排序
    timeline.sort(key=lambda x: x["start"])
    
    return timeline


def generate_segmented_draft(video_path: str, materials: dict,
                             output_dir: str, max_segments: int = 50):
    """
    生成完整分段草稿
    
    Args:
        video_path: 视频文件路径
        materials: 素材字典
        output_dir: 输出目录
        max_segments: 最大片段数（避免草稿过大）
    """
    
    print(f"\n生成完整分段草稿")
    print("-" * 70)
    
    # 合并时间线
    timeline = merge_timeline(materials)
    
    # 限制片段数
    if len(timeline) > max_segments:
        print(f"⚠ 片段过多 ({len(timeline)}个)，只取前 {max_segments} 个")
        timeline = timeline[:max_segments]
    
    print(f"总片段数: {len(timeline)}\n")
    
    # 统计各类型数量
    category_counts = {}
    for item in timeline:
        cat = item["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    for cat, count in category_counts.items():
        emoji = {"singing": "🎤", "gift": "🎁", "chat": "💬"}.get(cat, "❓")
        print(f"  {emoji} {cat}: {count} 个")
    
    # 创建草稿
    draft_name = f"完整分段_{len(timeline)}片段"
    draft = JianYingDraft(
        project_name=draft_name,
        output_dir=output_dir
    )
    
    # 添加视频素材
    video_material_id = draft.add_video_material(video_path)
    
    # 添加片段和标记
    print("\n添加片段...")
    category_colors = {
        "singing": [255, 200, 0],   # 金色
        "gift": [255, 100, 100],    # 红色
        "chat": [100, 200, 255]     # 蓝色
    }
    
    category_names = {
        "singing": "🎤 唱歌",
        "gift": "🎁 礼物",
        "chat": "💬 互动"
    }
    
    for i, item in enumerate(timeline, 1):
        if i % 10 == 0:
            print(f"  处理 {i}/{len(timeline)}...")
        
        # 添加视频片段
        draft.add_video_segment(
            material_id=video_material_id,
            duration=item["duration"],
            track_index=0
        )
        
        # 添加分类标记（前3秒）
        category = item["category"]
        label = category_names.get(category, category)
        
        draft.add_text_segment(
            text=label,
            start=sum(timeline[j]["duration"] for j in range(i-1)),
            duration=min(3.0, item["duration"]),
            style={
                "font": "默认",
                "font_size": 20.0,
                "color": category_colors.get(category, [255, 255, 255]),
                "bold": False
            }
        )
    
    # 保存草稿
    print(f"\n保存草稿...")
    draft_path = draft.save(draft_name)
    
    total_duration = draft.get_total_duration()
    print(f"✓ 总时长: {total_duration/60:.1f} 分钟")
    print(f"✓ 草稿路径: {draft_path}")
    
    return draft_path


def main():
    """主函数"""
    print("=" * 70)
    print("剪映草稿生成器 - 完整视频分段")
    print("=" * 70)
    
    # 配置
    video_path = "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4"
    material_dir = os.path.expanduser("~/shanshan_materials")
    output_dir = os.path.join(material_dir, "剪映草稿")
    
    # 验证文件
    if not os.path.exists(video_path):
        print(f"错误: 视频文件不存在: {video_path}")
        return
    
    print(f"\n视频文件: {video_path}")
    print(f"素材目录: {material_dir}")
    print(f"输出目录: {output_dir}\n")
    
    # 加载素材
    print("加载素材...")
    materials = load_materials(material_dir)
    
    if not materials:
        print("错误: 没有找到素材")
        return
    
    for cat, segs in materials.items():
        print(f"  {cat}: {len(segs)} 个片段")
    
    try:
        # 生成草稿
        draft_path = generate_segmented_draft(
            video_path, materials, output_dir
        )
        
        print("\n" + "=" * 70)
        print("✅ 剪映草稿生成完成！")
        print("=" * 70)
        print("\n使用方法:")
        print(f"1. 打开剪映专业版")
        print(f"2. 导入草稿: {draft_path}")
        print(f"3. 所有片段已按类型标记")
        print(f"4. 可根据标记进行二次剪辑")
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()



