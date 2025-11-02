#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕校对工具

功能：
1. 检测Whisper转录的置信度
2. 常见错误词自动纠正
3. 上下文智能纠错
4. 交互式人工校对
5. 生成校对报告
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
from difflib import SequenceMatcher


class SubtitleProofreader:
    """字幕校对器"""
    
    def __init__(self):
        """初始化"""
        # 常见错误词典（Whisper常见识别错误）
        self.error_dict = {
            # 人名/昵称
            "官山": "观山",
            "观沙": "观山",
            "冠山": "观山",
            
            # 口语/网络用语
            "老铁": "老铁们",
            "宝宝们": "宝宝",
            "家人门": "家人们",
            "家人民": "家人们",
            
            # 常见错字
            "谢谢你": "谢谢",
            "非常感谢": "谢谢",
            "在吗": "在吗",
            "拜拜": "拜拜",
            
            # 歌词常见错误
            "故是": "故事",
            "从出声": "从出生",
            "就飘着": "就飘着",
        }
        
        # 敏感词过滤（避免不当内容）
        self.sensitive_words = [
            # 添加需要过滤的敏感词
        ]
        
        # 标点符号规范
        self.punctuation_rules = {
            ",,": ",",
            "。。": "。",
            "！！": "！",
            "？？": "？",
            " ,": ",",
            " 。": "。",
            " ！": "！",
            " ？": "？",
        }
    
    def load_subtitle(self, subtitle_file: str) -> List[Dict]:
        """加载字幕文件"""
        if subtitle_file.endswith('.json'):
            # JSON格式（Whisper原始输出）
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("segments", [])
        
        elif subtitle_file.endswith('.srt'):
            # SRT格式
            return self._parse_srt(subtitle_file)
        
        else:
            raise ValueError(f"不支持的字幕格式: {subtitle_file}")
    
    def _parse_srt(self, srt_file: str) -> List[Dict]:
        """解析SRT文件"""
        segments = []
        
        with open(srt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # SRT格式：序号 -> 时间 -> 文本 -> 空行
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                # 时间行
                time_line = lines[1]
                times = re.findall(r'(\d+:\d+:\d+,\d+)', time_line)
                if len(times) == 2:
                    start = self._srt_time_to_seconds(times[0])
                    end = self._srt_time_to_seconds(times[1])
                    
                    # 文本（可能多行）
                    text = '\n'.join(lines[2:])
                    
                    segments.append({
                        "start": start,
                        "end": end,
                        "text": text
                    })
        
        return segments
    
    def _srt_time_to_seconds(self, time_str: str) -> float:
        """SRT时间转秒"""
        # 格式: HH:MM:SS,mmm
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    
    def detect_errors(self, segments: List[Dict]) -> Dict:
        """检测潜在错误"""
        issues = {
            "low_confidence": [],      # 低置信度
            "short_segments": [],      # 过短片段
            "repeated_text": [],       # 重复文本
            "suspicious_chars": [],    # 可疑字符
            "punctuation_issues": []   # 标点问题
        }
        
        prev_text = ""
        
        for i, seg in enumerate(segments):
            text = seg.get("text", "").strip()
            
            # 检查1：置信度（如果有）
            if "confidence" in seg and seg["confidence"] < 0.7:
                issues["low_confidence"].append({
                    "index": i,
                    "text": text,
                    "confidence": seg["confidence"]
                })
            
            # 检查2：过短片段（可能是识别错误）
            if len(text) < 3 and seg.get("end", 0) - seg.get("start", 0) > 2:
                issues["short_segments"].append({
                    "index": i,
                    "text": text,
                    "duration": seg.get("end", 0) - seg.get("start", 0)
                })
            
            # 检查3：重复文本
            if text == prev_text and len(text) > 5:
                issues["repeated_text"].append({
                    "index": i,
                    "text": text
                })
            
            # 检查4：可疑字符（乱码）
            if re.search(r'[^\u4e00-\u9fa5a-zA-Z0-9\s，。！？、；：""''（）【】…—]', text):
                issues["suspicious_chars"].append({
                    "index": i,
                    "text": text
                })
            
            # 检查5：标点问题
            for pattern in [",,", "。。", "！！", "？？"]:
                if pattern in text:
                    issues["punctuation_issues"].append({
                        "index": i,
                        "text": text,
                        "issue": f"重复标点: {pattern}"
                    })
            
            prev_text = text
        
        return issues
    
    def auto_correct(self, text: str) -> Tuple[str, List[str]]:
        """
        自动纠错
        
        Returns:
            (纠正后的文本, 修改列表)
        """
        corrections = []
        original = text
        
        # 1. 错误词典替换
        for wrong, right in self.error_dict.items():
            if wrong in text:
                text = text.replace(wrong, right)
                corrections.append(f"'{wrong}' → '{right}'")
        
        # 2. 标点规范化
        for pattern, replacement in self.punctuation_rules.items():
            if pattern in text:
                text = text.replace(pattern, replacement)
                corrections.append(f"标点规范: '{pattern}' → '{replacement}'")
        
        # 3. 去除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 4. 敏感词过滤
        for word in self.sensitive_words:
            if word in text:
                text = text.replace(word, "*" * len(word))
                corrections.append(f"过滤敏感词")
        
        return text, corrections
    
    def interactive_proofread(self, segments: List[Dict],
                             issues: Dict) -> List[Dict]:
        """
        交互式校对
        
        Args:
            segments: 字幕片段
            issues: 检测到的问题
            
        Returns:
            校对后的片段
        """
        print("\n" + "=" * 70)
        print("交互式校对")
        print("=" * 70)
        
        # 只校对有问题的片段
        to_check = set()
        for issue_type, issue_list in issues.items():
            for issue in issue_list:
                to_check.add(issue["index"])
        
        to_check = sorted(list(to_check))
        
        if not to_check:
            print("✓ 未发现需要校对的问题")
            return segments
        
        print(f"\n发现 {len(to_check)} 个可能需要校对的片段")
        print("操作: [回车]保持原文  [输入]修改  [s]跳过剩余\n")
        
        corrected_segments = segments.copy()
        
        for idx in to_check:
            seg = segments[idx]
            text = seg["text"]
            
            print(f"\n[{idx+1}/{len(segments)}] {seg['start']:.1f}s - {seg['end']:.1f}s")
            print(f"原文: {text}")
            
            # 显示问题类型
            for issue_type, issue_list in issues.items():
                for issue in issue_list:
                    if issue["index"] == idx:
                        print(f"问题: {issue_type}")
                        if "confidence" in issue:
                            print(f"置信度: {issue['confidence']:.2f}")
            
            # 自动纠错建议
            auto_corrected, corrections = self.auto_correct(text)
            if corrections:
                print(f"建议: {auto_corrected}")
                print(f"修改: {', '.join(corrections)}")
            
            # 用户输入
            new_text = input("修改为 (回车保持/s跳过): ").strip()
            
            if new_text.lower() == 's':
                print("跳过剩余")
                break
            elif new_text:
                corrected_segments[idx]["text"] = new_text
                print(f"✓ 已修改")
            elif corrections:
                # 如果用户回车且有自动纠错，应用自动纠错
                corrected_segments[idx]["text"] = auto_corrected
                print(f"✓ 应用自动纠错")
            else:
                print(f"○ 保持原文")
        
        return corrected_segments
    
    def generate_report(self, segments: List[Dict], issues: Dict,
                       corrections: int, output_file: str):
        """生成校对报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("字幕校对报告\n")
            f.write("=" * 70 + "\n\n")
            
            # 基本统计
            f.write(f"总片段数: {len(segments)}\n")
            f.write(f"人工修正: {corrections} 个\n\n")
            
            # 问题统计
            f.write("问题统计:\n")
            f.write("-" * 70 + "\n")
            
            total_issues = 0
            for issue_type, issue_list in issues.items():
                count = len(issue_list)
                total_issues += count
                if count > 0:
                    f.write(f"  {issue_type}: {count} 个\n")
            
            f.write(f"\n总问题数: {total_issues} 个\n\n")
            
            # 详细问题列表
            if total_issues > 0:
                f.write("详细问题:\n")
                f.write("-" * 70 + "\n\n")
                
                for issue_type, issue_list in issues.items():
                    if issue_list:
                        f.write(f"\n【{issue_type}】\n")
                        for issue in issue_list[:10]:  # 最多显示10个
                            f.write(f"  [{issue['index']}] {issue.get('text', '')}\n")
                        if len(issue_list) > 10:
                            f.write(f"  ... 还有 {len(issue_list) - 10} 个\n")
            
            # 建议
            f.write("\n\n建议:\n")
            f.write("-" * 70 + "\n")
            f.write("1. 对低置信度片段进行人工复查\n")
            f.write("2. 检查短片段是否为识别错误\n")
            f.write("3. 更新错误词典以提高后续准确性\n")
            f.write("4. 考虑使用更大的Whisper模型（large）\n")
        
        print(f"✓ 报告已保存: {output_file}")
    
    def save_corrected_subtitle(self, segments: List[Dict],
                                output_file: str, format: str = "srt"):
        """保存校对后的字幕"""
        if format == "srt":
            self._save_srt(segments, output_file)
        elif format == "json":
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({"segments": segments}, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 字幕已保存: {output_file}")
    
    def _save_srt(self, segments: List[Dict], output_file: str):
        """保存为SRT格式"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                start = self._seconds_to_srt_time(seg["start"])
                end = self._seconds_to_srt_time(seg["end"])
                text = seg["text"]
                
                f.write(f"{i}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """秒转SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def main():
    """主函数"""
    print("=" * 70)
    print("字幕校对工具")
    print("=" * 70)
    
    proofreader = SubtitleProofreader()
    
    # 输入文件
    material_dir = Path.home() / "shanshan_materials"
    
    # 选择来源
    print("\n请选择字幕来源:")
    print("  1. Whisper转录JSON（推荐）")
    print("  2. 已生成的SRT字幕")
    
    try:
        choice = input("\n选择 (1-2): ").strip()
        
        if choice == "1":
            subtitle_file = "speech_analysis_完整转录.json"
            if not os.path.exists(subtitle_file):
                print(f"错误: 文件不存在: {subtitle_file}")
                return
        elif choice == "2":
            subtitle_file = input("输入SRT文件路径: ").strip()
            if not os.path.exists(subtitle_file):
                print(f"错误: 文件不存在: {subtitle_file}")
                return
        else:
            print("无效选择")
            return
        
        # 加载字幕
        print(f"\n加载字幕: {subtitle_file}")
        segments = proofreader.load_subtitle(subtitle_file)
        print(f"✓ 加载了 {len(segments)} 个片段")
        
        # 检测问题
        print("\n检测潜在问题...")
        issues = proofreader.detect_errors(segments)
        
        total_issues = sum(len(v) for v in issues.values())
        print(f"✓ 发现 {total_issues} 个潜在问题")
        
        # 显示问题统计
        print("\n问题统计:")
        for issue_type, issue_list in issues.items():
            if issue_list:
                print(f"  {issue_type}: {len(issue_list)} 个")
        
        # 选择模式
        print("\n请选择校对模式:")
        print("  1. 仅自动纠错")
        print("  2. 交互式校对（推荐）")
        
        mode_choice = input("\n选择 (1-2): ").strip()
        
        if mode_choice == "1":
            # 自动纠错
            print("\n自动纠错...")
            corrections = 0
            for seg in segments:
                original = seg["text"]
                corrected, mods = proofreader.auto_correct(seg["text"])
                if corrected != original:
                    seg["text"] = corrected
                    corrections += 1
            print(f"✓ 自动修正了 {corrections} 个片段")
            corrected_segments = segments
        
        else:
            # 交互式校对
            corrected_segments = proofreader.interactive_proofread(segments, issues)
            corrections = sum(1 for i, seg in enumerate(segments) 
                            if seg["text"] != corrected_segments[i]["text"])
            print(f"\n✓ 修正了 {corrections} 个片段")
        
        # 保存结果
        output_dir = material_dir / "歌词字幕_校对后"
        output_dir.mkdir(exist_ok=True)
        
        # 保存SRT
        output_srt = output_dir / "字幕_校对后.srt"
        proofreader.save_corrected_subtitle(corrected_segments, str(output_srt), "srt")
        
        # 保存JSON
        output_json = output_dir / "字幕_校对后.json"
        proofreader.save_corrected_subtitle(corrected_segments, str(output_json), "json")
        
        # 生成报告
        report_file = output_dir / "校对报告.txt"
        proofreader.generate_report(segments, issues, corrections, str(report_file))
        
        print("\n" + "=" * 70)
        print("✅ 字幕校对完成！")
        print("=" * 70)
        print(f"\n输出目录: {output_dir}")
        print(f"  - 字幕_校对后.srt")
        print(f"  - 字幕_校对后.json")
        print(f"  - 校对报告.txt")
    
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()



