#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析语音识别结果，找出主播的高频词汇和口头禅
"""

import os
import sys
import json
from collections import Counter
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.multimodal_detector import SpeechAnalyzer


def analyze_speech_patterns(video_path, output_file="speech_analysis.txt"):
    """分析语音模式，找出高频词汇"""
    
    print("=" * 70)
    print("语音分析 - 寻找主播的口头禅和特征词汇")
    print("=" * 70)
    
    analyzer = SpeechAnalyzer()
    
    # 检查是否已有音频文件
    audio_path = video_path.rsplit('.', 1)[0] + "_audio.wav"
    
    if not os.path.exists(audio_path):
        print(f"\n提取音频: {os.path.basename(video_path)}")
        audio_path = analyzer.extract_audio(video_path)
    else:
        print(f"\n✅ 使用现有音频: {os.path.basename(audio_path)}")
    
    # 语音识别
    print("\n开始语音识别...")
    segments = analyzer.transcribe(audio_path)
    
    if not segments:
        print("❌ 语音识别失败")
        return
    
    print(f"✅ 识别了 {len(segments)} 段语音\n")
    
    # 分析词频
    print("=" * 70)
    print("词频分析")
    print("=" * 70)
    
    all_text = " ".join([seg["text"] for seg in segments])
    
    # 中文分词（简单版，按常见词汇）
    emotion_words = [
        "哈哈哈", "哈哈", "笑死", "我的天", "天啊", "可爱", "宝宝", "开心",
        "厉害", "太好了", "好可爱", "萌", "搞笑", "好笑", "有趣",
        "惊讶", "震惊", "卧槽", "牛逼", "牛", "强", "太强了",
        "谢谢", "感谢", "爱你", "喜欢", "爱了", "绝了",
    ]
    
    word_count = Counter()
    
    for word in emotion_words:
        count = all_text.count(word)
        if count > 0:
            word_count[word] = count
    
    # 显示Top 20高频词
    print("\nTop 20 高频情感词汇:\n")
    for i, (word, count) in enumerate(word_count.most_common(20), 1):
        # 计算频率（每小时）
        video_duration_hours = len(segments) / 3600 * 5  # 粗略估计
        freq_per_hour = count / video_duration_hours if video_duration_hours > 0 else 0
        
        print(f"  {i:2d}. {word:8s} - 出现{count:3d}次 (约{freq_per_hour:.1f}次/小时)")
    
    # 查找包含高频词的语音片段
    print("\n" + "=" * 70)
    print("示例片段 - 看看这些时刻是否有精彩内容")
    print("=" * 70)
    
    top_words = [word for word, _ in word_count.most_common(10)]
    
    example_segments = []
    for seg in segments:
        for word in top_words:
            if word in seg["text"]:
                example_segments.append((seg["start"], seg["text"], word))
                if len(example_segments) >= 20:
                    break
        if len(example_segments) >= 20:
            break
    
    print("\n前20个包含高频词的时刻:\n")
    for i, (timestamp, text, word) in enumerate(example_segments[:20], 1):
        minutes = int(timestamp // 60)
        seconds = int(timestamp % 60)
        print(f"  {i:2d}. {minutes:3d}:{seconds:02d} - 关键词[{word}] - {text}")
    
    # 保存完整分析
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("语音分析结果\n")
        f.write("=" * 70 + "\n\n")
        
        f.write(f"总语音段数: {len(segments)}\n\n")
        
        f.write("高频情感词汇:\n")
        f.write("-" * 70 + "\n")
        for i, (word, count) in enumerate(word_count.most_common(50), 1):
            f.write(f"{i:2d}. {word:10s} - {count:4d}次\n")
        
        f.write("\n\n包含高频词的时刻:\n")
        f.write("-" * 70 + "\n")
        for seg in segments:
            for word in top_words:
                if word in seg["text"]:
                    minutes = int(seg["start"] // 60)
                    seconds = int(seg["start"] % 60)
                    f.write(f"{minutes:3d}:{seconds:02d} [{word}] {seg['text']}\n")
    
    print(f"\n✅ 完整分析已保存到: {output_file}")
    
    # 建议
    print("\n" + "=" * 70)
    print("💡 关键词配置建议")
    print("=" * 70)
    
    print("\n建议的关键词配置：\n")
    suggested_keywords = [word for word, count in word_count.most_common(15) if count > 5]
    
    if suggested_keywords:
        print("```python")
        print("keywords = [")
        for word in suggested_keywords:
            count = word_count[word]
            print(f"    \"{word}\",  # 出现{count}次")
        print("]")
        print("```")
    else:
        print("⚠️ 未找到明显的高频情感词汇")
        print("可能需要手动观看视频，找出主播的口头禅")
    
    return word_count, segments


if __name__ == "__main__":
    video_path = "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4"
    
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        sys.exit(1)
    
    analyze_speech_patterns(video_path)

