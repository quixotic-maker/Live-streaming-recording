#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立弹幕录制器 - 不影响视频录制

使用方法:
    python3 standalone_danmaku_recorder.py

输出:
    ~/videos/shanshan/抖音直播/观山/观山_{date}_danmaku.jsonl
"""

import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from danmaku_douyin import DouyinDanmakuRecorder
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保在正确的目录运行此脚本")
    sys.exit(1)


def main():
    print("=" * 70)
    print("🎬 抖音弹幕独立录制器")
    print("=" * 70)
    print()
    
    # 配置
    live_url = "https://live.douyin.com/83970695603"
    anchor_name = "观山"
    output_dir = os.path.expanduser("~/videos/shanshan/抖音直播/观山")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📺 直播间: {live_url}")
    print(f"👤 主播: {anchor_name}")
    print(f"📁 输出目录: {output_dir}")
    print()
    
    # 检查websockets库
    try:
        import websockets
        print("✅ websockets库已安装")
    except ImportError:
        print("❌ websockets库未安装")
        print("   请运行: pip install websockets")
        return 1
    
    print()
    print("=" * 70)
    print("🚀 开始录制弹幕...")
    print("   按 Ctrl+C 停止录制")
    print("=" * 70)
    print()
    
    # 创建弹幕录制器
    try:
        recorder = DouyinDanmakuRecorder(
            room_url=live_url,
            output_dir=output_dir,
            anchor_name=anchor_name
        )
        
        # 启动录制
        recorder.start_recording(mode='auto')
        
        # 保持运行
        try:
            print("📊 录制中... (按Ctrl+C停止)")
            while recorder.is_recording:
                time.sleep(1)
                # 显示统计
                stats = recorder.stats
                print(f"💬 弹幕: {stats['chat_messages']} | 🎁 礼物: {stats['gift_events']} | 📊 总消息: {stats['total_messages']}", end='\r')
        except KeyboardInterrupt:
            print("\n\n⏹️  停止录制...")
            recorder.stop_recording()
            
            print()
            print("=" * 70)
            print("✅ 录制完成")
            print("=" * 70)
            print(f"📊 统计信息:")
            stats = recorder.stats
            print(f"   💬 弹幕: {stats['chat_messages']} 条")
            print(f"   🎁 礼物: {stats['gift_events']} 个")
            print(f"   👍 点赞: {stats['like_count']} 次")
            print(f"   👥 加入: {stats['member_join']} 人")
            print(f"   📊 总消息: {stats['total_messages']} 条")
            
            # 输出文件
            date_str = datetime.now().strftime('%Y-%m-%d')
            output_file = os.path.join(output_dir, f"{anchor_name}_{date_str}_danmaku.jsonl")
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file) / 1024 / 1024
                print(f"   📝 输出文件: {output_file}")
                print(f"   💾 文件大小: {file_size:.2f} MB")
            print()
                
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

