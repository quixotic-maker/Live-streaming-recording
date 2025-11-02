#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表情包素材生成 - 优化版（降低检测阈值）

优化内容：
1. 降低运动检测阈值：0.15 → 0.08
2. 降低推荐阈值：0.7 → 0.4
3. 缩短检测时长：60分钟 → 30分钟（加快测试）
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from gesture_detector import MotionDetector, PoseDetector, MultimodalDetector
from emoji_generator import EmojiGenerator
# ✅ 移除MaterialOrganizer - 改用简单目录创建
# from material_organizer import MaterialOrganizer


# 配置参数
config = {
    "video_path": "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4",
    "output_dir": os.path.expanduser("~/shanshan_materials/表情包素材库"),
    "temp_dir": "temp_emojis",
    
    # 优化参数
    "motion_config": {
        "motion_threshold": 0.08,      # 从0.15降到0.08（更容易检测到）
        "min_duration": 1.5,            # 最短1.5秒
        "merge_gap": 2.0                # 合并间隔2秒
    },
    
    "multimodal_config": {
        "recommend_threshold": 0.4,     # 从0.7降到0.4（更多候选）
        "gesture_weight": 0.5,          # 增加手势权重
        "effect_weight": 0.3            # 增加特效权重
    },
    
    # 测试参数
    "test_duration": 1800,              # 只分析前30分钟（测试用）
    "max_dance_moments": 10,            # 最多取10个手势舞
    "max_thank_moments": 30             # 最多取30个感谢表情
}


