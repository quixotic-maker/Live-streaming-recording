#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表情包素材生成 - 完整版

与优化版的区别：
1. 分析完整视频（不限制时长）
2. 更低的检测阈值（更多候选）
3. 更大的文件大小限制（更好的质量）
4. 更多的表情包类型
5. 更智能的可爱表情识别
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gesture_detector import MotionDetector, PoseDetector, MultimodalDetector
from emoji_generator import EmojiGenerator
from material_organizer import MaterialOrganizer


# 完整版配置参数
config = {
    "video_path": "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4",
    "output_dir": os.path.expanduser("~/shanshan_materials/表情包素材库"),
    "temp_dir": "temp_emojis_full",
    
    # 检测参数（更宽松）
    "motion_config": {
        "motion_threshold": 0.05,      # 更低（从0.08降到0.05）
        "min_duration": 1.0,            # 更短（从1.5降到1.0）
        "merge_gap": 3.0                # 更大（从2.0升到3.0）
    },
    
    "multimodal_config": {
        "recommend_threshold": 0.3,     # 更低（从0.4降到0.3）
        "gesture_weight": 0.5,
        "effect_weight": 0.3,
        "emotion_weight": 0.3           # 增加情绪权重
    },
    
    # 质量参数（更高）
    "emoji_config": {
        "max_size_kb": 2000,            # 从1000KB提升到2000KB
        "quality": 95,                  # 从85提升到95
        "optimize": True,
        "default_fps": 20,              # 从15提升到20
    },
    
    # 完整版参数
    "analysis_config": {
        "analyze_duration": None,       # None = 完整视频
        "dance_duration": 3600,         # 前60分钟查找手势舞
        "max_dance_moments": 50,        # 最多50个手势舞
        "max_thank_moments": 100,       # 最多100个感谢
        "max_cute_moments": 50,         # 最多50个可爱表情
    }
}


