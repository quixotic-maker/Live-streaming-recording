#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态精彩片段检测 - 测试脚本
"""

import os
import sys
import logging
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.multimodal_detector import MultimodalDetector, create_anchor_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """检查依赖"""
    print("=" * 70)
    print("检查依赖...")
    print("=" * 70)
    
    # OpenCV
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
    except ImportError:
        print("❌ OpenCV 未安装")
        print("   安装: pip install opencv-python")
        return False
    
    # NumPy
    try:
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
    except ImportError:
        print("❌ NumPy 未安装")
        return False
    
    # Whisper（可选）
    try:
        import whisper
        print(f"✅ Whisper: 已安装（语音识别功能可用）")
    except ImportError:
        print("⚠️  Whisper 未安装（将无法使用语音识别）")
        print("   安装: pip install openai-whisper")
        print("   可选安装，不影响其他功能")
    
    print("\n✅ 基础依赖检查通过！\n")
    return True


def setup_anchor_config():
    """设置主播配置"""
    print("=" * 70)
    print("主播配置设置")
    print("=" * 70)
    
    anchor_name = input("\n请输入主播名称（例如：山山）: ").strip()
    
    if not anchor_name:
        print("❌ 主播名称不能为空")
        return None
    
    # 检查配置是否已存在
    config_path = Path(f"config/anchors/{anchor_name}.json")
    if config_path.exists():
        use_existing = input(f"配置文件已存在，是否使用现有配置？(y/n): ").strip().lower()
        if use_existing == 'y':
            print(f"✅ 使用现有配置: {config_path}")
            return anchor_name
    
    # 创建新配置
    print(f"\n为主播 {anchor_name} 创建个性化配置")
    print("=" * 70)
    print("请输入触发关键词（主播常说的话，回车结束输入）：")
    print("例如：哈哈哈、笑死、我的天、可爱、宝宝等")
    print("提示：根据您看直播的经验，哪些话会伴随表情包？")
    print()
    
    keywords = []
    while True:
        keyword = input(f"关键词 {len(keywords)+1} (直接回车结束): ").strip()
        if not keyword:
            break
        keywords.append(keyword)
        print(f"  ✅ 已添加: {keyword}")
    
    if not keywords:
        print("\n⚠️  未添加任何关键词，使用默认配置")
        keywords = ["哈哈哈", "笑死", "我的天", "可爱", "宝宝"]
    
    # 创建配置
    create_anchor_config(anchor_name, keywords)
    
    print(f"\n✅ 配置已创建: {config_path}")
    print(f"   关键词数量: {len(keywords)}")
    print(f"   可以后续编辑配置文件添加更多关键词")
    
    return anchor_name


def select_video():
    """选择要分析的视频"""
    print("\n" + "=" * 70)
    print("选择视频文件")
    print("=" * 70)
    
    downloads_dir = Path("downloads")
    if not downloads_dir.exists():
        print(f"❌ 下载目录不存在: {downloads_dir}")
        return None
    
    # 查找视频文件
    video_files = []
    for root, dirs, files in os.walk(downloads_dir):
        for file in files:
            if file.endswith(('.ts', '.mp4', '.flv')):
                video_files.append(os.path.join(root, file))
    
    if not video_files:
        print("❌ 未找到视频文件")
        return None
    
    print(f"\n找到 {len(video_files)} 个视频文件：")
    
    # 显示视频列表
    for i, video in enumerate(video_files[:20]):  # 最多显示20个
        size_mb = os.path.getsize(video) / (1024 * 1024)
        print(f"{i+1}. {os.path.basename(video)} ({size_mb:.1f} MB)")
    
    if len(video_files) > 20:
        print(f"... 还有 {len(video_files) - 20} 个文件")
    
    # 让用户选择
    try:
        choice = input("\n请选择视频序号（直接回车选择第一个）: ").strip()
        if choice:
            index = int(choice) - 1
        else:
            index = 0
        
        if 0 <= index < len(video_files):
            return video_files[index]
        else:
            print("❌ 无效的选择")
            return None
    except (ValueError, IndexError):
        print("❌ 无效的输入")
        return None


def run_multimodal_analysis(video_path: str, anchor_name: str):
    """运行多模态分析"""
    print("\n" + "=" * 70)
    print("开始多模态分析")
    print("=" * 70)
    
    print(f"\n📹 视频: {os.path.basename(video_path)}")
    print(f"👤 主播: {anchor_name}")
    print()
    
    # 询问是否使用语音识别
    use_whisper = False
    try:
        import whisper
        response = input("是否使用语音识别？(y/n，语音识别可能需要10-30分钟): ").strip().lower()
        use_whisper = (response == 'y')
    except ImportError:
        print("⚠️  Whisper未安装，跳过语音识别")
    
    print("\n⏳ 分析中，这可能需要几分钟到几十分钟...")
    print("   提示：可以去泡杯咖啡，回来查看结果 ☕")
    print()
    
    # 创建检测器
    detector = MultimodalDetector(anchor_name)
    
    # 根据用户选择决定是否进行语音识别
    if not use_whisper:
        # 不使用语音识别，只使用礼物检测和时间规律
        print("📊 使用简化模式（礼物检测 + 时间规律）")
        
        # 只做礼物检测
        gift_moments = detector.detect_gift_effects(video_path)
        
        # 简化的融合分析
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        video_duration = frame_count / fps
        cap.release()
        
        from collections import defaultdict
        score_timeline = defaultdict(float)
        
        for timestamp, intensity in gift_moments:
            time_weight = detector.calculate_time_weight(timestamp, video_duration)
            score = intensity * 5.0 * time_weight
            score_timeline[int(timestamp)] += score
        
        # 提取高分时刻
        highlights = []
        sorted_times = sorted(score_timeline.items(), key=lambda x: x[1], reverse=True)
        
        for timestamp, score in sorted_times[:10]:
            start = max(0, timestamp - 2)
            end = min(video_duration, timestamp + 5)
            highlights.append((
                float(start),
                float(end),
                {
                    'score': score,
                    'sources': [f'礼物({score:.1f})'],
                    'time_weight': detector.calculate_time_weight(timestamp, video_duration)
                }
            ))
    else:
        # 完整的多模态分析
        print("🎯 使用完整模式（语音识别 + 礼物检测 + 时间规律）")
        highlights = detector.fusion_analysis(video_path)
    
    # 显示结果
    print("\n" + "=" * 70)
    print("分析结果")
    print("=" * 70)
    
    if highlights:
        print(f"\n✅ 找到 {len(highlights)} 个精彩片段:\n")
        
        for i, (start, end, details) in enumerate(highlights):
            duration = end - start
            minutes = int(start // 60)
            seconds = int(start % 60)
            
            print(f"{i+1}. 时间: {minutes:02d}:{seconds:02d} ({duration:.1f}秒)")
            print(f"   得分: {details['score']:.1f}")
            print(f"   来源: {', '.join(details['sources'])}")
            print(f"   时间权重: {details['time_weight']:.2f}x")
            print()
        
        # 询问是否生成剪映草稿
        try:
            from pyJianYingDraft import ScriptFile, trange, FilterType
            
            response = input("\n是否生成剪映草稿？(y/n): ").strip().lower()
            if response == 'y':
                draft = ScriptFile()
                
                for start, end, details in highlights[:10]:
                    seg = draft.add_video(video_path, trange(start, end))
                    
                    # 根据得分添加特效
                    score = details['score']
                    if score > 30:
                        seg.add_filter(FilterType.赛博朋克, 70)
                    elif score > 20:
                        seg.add_filter(FilterType.活力, 60)
                    else:
                        seg.add_filter(FilterType.甜美, 50)
                
                draft_name = f"精彩集锦_{anchor_name}"
                draft.export(draft_name)
                print(f"\n✅ 剪映草稿已生成: {draft_name}.jianying")
                print("   在剪映中打开即可编辑和导出！")
        except ImportError:
            print("\n💡 提示: 安装 pyJianYingDraft 可自动生成剪映草稿")
            print("   pip install pyJianYingDraft")
    else:
        print("\n⚠️  未找到精彩片段")
        print("\n可能的原因：")
        print("  - 视频中没有明显的礼物特效")
        print("  - 未使用语音识别（建议启用）")
        print("  - 需要调整主播配置中的关键词")


def main():
    """主函数"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║      多模态精彩片段检测器 - 针对主播定制                      ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    try:
        # 1. 检查依赖
        if not check_dependencies():
            return
        
        # 2. 设置主播配置
        anchor_name = setup_anchor_config()
        if not anchor_name:
            return
        
        # 3. 选择视频
        video_path = select_video()
        if not video_path:
            return
        
        # 4. 运行分析
        run_multimodal_analysis(video_path, anchor_name)
        
        print("\n" + "=" * 70)
        print("✅ 测试完成！")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)


if __name__ == "__main__":
    main()

