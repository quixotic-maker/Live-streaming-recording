#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精彩集锦生成工具

功能：
1. 基于多模态检测/分类素材自动选择精彩片段
2. 智能剪辑和排序
3. 生成不同时长版本（1分钟/3分钟/5分钟）
4. FFmpeg视频剪辑和转场
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import random


class HighlightGenerator:
    """精彩集锦生成器"""
    
    def __init__(self, video_path: str, output_dir: str):
        """
        初始化生成器
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
        """
        self.video_path = video_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 验证ffmpeg
        if subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0:
            raise RuntimeError("未找到ffmpeg，请先安装")
        
        print(f"视频文件: {video_path}")
        print(f"输出目录: {output_dir}\n")
    
    def load_materials(self, material_dir: str) -> Dict[str, List[Dict]]:
        """
        加载素材数据
        
        Args:
            material_dir: 素材目录
            
        Returns:
            分类素材字典
        """
        print("加载素材数据...")
        material_dir = Path(material_dir)
        materials = {}
        
        # 加载歌曲
        song_file = material_dir / "歌曲素材库" / "歌曲列表.json"
        if song_file.exists():
            with open(song_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            materials["songs"] = data.get("songs", [])
            print(f"  ✓ 歌曲: {len(materials['songs'])} 首")
        
        # 加载礼物感谢
        gift_file = material_dir / "素材库_最新" / "gift_素材.json"
        if gift_file.exists():
            with open(gift_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            segments = data.get("segments", []) if isinstance(data, dict) else data
            materials["gifts"] = segments
            print(f"  ✓ 礼物感谢: {len(materials['gifts'])} 个")
        
        # 加载闲聊
        chat_file = material_dir / "素材库_最新" / "chat_素材.json"
        if chat_file.exists():
            with open(chat_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            segments = data.get("segments", []) if isinstance(data, dict) else data
            materials["chats"] = segments
            print(f"  ✓ 闲聊互动: {len(materials['chats'])} 个")
        
        return materials
    
    def select_highlights(self, materials: Dict, target_duration: int,
                          weights: Dict[str, float] = None) -> List[Dict]:
        """
        智能选择精彩片段
        
        Args:
            materials: 素材字典
            target_duration: 目标总时长（秒）
            weights: 各类型权重 {"songs": 0.6, "gifts": 0.3, "chats": 0.1}
            
        Returns:
            选中的片段列表
        """
        if weights is None:
            weights = {
                "songs": 0.60,   # 歌曲占60%
                "gifts": 0.30,   # 礼物占30%
                "chats": 0.10    # 闲聊占10%
            }
        
        print(f"\n选择精彩片段 (目标时长: {target_duration}秒)")
        print("-" * 70)
        
        selected = []
        
        # 1. 选择歌曲片段
        if "songs" in materials and materials["songs"]:
            songs = materials["songs"]
            song_duration = target_duration * weights["songs"]
            
            # 优先选择时长适中的歌曲（60-180秒）
            suitable_songs = [
                s for s in songs
                if 60 <= s.get("duration", 0) <= 180
            ]
            
            if not suitable_songs:
                suitable_songs = songs
            
            # 随机选择
            selected_songs = []
            current_duration = 0
            
            for song in random.sample(suitable_songs, min(len(suitable_songs), 10)):
                if current_duration >= song_duration:
                    break
                
                # 取高潮部分（中间1/3）
                duration = song["duration"]
                start = song["start"] + duration * 0.33
                clip_duration = min(30, duration * 0.33)  # 最多30秒
                
                selected_songs.append({
                    "type": "song",
                    "title": song.get("title", "歌曲"),
                    "start": start,
                    "duration": clip_duration,
                    "priority": 10
                })
                
                current_duration += clip_duration
            
            selected.extend(selected_songs)
            print(f"  选择歌曲: {len(selected_songs)} 个片段，共 {current_duration:.1f}秒")
        
        # 2. 选择礼物感谢片段
        if "gifts" in materials and materials["gifts"]:
            gifts = materials["gifts"]
            gift_duration = target_duration * weights["gifts"]
            
            # 选择时长适中的片段（3-15秒）
            suitable_gifts = [
                g for g in gifts
                if 3 <= g.get("duration", 0) <= 15
            ]
            
            selected_gifts = []
            current_duration = 0
            
            for gift in random.sample(suitable_gifts, min(len(suitable_gifts), 20)):
                if current_duration >= gift_duration:
                    break
                
                selected_gifts.append({
                    "type": "gift",
                    "title": "感谢礼物",
                    "start": gift["start"],
                    "duration": min(gift["duration"], 10),  # 最多10秒
                    "priority": 8,
                    "text": gift.get("text", "")[:30]
                })
                
                current_duration += selected_gifts[-1]["duration"]
            
            selected.extend(selected_gifts)
            print(f"  选择礼物: {len(selected_gifts)} 个片段，共 {current_duration:.1f}秒")
        
        # 3. 选择闲聊互动片段
        if "chats" in materials and materials["chats"]:
            chats = materials["chats"]
            chat_duration = target_duration * weights["chats"]
            
            # 选择短小精悍的片段（3-8秒）
            suitable_chats = [
                c for c in chats
                if 3 <= c.get("duration", 0) <= 8 and len(c.get("text", "")) > 10
            ]
            
            selected_chats = []
            current_duration = 0
            
            for chat in random.sample(suitable_chats, min(len(suitable_chats), 10)):
                if current_duration >= chat_duration:
                    break
                
                selected_chats.append({
                    "type": "chat",
                    "title": "互动时刻",
                    "start": chat["start"],
                    "duration": min(chat["duration"], 6),  # 最多6秒
                    "priority": 5,
                    "text": chat.get("text", "")[:30]
                })
                
                current_duration += selected_chats[-1]["duration"]
            
            selected.extend(selected_chats)
            print(f"  选择互动: {len(selected_chats)} 个片段，共 {current_duration:.1f}秒")
        
        # 按时间排序（保持故事线）
        selected.sort(key=lambda x: x["start"])
        
        total_duration = sum(s["duration"] for s in selected)
        print(f"\n总计: {len(selected)} 个片段，总时长 {total_duration:.1f}秒")
        
        return selected
    
    def generate_clip(self, segments: List[Dict], output_file: str,
                      add_transitions: bool = True) -> bool:
        """
        生成视频集锦
        
        Args:
            segments: 片段列表
            output_file: 输出文件
            add_transitions: 是否添加转场
            
        Returns:
            是否成功
        """
        print(f"\n生成视频集锦: {output_file}")
        print("-" * 70)
        
        if not segments:
            print("错误: 没有可用片段")
            return False
        
        temp_dir = self.output_dir / "temp_clips"
        temp_dir.mkdir(exist_ok=True)
        
        # 1. 提取各个片段
        clip_files = []
        for i, seg in enumerate(segments):
            clip_file = temp_dir / f"clip_{i:03d}.mp4"
            
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(seg["start"]),
                "-t", str(seg["duration"]),
                "-i", self.video_path,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                str(clip_file)
            ]
            
            print(f"  提取片段 {i+1}/{len(segments)}: {seg.get('title', '?')}")
            
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                clip_files.append(clip_file)
            else:
                print(f"    ⚠ 提取失败")
        
        if not clip_files:
            print("错误: 没有成功提取的片段")
            return False
        
        # 2. 合并片段
        print(f"\n合并 {len(clip_files)} 个片段...")
        
        # 创建concat文件
        concat_file = temp_dir / "concat.txt"
        with open(concat_file, 'w', encoding='utf-8') as f:
            for clip in clip_files:
                f.write(f"file '{clip.absolute()}'\n")
        
        # 合并
        output_path = self.output_dir / output_file
        
        if add_transitions:
            # 使用xfade滤镜添加转场（更复杂，这里简化）
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                str(output_path)
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                str(output_path)
            ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            # 获取文件大小
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"✓ 生成成功: {output_path}")
            print(f"  文件大小: {size_mb:.1f} MB")
            
            # 清理临时文件
            for clip in clip_files:
                clip.unlink()
            concat_file.unlink()
            
            return True
        else:
            print(f"✗ 合并失败")
            return False
    
    def generate_all_versions(self, materials: Dict):
        """
        生成所有版本的集锦
        
        Args:
            materials: 素材字典
        """
        versions = [
            {"name": "1分钟精华版", "duration": 60, "file": "精彩集锦_1分钟.mp4"},
            {"name": "3分钟完整版", "duration": 180, "file": "精彩集锦_3分钟.mp4"},
            {"name": "5分钟加长版", "duration": 300, "file": "精彩集锦_5分钟.mp4"},
        ]
        
        results = []
        
        for version in versions:
            print("\n" + "=" * 70)
            print(f"生成 {version['name']}")
            print("=" * 70)
            
            # 选择片段
            segments = self.select_highlights(materials, version["duration"])
            
            if segments:
                # 生成视频
                success = self.generate_clip(segments, version["file"])
                
                if success:
                    results.append({
                        "version": version["name"],
                        "file": version["file"],
                        "segment_count": len(segments),
                        "duration": sum(s["duration"] for s in segments)
                    })
                    
                    # 保存片段列表
                    segment_file = self.output_dir / version["file"].replace(".mp4", "_片段列表.json")
                    with open(segment_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "version": version["name"],
                            "total_segments": len(segments),
                            "total_duration": sum(s["duration"] for s in segments),
                            "segments": segments
                        }, f, ensure_ascii=False, indent=2)
        
        return results
    
    def generate_summary(self, results: List[Dict]):
        """
        生成总结报告
        
        Args:
            results: 生成结果列表
        """
        summary_file = self.output_dir / "生成报告.txt"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("精彩集锦生成报告\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"源视频: {self.video_path}\n")
            f.write(f"输出目录: {self.output_dir}\n\n")
            
            f.write("生成结果:\n")
            f.write("-" * 70 + "\n")
            
            for result in results:
                f.write(f"\n{result['version']}\n")
                f.write(f"  文件: {result['file']}\n")
                f.write(f"  片段数: {result['segment_count']}\n")
                f.write(f"  时长: {result['duration']:.1f}秒\n")
            
            f.write("\n使用说明:\n")
            f.write("-" * 70 + "\n")
            f.write("1. 查看各版本视频\n")
            f.write("2. 查看 *_片段列表.json 了解详细时间点\n")
            f.write("3. 可用于后续二次剪辑\n")
        
        print(f"\n✓ 总结报告: {summary_file}")


def main():
    """主函数"""
    print("=" * 70)
    print("精彩集锦生成工具")
    print("=" * 70)
    
    # 配置
    video_path = "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4"
    output_dir = os.path.expanduser("~/shanshan_materials/精彩集锦")
    material_dir = os.path.expanduser("~/shanshan_materials")
    
    # 验证视频文件
    if not os.path.exists(video_path):
        print(f"错误: 视频文件不存在: {video_path}")
        print("\n请修改脚本中的 video_path 为实际路径")
        return
    
    try:
        # 创建生成器
        generator = HighlightGenerator(video_path, output_dir)
        
        # 加载素材
        materials = generator.load_materials(material_dir)
        
        if not materials:
            print("错误: 没有找到可用素材")
            return
        
        # 生成所有版本
        results = generator.generate_all_versions(materials)
        
        # 生成总结
        if results:
            generator.generate_summary(results)
            
            print("\n" + "=" * 70)
            print("✅ 所有集锦生成完成！")
            print("=" * 70)
            print(f"\n输出目录: {output_dir}")
            for result in results:
                print(f"  - {result['file']} ({result['duration']:.0f}秒)")
        else:
            print("\n⚠ 未能生成任何集锦")
    
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()



