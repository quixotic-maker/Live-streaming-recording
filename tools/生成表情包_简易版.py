#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表情包生成 - 简易版

特点：
1. 跳过复杂检测，直接使用已有的素材数据
2. 高质量GIF（2MB, 256色, 20fps）
3. 快速生成（10-20分钟）
4. 3种类型：手势舞 + 感谢 + 可爱
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from emoji_generator import EmojiGenerator


def load_material_data():
    """加载素材数据"""
    material_dir = os.path.expanduser("~/shanshan_materials/素材库_最新")
    
    # 1. 加载感谢素材
    thank_moments = []
    gift_file = os.path.join(material_dir, "gift_素材.json")
    if os.path.exists(gift_file):
        with open(gift_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        segments = data.get("segments", []) if isinstance(data, dict) else data
        for seg in segments[:100]:  # 最多100个
            if "谢谢" in seg.get("text", ""):
                thank_moments.append({
                    "start": seg["start"],
                    "end": min(seg["start"] + 2.0, seg["end"]),  # 2秒
                    "type": "thank"
                })
    
    # 2. 加载可爱表情素材
    cute_moments = []
    chat_file = os.path.join(material_dir, "chat_素材.json")
    if os.path.exists(chat_file):
        with open(chat_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        segments = data.get("segments", []) if isinstance(data, dict) else data
        
        cute_keywords = ["哈哈", "嘿嘿", "嘻嘻", "爱你", "么么", "亲亲", "抱抱", "比心"]
        
        for seg in segments[:200]:  # 检查前200个
            text = seg.get("text", "")
            if any(kw in text for kw in cute_keywords):
                cute_moments.append({
                    "start": seg["start"],
                    "end": min(seg["start"] + 2.0, seg["end"]),
                    "type": "cute"
                })
                if len(cute_moments) >= 50:
                    break
    
    # 3. 手动添加一些可能的手势舞时间点（根据经验）
    dance_moments = []
    # 前30分钟每5分钟取一个2秒片段
    for i in range(0, 1800, 300):
        dance_moments.append({
            "start": i,
            "end": i + 2.0,
            "type": "dance"
        })
    
    return {
        "thank": thank_moments,
        "cute": cute_moments,
        "dance": dance_moments
    }


def generate_emojis(video_path, output_dir, max_per_type=30):
    """生成表情包"""
    
    print("=" * 80)
    print("表情包生成 - 简易版")
    print("=" * 80)
    print()
    
    # 检查视频
    if not os.path.exists(video_path):
        print(f"✗ 视频不存在: {video_path}")
        return
    
    print(f"视频: {video_path}")
    print()
    
    # 加载数据
    print("加载素材数据...")
    materials = load_material_data()
    
    print(f"  感谢表情: {len(materials['thank'])}个")
    print(f"  可爱表情: {len(materials['cute'])}个")
    print(f"  手势舞候选: {len(materials['dance'])}个")
    print()
    
    # 创建生成器（高质量配置）
    emoji_config = {
        "max_size_kb": 2000,    # 2MB
        "quality": 95,
        "default_fps": 20,
        "optimize": True
    }
    
    generator = EmojiGenerator(emoji_config)
    
    # 创建临时目录
    temp_dir = Path("temp_emojis_simple")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 收集所有候选
    all_candidates = []
    
    for emoji_type, moments in materials.items():
        for moment in moments[:max_per_type]:
            all_candidates.append({
                **moment,
                "type": emoji_type
            })
    
    print(f"准备生成 {len(all_candidates)} 个表情包")
    print(f"  感谢: {min(len(materials['thank']), max_per_type)}个")
    print(f"  可爱: {min(len(materials['cute']), max_per_type)}个")
    print(f"  手势舞: {min(len(materials['dance']), max_per_type)}个")
    print()
    print("高质量配置: 2MB, 256色, 20fps")
    print()
    
    # 生成
    success_count = 0
    
    for i, candidate in enumerate(all_candidates, 1):
        emoji_type = candidate["type"]
        
        print(f"[{i}/{len(all_candidates)}] 生成 {emoji_type} 表情包...", end="", flush=True)
        
        try:
            base_name = f"emoji_{emoji_type}_{i:03d}"
            output_type_dir = temp_dir / emoji_type
            
            result = generator.generate_multi_specs(
                video_path=video_path,
                start=candidate["start"],
                end=candidate["end"],
                output_dir=str(output_type_dir),
                base_name=base_name
            )
            
            print(f" ✓")
            success_count += 1
            
        except Exception as e:
            print(f" ✗ {e}")
    
    print()
    print("=" * 80)
    print(f"✅ 完成！成功生成 {success_count}/{len(all_candidates)} 个表情包")
    print("=" * 80)
    print()
    print(f"输出目录: {temp_dir}/")
    print()
    print("下一步:")
    print("  1. 查看: ls -lh temp_emojis_simple/")
    print("  2. 适配抖音: python3 抖音表情包完整适配.py")
    print("  3. 添加文字: python3 表情包添加文字.py")
    print()


def main():
    video_path = "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4"
    output_dir = os.path.expanduser("~/shanshan_materials/表情包素材库")
    
    print()
    choice = input("确认生成表情包？[y/N]: ").strip().lower()
    
    if choice == 'y':
        generate_emojis(video_path, output_dir)
    else:
        print("已取消")


if __name__ == "__main__":
    main()