class EmojiMaterialGenerator:
    """表情包素材生成器 - 优化版"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.video_path = config["video_path"]
        self.output_dir = config["output_dir"]
        self.temp_dir = config.get("temp_dir", "temp_emojis")
        
        if not os.path.exists(self.video_path):
            raise FileNotFoundError(f"视频文件不存在: {self.video_path}")
        
        # 创建检测器（使用优化参数）
        self.motion_detector = MotionDetector(config.get("motion_config", {}))
        self.pose_detector = PoseDetector()
        self.multimodal_detector = MultimodalDetector(config.get("multimodal_config", {}))
        
        self.emoji_generator = EmojiGenerator()
        # ✅ 移除MaterialOrganizer，改用简单目录创建
        # self.organizer = MaterialOrganizer(self.output_dir)
        
        # 创建简化的输出目录结构
        self._create_simple_structure()
        
        self.dance_moments = []
        self.thank_moments = []
        self.all_emojis = []
        
        print("=" * 70)
        print("表情包素材生成系统（优化版）已初始化")
        print("=" * 70)
        print(f"视频路径: {self.video_path}")
        print(f"输出目录: {self.output_dir}")
        print(f"\n优化配置:")
        print(f"  运动阈值: {config['motion_config']['motion_threshold']}")
        print(f"  推荐阈值: {config['multimodal_config']['recommend_threshold']}")
        if config.get('test_duration'):
            print(f"  分析时长: {config['test_duration']/60:.0f}分钟")
        else:
            print(f"  分析时长: 全部视频")
        print()
    
    def _create_simple_structure(self):
        """创建简化的目录结构（不使用MaterialOrganizer）"""
        output_path = Path(self.output_dir)
        
        # 创建基础目录
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 无需创建复杂的"站"结构，只创建实际需要的
        # 表情包会直接保存在output_dir下
        print("✅ 使用简化目录结构（无MaterialOrganizer）")
    
    def load_data(self):
        """加载已有数据"""
        print("\n[步骤1] 加载已有数据")
        print("-" * 70)
        
        gift_file = os.path.expanduser("~/shanshan_materials/素材库_最新/gift_素材.json")
        if os.path.exists(gift_file):
            with open(gift_file, 'r', encoding='utf-8') as f:
                gift_data = json.load(f)
            
            segments = gift_data.get("segments", []) if isinstance(gift_data, dict) else gift_data
            for item in segments:
                if isinstance(item, dict) and "谢谢" in item.get("text", ""):
                    self.thank_moments.append({
                        "time": item["start"],
                        "keyword": "谢谢",
                        "text": item["text"]
                    })
            
            print(f"✓ 加载礼物感谢数据: {len(self.thank_moments)}个时刻")
        else:
            print(f"⚠ 礼物感谢数据文件不存在: {gift_file}")
            self.thank_moments = [{"time": 132.5, "keyword": "谢谢", "text": "谢谢"}]
        
        print(f"\n数据加载完成:")
        print(f"  感谢时刻: {len(self.thank_moments)}个")
    
    def detect_dance_moments(self):
        """方案A: 检测手势舞"""
        print("\n[步骤2] 方案A: 运动检测 - 查找手势舞")
        print("-" * 70)
        
        test_duration = self.config.get("test_duration")
        if test_duration:
            print(f"分析时间范围: 0-{test_duration/60:.0f}分钟")
        else:
            print(f"分析时间范围: 全部视频")
        print(f"运动阈值: {self.config['motion_config']['motion_threshold']}")
        print("这可能需要几分钟...")
        
        detect_kwargs = {"video_path": self.video_path, "start_time": 0}
        if test_duration:
            detect_kwargs["end_time"] = test_duration
        self.dance_moments = self.motion_detector.detect_dance_moments(**detect_kwargs)
        
        print(f"\n✓ 找到 {len(self.dance_moments)} 个手势舞候选片段")
        
        if len(self.dance_moments) > 0:
            print("\n前5个候选:")
            for i, moment in enumerate(self.dance_moments[:5], 1):
                print(f"  {i}. {moment['start']:.2f}s - {moment['end']:.2f}s, "
                      f"得分: {moment['motion_score']:.3f}, 置信度: {moment['confidence']:.2f}")
            
            if len(self.dance_moments) > 5:
                print(f"  ... 还有{len(self.dance_moments) - 5}个")
        else:
            print("⚠ 未找到手势舞候选，建议:")
            print("  1. 进一步降低阈值（当前0.08）")
            print("  2. 检查视频前30分钟是否有大幅度动作")
            print("  3. 可以手动指定时间段进行测试")
    
    def analyze_thank_moments(self):
        """方案C: 多模态检测 - 分析感谢时刻"""
        print("\n[步骤3] 方案C: 多模态检测 - 分析感谢时刻")
        print("-" * 70)
        
        max_moments = self.config.get("max_thank_moments", 50)
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
                print(f"\n  ⚠ 处理失败: {e}")
        
        print(f"\n\n✓ 推荐 {len(analyzed_moments)} 个感谢表情")
        
        if len(analyzed_moments) > 0:
            print("\n前5个推荐:")
            for i, moment in enumerate(analyzed_moments[:5], 1):
                print(f"  {i}. {moment['start']:.2f}s - {moment['end']:.2f}s, "
                      f"得分: {moment['score']:.2f}")
        else:
            print("⚠ 未找到推荐的感谢表情，建议:")
            print("  1. 进一步降低阈值（当前0.4）")
            print("  2. 检查视频中感谢时刻是否有明显表情/手势")
        
        self.thank_moments = analyzed_moments
    
    def generate_emojis(self):
        """生成表情包"""
        print("\n[步骤4] 生成表情包")
        print("-" * 70)
        
        temp_path = Path(self.temp_dir)
        temp_path.mkdir(parents=True, exist_ok=True)
        
        all_candidates = []
        
        # 添加手势舞
        max_dance = self.config.get("max_dance_moments", 15)
        for moment in self.dance_moments[:max_dance]:
            all_candidates.append({
                "start": moment["start"],
                "end": moment["end"],
                "type": "hand_dance",
                "gesture_type": moment.get("gesture_type", "dance")
            })
        
        # 添加感谢表情
        max_thank = self.config.get("max_thank_moments", 50)
        for moment in self.thank_moments[:max_thank]:
            all_candidates.append({
                "start": moment["start"],
                "end": moment["end"],
                "type": "thank",
                "gesture_type": "thank"
            })
        
        if len(all_candidates) == 0:
            print("⚠ 没有找到候选片段，无法生成表情包")
            print("  建议调整检测参数后重新运行")
            return
        
        print(f"准备生成 {len(all_candidates)} 个表情包")
        print("每个表情包生成3种规格（240x240, 300x300, 512x512）")
        print(f"预计生成 {len(all_candidates) * 3} 个GIF文件")
        print()
        
        for i, candidate in enumerate(all_candidates, 1):
            print(f"[{i}/{len(all_candidates)}] 生成表情包...", end="", flush=True)
            
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
    
    def organize_emojis(self):
        """分类存储表情包（已禁用 - 使用简化结构）"""
        print("\n[步骤5] 分类存储")
        print("-" * 70)
        print("⚠️  MaterialOrganizer已禁用，表情包直接保存在输出目录")
        print("✓ 跳过分类存储步骤")
        return
        
        # ❌ 以下代码已禁用（依赖MaterialOrganizer）
        # self.organizer.create_directory_structure()
        
        print(f"整理 {len(self.all_emojis)} 个表情包...")
        
        organized_count = 0
        
        for emoji_result in self.all_emojis:
            for spec_name, gif_info in emoji_result.get("gifs", {}).items():
                try:
                    metadata = {
                        "size": gif_info["size"],
                        "gesture_type": emoji_result.get("gesture_type", "unknown"),
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
                    print(f"  ⚠ 整理失败: {e}")
            
            if emoji_result.get("static"):
                try:
                    static_info = emoji_result["static"]
                    metadata = {
                        "size": static_info["size"],
                        "gesture_type": emoji_result.get("gesture_type", "unknown"),
                        "file_size_kb": static_info["file_size_kb"],
                        "source_time": emoji_result["source"]["start"]
                    }
                    
                    target_path = self.organizer.move_to_category(
                        static_info["path"],
                        "表情包站",
                        "高清截图",
                        copy=False
                    )
                    
                    self.organizer.add_to_index(target_path, metadata, "photos")
                    organized_count += 1
                    
                except Exception as e:
                    print(f"  ⚠ 整理失败: {e}")
        
        print(f"✓ 整理完成: {organized_count}个文件")
        
        # 显示输出位置
        print(f"\n📁 素材输出位置:")
        print(f"   {os.path.abspath(self.output_dir)}/表情包站/")
    
    def generate_reports(self):
        """生成报告（已禁用 - 使用简化结构）"""
        print("\n[步骤6] 生成报告和索引")
        print("-" * 70)
        print("⚠️  MaterialOrganizer已禁用，跳过报告生成")
        print("✓ 跳过报告步骤")
        return
        
        # ❌ 以下代码已禁用（依赖MaterialOrganizer）
        # self.organizer.save_indexes()
        # stats = self.organizer.generate_statistics()
        
        print("\n📊 统计报告:")
        print(f"  总文件数: {stats['total_files']}")
        print(f"  总大小: {stats['total_size_mb']:.2f}MB")
        print("\n按类型统计:")
        for type_name, type_stats in stats['by_type'].items():
            if type_stats['count'] > 0:
                print(f"  {type_name}: {type_stats['count']}个, {type_stats['size_mb']:.2f}MB")
        
        stats_path = Path(self.output_dir) / "元数据库" / "统计报告.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n统计报告已保存: {stats_path}")
    
    def run(self):
        """运行完整流程"""
        print("\n" + "=" * 70)
        print("开始表情包素材生成流程（优化版）")
        print("=" * 70)
        
        start_time = datetime.now()
        
        try:
            self.load_data()
            self.detect_dance_moments()
            # self.identify_gestures()  # 跳过姿态估计，加快速度
            self.analyze_thank_moments()
            self.generate_emojis()
            
            if len(self.all_emojis) > 0:
                self.organize_emojis()
                self.generate_reports()
            else:
                print("\n⚠ 未生成任何表情包")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("\n" + "=" * 70)
            print("✓ 表情包素材生成完成！")
            print("=" * 70)
            print(f"总用时: {duration/60:.1f}分钟")
            print(f"输出目录: {os.path.abspath(self.output_dir)}")
            print("\n查看结果:")
            print(f"  1. 表情包文件: {self.output_dir}/表情包站/")
            print(f"  2. 元数据索引: {self.output_dir}/元数据库/表情包索引.json")
            print()
        
        except Exception as e:
            print(f"\n✗ 错误: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='表情包素材生成 - 优化版')
    parser.add_argument('--video', type=str, help='视频文件路径')
    parser.add_argument('--output', type=str, help='输出目录')
    parser.add_argument('--max_emojis', type=int, default=20, help='最大表情包数量')
    parser.add_argument('--duration', type=int, help='分析时长（秒），不指定则分析全部')
    args = parser.parse_args()
    
    # 使用命令行参数覆盖配置
    if args.video:
        config["video_path"] = args.video
    if args.output:
        config["output_dir"] = args.output
    if args.duration:
        config["test_duration"] = args.duration
    else:
        # 如果没有指定duration，移除限制（分析全部）
        config["test_duration"] = None
    
    config["max_dance_moments"] = args.max_emojis // 2
    config["max_thank_moments"] = args.max_emojis
    
    if not os.path.exists(config["video_path"]):
        print(f"错误: 视频文件不存在: {config['video_path']}")
        return
    
    generator = EmojiMaterialGenerator(config)
    success = generator.run()
    
    if success:
        print("✓ 全部完成！")
    else:
        print("✗ 生成过程中出现错误")


if __name__ == "__main__":
    main()

