#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播内容分类器
将语音识别结果分类为：唱歌、礼物感谢、闲聊等
"""

import os
import json
import re
import logging
from typing import List, Dict, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class ContentClassifier:
    """直播内容分类器"""
    
    def __init__(self):
        """初始化分类器"""
        
        # 礼物感谢关键词
        self.gift_keywords = {
            "谢谢", "感谢", "爱你", "爱了", "么么哒",
            "礼物", "送礼", "刷礼物", "送个", "打赏",
            "比心", "爱心", "小心心"
        }
        
        # 互动关键词
        self.chat_keywords = {
            "宝宝", "宝贝", "亲爱的", "家人们", "兄弟们",
            "大家好", "晚上好", "怎么样", "对不对", "是不是",
            "喜欢", "好看", "漂亮", "帅", "美"
        }
        
        # 日常活动关键词
        self.daily_keywords = {
            # 开场/结束
            "开始", "来了", "上播", "下播", "拜拜", "再见", "结束",
            # 日常活动
            "喝水", "喝口水", "吃东西", "吃点", "休息", "等一下", "稍等",
            "看看", "看一下", "手机", "消息", "整理", "弄一下",
            # 状态描述
            "累了", "困了", "饿了", "渴了",
            # 无意义发音（非唱歌） - 移除"这个"、"那个"避免误捕获
            "嗯嗯", "啊啊", "哦哦", "呃呃"
        }
        
        # 歌曲相关词汇（通常是歌词）
        self.song_patterns = [
            r'[^\u4e00-\u9fa5\s]{15,}',  # 连续15个以上非中文非空格（可能是歌词，排除"happy night"）
            r'(啊+|呜+|哦+|嗯+){3,}',  # 拟声词重复
            r'.{2,}你.{2,}我.{2,}',  # 歌词模式：你...我...
        ]
    
    def classify_segment(self, text: str, duration: float = 0) -> str:
        """
        分类单个语音片段
        
        Args:
            text: 语音文字内容
            duration: 持续时间（秒）
            
        Returns:
            类别: "singing", "gift", "chat", "daily", "unknown"
        """
        text = text.strip()
        
        if not text:
            return "unknown"
        
        # 1. 检查是否是唱歌（优先级提高，避免被礼物感谢误捕获）
        if self._is_singing(text, duration):
            return "singing"
        
        # 2. 检查是否是礼物感谢
        if self._is_gift_thanks(text):
            return "gift"
        
        # 3. 检查是否是日常活动
        if self._is_daily(text):
            return "daily"
        
        # 4. 检查是否是闲聊
        if self._is_chatting(text):
            return "chat"
        
        return "unknown"
    
    def _is_gift_thanks(self, text: str) -> bool:
        """判断是否是礼物感谢"""
        # 包含礼物关键词
        for keyword in self.gift_keywords:
            if keyword in text:
                return True
        return False
    
    def _is_singing(self, text: str, duration: float) -> bool:
        """
        判断是否是唱歌（优化版，降低阈值）
        
        特征：
        1. 文字内容符合歌词模式
        2. 持续时间较长
        3. 包含拟声词或歌词特征
        4. 排除明确的聊天内容
        """
        text = text.strip()
        
        # 空文本
        if not text:
            return False
        
        # ✅ 降低最小长度: 5 → 3
        if len(text) < 3:
            return False
        
        # ✅ 排除：提到歌曲但不是在唱（聊天内容）
        chat_about_song_patterns = [
            '这首歌', '那首歌', '唱首', '唱一首', '来唱', '我们唱', '下一首',
            '点歌', '点首', '要听', '想听', '什么歌', '歌名', '好听吗',
            '叫什么', '是什么', '叫《', '歌叫', '来个', '我会唱', '我不会', '会不会'
        ]
        if any(p in text for p in chat_about_song_patterns):
            return False
        
        # ✅ 排除：问句（唱歌时很少问问题）
        if '？' in text or ('吗' in text and len(text) < 30):
            return False
        
        # ✅ 降低长文本阈值: 80 → 50
        if len(text) > 50:
            return True
        
        # ✅ 降低时长阈值: 45s → 30s
        if duration > 30 and len(text) > 15:
            return True
        
        # ✅ 降低组合阈值: 20s+40字 → 15s+25字
        if duration > 15 and len(text) > 25:
            return True
        
        # ✅ 新增: 短时长+歌词特征
        if duration > 8 and len(text) > 15:
            if self._has_lyric_patterns(text):
                return True
        
        # ✅ 新增: 中等时长+一定文字量
        if duration > 10 and len(text) > 20:
            return True
        
        # ✅ 保持: 重复词模式（"kiss kiss", "yeah yeah", "baby baby"）
        words = text.lower().split()
        if len(words) >= 2:
            # 计算重复词数量
            from collections import Counter
            word_counts = Counter(words)
            repeated_words = sum(1 for count in word_counts.values() if count >= 2)
            # 如果一半以上的单词都是重复的，很可能是歌词
            if repeated_words / len(word_counts) >= 0.4:
                return True
        
        # ✅ 保持: 检查歌词正则模式
        for pattern in self.song_patterns:
            if re.search(pattern, text):
                return True
        
        # ✅ 保持: 检查拟声词
        vocal_sounds = len(re.findall(r'[啊呜哦嗯唉]{2,}', text))
        if vocal_sounds >= 2:
            return True
        
        # ✅ 新增: 音符符号
        if '♪' in text or '🎵' in text or '🎶' in text:
            return True
        
        return False
    
    def _has_lyric_patterns(self, text: str) -> bool:
        """检查是否有歌词特征"""
        patterns = [
            r'你.{1,5}我',  # 你...我
            r'爱.{1,5}心',  # 爱...心
            r'[的了着过]{3,}',  # 连续虚词
            r'(啦|呀|哇|吧){2,}',  # 语气词重复
            r'想.{1,5}你',  # 想...你
            r'(oh|yeah|baby|love).{1,10}(oh|yeah|baby|love)',  # 英文歌词模式
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
    
    def _is_daily(self, text: str) -> bool:
        """判断是否是日常活动"""
        # 问句优先不判定为日常（避免误捕获聊天）
        if text.endswith('?') or text.endswith('？'):
            return False
        
        # 包含日常关键词
        for keyword in self.daily_keywords:
            if keyword in text:
                return True
        
        # 非常短的文字（<5字）通常是日常无意义发音
        if len(text) < 5:
            return True
        
        return False
    
    def _is_chatting(self, text: str) -> bool:
        """判断是否是闲聊"""
        # ✅ 新增：提到歌曲的聊天
        chat_about_song = ['这首歌', '那首歌', '什么歌', '歌名', '叫《', '来个', '唱首', '我们唱', '来唱', '下一首', '晚上好', '早上好', '好听']
        if any(p in text for p in chat_about_song):
            return True
        
        # 包含互动关键词
        for keyword in self.chat_keywords:
            if keyword in text:
                return True
        
        # 短句、问句通常是闲聊
        if text.endswith('?') or text.endswith('？'):
            return True
        
        if text.endswith('吗') or text.endswith('呢'):
            return True
        
        return False
    
    def classify_all(self, segments: List[Dict]) -> Dict[str, List[Dict]]:
        """
        分类所有语音片段
        
        Args:
            segments: 语音识别结果列表
                [{"start": 10.5, "end": 15.2, "text": "..."}]
        
        Returns:
            分类结果: {
                "singing": [...],
                "gift": [...],
                "chat": [...],
                "unknown": [...]
            }
        """
        classified = {
            "singing": [],
            "gift": [],
            "chat": [],
            "daily": [],
            "unknown": []
        }
        
        for seg in segments:
            duration = seg.get("end", 0) - seg.get("start", 0)
            category = self.classify_segment(seg["text"], duration)
            
            classified[category].append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "duration": duration
            })
        
        # ✅ 后处理: 优化singing片段
        classified = self._post_process_singing(classified)
        
        return classified
    
    def _post_process_singing(
        self, 
        classified: Dict[str, List[Dict]], 
        min_duration: float = 3.0,  # ✅ 降低: 5秒 → 3秒
        merge_gap: float = 10.0
    ) -> Dict[str, List[Dict]]:
        """
        后处理singing片段：过滤短片段、合并连续片段（优化版）
        
        Args:
            classified: 原始分类结果
            min_duration: 最小片段长度（秒），默认3秒（降低以保留更多片段）
            merge_gap: 合并间隔（秒），默认10秒
            
        Returns:
            优化后的分类结果
        """
        singing_segments = classified.get("singing", [])
        
        if not singing_segments:
            return classified
        
        logger.info(f"后处理singing片段: 原始{len(singing_segments)}个")
        
        # 步骤1: 按时间排序
        singing_segments = sorted(singing_segments, key=lambda x: x["start"])
        
        # 步骤2: 合并连续片段（间隔<10秒）
        merged_segments = []
        current = None
        
        for seg in singing_segments:
            if current is None:
                current = seg.copy()
                current["texts"] = [seg["text"]]
            else:
                gap = seg["start"] - current["end"]
                
                if gap <= merge_gap:
                    # 合并
                    current["end"] = seg["end"]
                    current["duration"] = current["end"] - current["start"]
                    current["text"] += " " + seg["text"]
                    current["texts"].append(seg["text"])
                else:
                    # 保存当前，开始新的
                    merged_segments.append(current)
                    current = seg.copy()
                    current["texts"] = [seg["text"]]
        
        # 添加最后一个
        if current is not None:
            merged_segments.append(current)
        
        logger.info(f"  合并后: {len(merged_segments)}个")
        
        # 步骤3: 过滤短片段（<5秒）
        filtered_singing = []
        reclassified = []
        
        for seg in merged_segments:
            if seg["duration"] >= min_duration:
                filtered_singing.append(seg)
            else:
                # 短片段重新分类为chat或unknown
                reclassified.append(seg)
        
        logger.info(f"  过滤<{min_duration}秒: 保留{len(filtered_singing)}个，重分类{len(reclassified)}个")
        
        # 步骤4: 将短片段重新分类为chat
        for seg in reclassified:
            # 简单策略：短片段大多是chat
            if any(keyword in seg["text"] for keyword in ["好听", "唱", "歌", "喜欢", "加油"]):
                classified["chat"].append(seg)
            else:
                classified["unknown"].append(seg)
        
        # 步骤5: 统计最终结果
        if filtered_singing:
            avg_duration = sum(s["duration"] for s in filtered_singing) / len(filtered_singing)
            logger.info(f"  最终singing: {len(filtered_singing)}个，平均时长{avg_duration:.1f}秒")
        else:
            logger.warning("  ⚠️  没有符合条件的singing片段")
        
        # 更新classified
        classified["singing"] = filtered_singing
        
        return classified
    
    def merge_continuous_segments(self, segments: List[Dict], max_gap: float = 3.0) -> List[Dict]:
        """
        合并连续的同类片段
        
        Args:
            segments: 同类别的片段列表
            max_gap: 最大间隔（秒），小于此间隔的片段会合并
            
        Returns:
            合并后的片段列表
        """
        if not segments:
            return []
        
        # 按开始时间排序
        segments = sorted(segments, key=lambda x: x["start"])
        
        merged = []
        current = segments[0].copy()
        current["texts"] = [current["text"]]
        
        for seg in segments[1:]:
            gap = seg["start"] - current["end"]
            
            # 间隔小，合并
            if gap <= max_gap:
                current["end"] = seg["end"]
                current["duration"] = current["end"] - current["start"]
                current["texts"].append(seg["text"])
            else:
                # 保存当前片段，开始新片段
                current["text"] = " | ".join(current["texts"])
                merged.append(current)
                
                current = seg.copy()
                current["texts"] = [current["text"]]
        
        # 添加最后一个片段
        current["text"] = " | ".join(current["texts"])
        merged.append(current)
        
        return merged
    
    def generate_material_library(self, classified: Dict, output_dir: str = "素材库"):
        """
        生成素材库文件
        
        Args:
            classified: 分类结果
            output_dir: 输出目录
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 为每个类别生成素材文件
        for category, segments in classified.items():
            if not segments:
                continue
            
            # 合并连续片段
            merged = self.merge_continuous_segments(segments)
            
            # 生成JSON格式
            json_file = os.path.join(output_dir, f"{category}_素材.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "category": category,
                    "total_count": len(merged),
                    "total_duration": sum(s["duration"] for s in merged),
                    "segments": merged
                }, f, ensure_ascii=False, indent=2)
            
            # 生成文本格式（方便查看）
            txt_file = os.path.join(output_dir, f"{category}_素材.txt")
            with open(txt_file, 'w', encoding='utf-8') as f:
                category_names = {
                    "singing": "🎤 唱歌片段",
                    "gift": "🎁 礼物感谢",
                    "chat": "💬 闲聊互动",
                    "unknown": "❓ 未分类"
                }
                
                f.write(f"{category_names.get(category, category)}\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"总片段数: {len(merged)}\n")
                f.write(f"总时长: {sum(s['duration'] for s in merged)/60:.1f} 分钟\n\n")
                
                for i, seg in enumerate(merged, 1):
                    start_min = int(seg["start"] // 60)
                    start_sec = int(seg["start"] % 60)
                    end_min = int(seg["end"] // 60)
                    end_sec = int(seg["end"] % 60)
                    
                    f.write(f"{i:3d}. {start_min:3d}:{start_sec:02d} - {end_min:3d}:{end_sec:02d} "
                           f"({seg['duration']:.1f}秒)\n")
                    f.write(f"     {seg['text']}\n\n")
        
        print(f"✅ 素材库已生成到: {output_dir}/")
    
    def analyze_statistics(self, classified: Dict) -> Dict:
        """
        统计分析
        
        Returns:
            统计信息
        """
        stats = {}
        
        for category, segments in classified.items():
            merged = self.merge_continuous_segments(segments)
            
            stats[category] = {
                "count": len(merged),
                "total_duration": sum(s["duration"] for s in merged),
                "avg_duration": sum(s["duration"] for s in merged) / len(merged) if merged else 0,
                "percentage": 0  # 稍后计算
            }
        
        # 计算百分比
        total_duration = sum(s["total_duration"] for s in stats.values())
        if total_duration > 0:
            for category in stats:
                stats[category]["percentage"] = (stats[category]["total_duration"] / total_duration) * 100
        
        return stats


def classify_from_transcript(transcript_file: str, output_dir: str = None):
    """
    从语音转录文件进行分类
    
    Args:
        transcript_file: 语音转录JSON文件
        output_dir: 输出目录
    """
    if output_dir is None:
        output_dir = os.path.expanduser("~/shanshan_materials/素材库")
    print("=" * 70)
    print("直播内容分类器")
    print("=" * 70)
    
    # 读取转录文件
    with open(transcript_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    segments = data.get("segments", [])
    print(f"\n总语音段数: {len(segments)}")
    
    # 创建分类器
    classifier = ContentClassifier()
    
    # 分类
    print("\n开始分类...")
    classified = classifier.classify_all(segments)
    
    # 统计
    print("\n分类结果:")
    print("-" * 70)
    
    category_names = {
        "singing": "🎤 唱歌片段",
        "gift": "🎁 礼物感谢",
        "chat": "💬 闲聊互动",
        "unknown": "❓ 未分类"
    }
    
    stats = classifier.analyze_statistics(classified)
    
    for category, info in stats.items():
        name = category_names.get(category, category)
        print(f"{name}:")
        print(f"  片段数: {info['count']:4d} 个")
        print(f"  总时长: {info['total_duration']/60:6.1f} 分钟 ({info['percentage']:.1f}%)")
        print(f"  平均时长: {info['avg_duration']:5.1f} 秒")
        print()
    
    # 生成素材库
    print("生成素材库...")
    classifier.generate_material_library(classified, output_dir)
    
    # 生成统计报告
    report_file = os.path.join(output_dir, "分类统计报告.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("直播内容分类统计报告\n")
        f.write("=" * 70 + "\n\n")
        
        total_segments = sum(info['count'] for info in stats.values())
        total_duration = sum(info['total_duration'] for info in stats.values())
        
        f.write(f"总片段数: {total_segments}\n")
        f.write(f"总时长: {total_duration/60:.1f} 分钟\n\n")
        
        f.write("各类别统计:\n")
        f.write("-" * 70 + "\n")
        
        for category, info in sorted(stats.items(), key=lambda x: x[1]['total_duration'], reverse=True):
            name = category_names.get(category, category)
            f.write(f"\n{name}\n")
            f.write(f"  片段数: {info['count']} 个\n")
            f.write(f"  总时长: {info['total_duration']/60:.1f} 分钟 ({info['percentage']:.1f}%)\n")
            f.write(f"  平均时长: {info['avg_duration']:.1f} 秒\n")
    
    print(f"✅ 统计报告: {report_file}")
    
    return classified, stats


if __name__ == "__main__":
    import sys
    
    transcript_file = "speech_analysis_完整转录.json"
    
    if len(sys.argv) > 1:
        transcript_file = sys.argv[1]
    
    if not os.path.exists(transcript_file):
        print(f"❌ 文件不存在: {transcript_file}")
        sys.exit(1)
    
    classify_from_transcript(transcript_file)
    
    print("\n" + "=" * 70)
    print("✅ 分类完成！")
    print("=" * 70)

