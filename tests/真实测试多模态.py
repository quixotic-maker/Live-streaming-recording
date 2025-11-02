#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实视频多模态检测测试
使用实际录制的视频进行精彩片段检测
"""

import os
import sys
import logging
from pathlib import Path
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.multimodal_detector import MultimodalDetector, create_anchor_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║          真实视频多模态检测测试                                ║")
    print("║          针对观山主播的精彩片段提取                             ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    # 视频路径
    video_dir = "/home/liu/videos/shanshan/抖音直播/观山"
    
    # 查找合并后的视频
    videos = [
        os.path.join(video_dir, "观山_2025-10-28.mp4"),
        os.path.join(video_dir, "观山_2025-10-30.mp4"),
    ]
    
    # 显示可用视频
    print("找到的视频文件:\n")
    available_videos = []
    for i, video_path in enumerate(videos):
        if os.path.exists(video_path):
            size_gb = os.path.getsize(video_path) / (1024**3)
            print(f"{i+1}. {os.path.basename(video_path)} ({size_gb:.2f} GB)")
            available_videos.append(video_path)
    
    if not available_videos:
        print("❌ 未找到视频文件")
        return
    
    # 选择视频
    print("\n请选择要分析的视频:")
    print("1. 10月28日视频")
    print("2. 10月30日视频")
    print("3. 两个都分析")
    
    choice = input("\n请输入选择 (1/2/3，直接回车默认选1): ").strip()
    
    if choice == "3":
        selected_videos = available_videos
    elif choice == "2" and len(available_videos) > 1:
        selected_videos = [available_videos[1]]
    else:
        selected_videos = [available_videos[0]]
    
    print(f"\n将分析 {len(selected_videos)} 个视频")
    
    # 创建或加载主播配置
    config_path = "config/anchor_观山.json"
    
    if os.path.exists(config_path):
        print(f"\n✅ 找到现有配置: {config_path}")
        config = None
    else:
        print("\n创建主播配置...")
        print("\n💡 根据您的观看经验，观山主播常说哪些话时会有表情包？")
        print("   例如：哈哈哈、笑死、我的天、可爱、宝宝等")
        
        keywords_input = input("\n请输入关键词（逗号分隔），直接回车使用默认: ").strip()
        
        if keywords_input:
            keywords = [k.strip() for k in keywords_input.replace('，', ',').split(',') if k.strip()]
        else:
            # 默认关键词
            keywords = [
                "哈哈哈",
                "笑死",
                "我的天",
                "可爱",
                "宝宝",
                "太搞笑了",
                "厉害",
                "好可爱",
            ]
            print(f"使用默认关键词: {', '.join(keywords)}")
        
        config = create_anchor_config("观山", keywords, save=True)
    
    # 创建检测器
    print("\n创建多模态检测器...")
    detector = MultimodalDetector(anchor_name="观山")
    
    # 分析每个视频
    all_results = {}
    
    for video_path in selected_videos:
        video_name = os.path.basename(video_path)
        print("\n" + "="*70)
        print(f"分析视频: {video_name}")
        print("="*70)
        
        size_gb = os.path.getsize(video_path) / (1024**3)
        print(f"文件大小: {size_gb:.2f} GB")
        print(f"预计处理时间: 30-45 分钟")
        print("\n💡 处理步骤:")
        print("  1. 礼物特效检测 (快)")
        print("  2. 语音识别 (慢，需要Whisper)")
        print("  3. 综合分析\n")
        
        # 检查是否已有结果
        result_file = f"highlights_{video_name.replace('.mp4', '')}.json"
        if os.path.exists(result_file):
            print(f"⚠️ 发现已有分析结果: {result_file}")
            use_existing = input("是否使用已有结果？(y/n，直接回车使用): ").strip().lower()
            
            if use_existing != 'n':
                with open(result_file, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                    highlights = [
                        (h['start'], h['end'], {
                            'score': h['score'],
                            'sources': h['sources'],
                            'details': h['details']
                        })
                        for h in result_data['highlights']
                    ]
                print(f"✅ 加载了 {len(highlights)} 个精彩片段")
                all_results[video_name] = highlights
                continue
        
        try:
            print("\n开始分析...\n")
            
            # 分析视频
            highlights = detector.fusion_analysis(
                video_path,
                gift_weight=3.0,        # 礼物权重
                keyword_weight=5.0,     # 关键词权重（最重要）
                peak_time_boost=2.0     # 前20分钟权重翻倍
            )
            
            all_results[video_name] = highlights
            
            # 显示结果
            print("\n" + "="*70)
            print("分析结果")
            print("="*70)
            
            if highlights:
                print(f"\n✅ 找到 {len(highlights)} 个精彩片段:\n")
                
                # 显示Top 15
                for i, (start, end, info) in enumerate(highlights[:15]):
                    duration = end - start
                    start_min = int(start // 60)
                    start_sec = int(start % 60)
                    end_min = int(end // 60)
                    end_sec = int(end % 60)
                    
                    print(f"  {i+1:2d}. {start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d} "
                          f"({duration:.1f}秒) - 得分:{info['score']:.1f}")
                    
                    # 显示来源
                    sources = ', '.join(info['sources'][:3])
                    if len(info['sources']) > 3:
                        sources += f" +{len(info['sources'])-3}项"
                    print(f"       来源: {sources}")
                
                if len(highlights) > 15:
                    print(f"\n  ... 还有 {len(highlights) - 15} 个片段")
                
                # 统计信息
                print("\n" + "-"*70)
                print("统计信息:")
                print("-"*70)
                
                total_duration = sum(end - start for start, end, _ in highlights)
                avg_score = sum(info['score'] for _, _, info in highlights) / len(highlights)
                
                high_score_count = sum(1 for _, _, info in highlights if info['score'] > 10)
                keyword_count = sum(1 for _, _, info in highlights 
                                   if any("关键词" in s for s in info['sources']))
                gift_count = sum(1 for _, _, info in highlights 
                                if "礼物" in info['sources'])
                peak_count = sum(1 for _, _, info in highlights 
                                if "高峰期" in info['sources'])
                
                print(f"  精彩片段总时长: {total_duration:.1f} 秒 ({total_duration/60:.1f} 分钟)")
                print(f"  平均得分: {avg_score:.1f}")
                print(f"  高分片段(>10分): {high_score_count} 个 ({high_score_count/len(highlights)*100:.1f}%)")
                print(f"  包含关键词: {keyword_count} 个")
                print(f"  包含礼物: {gift_count} 个")
                print(f"  在高峰期: {peak_count} 个")
                
                # 保存结果
                print("\n保存结果...")
                
                result_data = {
                    "video": video_path,
                    "video_name": video_name,
                    "total_highlights": len(highlights),
                    "statistics": {
                        "total_duration": total_duration,
                        "avg_score": avg_score,
                        "high_score_count": high_score_count,
                        "keyword_count": keyword_count,
                        "gift_count": gift_count,
                        "peak_count": peak_count
                    },
                    "highlights": [
                        {
                            "index": i + 1,
                            "start": start,
                            "end": end,
                            "duration": end - start,
                            "score": info["score"],
                            "sources": info["sources"],
                            "details": info["details"]
                        }
                        for i, (start, end, info) in enumerate(highlights)
                    ]
                }
                
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                
                print(f"✅ JSON结果已保存: {result_file}")
                
                # 保存时间轴
                timeline_file = f"timeline_{video_name.replace('.mp4', '')}.txt"
                with open(timeline_file, 'w', encoding='utf-8') as f:
                    f.write(f"精彩片段时间轴 - {video_name}\n")
                    f.write("="*70 + "\n\n")
                    
                    for i, (start, end, info) in enumerate(highlights):
                        start_time = f"{int(start//60):02d}:{int(start%60):02d}"
                        end_time = f"{int(end//60):02d}:{int(end%60):02d}"
                        f.write(f"{i+1:2d}. {start_time} - {end_time} "
                               f"(得分:{info['score']:.1f})\n")
                        f.write(f"    {', '.join(info['sources'][:3])}\n\n")
                
                print(f"✅ 时间轴已保存: {timeline_file}")
            
            else:
                print("\n⚠️ 未检测到精彩片段")
                print("\n可能的原因:")
                print("  1. 视频中没有明显的礼物特效")
                print("  2. 未安装Whisper，无法识别语音")
                print("  3. 关键词配置不匹配主播的话语")
        
        except Exception as e:
            logger.error(f"分析失败: {e}", exc_info=True)
            print(f"\n❌ 分析失败: {e}")
    
    # 汇总结果
    if all_results:
        print("\n" + "="*70)
        print("汇总统计")
        print("="*70)
        
        total_highlights = sum(len(highlights) for highlights in all_results.values())
        print(f"\n总共找到 {total_highlights} 个精彩片段")
        
        for video_name, highlights in all_results.items():
            print(f"  - {video_name}: {len(highlights)} 个片段")
    
    print("\n" + "="*70)
    print("✅ 测试完成！")
    print("="*70)
    print("\n💡 下一步:")
    print("  1. 查看生成的 JSON 文件了解详细结果")
    print("  2. 查看时间轴文件快速查看精彩时刻")
    print("  3. 使用 pyJianYingDraft 生成剪映草稿")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)



