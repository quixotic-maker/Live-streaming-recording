#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试弹幕渲染系统
"""

import sys
import os
import json
import logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from danmaku_renderer import DanmakuRenderer, generate_three_versions, DanmakuAligner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_mock_danmaku_file(output_path: str):
    """创建模拟弹幕文件"""
    messages = []
    
    # 生成100条模拟弹幕
    start_time = 1730382000  # 2025-10-31 19:00:00
    
    for i in range(100):
        timestamp = start_time + i * 2  # 每2秒一条
        messages.append({
            'type': 'chat',
            'timestamp': timestamp,
            'user': f'观众{i%10 + 1}',
            'content': f'这是第{i+1}条弹幕消息'
        })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + '\n')
    
    logger.info(f"✅ 模拟弹幕文件已创建: {output_path}")
    logger.info(f"   共 {len(messages)} 条弹幕")


def test_ass_generation():
    """测试ASS字幕生成"""
    print("\n" + "="*80)
    print("测试1: ASS字幕生成")
    print("="*80 + "\n")
    
    # 创建测试目录
    test_dir = "./test_output/danmaku_render_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建模拟弹幕
    danmaku_file = os.path.join(test_dir, "test_danmaku.jsonl")
    create_mock_danmaku_file(danmaku_file)
    
    # 创建渲染器
    renderer = DanmakuRenderer({
        'video_width': 1920,
        'video_height': 1080,
        'font_size': 30,
        'duration': 8,
        'max_per_second': 10
    })
    
    # 加载弹幕
    print("\n步骤1: 加载弹幕...")
    danmaku_list = renderer.load_danmaku(danmaku_file)
    print(f"  加载了 {len(danmaku_list)} 条弹幕")
    
    # 过滤弹幕
    print("\n步骤2: 过滤弹幕...")
    filtered = renderer.filter_danmaku(danmaku_list)
    print(f"  过滤后 {len(filtered)} 条弹幕")
    
    # 生成ASS字幕
    print("\n步骤3: 生成ASS字幕...")
    ass_file = os.path.join(test_dir, "test_danmaku.ass")
    
    if renderer.generate_ass_subtitle(
        filtered,
        ass_file,
        video_start_time=1730382000
    ):
        print(f"  ✅ ASS字幕生成成功")
        print(f"  文件位置: {ass_file}")
        
        # 显示前10行内容
        print("\n  前10行内容:")
        with open(ass_file, 'r', encoding='utf-8-sig') as f:
            for i, line in enumerate(f):
                if i >= 10:
                    break
                print(f"    {line.rstrip()}")
    
    print("\n" + "="*80)
    print("测试完成！")
    print("="*80)
    print(f"\n输出目录: {test_dir}")
    print()


def test_time_sync():
    """测试时间戳同步"""
    print("\n" + "="*80)
    print("测试2: 时间戳同步")
    print("="*80 + "\n")
    
    # 创建测试目录
    test_dir = "./test_output/danmaku_sync_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建模拟弹幕
    danmaku_file = os.path.join(test_dir, "test_danmaku.jsonl")
    create_mock_danmaku_file(danmaku_file)
    
    # 创建对齐器
    aligner = DanmakuAligner()
    
    # 同步时间戳
    video_start = 1730382000  # 视频开始时间
    
    print("同步时间戳...")
    offset = aligner.sync_timestamps(video_start, danmaku_file)
    
    print(f"\n同步结果:")
    print(f"  视频开始: {datetime.fromtimestamp(video_start)}")
    print(f"  弹幕开始: {datetime.fromtimestamp(aligner.danmaku_start_time)}")
    print(f"  时间偏移: {offset:.2f} 秒")
    
    # 调整弹幕时间戳
    print("\n调整弹幕时间戳...")
    adjusted_file = os.path.join(test_dir, "test_danmaku_adjusted.jsonl")
    aligner.adjust_danmaku_timestamps(danmaku_file, adjusted_file, offset)
    
    # 验证调整结果
    print("\n验证调整结果（前5条）:")
    with open(adjusted_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 5:
                break
            msg = json.loads(line)
            print(f"  {i+1}. 时间戳: {msg['timestamp']:.2f}s - {msg['content']}")
    
    print("\n" + "="*80)
    print("测试完成！")
    print("="*80)
    print(f"\n输出目录: {test_dir}")
    print()


def test_full_render():
    """测试完整渲染流程（需要真实视频）"""
    print("\n" + "="*80)
    print("测试3: 完整渲染流程")
    print("="*80 + "\n")
    
    # 获取视频文件
    video_path = input("请输入视频文件路径（留空跳过）: ").strip()
    
    if not video_path:
        print("❌ 未提供视频文件，跳过完整渲染测试")
        return
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    # 创建测试目录
    test_dir = "./test_output/danmaku_full_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建模拟弹幕
    danmaku_file = os.path.join(test_dir, "test_danmaku.jsonl")
    create_mock_danmaku_file(danmaku_file)
    
    # 渲染弹幕视频
    print("\n开始渲染弹幕视频...")
    output_path = os.path.join(test_dir, "video_with_danmaku.mp4")
    
    renderer = DanmakuRenderer()
    
    success = renderer.render_video_with_danmaku(
        video_path=video_path,
        danmaku_file=danmaku_file,
        output_path=output_path,
        video_start_time=0
    )
    
    if success:
        print("\n" + "="*80)
        print("✅ 弹幕视频生成成功！")
        print("="*80)
        print(f"\n输出文件: {output_path}")
        print(f"文件大小: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
    else:
        print("\n❌ 弹幕视频生成失败")
    
    print()


def test_three_versions():
    """测试三版本生成（需要真实视频）"""
    print("\n" + "="*80)
    print("测试4: 三版本生成")
    print("="*80 + "\n")
    
    # 获取文件
    video_path = input("请输入视频文件路径（留空跳过）: ").strip()
    
    if not video_path:
        print("❌ 未提供视频文件，跳过三版本测试")
        return
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    subtitle_file = input("请输入字幕文件路径（可选，留空跳过）: ").strip()
    
    # 创建测试目录
    test_dir = "./test_output/three_versions_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建模拟弹幕
    danmaku_file = os.path.join(test_dir, "test_danmaku.jsonl")
    create_mock_danmaku_file(danmaku_file)
    
    # 生成三个版本
    print("\n开始生成三个版本...")
    
    results = generate_three_versions(
        video_path=video_path,
        danmaku_file=danmaku_file,
        subtitle_file=subtitle_file if subtitle_file and os.path.exists(subtitle_file) else None,
        output_dir=test_dir,
        base_name="测试视频"
    )
    
    # 显示结果
    print("\n" + "="*80)
    print("生成结果")
    print("="*80)
    
    for version, path in results.items():
        if os.path.exists(path):
            size = os.path.getsize(path) / 1024 / 1024
            print(f"\n✅ {version} 版本:")
            print(f"   路径: {path}")
            print(f"   大小: {size:.2f} MB")
        else:
            print(f"\n❌ {version} 版本生成失败")
    
    print(f"\n输出目录: {test_dir}")
    print()


def main():
    """主函数"""
    print()
    print("="*80)
    print("弹幕渲染系统测试")
    print("="*80)
    print()
    print("测试选项:")
    print("  1. 测试ASS字幕生成（推荐，快速）")
    print("  2. 测试时间戳同步")
    print("  3. 测试完整渲染流程（需要视频文件）")
    print("  4. 测试三版本生成（需要视频文件）")
    print("  5. 全部测试")
    print("  6. 退出")
    print()
    
    choice = input("请选择 [1-6]: ").strip()
    
    if choice == '1':
        test_ass_generation()
    elif choice == '2':
        test_time_sync()
    elif choice == '3':
        test_full_render()
    elif choice == '4':
        test_three_versions()
    elif choice == '5':
        test_ass_generation()
        test_time_sync()
        test_full_render()
        test_three_versions()
    elif choice == '6':
        print("再见！")
    else:
        print("❌ 无效选择")


if __name__ == "__main__":
    main()



