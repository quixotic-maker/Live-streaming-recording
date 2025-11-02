#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表情识别功能测试脚本
"""

import os
import sys
import logging

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.emotion_detector import EmotionDetector, analyze_video_emotions

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """检查依赖是否安装"""
    print("=" * 70)
    print("检查依赖...")
    print("=" * 70)
    
    missing_deps = []
    
    # 检查OpenCV
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
    except ImportError:
        print("❌ OpenCV 未安装")
        missing_deps.append("opencv-python")
    
    # 检查FER
    try:
        import fer
        print(f"✅ FER (表情识别): {fer.__version__}")
    except ImportError:
        print("⚠️ FER 未安装（将使用简化版人脸检测）")
        print("   安装方法: pip install fer")
    
    # 检查numpy
    try:
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
    except ImportError:
        print("❌ NumPy 未安装")
        missing_deps.append("numpy")
    
    if missing_deps:
        print(f"\n⚠️ 缺少必要依赖: {', '.join(missing_deps)}")
        print(f"\n安装命令:")
        print(f"pip install {' '.join(missing_deps)}")
        return False
    
    print("\n✅ 所有依赖检查通过！\n")
    return True


def test_initialization():
    """测试初始化"""
    print("=" * 70)
    print("测试表情识别器初始化...")
    print("=" * 70)
    
    detector = EmotionDetector()
    success = detector.initialize()
    
    if success:
        print("✅ 表情识别器初始化成功！")
        return detector
    else:
        print("❌ 表情识别器初始化失败")
        return None


def test_video_analysis():
    """测试视频分析"""
    print("\n" + "=" * 70)
    print("测试视频分析...")
    print("=" * 70)
    
    # 查找测试视频
    downloads_dir = os.path.join(os.path.dirname(__file__), "downloads")
    
    if not os.path.exists(downloads_dir):
        print(f"\n❌ 下载目录不存在: {downloads_dir}")
        print("💡 请先录制一些视频")
        return
    
    # 查找视频文件
    video_files = []
    for root, dirs, files in os.walk(downloads_dir):
        for file in files:
            if file.endswith(('.ts', '.mp4', '.flv')):
                video_files.append(os.path.join(root, file))
    
    if not video_files:
        print("\n❌ 未找到视频文件")
        print("💡 支持的格式: .ts, .mp4, .flv")
        return
    
    print(f"\n找到 {len(video_files)} 个视频文件")
    
    # 让用户选择要分析的视频
    for i, video in enumerate(video_files[:10]):  # 只显示前10个
        size_mb = os.path.getsize(video) / (1024 * 1024)
        print(f"{i+1}. {os.path.basename(video)} ({size_mb:.1f} MB)")
    
    if len(video_files) > 10:
        print(f"... 还有 {len(video_files) - 10} 个文件")
    
    try:
        choice = input("\n请选择要分析的视频序号（直接回车使用第一个）: ").strip()
        if choice:
            index = int(choice) - 1
        else:
            index = 0
        
        if 0 <= index < len(video_files):
            video_path = video_files[index]
        else:
            print("❌ 无效的选择")
            return
    except (ValueError, IndexError):
        print("❌ 无效的输入")
        return
    
    print(f"\n📹 分析视频: {os.path.basename(video_path)}")
    print("⏳ 这可能需要几分钟，请耐心等待...\n")
    
    # 分析视频
    try:
        highlights = analyze_video_emotions(video_path, top_n=10)
        
        if highlights:
            print(f"\n✅ 找到 {len(highlights)} 个精彩片段:\n")
            
            detector = EmotionDetector()
            for i, (start, end, emotion) in enumerate(highlights):
                duration = end - start
                emotion_zh = detector.EMOTIONS_ZH.get(emotion, emotion)
                print(f"  {i+1}. {int(start//60):02d}:{int(start%60):02d} - "
                      f"{int(end//60):02d}:{int(end%60):02d} "
                      f"({duration:.1f}秒) - {emotion_zh}")
            
            print("\n💡 这些时间段包含主播的可爱表情！")
            print("   可以用这些片段生成精彩集锦。")
        else:
            print("\n⚠️ 未检测到精彩片段")
            print("💡 可能的原因：")
            print("   - 视频中没有清晰的人脸")
            print("   - 表情变化不够明显")
            print("   - 视频质量较低")
    
    except Exception as e:
        logger.error(f"分析过程中出错: {e}", exc_info=True)


def demo_usage():
    """使用示例"""
    print("\n" + "=" * 70)
    print("使用示例")
    print("=" * 70)
    
    print("""
# 方法1：快速分析（推荐）
from src.emotion_detector import analyze_video_emotions

highlights = analyze_video_emotions("video.mp4", top_n=10)
for start, end, emotion in highlights:
    print(f"{start:.1f}s - {end:.1f}s: {emotion}")


# 方法2：详细控制
from src.emotion_detector import EmotionDetector

detector = EmotionDetector()
detector.initialize()

# 分析视频
emotion_timeline = detector.analyze_video("video.mp4", sample_rate=30)

# 提取精彩片段
highlights = detector.find_highlights_by_emotion(
    emotion_timeline,
    min_duration=3.0,  # 最短3秒
    merge_gap=2.0      # 2秒内的片段合并
)

# 处理结果
for start, end, emotion, intensity in highlights:
    print(f"{start:.1f}s - {end:.1f}s: {emotion} (强度: {intensity:.2f})")
""")


if __name__ == "__main__":
    try:
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║          表情识别精彩片段提取 - 功能测试                      ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        
        # 1. 检查依赖
        if not check_dependencies():
            print("\n请先安装依赖:")
            print("pip install -r requirements_emotion.txt")
            sys.exit(1)
        
        # 2. 测试初始化
        detector = test_initialization()
        if not detector:
            sys.exit(1)
        
        # 3. 测试视频分析
        test_video_analysis()
        
        # 4. 显示使用示例
        demo_usage()
        
        print("\n" + "=" * 70)
        print("✅ 测试完成！")
        print("=" * 70)
    
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)

