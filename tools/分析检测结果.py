#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析已有的检测结果，看看都找到了什么
"""

import json
from collections import Counter

def analyze_highlights(json_file):
    """分析精彩片段检测结果"""
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    highlights = data['highlights']
    stats = data['statistics']
    
    print("=" * 70)
    print(f"检测结果分析 - {data['video_name']}")
    print("=" * 70)
    
    print(f"\n📊 总体统计:")
    print(f"  - 精彩片段数: {data['total_highlights']}")
    print(f"  - 总时长: {stats['total_duration']}秒 ({stats['total_duration']/60:.1f}分钟)")
    print(f"  - 平均得分: {stats['avg_score']:.2f}")
    print(f"  - 高分片段(>10): {stats['high_score_count']}")
    print(f"  - 包含关键词: {stats['keyword_count']}")
    print(f"  - 包含礼物: {stats['gift_count']}")
    print(f"  - 在高峰期: {stats['peak_count']}")
    
    # 分析关键词分布
    print("\n" + "=" * 70)
    print("🎤 检测到的关键词分布")
    print("=" * 70)
    
    keyword_count = Counter()
    for h in highlights:
        if 'keyword' in h['details']:
            keyword_count[h['details']['keyword']] += 1
    
    print(f"\n总共找到 {len(keyword_count)} 种关键词:\n")
    for i, (keyword, count) in enumerate(keyword_count.most_common(), 1):
        percentage = (count / len(highlights)) * 100
        print(f"  {i}. \"{keyword}\" - {count}次 ({percentage:.1f}%)")
    
    # 分析得分分布
    print("\n" + "=" * 70)
    print("📈 得分分布")
    print("=" * 70)
    
    scores = [h['score'] for h in highlights]
    score_ranges = {
        "⭐⭐⭐⭐⭐ (15+)": [s for s in scores if s >= 15],
        "⭐⭐⭐⭐ (10-15)": [s for s in scores if 10 <= s < 15],
        "⭐⭐⭐ (5-10)": [s for s in scores if 5 <= s < 10],
        "⭐⭐ (0-5)": [s for s in scores if s < 5],
    }
    
    print()
    for range_name, range_scores in score_ranges.items():
        count = len(range_scores)
        percentage = (count / len(scores)) * 100 if scores else 0
        print(f"  {range_name}: {count}个 ({percentage:.1f}%)")
    
    # 分析时间分布
    print("\n" + "=" * 70)
    print("⏰ 时间分布")
    print("=" * 70)
    
    time_periods = {
        "前20分钟 (高峰期)": [],
        "20-60分钟": [],
        "1-2小时": [],
        "2小时以后": []
    }
    
    for h in highlights:
        start_min = h['start'] / 60
        if start_min < 20:
            time_periods["前20分钟 (高峰期)"].append(h)
        elif start_min < 60:
            time_periods["20-60分钟"].append(h)
        elif start_min < 120:
            time_periods["1-2小时"].append(h)
        else:
            time_periods["2小时以后"].append(h)
    
    print()
    for period, period_highlights in time_periods.items():
        count = len(period_highlights)
        percentage = (count / len(highlights)) * 100 if highlights else 0
        if count > 0:
            avg_score = sum(h['score'] for h in period_highlights) / count
            print(f"  {period}: {count}个 ({percentage:.1f}%), 平均得分{avg_score:.1f}")
        else:
            print(f"  {period}: 0个")
    
    # Top 10精彩片段详情
    print("\n" + "=" * 70)
    print("🌟 Top 10 精彩片段")
    print("=" * 70)
    
    top_highlights = sorted(highlights, key=lambda h: h['score'], reverse=True)[:10]
    
    print()
    for i, h in enumerate(top_highlights, 1):
        start_min = int(h['start'] // 60)
        start_sec = int(h['start'] % 60)
        end_min = int(h['end'] // 60)
        end_sec = int(h['end'] % 60)
        
        print(f"{i:2d}. {start_min:3d}:{start_sec:02d}-{end_min:3d}:{end_sec:02d} "
              f"得分{h['score']:.1f} ", end="")
        
        if 'keyword' in h['details']:
            print(f"[{h['details']['keyword']}]", end=" ")
        
        sources_short = ', '.join([s.replace('关键词:', '') for s in h['sources'][:2]])
        print(f"({sources_short})")
    
    # 问题分析
    print("\n" + "=" * 70)
    print("🔍 问题分析")
    print("=" * 70)
    
    issues = []
    
    if stats['high_score_count'] == 0:
        issues.append("❌ 没有高分片段(>10)，说明没有检测到\"超级精彩\"时刻")
    
    if stats['gift_count'] == 0:
        issues.append("⚠️ 没有检测到礼物，可能主播没收到礼物或检测不准确")
    
    if stats['peak_count'] < data['total_highlights'] * 0.2:
        issues.append(f"⚠️ 高峰期片段只有{stats['peak_count']}个，可能前20分钟确实精彩内容较少")
    
    # 检查关键词是否太普通
    common_keywords = ["可爱", "宝宝", "开心", "厉害"]
    common_count = sum(keyword_count.get(kw, 0) for kw in common_keywords)
    if common_count > len(highlights) * 0.7:
        issues.append(f"⚠️ 超过70%是常见词汇({', '.join(common_keywords)})，可能不够精准")
    
    if stats['avg_score'] < 7:
        issues.append(f"⚠️ 平均得分{stats['avg_score']:.1f}较低，说明整体质量不高")
    
    print("\n发现的问题:\n")
    for issue in issues:
        print(f"  {issue}")
    
    # 优化建议
    print("\n" + "=" * 70)
    print("💡 优化建议")
    print("=" * 70)
    
    print("\n1. 调整关键词配置:")
    print("   当前关键词可能太常见，建议更换为：")
    print("   - 更有表情特征的词：\"哈哈哈\"、\"笑死\"、\"我的天\"")
    print("   - 情绪爆发的词：\"卧槽\"、\"天啊\"、\"太搞笑了\"")
    print("   - 主播独特的口头禅（需要观看视频总结）")
    
    print("\n2. 降低检测阈值:")
    print("   当前可能阈值过高，可以尝试：")
    print("   - 降低最小片段时长要求")
    print("   - 降低最小得分要求")
    
    print("\n3. 手动验证几个时刻:")
    print("   建议打开视频，检查以下时刻是否真的精彩：")
    for i, h in enumerate(top_highlights[:5], 1):
        start_min = int(h['start'] // 60)
        start_sec = int(h['start'] % 60)
        keyword = h['details'].get('keyword', '未知')
        print(f"   {i}. {start_min:3d}:{start_sec:02d} (关键词: {keyword})")


if __name__ == "__main__":
    import sys
    
    json_file = "highlights_观山_2025-10-30.json"
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    
    analyze_highlights(json_file)



