#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试多模态检测 - 非交互式版本
直接分析指定的视频文件
"""

import os
import sys
import logging
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
    print("║          真实视频多模态检测 - 观山主播                         ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    # 指定要分析的视频（可以通过命令行参数修改）
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        # 默认使用10月30日的视频（较新）
        video_path = "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        print("\n💡 使用方法:")
        print(f"   python3 {sys.argv[0]} <视频路径>")
        return
    
    video_name = os.path.basename(video_path)
    size_gb = os.path.getsize(video_path) / (1024**3)
    
    print(f"视频文件: {video_name}")
    print(f"文件大小: {size_gb:.2f} GB")
    print(f"预计处理时间: 30-50 分钟\n")
    
    # 检查是否已有结果
    result_file = f"highlights_{video_name.replace('.mp4', '')}.json"
    if os.path.exists(result_file):
        print(f"✅ 发现已有分析结果: {result_file}")
        
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        print(f"找到 {result_data['total_highlights']} 个精彩片段")
        print("\n显示结果...")
        
        # 显示Top 15
        highlights = result_data['highlights']
        for i, h in enumerate(highlights[:15]):
            start_min = int(h['start'] // 60)
            start_sec = int(h['start'] % 60)
            end_min = int(h['end'] // 60)
            end_sec = int(h['end'] % 60)
            
            print(f"  {i+1:2d}. {start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d} "
                  f"({h['duration']:.1f}秒) - 得分:{h['score']:.1f}")
            print(f"       来源: {', '.join(h['sources'][:3])}")
        
        if len(highlights) > 15:
            print(f"\n  ... 还有 {len(highlights) - 15} 个片段")
        
        # 统计信息
        stats = result_data.get('statistics', {})
        if stats:
            print("\n统计信息:")
            print(f"  总时长: {stats.get('total_duration', 0):.1f} 秒")
            print(f"  平均得分: {stats.get('avg_score', 0):.1f}")
            print(f"  高分片段: {stats.get('high_score_count', 0)} 个")
            print(f"  包含关键词: {stats.get('keyword_count', 0)} 个")
            print(f"  包含礼物: {stats.get('gift_count', 0)} 个")
        
        print(f"\n✅ 如需重新分析，请删除 {result_file} 文件")
        return
    
    # 创建或加载主播配置
    config_path = "config/anchor_观山.json"
    
    if not os.path.exists(config_path):
        print("创建主播配置...")
        
        # 默认关键词（根据观山主播的特点）
        keywords = [
            "哈哈哈",
            "笑死",
            "我的天",
            "可爱",
            "宝宝",
            "太搞笑了",
            "厉害",
            "好可爱",
            "萌",
            "开心",
        ]
        
        config = create_anchor_config("观山", keywords, save=True)
        print(f"✅ 配置已创建，关键词: {', '.join(keywords)}\n")
    else:
        print(f"✅ 使用现有配置: {config_path}\n")
    
    # 检查Whisper
    print("检查依赖...")
    try:
        import whisper
        print("✅ Whisper已安装，将进行语音识别")
    except ImportError:
        print("⚠️ Whisper未安装，只能进行礼物检测")
        print("   安装: pip install openai-whisper")
        print("   注意：没有语音识别，准确率会降低！\n")
    
    print("\n开始分析...")
    print("="*70)
    print("💡 处理步骤:")
    print("  1. 视频信息提取")
    print("  2. 礼物特效检测 (较快，约5-10分钟)")
    print("  3. 语音识别 (较慢，约20-40分钟)")
    print("  4. 综合分析")
    print("="*70 + "\n")
    
    # 创建检测器
    detector = MultimodalDetector(anchor_name="观山")
    
    try:
        # 分析视频
        highlights = detector.fusion_analysis(
            video_path,
            gift_weight=3.0,        # 礼物权重
            keyword_weight=5.0,     # 关键词权重（最重要）
            peak_time_boost=2.0     # 前20分钟权重翻倍
        )
        
        # 显示结果
        print("\n" + "="*70)
        print("分析完成！")
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
                
                # 显示关键词
                if 'keyword' in info['details']:
                    print(f"       关键词: \"{info['details']['keyword']}\"")
            
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
            
            print(f"✅ JSON结果: {result_file}")
            
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
                    f.write(f"    {', '.join(info['sources'][:3])}\n")
                    if 'keyword' in info['details']:
                        f.write(f"    关键词: \"{info['details']['keyword']}\"\n")
                    f.write("\n")
            
            print(f"✅ 时间轴文件: {timeline_file}")
        
        else:
            print("\n⚠️ 未检测到精彩片段")
            print("\n可能的原因:")
            print("  1. 视频中没有明显的礼物特效")
            print("  2. 未安装Whisper，无法识别语音")
            print("  3. 关键词配置不匹配主播的话语")
    
    except Exception as e:
        logger.error(f"分析失败: {e}", exc_info=True)
        print(f"\n❌ 分析失败: {e}")
        print("\n💡 请检查:")
        print("  1. 是否安装了 Whisper: pip install openai-whisper")
        print("  2. 视频文件是否完整")
        print("  3. 是否有足够的磁盘空间")
    
    print("\n" + "="*70)
    print("测试完成！")
    print("="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        logger.error(f"发生错误: {e}", exc_info=True)