class FullEmojiMaterialGenerator:
    """表情包素材生成器 - 完整版"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.video_path = config["video_path"]
        self.output_dir = config["output_dir"]
        self.temp_dir = config.get("temp_dir", "temp_emojis_full")
        
        if not os.path.exists(self.video_path):
            raise FileNotFoundError(f"视频文件不存在: {self.video_path}")
        
        # 创建检测器（使用完整版参数）
        self.motion_detector = MotionDetector(config.get("motion_config", {}))
        self.pose_detector = PoseDetector()
        self.multimodal_detector = MultimodalDetector(config.get("multimodal_config", {}))
        
        # 创建生成器（使用高质量参数）
        emoji_config = config.get("emoji_config", {})
        self.emoji_generator = EmojiGenerator(emoji_config)
        
        self.organizer = MaterialOrganizer(self.output_dir)
        
        self.dance_moments = []
        self.thank_moments = []
        self.cute_moments = []
        self.all_emojis = []
        
        print("=" * 80)
        print("表情包素材生成系统（完整版）已初始化")
        print("=" * 80)
        print(f"视频路径: {self.video_path}")
        print(f"输出目录: {self.output_dir}")
        print(f"\n完整版配置:")
        print(f"  运动阈值: {config['motion_config']['motion_threshold']} (更低)")
        print(f"  推荐阈值: {config['multimodal_config']['recommend_threshold']} (更低)")
        print(f"  文件大小限制: {config['emoji_config']['max_size_kb']}KB (更大)")
        print(f"  帧率: {config['emoji_config']['default_fps']}fps (更高)")
        print(f"  手势舞分析: 前{config['analysis_config']['dance_duration']/60:.0f}分钟")
        print(f"  完整视频分析: {'是' if not config['analysis_config']['analyze_duration'] else '否'}")
        print()
    
    def load_data(self):
        """加载已有数据"""
        print("\n[步骤1] 加载已有数据")
        print("-" * 80)
        
        # 加载礼物感谢数据
        gift_file = os.path.expanduser("~/shanshan_materials/素材库_最新/gift_素材.json")
        if os.path.exists(gift_file):
            with open(gift_file, 'r', encoding='utf-8') as f:
                gift_data = json.load(f)
            
            segments = gift_data.get("segments", []) if isinstance(gift_data, dict) else gift_data
            for item in segments:
                if isinstance(item, dict) and "谢谢" in item.get("text", ""):
                    self.thank_moments.append({
                        "time": item.get("start", 0),
                        "keyword": "谢谢",
                        "text": item.get("text", "")
                    })
            
            print(f"✓ 加载礼物感谢数据: {len(self.thank_moments)}个时刻")
        else:
            print("⚠ 未找到礼物感谢数据")
        
        # 加载聊天数据（查找可爱表情）
        chat_file = os.path.expanduser("~/shanshan_materials/素材库_最新/chat_素材.json")
        if os.path.exists(chat_file):
            with open(chat_file, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
            
            segments = chat_data.get("segments", []) if isinstance(chat_data, dict) else chat_data
            
            # 可爱表情的关键词
            cute_keywords = [
                "哈哈", "嘿嘿", "嘻嘻", "哎呀", "呀", "哇",
                "好可爱", "好萌", "好喜欢", "爱你", "么么",
                "亲亲", "抱抱", "啵啵", "笔芯", "比心"
            ]
            
            for item in segments:
                if isinstance(item, dict):
                    text = item.get("text", "")
                    for keyword in cute_keywords:
                        if keyword in text:
                            self.cute_moments.append({
                                "time": item.get("start", 0),
                                "keyword": keyword,
                                "text": text
                            })
                            break  # 只记录一次
            
            print(f"✓ 加载可爱表情数据: {len(self.cute_moments)}个候选")
        else:
            print("⚠ 未找到聊天数据")
        
        print(f"\n数据加载完成:")
        print(f"  感谢时刻: {len(self.thank_moments)}个")
        print(f"  可爱表情候选: {len(self.cute_moments)}个")
    
    def detect_dance_moments(self):
        """检测手势舞片段（分析前60分钟）"""
        print("\n[步骤2] 手势舞检测")
        print("-" * 80)
        
        dance_duration = self.config["analysis_config"]["dance_duration"]
        threshold = self.config["motion_config"]["motion_threshold"]
        
        print(f"分析时间范围: 0-{dance_duration/60:.0f}分钟")
        print(f"运动阈值: {threshold}")
        print("这可能需要5-10分钟...")
        
        try:
            candidates = self.motion_detector.detect_dance_moments(
                video_path=self.video_path,
                start_time=0,
                end_time=dance_duration
            )
            
            print(f"\n✓ 找到 {len(candidates)} 个手势舞候选片段")
            
            if len(candidates) > 0:
                print("\n前5个候选:")
                for i, candidate in enumerate(candidates[:5], 1):
                    print(f"  {i}. {candidate['start']:.2f}s - {candidate['end']:.2f}s, "
                          f"运动得分: {candidate.get('score', 0):.2f}")
            else:
                print("⚠ 未找到手势舞候选，建议:")
                print("  1. 检查视频前60分钟是否有大幅度动作")
                print("  2. 尝试运行: python3 分析手势舞阈值.py")
                print("  3. 手动指定时间段")
            
            self.dance_moments = candidates
        
        except Exception as e:
            print(f"✗ 手势舞检测失败: {e}")
            self.dance_moments = []
    
    def analyze_thank_moments(self):
        """分析感谢时刻（多模态）"""
        print("\n[步骤3] 感谢表情分析")
        print("-" * 80)
        
        max_moments = self.config["analysis_config"]["max_thank_moments"]
        moments_to_analyze = self.thank_moments[:max_moments]
        
        print(f"分析 {len(moments_to_analyze)} 个感谢时刻（共{len(self.thank_moments)}个）...")
        print(f"推荐阈值: {self.config['multimodal_config']['recommend_threshold']}")
        
        analyzed_moments = []
        
        for i, moment in enumerate(moments_to_analyze, 1):
            print(f"\r处理中... {i}/{len(moments_to_analyze)}", end="", flush=True)
            
            try:
                result = self.multimodal_detector.analyze_thank_moment(
                    video_path=self.video_path,
                    time=moment["time"],
                    keyword=moment["keyword"]
                )
                
                if result["recommended"]:
                    analyzed_moments.append({
                        "start": result["best_moment"]["start"],
                        "end": result["best_moment"]["end"],
                        "score": result["best_moment"]["score"],
                        "gesture_type": "thank",
                        "features": result["features"]
                    })
            
            except Exception as e:
                pass
        
        print(f"\n\n✓ 推荐 {len(analyzed_moments)} 个感谢表情")
        
        if len(analyzed_moments) > 0:
            print("\n前5个推荐:")
            for i, moment in enumerate(analyzed_moments[:5], 1):
                print(f"  {i}. {moment['start']:.2f}s - {moment['end']:.2f}s, "
                      f"得分: {moment['score']:.2f}")
        
        self.thank_moments = analyzed_moments
    
    def analyze_cute_moments(self):
        """分析可爱表情"""
        print("\n[步骤4] 可爱表情分析")
        print("-" * 80)
        
        max_moments = self.config["analysis_config"]["max_cute_moments"]
        moments_to_analyze = self.cute_moments[:max_moments]
        
        print(f"分析 {len(moments_to_analyze)} 个可爱表情候选（共{len(self.cute_moments)}个）...")
        
        analyzed_moments = []
        
        for i, moment in enumerate(moments_to_analyze, 1):
            print(f"\r处理中... {i}/{len(moments_to_analyze)}", end="", flush=True)
            
            try:
                # 使用多模态分析
                result = self.multimodal_detector.analyze_thank_moment(
                    video_path=self.video_path,
                    time=moment["time"],
                    keyword=moment["keyword"]
                )
                
                # 降低阈值，因为可爱表情可能比较微妙
                if result["best_moment"]["score"] > 0.25:
                    analyzed_moments.append({
                        "start": result["best_moment"]["start"],
                        "end": result["best_moment"]["end"],
                        "score": result["best_moment"]["score"],
                        "gesture_type": "cute",
                        "keyword": moment["keyword"],
                        "features": result["features"]
                    })
            
            except Exception as e:
                pass
        
        print(f"\n\n✓ 推荐 {len(analyzed_moments)} 个可爱表情")
        
        if len(analyzed_moments) > 0:
            print("\n前5个推荐:")
            for i, moment in enumerate(analyzed_moments[:5], 1):
                print(f"  {i}. {moment['start']:.2f}s - {moment['end']:.2f}s, "
                      f"关键词: {moment.get('keyword', '')}, "
                      f"得分: {moment['score']:.2f}")
        
        self.cute_moments = analyzed_moments
    
    def generate_emojis(self):
        """生成表情包"""
        print("\n[步骤5] 生成表情包")
        print("-" * 80)
        
        temp_path = Path(self.temp_dir)
        temp_path.mkdir(parents=True, exist_ok=True)
        
        all_candidates = []
        
        # 添加手势舞
        max_dance = self.config["analysis_config"]["max_dance_moments"]
        for moment in self.dance_moments[:max_dance]:
            all_candidates.append({
                "start": moment["start"],
                "end": moment["end"],
                "type": "hand_dance",
                "gesture_type": "dance"
            })
        
        # 添加感谢表情
        for moment in self.thank_moments:
            all_candidates.append({
                "start": moment["start"],
                "end": moment["end"],
                "type": "thank",
                "gesture_type": "thank"
            })
        
        # 添加可爱表情
        for moment in self.cute_moments:
            all_candidates.append({
                "start": moment["start"],
                "end": moment["end"],
                "type": "cute",
                "gesture_type": moment.get("keyword", "cute")
            })
        
        if len(all_candidates) == 0:
            print("⚠ 没有找到候选片段，无法生成表情包")
            return
        
        print(f"准备生成 {len(all_candidates)} 个表情包")
        print(f"  手势舞: {len([c for c in all_candidates if c['type'] == 'hand_dance'])}个")
        print(f"  感谢表情: {len([c for c in all_candidates if c['type'] == 'thank'])}个")
        print(f"  可爱表情: {len([c for c in all_candidates if c['type'] == 'cute'])}个")
        print()
        print("每个表情包生成3种规格（240x240, 300x300, 512x512）")
        print(f"预计生成 {len(all_candidates) * 3} 个GIF文件 + {len(all_candidates)} 个高清静态图")
        print(f"质量设置: {self.config['emoji_config']['quality']}, 最大{self.config['emoji_config']['max_size_kb']}KB")
        print()
        
        for i, candidate in enumerate(all_candidates, 1):
            print(f"[{i}/{len(all_candidates)}] 生成{candidate['type']}表情包...", end="", flush=True)
            
            try:
                emoji_type = candidate["type"]
                base_name = f"emoji_{emoji_type}_{i:03d}"
                
                result = self.emoji_generator.generate_multi_specs(
                    video_path=self.video_path,
                    start=candidate["start"],
                    end=candidate["end"],
                    output_dir=str(temp_path / emoji_type),
                    base_name=base_name
                )
                
                result["gesture_type"] = candidate["gesture_type"]
                result["category"] = emoji_type
                self.all_emojis.append(result)
                
                print(f" ✓")
                
            except Exception as e:
                print(f" ✗ 失败: {e}")
        
        print(f"\n✓ 表情包生成完成: {len(self.all_emojis)}个")
        
        # 统计
        types_count = {}
        for emoji in self.all_emojis:
            t = emoji.get("category", "unknown")
            types_count[t] = types_count.get(t, 0) + 1
        
        print("\n生成统计:")
        for emoji_type, count in types_count.items():
            print(f"  {emoji_type}: {count}个")
    
    def organize_emojis(self):
        """分类存储表情包"""
        print("\n[步骤6] 分类存储")
        print("-" * 80)
        
        self.organizer.create_directory_structure()
        
        print(f"整理 {len(self.all_emojis)} 个表情包...")
        
        organized_count = 0
        
        for emoji_result in self.all_emojis:
            # 整理GIF
            for spec_name, gif_info in emoji_result.get("gifs", {}).items():
                try:
                    metadata = {
                        "size": gif_info["size"],
                        "gesture_type": emoji_result.get("gesture_type", "unknown"),
                        "category": emoji_result.get("category", "unknown"),
                        "duration": gif_info["duration"],
                        "frames": gif_info["frames"],
                        "file_size_kb": gif_info["file_size_kb"],
                        "source_time": emoji_result["source"]["start"]
                    }
                    
                    category, subcategory = self.organizer.classify_emoji(
                        gif_info["path"],
                        metadata
                    )
                    
                    target_path = self.organizer.move_to_category(
                        gif_info["path"],
                        category,
                        subcategory,
                        copy=False
                    )
                    
                    self.organizer.add_to_index(target_path, metadata, "emojis")
                    organized_count += 1
                    
                except Exception as e:
                    print(f"  ⚠ 整理GIF失败: {e}")
            
            # 整理静态图
            if emoji_result.get("static"):
                try:
                    static_info = emoji_result["static"]
                    metadata = {
                        "size": static_info["size"],
                        "gesture_type": emoji_result.get("gesture_type", "unknown"),
                        "category": emoji_result.get("category", "unknown"),
                        "file_size_kb": static_info["file_size_kb"],
                        "source_time": emoji_result["source"]["start"]
                    }
                    
                    category, subcategory = self.organizer.classify_emoji(
                        static_info["path"],
                        metadata
                    )
                    
                    target_path = self.organizer.move_to_category(
                        static_info["path"],
                        category,
                        subcategory + "/static",
                        copy=False
                    )
                    
                    self.organizer.add_to_index(target_path, metadata, "photos")
                    organized_count += 1
                    
                except Exception as e:
                    print(f"  ⚠ 整理静态图失败: {e}")
        
        print(f"\n✓ 文件整理完成: {organized_count}个文件")
        
        # 生成索引
        self.organizer.save_indexes()
        index_dir = os.path.join(self.output_dir, "元数据库")
        print(f"✓ 索引已生成: {index_dir}")
    
    def run(self):
        """运行完整流程"""
        print("\n" + "=" * 80)
        print("开始表情包素材生成流程（完整版）")
        print("=" * 80)
        
        try:
            # 步骤1: 加载数据
            self.load_data()
            
            # 步骤2: 检测手势舞
            self.detect_dance_moments()
            
            # 步骤3: 分析感谢表情
            self.analyze_thank_moments()
            
            # 步骤4: 分析可爱表情
            self.analyze_cute_moments()
            
            # 步骤5: 生成表情包
            self.generate_emojis()
            
            # 步骤6: 整理存储
            self.organize_emojis()
            
            print("\n" + "=" * 80)
            print("✅ 表情包生成完成！（完整版）")
            print("=" * 80)
            print(f"\n输出目录: {self.output_dir}")
            print(f"生成数量: {len(self.all_emojis)}个表情包")
            print()
            print("下一步:")
            print("  1. 查看生成的表情包")
            print("  2. python3 抖音表情包完整适配.py（适配抖音规格）")
            print("  3. python3 表情包添加文字.py（添加文字）")
            
        except KeyboardInterrupt:
            print("\n\n⚠ 用户中断")
        except Exception as e:
            print(f"\n\n✗ 错误: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    
    if not os.path.exists(config["video_path"]):
        print(f"错误: 视频文件不存在: {config['video_path']}")
        return
    
    # 询问用户
    print("=" * 80)
    print("表情包素材生成 - 完整版")
    print("=" * 80)
    print()
    print("完整版特点:")
    print("  ✓ 分析完整视频（不限时长）")
    print("  ✓ 更低的检测阈值（更多候选）")
    print("  ✓ 更大的文件大小（2MB，更好的质量）")
    print("  ✓ 更高的帧率（20fps）")
    print("  ✓ 3种类型：手势舞 + 感谢表情 + 可爱表情")
    print()
    print("预计生成：50-200个表情包")
    print("预计耗时：30-90分钟")
    print()
    
    choice = input("确认运行？[y/N]: ").strip().lower()
    
    if choice != 'y':
        print("已取消")
        return
    
    generator = FullEmojiMaterialGenerator(config)
    generator.run()


if __name__ == "__main__":
    main()

