#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新分类素材 - 将unknown中的唱歌片段识别出来

优化策略：
1. 长时长片段（>15秒）→ 唱歌
2. 包含音符符号、歌词特征 → 唱歌
3. 短文本+长时长 → 唱歌（唱歌时识别不准）
"""

import json
import os
from pathlib import Path


def is_singing_segment(text, duration, original_category):
    """
    判断是否为唱歌片段
    
    Args:
        text: 文本内容
        duration: 持续时间（秒）
        original_category: 原分类
    
    Returns:
        bool
    """
    # 如果已经是singing，保留
    if original_category == "singing":
        return True
    
    # 规则1: 长时长片段很可能是唱歌
    if duration > 15:
        return True
    
    # 规则2: 检测歌曲特征词
    singing_keywords = [
        "♪", "♫", "🎵", "🎶",  # 音符符号
        "啦啦", "哦哦", "呜呜",  # 语气词（唱歌常见）
        "嗯嗯", "呀呀", "唔唔"
    ]
    
    for keyword in singing_keywords:
        if keyword in text:
            return True
    
    # 规则3: 短文本+中等时长 → 可能是唱歌（识别不准）
    if len(text) < 10 and duration > 8:
        return True
    
    # 规则4: 文本长度与时长不匹配（语速很慢，可能是唱歌）
    if len(text) > 0:
        chars_per_second = len(text) / duration
        if chars_per_second < 2:  # 每秒少于2个字
            return True
    
    return False


def reclassify_materials(base_dir=None, output_dir=None):
    """
    重新分类所有素材
    
    Args:
        base_dir: 源目录
        output_dir: 输出目录
    """
    if base_dir is None:
        base_dir = os.path.expanduser("~/shanshan_materials/素材库_原始")
    if output_dir is None:
        output_dir = os.path.expanduser("~/shanshan_materials/素材库_最新")
    print("=" * 70)
    print("重新分类素材")
    print("=" * 70)
    
    # 读取所有分类文件
    categories = ["singing", "gift", "chat", "unknown"]
    all_segments = []
    
    for category in categories:
        file_path = f"{base_dir}/{category}_素材.json"
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                segments = data.get("segments", [])
            else:
                segments = data
            
            print(f"加载 {category}: {len(segments)} 个片段")
            
            for seg in segments:
                seg["original_category"] = category
                all_segments.append(seg)
    
    print(f"\n总计: {len(all_segments)} 个片段")
    
    # 重新分类
    print("\n开始重新分类...")
    
    new_singing = []
    new_gift = []
    new_chat = []
    new_unknown = []
    
    for seg in all_segments:
        text = seg.get("text", "")
        duration = seg.get("duration", 0)
        original = seg.get("original_category", "unknown")
        
        # 保留gift分类
        if original == "gift":
            new_gift.append(seg)
        # 判断是否为唱歌
        elif is_singing_segment(text, duration, original):
            new_singing.append(seg)
        # 短文本+短时长 → 闲聊
        elif len(text) < 20 and duration < 5:
            new_chat.append(seg)
        # 其他归为未知
        else:
            new_unknown.append(seg)
    
    # 输出统计
    print("\n重新分类结果:")
    print(f"  唱歌: {len(new_singing)} 个 (原 {sum(1 for s in all_segments if s['original_category']=='singing')} 个)")
    print(f"  礼物: {len(new_gift)} 个")
    print(f"  闲聊: {len(new_chat)} 个")
    print(f"  未知: {len(new_unknown)} 个")
    
    # 保存到新路径
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    categories_data = {
        "singing": new_singing,
        "gift": new_gift,
        "chat": new_chat,
        "unknown": new_unknown
    }
    
    for category, segments in categories_data.items():
        # 保存JSON
        json_path = output_path / f"{category}_素材.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "category": category,
                "total_count": len(segments),
                "total_duration": sum(s.get("duration", 0) for s in segments),
                "segments": segments
            }, f, ensure_ascii=False, indent=2)
        
        # 保存TXT
        txt_path = output_path / f"{category}_素材.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"{category.upper()} 素材列表\n")
            f.write("=" * 70 + "\n\n")
            
            for i, seg in enumerate(segments, 1):
                f.write(f"[{i}] {seg.get('start', 0):.2f}s - {seg.get('end', 0):.2f}s "
                       f"({seg.get('duration', 0):.1f}s)\n")
                f.write(f"    {seg.get('text', '')}\n\n")
    
    # 生成统计报告
    report_path = output_path / "分类统计报告.txt"
    total_duration = sum(s.get("duration", 0) for s in all_segments)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("直播内容分类统计报告（重新分类）\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"总片段数: {len(all_segments)}\n")
        f.write(f"总时长: {total_duration/60:.1f} 分钟\n\n")
        f.write("各类别统计:\n")
        f.write("-" * 70 + "\n\n")
        
        for category, segments in categories_data.items():
            icon = {"singing": "🎤", "gift": "🎁", "chat": "💬", "unknown": "❓"}
            name = {"singing": "唱歌片段", "gift": "礼物感谢", "chat": "闲聊互动", "unknown": "未分类"}
            
            cat_duration = sum(s.get("duration", 0) for s in segments)
            avg_duration = cat_duration / len(segments) if segments else 0
            
            f.write(f"{icon[category]} {name[category]}\n")
            f.write(f"  片段数: {len(segments)} 个\n")
            f.write(f"  总时长: {cat_duration/60:.1f} 分钟 ({cat_duration/total_duration*100:.1f}%)\n")
            f.write(f"  平均时长: {avg_duration:.1f} 秒\n\n")
    
    print(f"\n✓ 素材已保存到: {output_dir}")
    print(f"✓ 统计报告: {report_path}")


if __name__ == "__main__":
    reclassify_materials()

