#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试升级检测系统
"""

import sys
import os
import json
import logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from upgrade_detector import UpgradeDetector, process_upgrade_detection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_mock_danmaku_file(output_path: str):
    """创建模拟弹幕文件"""
    messages = [
        # 正常聊天
        {'type': 'chat', 'timestamp': 100, 'user': '观众A', 'content': '主播唱得真好听'},
        {'type': 'chat', 'timestamp': 105, 'user': '观众B', 'content': '666'},
        
        # 升级事件1
        {'type': 'chat', 'timestamp': 120, 'user': '系统', 'content': '恭喜观众C升到16级！'},
        
        # 更多聊天
        {'type': 'chat', 'timestamp': 130, 'user': '观众D', 'content': '谢谢大家'},
        
        # 升级事件2
        {'type': 'chat', 'timestamp': 200, 'user': '系统', 'content': '观众E达到18级'},
        
        # 礼物
        {'type': 'gift', 'timestamp': 250, 'user': '土豪F', 'gift_name': '火箭', 'gift_count': 3},
        
        # 升级事件3（低于阈值，应该被过滤）
        {'type': 'chat', 'timestamp': 300, 'user': '系统', 'content': '观众G升到10级'},
        
        # 升级事件4
        {'type': 'chat', 'timestamp': 400, 'user': '系统', 'content': '恭喜观众H lv20'},
    ]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + '\n')
    
    logger.info(f"✅ 模拟弹幕文件已创建: {output_path}")


def create_mock_transcript_file(output_path: str):
    """创建模拟转文字文件"""
    transcript = {
        'text': '这是完整的转文字结果...',
        'segments': [
            {'start': 115, 'end': 125, 'text': '谢谢宝宝们的支持'},
            {'start': 125, 'end': 135, 'text': '恭喜这位宝宝升到16级'},  # 升级
            {'start': 205, 'end': 215, 'text': '哇有宝宝升到18级了谢谢'},  # 升级
            {'start': 410, 'end': 420, 'text': '恭喜恭喜达到20级'},  # 升级
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ 模拟转文字文件已创建: {output_path}")


def test_detection_only():
    """测试检测功能（不生成视频）"""
    print("\n" + "="*80)
    print("测试升级检测 - 仅检测（不生成视频）")
    print("="*80 + "\n")
    
    # 创建测试目录
    test_dir = "./test_output/upgrade_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建模拟数据
    danmaku_file = os.path.join(test_dir, "test_danmaku.jsonl")
    transcript_file = os.path.join(test_dir, "test_transcript.json")
    
    create_mock_danmaku_file(danmaku_file)
    create_mock_transcript_file(transcript_file)
    
    # 创建检测器
    detector = UpgradeDetector({
        'min_level': 16,
        'before_seconds': 5,
        'after_seconds': 10
    })
    
    # 1. 从弹幕检测
    print("\n" + "-"*80)
    print("步骤1: 从弹幕数据检测")
    print("-"*80)
    danmaku_upgrades = detector.detect_from_danmaku(danmaku_file)
    
    print(f"\n检测到 {len(danmaku_upgrades)} 个升级事件:")
    for i, upgrade in enumerate(danmaku_upgrades, 1):
        print(f"  {i}. [{upgrade['timestamp']}s] {upgrade['user']} 升到 {upgrade['level']} 级")
        print(f"     原文: {upgrade['original_text']}")
    
    # 2. 从语音识别检测
    print("\n" + "-"*80)
    print("步骤2: 从语音识别检测")
    print("-"*80)
    speech_upgrades = detector.detect_from_transcript(transcript_file)
    
    print(f"\n检测到 {len(speech_upgrades)} 个升级事件:")
    for i, upgrade in enumerate(speech_upgrades, 1):
        print(f"  {i}. [{upgrade['timestamp']}s] {upgrade['user']} 说到 {upgrade['level']} 级")
        print(f"     原文: {upgrade['original_text']}")
    
    # 3. 合并结果
    print("\n" + "-"*80)
    print("步骤3: 合并检测结果")
    print("-"*80)
    all_upgrades = detector.merge_detections(danmaku_upgrades, speech_upgrades)
    
    print(f"\n合并后共 {len(all_upgrades)} 个升级事件:")
    for i, upgrade in enumerate(all_upgrades, 1):
        verified = "✓ 已验证" if upgrade.get('verified') else ""
        sources = upgrade.get('sources', [upgrade.get('source')])
        sources_str = "+".join(sources)
        
        print(f"  {i}. [{upgrade['timestamp']}s] {upgrade['user']} 升到 {upgrade['level']} 级")
        print(f"     来源: {sources_str} {verified}")
    
    # 保存元数据
    metadata_file = os.path.join(test_dir, "upgrades_metadata.json")
    detector.save_upgrade_metadata(all_upgrades, metadata_file)
    
    print("\n" + "="*80)
    print("测试完成！")
    print("="*80)
    print(f"\n输出文件:")
    print(f"  弹幕文件: {danmaku_file}")
    print(f"  转文字文件: {transcript_file}")
    print(f"  元数据文件: {metadata_file}")
    print()


def test_full_process():
    """测试完整流程（包括视频生成）"""
    print("\n" + "="*80)
    print("测试升级检测 - 完整流程（包括视频生成）")
    print("="*80 + "\n")
    
    # 检查是否有真实视频文件
    video_path = input("请输入视频文件路径（留空跳过视频生成）: ").strip()
    
    if not video_path:
        print("❌ 未提供视频文件，跳过视频生成")
        return
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    # 创建测试目录
    test_dir = "./test_output/upgrade_full_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建模拟数据
    danmaku_file = os.path.join(test_dir, "test_danmaku.jsonl")
    transcript_file = os.path.join(test_dir, "test_transcript.json")
    
    create_mock_danmaku_file(danmaku_file)
    create_mock_transcript_file(transcript_file)
    
    # 运行完整流程
    result = process_upgrade_detection(
        video_path=video_path,
        danmaku_file=danmaku_file,
        transcript_file=transcript_file,
        output_dir=test_dir
    )
    
    # 显示结果
    print("\n" + "="*80)
    print("处理结果")
    print("="*80)
    print(f"\n检测到的升级事件: {len(result['upgrades'])}")
    print(f"生成的视频文件: {len(result['videos']['generated_files'])}")
    
    print("\n升级事件列表:")
    for upgrade in result['upgrades']:
        print(f"  • {upgrade['user']} 升到 {upgrade['level']} 级 ({upgrade['timestamp']}s)")
    
    print("\n生成的文件:")
    for filename in result['videos']['generated_files']:
        print(f"  • {filename}")
    
    print(f"\n输出目录: {test_dir}")
    print()


def main():
    """主函数"""
    print()
    print("="*80)
    print("升级检测系统测试")
    print("="*80)
    print()
    print("测试模式:")
    print("  1. 仅测试检测功能（不生成视频，推荐）")
    print("  2. 测试完整流程（包括视频生成，需要提供视频文件）")
    print("  3. 退出")
    print()
    
    choice = input("请选择 [1-3]: ").strip()
    
    if choice == '1':
        test_detection_only()
    elif choice == '2':
        test_full_process()
    elif choice == '3':
        print("再见！")
    else:
        print("❌ 无效选择")


if __name__ == "__main__":
    main()



