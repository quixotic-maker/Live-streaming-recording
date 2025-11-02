#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表情包素材生成 - 完整流程

流程：
1. 加载已有数据（语音分析、歌曲列表、礼物时刻）
2. 方案A：运动检测 - 查找手势舞（0-60分钟）
3. 方案B：姿态估计 - 精确识别手势类型
4. 方案C：多模态检测 - 分析感谢时刻
5. 生成多规格表情包（240/300/512px GIF + 高清图）
6. 自动分类存储
7. 生成索引和统计报告
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


class EmojiMaterialGenerator:
    """表情包素材生成器"""
    
    def __init__(self, config: Dict):
        """
        初始化生成器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.video_path = config["video_path"]
        self.output_dir = config["output_dir"]
        self.temp_dir = config.get("temp_dir", "temp_emojis")
        
        # 验证视频文件
        if not os.path.exists(self.video_path):
            raise FileNotFoundError(f"视频文件不存在: {self.video_path}")
        
        # 创建检测器
        self.motion_detector = MotionDetector()
        self.pose_detector = PoseDetector()
        self.multimodal_detector = MultimodalDetector()
        
        # 创建生成器
        self.emoji_generator = EmojiGenerator()
        
        # 创建管理器
        self.organizer = MaterialOrganizer(self.output_dir)
        
        # 结果存储
        self.dance_moments = []
        self.thank_moments = []
        self.all_emojis = []
        
        print("=" * 70)
        print("表情包素材生成系统已初始化")
        print("=" * 70)
        print(f"视频路径: {self.video_path}")
        print(f"输出目录: {self.output_dir}")
        print()
    
    def load_data(self):
        """加载已有数据"""
        print("\n[步骤1] 加载已有数据")
        print("-" * 70)
        
        # 加载礼物感谢素材
        gift_file = os.path.expanduser("~/shanshan_materials/素材库_最新/gift_素材.json")
        if os.path.exists(gift_file):
            with open(gift_file, 'r', encoding='utf-8') as f:
                gift_data = json.load(f)
            
            # 提取"谢谢"时刻
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
            print(f"  将使用默认测试数据")
            # 使用默认测试时刻
            self.thank_moments = [
                {"time": 132.5, "keyword": "谢谢", "text": "谢谢"}
            ]
        
        print(f"\n数据加载完成:")
        print(f"  感谢时刻: {len(self.thank_moments)}个")
    
    def detect_dance_moments(self):
        """方案A: 检测手势舞"""
        print("\n[步骤2] 方案A: 运动检测 - 查找手势舞")
        print("-" * 70)
        print("分析时间范围: 0-60分钟（前1小时）")
        print("这可能需要几分钟...")
        
        self.dance_moments = self.motion_detector.detect_dance_moments(
            video_path=self.video_path,
            start_time=0,
            end_time=3600  # 60分钟
        )
        
        print(f"\n✓ 找到 {len(self.dance_moments)} 个手势舞候选片段")
        
        # 显示前5个
        for i, moment in enumerate(self.dance_moments[:5], 1):
            print(f"  {i}. {moment['start']:.2f}s - {moment['end']:.2f}s, "
                  f"得分: {moment['motion_score']:.3f}")
        
        if len(self.dance_moments) > 5:
            print(f"  ... 还有{len(self.dance_moments) - 5}个")
    
    def identify_gestures(self):
        """方案B: 精确识别手势类型"""
        print("\n[步骤3] 方案B: 姿态估计 - 识别具体手势")
        print("-" * 70)
        
        if not self.pose_detector.available:
            print("⚠ MediaPipe不可用，跳过姿态估计")
            print("  将使用运动检测结果")
            return
        
        print(f"分析 {len(self.dance_moments)} 个候选片段...")
        
        confirmed_moments = []
        
        for i, moment in enumerate(self.dance_moments, 1):
            print(f"\r处理中... {i}/{len(self.dance_moments)}", end="", flush=True)
            
            try:
                result = self.pose_detector.identify_gesture(
                    video_path=self.video_path,
                    start=moment["start"],
                    end=moment["end"]
                )
                
                # 只保留置信度高的结果
                if result["confidence"] > 0.6:
                    moment["gesture_type"] = result["gesture_type"]
                    moment["gesture_confidence"] = result["confidence"]
                    confirmed_moments.append(moment)
            
            except Exception as e:
                print(f"\n  ⚠ 处理失败: {e}")
        
        print(f"\n\n✓ 确认 {len(confirmed_moments)} 个手势片段")
        
        # 按类型统计
        type_counts = {}
        for moment in confirmed_moments:
            g_type = moment.get("gesture_type", "unknown")
            type_counts[g_type] = type_counts.get(g_type, 0) + 1
        
        print("手势类型统计:")
        for g_type, count in type_counts.items():
            print(f"  {g_type}: {count}个")
        
        self.dance_moments = confirmed_moments
    
    def analyze_thank_moments(self):
        """方案C: 多模态检测 - 分析感谢时刻"""
        print("\n[步骤4] 方案C: 多模态检测 - 分析感谢时刻")
        print("-" * 70)
        print(f"分析 {len(self.thank_moments)} 个感谢时刻...")
        
        analyzed_moments = []
        
        for i, moment in enumerate(self.thank_moments, 1):
            print(f"\r处理中... {i}/{len(self.thank_moments)}", end="", flush=True)
            
            try:
                result = self.multimodal_detector.analyze_thank_moment(
                    video_path=self.video_path,
                    time=moment["time"],
                    keyword=moment["keyword"]
                )
                
                # 只保留推荐的时刻
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
        
        self.thank_moments = analyzed_moments
    
    def generate_emojis(self):
        """生成表情包"""
        print("\n[步骤5] 生成表情包")
        print("-" * 70)
        
        # 创建临时目录
        temp_path = Path(self.temp_dir)
        temp_path.mkdir(parents=True, exist_ok=True)
        
        # 合并所有候选
        all_candidates = []
        
        # 添加手势舞
        for moment in self.dance_moments[:15]:  # 最多取15个
            all_candidates.append({
                "start": moment["start"],
                "end": moment["end"],
                "type": "hand_dance",
                "gesture_type": moment.get("gesture_type", "dance")
            })
        
        # 添加感谢表情
        for moment in self.thank_moments[:50]:  # 最多取50个
            all_candidates.append({
                "start": moment["start"],
                "end": moment["end"],
                "type": "thank",
                "gesture_type": "thank"
            })
        
        print(f"准备生成 {len(all_candidates)} 个表情包")
        print("每个表情包生成3种规格（240x240, 300x300, 512x512）")
        print(f"预计生成 {len(all_candidates) * 3} 个GIF文件")
        print()
        
        # 批量生成
        for i, candidate in enumerate(all_candidates, 1):
            print(f"[{i}/{len(all_candidates)}] 生成表情包...")
            
            try:
                # 生成基础名称
                emoji_type = candidate["type"]
                base_name = f"emoji_{emoji_type}_{i:03d}"
                
                # 生成多规格
                result = self.emoji_generator.generate_multi_specs(
                    video_path=self.video_path,
                    start=candidate["start"],
                    end=candidate["end"],
                    output_dir=str(temp_path / emoji_type),
                    base_name=base_name
                )
                
                # 添加元数据
                result["gesture_type"] = candidate["gesture_type"]
                result["category"] = emoji_type
                
                self.all_emojis.append(result)
                
                print(f"  ✓ 生成完成: {base_name}")
            
            except Exception as e:
                print(f"  ✗ 生成失败: {e}")
        
        print(f"\n✓ 表情包生成完成: {len(self.all_emojis)}个")
    
    def organize_emojis(self):
        """分类存储表情包"""
        print("\n[步骤6] 分类存储")
        print("-" * 70)
        
        # 创建目录结构
        self.organizer.create_directory_structure()
        
        print(f"整理 {len(self.all_emojis)} 个表情包...")
        
        organized_count = 0
        
        for emoji_result in self.all_emojis:
            # 处理每个规格的GIF
            for spec_name, gif_info in emoji_result.get("gifs", {}).items():
                try:
                    # 构建元数据
                    metadata = {
                        "size": gif_info["size"],
                        "gesture_type": emoji_result.get("gesture_type", "unknown"),
                        "duration": gif_info["duration"],
                        "frames": gif_info["frames"],
                        "file_size_kb": gif_info["file_size_kb"],
                        "source_time": emoji_result["source"]["start"]
                    }
                    
                    # 分类
                    category, subcategory = self.organizer.classify_emoji(
                        gif_info["path"],
                        metadata
                    )
                    
                    # 移动文件
                    target_path = self.organizer.move_to_category(
                        gif_info["path"],
                        category,
                        subcategory,
                        copy=False
                    )
                    
                    # 添加到索引
                    self.organizer.add_to_index(
                        target_path,
                        metadata,
                        "emojis"
                    )
                    
                    organized_count += 1
                
                except Exception as e:
                    print(f"  ⚠ 整理失败: {e}")
            
            # 处理高清静态图
            if emoji_result.get("static"):
                try:
                    static_info = emoji_result["static"]
                    
                    metadata = {
                        "size": static_info["size"],
                        "gesture_type": emoji_result.get("gesture_type", "unknown"),
                        "file_size_kb": static_info["file_size_kb"],
                        "source_time": emoji_result["source"]["start"]
                    }
                    
                    category = "表情包站"
                    subcategory = "高清截图"
                    
                    target_path = self.organizer.move_to_category(
                        static_info["path"],
                        category,
                        subcategory,
                        copy=False
                    )
                    
                    self.organizer.add_to_index(
                        target_path,
                        metadata,
                        "photos"
                    )
                    
                    organized_count += 1
                
                except Exception as e:
                    print(f"  ⚠ 整理失败: {e}")
        
        print(f"✓ 整理完成: {organized_count}个文件")
    
    def generate_reports(self):
        """生成报告"""
        print("\n[步骤7] 生成报告和索引")
        print("-" * 70)
        
        # 保存索引
        self.organizer.save_indexes()
        
        # 生成统计
        stats = self.organizer.generate_statistics()
        
        print("\n📊 统计报告:")
        print(f"  总文件数: {stats['total_files']}")
        print(f"  总大小: {stats['total_size_mb']}MB")
        print("\n按类型统计:")
        for type_name, type_stats in stats['by_type'].items():
            if type_stats['count'] > 0:
                print(f"  {type_name}: {type_stats['count']}个, {type_stats['size_mb']}MB")
        
        # 保存统计报告
        stats_path = Path(self.output_dir) / "元数据库" / "统计报告.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n统计报告已保存: {stats_path}")
        
        # 生成下载脚本
        if self.organizer.metadata['emojis']:
            script_path = Path(self.output_dir) / "下载所有表情包.sh"
            self.organizer.generate_download_script(
                "emojis",
                str(script_path),
                "bash"
            )
            print(f"下载脚本已生成: {script_path}")
    
    def run(self):
        """运行完整流程"""
        print("\n" + "=" * 70)
        print("开始表情包素材生成流程")
        print("=" * 70)
        
        start_time = datetime.now()
        
        try:
            # 步骤1: 加载数据
            self.load_data()
            
            # 步骤2: 检测手势舞
            self.detect_dance_moments()
            
            # 步骤3: 识别手势类型
            # self.identify_gestures()  # 可选：需要MediaPipe
            
            # 步骤4: 分析感谢时刻
            self.analyze_thank_moments()
            
            # 步骤5: 生成表情包
            self.generate_emojis()
            
            # 步骤6: 分类存储
            self.organize_emojis()
            
            # 步骤7: 生成报告
            self.generate_reports()
            
            # 完成
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("\n" + "=" * 70)
            print("✓ 表情包素材生成完成！")
            print("=" * 70)
            print(f"总用时: {duration/60:.1f}分钟")
            print(f"输出目录: {self.output_dir}")
            print("\n查看结果:")
            print(f"  1. 表情包文件: {self.output_dir}/表情包站/")
            print(f"  2. 元数据索引: {self.output_dir}/元数据库/表情包索引.json")
            print(f"  3. 统计报告: {self.output_dir}/元数据库/统计报告.json")
            print()
        
        except Exception as e:
            print(f"\n✗ 错误: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True


def main():
    """主函数"""
    
    # 配置参数
    config = {
        "video_path": "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4",
        "output_dir": os.path.expanduser("~/shanshan_materials/表情包素材库"),
        "temp_dir": "temp_emojis"
    }
    
    # 验证视频文件
    if not os.path.exists(config["video_path"]):
        print(f"错误: 视频文件不存在: {config['video_path']}")
        print("\n请修改config中的video_path为实际路径")
        return
    
    # 创建生成器
    generator = EmojiMaterialGenerator(config)
    
    # 运行流程
    success = generator.run()
    
    if success:
        print("✓ 全部完成！")
    else:
        print("✗ 生成过程中出现错误")


if __name__ == "__main__":
    main()

