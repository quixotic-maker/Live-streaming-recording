#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试弹幕录制系统

测试方式：
1. 模拟弹幕数据测试
2. 真实连接测试（需要DouyinBarrageGrab）
"""

import sys
import os
import time
import json
import logging
from datetime import datetime

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from danmaku_douyin import DouyinDanmakuRecorder

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_with_mock_data():
    """使用模拟数据测试"""
    print("="*80)
    print("测试弹幕录制系统 - 模拟数据模式")
    print("="*80)
    print()
    
    # 创建录制器
    recorder = DouyinDanmakuRecorder(
        room_url="https://live.douyin.com/test",
        output_dir="./test_output/danmaku_test",
        anchor_name="测试主播"
    )
    
    # 设置回调
    upgrade_count = [0]
    gift_count = [0]
    
    def on_upgrade(event):
        upgrade_count[0] += 1
        print(f"\n🎉 检测到升级事件 #{upgrade_count[0]}:")
        print(f"   用户: {event['user']}")
        print(f"   等级: {event['level']}")
        print(f"   时间: {event['time']}")
        print()
    
    def on_gift(event):
        gift_count[0] += 1
        print(f"\n🎁 检测到礼物事件 #{gift_count[0]}:")
        print(f"   用户: {event['user']}")
        print(f"   礼物: {event['gift_name']} x{event['gift_count']}")
        print(f"   价值: {event['total_value']} 抖音币")
        print()
    
    def on_chat(message):
        print(f"💬 [{message['user']}]: {message['content']}")
    
    recorder.set_callback('on_upgrade', on_upgrade)
    recorder.set_callback('on_gift', on_gift)
    recorder.set_callback('on_chat', on_chat)
    
    # 模拟消息
    print("\n开始模拟弹幕消息...")
    print("-"*80)
    print()
    
    # 1. 聊天消息
    recorder.process_message({
        'type': 'chat',
        'user': {'nickname': '观众A', 'id': '001'},
        'content': '主播唱得好好听！'
    })
    
    time.sleep(0.5)
    
    # 2. 升级消息
    recorder.process_message({
        'type': 'chat',
        'user': {'nickname': '观众B', 'id': '002'},
        'content': '恭喜观众B升到16级！'
    })
    
    time.sleep(0.5)
    
    # 3. 礼物消息
    recorder.process_message({
        'type': 'gift',
        'user': {'nickname': '土豪C', 'id': '003'},
        'gift': {'name': '火箭', 'id': '001', 'diamondCount': 1000},
        'count': 3
    })
    
    time.sleep(0.5)
    
    # 4. 更多聊天
    recorder.process_message({
        'type': 'chat',
        'user': {'nickname': '观众D', 'id': '004'},
        'content': '谢谢送礼物的宝宝们'
    })
    
    time.sleep(0.5)
    
    # 5. 另一个升级
    recorder.process_message({
        'type': 'chat',
        'user': {'nickname': '观众E', 'id': '005'},
        'content': '观众E达到18级啦！'
    })
    
    time.sleep(0.5)
    
    # 6. 更多礼物
    recorder.process_message({
        'type': 'gift',
        'user': {'nickname': '土豪F', 'id': '006'},
        'gift': {'name': '跑车', 'id': '002', 'diamondCount': 1000},
        'count': 5
    })
    
    # 保存数据
    print()
    print("-"*80)
    print("保存数据...")
    recorder._flush_buffers()
    recorder.stats['end_time'] = time.time()
    recorder.stats['recording_duration'] = 10  # 模拟10秒
    recorder._save_final_data()
    
    # 统计
    print()
    print("="*80)
    print("测试完成！统计信息:")
    print("="*80)
    stats = recorder.get_stats()
    print(f"总消息数: {stats['total_messages']}")
    print(f"聊天消息: {stats['chat_messages']}")
    print(f"礼物事件: {stats['gift_events']}")
    print(f"升级事件: {stats['upgrade_events']}")
    print()
    print(f"输出目录: {recorder.output_dir}")
    print(f"弹幕文件: {os.path.basename(recorder.danmaku_file)}")
    print(f"事件文件: {os.path.basename(recorder.events_file)}")
    print(f"统计文件: {os.path.basename(recorder.stats_file)}")
    print(f"时间线文件: {os.path.basename(recorder.timeline_file)}")
    print()
    
    # 显示生成的文件内容
    print("="*80)
    print("生成的文件内容预览:")
    print("="*80)
    
    # 1. 事件文件
    if os.path.exists(recorder.events_file):
        print(f"\n📄 {os.path.basename(recorder.events_file)}:")
        print("-"*80)
        with open(recorder.events_file, 'r', encoding='utf-8') as f:
            events = json.load(f)
            for event in events:
                print(f"• [{event['event_type']}] {event['description']}")
    
    # 2. 时间线文件
    if os.path.exists(recorder.timeline_file):
        print(f"\n📄 {os.path.basename(recorder.timeline_file)}:")
        print("-"*80)
        with open(recorder.timeline_file, 'r', encoding='utf-8') as f:
            print(f.read())
    
    print()
    print("✅ 测试完成！")
    print()


def test_with_real_connection():
    """使用真实连接测试"""
    print("="*80)
    print("测试弹幕录制系统 - 真实连接模式")
    print("="*80)
    print()
    
    # 检查是否安装了DouyinBarrageGrab
    try:
        sys.path.insert(0, '/home/liu/app_github/DouyinBarrageGrab')
        import douyin_barrage
        has_barrage = True
    except ImportError:
        has_barrage = False
    
    if not has_barrage:
        print("❌ DouyinBarrageGrab未安装")
        print()
        print("安装步骤:")
        print("  1. cd /home/liu/app_github/")
        print("  2. git clone https://github.com/ape-byte/DouyinBarrageGrab.git")
        print("  3. cd DouyinBarrageGrab")
        print("  4. pip install -r requirements.txt")
        print()
        return
    
    # 获取房间URL
    room_url = input("请输入直播间URL (如: https://live.douyin.com/123456): ").strip()
    if not room_url:
        print("❌ 未输入房间URL")
        return
    
    # 创建录制器
    recorder = DouyinDanmakuRecorder(
        room_url=room_url,
        output_dir="./test_output/danmaku_real",
        anchor_name="真实测试"
    )
    
    # 设置回调
    def on_upgrade(event):
        print(f"\n🎉 {event['description']}")
    
    def on_gift(event):
        print(f"\n🎁 {event['user']} 送出 {event['gift_name']} x{event['gift_count']}")
    
    recorder.set_callback('on_upgrade', on_upgrade)
    recorder.set_callback('on_gift', on_gift)
    
    # 启动录制
    print(f"\n开始录制弹幕: {room_url}")
    print("按 Ctrl+C 停止录制")
    print("-"*80)
    
    recorder.start_recording(mode='websocket')
    
    try:
        # 等待用户中断
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n停止录制...")
        recorder.stop_recording()
        print("\n✅ 录制完成！")


def main():
    """主函数"""
    print()
    print("="*80)
    print("弹幕录制系统测试")
    print("="*80)
    print()
    print("请选择测试模式:")
    print("  1. 模拟数据测试（推荐，快速验证功能）")
    print("  2. 真实连接测试（需要DouyinBarrageGrab）")
    print("  3. 退出")
    print()
    
    choice = input("请选择 [1-3]: ").strip()
    
    if choice == '1':
        test_with_mock_data()
    elif choice == '2':
        test_with_real_connection()
    elif choice == '3':
        print("再见！")
    else:
        print("❌ 无效选择")


if __name__ == "__main__":
    main()



