#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整语音分析 - 分析所有识别出的文字
找出主播的真实口头禅和高频词汇
"""

import os
import sys
import json
from collections import Counter
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.multimodal_detector import SpeechAnalyzer


def analyze_full_speech(audio_path, output_prefix="speech_analysis"):
    """完整分析语音内容"""
    
    print("=" * 70)
    print("完整语音分析")
    print("=" * 70)
    
    if not os.path.exists(audio_path):
        print(f"❌ 音频文件不存在: {audio_path}")
        return
    
    size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    print(f"\n音频文件: {os.path.basename(audio_path)}")
    print(f"文件大小: {size_mb:.1f} MB")
    
    # 创建分析器
    analyzer = SpeechAnalyzer(use_whisper=True)
    
    if not analyzer.use_whisper:
        print("\n❌ Whisper未安装，无法进行语音识别")
        print("   请在conda环境中运行: conda activate shanshan")
        return
    
    # 语音识别
    print("\n开始语音识别...")
    print("⏳ 这可能需要15-20分钟，请耐心等待...\n")
    
    segments = analyzer.transcribe(audio_path)
    
    if not segments:
        print("❌ 语音识别失败")
        return
    
    print(f"\n✅ 识别了 {len(segments)} 段语音\n")
    
    # 保存完整的语音识别结果
    transcript_file = f"{output_prefix}_完整转录.json"
    with open(transcript_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_segments": len(segments),
            "segments": segments
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 完整转录已保存: {transcript_file}")
    
    # 合并所有文字
    all_text = " ".join([seg["text"] for seg in segments])
    
    # 保存纯文本版本
    text_file = f"{output_prefix}_纯文本.txt"
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write("完整语音转录\n")
        f.write("=" * 70 + "\n\n")
        for seg in segments:
            minutes = int(seg["start"] // 60)
            seconds = int(seg["start"] % 60)
            f.write(f"[{minutes:3d}:{seconds:02d}] {seg['text']}\n")
    
    print(f"✅ 纯文本版本: {text_file}")
    
    # ======== 词频分析 ========
    print("\n" + "=" * 70)
    print("📊 高频词汇分析")
    print("=" * 70)
    
    # 定义要分析的情感词汇
    emotion_keywords = {
        "笑声类": ["哈哈哈", "哈哈哈哈", "哈哈", "嘻嘻", "呵呵"],
        "强烈情感": ["笑死", "我的天", "天啊", "卧槽", "牛逼", "厉害", "绝了"],
        "惊讶类": ["哇", "啊", "诶", "哎呀", "我去"],
        "可爱类": ["可爱", "萌", "好可爱", "萌死了"],
        "称呼类": ["宝宝", "宝贝", "亲爱的", "家人们"],
        "情绪类": ["开心", "高兴", "爽", "舒服", "难过", "气死了"],
        "赞美类": ["好棒", "太好了", "太强了", "牛", "强"],
        "感谢类": ["谢谢", "感谢", "爱你", "爱了"],
    }
    
    # 统计词频
    category_counts = {}
    word_counts = Counter()
    
    for category, keywords in emotion_keywords.items():
        category_counts[category] = {}
        for keyword in keywords:
            count = all_text.count(keyword)
            if count > 0:
                category_counts[category][keyword] = count
                word_counts[keyword] = count
    
    # 显示分类统计
    print("\n按类别统计:\n")
    for category, words in category_counts.items():
        if words:
            total = sum(words.values())
            print(f"  【{category}】 共 {total} 次")
            for word, count in sorted(words.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"    - {word}: {count}次")
    
    # Top 30高频词
    print("\n" + "=" * 70)
    print("🔥 Top 30 高频情感词汇")
    print("=" * 70 + "\n")
    
    if word_counts:
        for i, (word, count) in enumerate(word_counts.most_common(30), 1):
            # 找出这个词属于哪个类别
            word_category = "其他"
            for cat, words in emotion_keywords.items():
                if word in words:
                    word_category = cat
                    break
            
            print(f"  {i:2d}. {word:10s} - {count:4d}次  [{word_category}]")
    else:
        print("  ⚠️ 未找到预定义的情感词汇")
    
    # ======== 找出包含高频词的精彩时刻 ========
    print("\n" + "=" * 70)
    print("⭐ 可能的精彩时刻 (包含高频词)")
    print("=" * 70)
    
    top_keywords = [word for word, _ in word_counts.most_common(10)]
    
    highlight_moments = []
    for seg in segments:
        for keyword in top_keywords:
            if keyword in seg["text"]:
                highlight_moments.append({
                    "time": seg["start"],
                    "keyword": keyword,
                    "text": seg["text"]
                })
    
    # 按时间排序
    highlight_moments.sort(key=lambda x: x["time"])
    
    print(f"\n找到 {len(highlight_moments)} 个可能的精彩时刻\n")
    print("前30个时刻:\n")
    
    for i, moment in enumerate(highlight_moments[:30], 1):
        minutes = int(moment["time"] // 60)
        seconds = int(moment["time"] % 60)
        print(f"  {i:2d}. {minutes:3d}:{seconds:02d} [{moment['keyword']}] {moment['text']}")
    
    # 保存所有精彩时刻
    moments_file = f"{output_prefix}_精彩时刻.txt"
    with open(moments_file, 'w', encoding='utf-8') as f:
        f.write("可能的精彩时刻 (包含高频情感词汇)\n")
        f.write("=" * 70 + "\n\n")
        for moment in highlight_moments:
            minutes = int(moment["time"] // 60)
            seconds = int(moment["time"] % 60)
            f.write(f"{minutes:3d}:{seconds:02d} [{moment['keyword']}] {moment['text']}\n")
    
    print(f"\n✅ 完整精彩时刻列表: {moments_file}")
    
    # ======== 推荐的关键词配置 ========
    print("\n" + "=" * 70)
    print("💡 推荐的关键词配置")
    print("=" * 70)
    
    # 选择高频且有表情特征的词
    recommended_keywords = []
    
    # 笑声类（最重要）
    laugh_words = [(w, c) for w, c in word_counts.items() if w in emotion_keywords["笑声类"]]
    laugh_words.sort(key=lambda x: x[1], reverse=True)
    recommended_keywords.extend([w for w, c in laugh_words[:3] if c > 5])
    
    # 强烈情感（很重要）
    strong_words = [(w, c) for w, c in word_counts.items() if w in emotion_keywords["强烈情感"]]
    strong_words.sort(key=lambda x: x[1], reverse=True)
    recommended_keywords.extend([w for w, c in strong_words[:5] if c > 3])
    
    # 其他高频词
    other_high_freq = [w for w, c in word_counts.most_common(20) if c > 10 and w not in recommended_keywords]
    recommended_keywords.extend(other_high_freq[:5])
    
    if recommended_keywords:
        print("\n建议使用的关键词:\n")
        print("```python")
        print("keywords = [")
        for word in recommended_keywords[:15]:
            count = word_counts[word]
            print(f"    \"{word}\",  # 出现{count}次")
        print("]")
        print("```")
        
        # 生成配置文件
        config_file = "config/anchor_观山_推荐.json"
        config_data = {
            "name": "观山",
            "trigger_keywords": recommended_keywords[:15],
            "emotion_keywords": [],
            "gift_colors": [],
            "peak_time_start": 0,
            "peak_time_end": 20,
            "peak_weight": 2.0,
            "analysis_notes": "基于完整语音分析自动生成"
        }
        
        os.makedirs("config", exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 推荐配置已保存: {config_file}")
    else:
        print("\n⚠️ 未找到合适的高频词汇")
        print("   可能需要手动观看视频，总结主播的口头禅")
    
    # ======== 统计摘要 ========
    print("\n" + "=" * 70)
    print("📈 统计摘要")
    print("=" * 70)
    
    total_duration = segments[-1]["end"] if segments else 0
    total_words = len(all_text)
    
    print(f"\n  语音总时长: {total_duration/60:.1f} 分钟")
    print(f"  识别段数: {len(segments)} 段")
    print(f"  总字符数: {total_words} 字")
    print(f"  识别密度: {len(segments)/(total_duration/60):.1f} 段/分钟")
    print(f"  找到情感词汇: {len(word_counts)} 种")
    print(f"  情感词汇总出现: {sum(word_counts.values())} 次")


if __name__ == "__main__":
    audio_path = "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30_audio.wav"
    
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
    
    if not os.path.exists(audio_path):
        print(f"❌ 音频文件不存在: {audio_path}")
        sys.exit(1)
    
    analyze_full_speech(audio_path)
    
    print("\n" + "=" * 70)
    print("✅ 分析完成！")
    print("=" * 70)



