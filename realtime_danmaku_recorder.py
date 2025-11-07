#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实可用的抖音弹幕录制器
基于TikTokLive库实现

使用方法:
    python3 realtime_danmaku_recorder.py

输出:
    ~/videos/shanshan/抖音直播/观山/观山_{date}_danmaku.jsonl
"""

import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

# ✅ 临时清除代理环境变量（TikTokLive使用httpx，不支持socks://协议）
# 抖音直播通常不需要代理（国内可直连）
for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 
                  'http_proxy', 'https_proxy', 'all_proxy']:
    if proxy_var in os.environ:
        del os.environ[proxy_var]

try:
    from TikTokLive import TikTokLiveClient
    from TikTokLive.events import (
        ConnectEvent,
        DisconnectEvent,
        CommentEvent,
        GiftEvent,
        FollowEvent,
        ShareEvent,
        LikeEvent,
        JoinEvent
    )
except ImportError as e:
    print(f"❌ TikTokLive库未安装或版本不兼容: {e}")
    print("   请运行: pip install TikTokLive")
    sys.exit(1)


class RealtimeDanmakuRecorder:
    """真实可用的抖音弹幕录制器"""
    
    def __init__(self, room_id: str, output_file: str):
        """
        初始化
        
        Args:
            room_id: 直播间ID（纯数字）
            output_file: 输出文件路径
        """
        self.room_id = room_id
        self.output_file = output_file
        self.client = TikTokLiveClient(unique_id=f"@{room_id}")
        
        # 统计
        self.stats = {
            'comments': 0,
            'gifts': 0,
            'likes': 0,
            'joins': 0,
            'follows': 0,
            'shares': 0,
            'total': 0
        }
        
        # 打开输出文件
        self.file_handle = open(output_file, 'a', encoding='utf-8')
        
        # 注册事件处理
        self._register_handlers()
    
    def _register_handlers(self):
        """注册事件处理器"""
        
        @self.client.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            print(f"✅ 已连接到直播间: {self.room_id}")
            print(f"📝 弹幕保存到: {self.output_file}")
            print()
            self._write_event('system', {'type': 'connect', 'room_id': self.room_id})
        
        @self.client.on(DisconnectEvent)
        async def on_disconnect(event: DisconnectEvent):
            print(f"\n⏹️  已断开连接")
            self._write_event('system', {'type': 'disconnect'})
        
        @self.client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            self.stats['comments'] += 1
            self.stats['total'] += 1
            
            data = {
                'user': event.user.nickname,
                'user_id': event.user.user_id,
                'comment': event.comment
            }
            self._write_event('comment', data)
            
            if self.stats['comments'] % 10 == 0:
                self._print_stats()
        
        @self.client.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            # 只记录completed gift（完整礼物，非连击中）
            if event.gift.streakable and not event.gift.streaking:
                self.stats['gifts'] += 1
                self.stats['total'] += 1
                
                data = {
                    'user': event.user.nickname,
                    'user_id': event.user.user_id,
                    'gift_name': event.gift.name,
                    'gift_id': event.gift.id,
                    'diamond_count': event.gift.diamond_count,
                    'repeat_count': event.gift.repeat_count,
                    'repeat_end': event.gift.repeat_end
                }
                self._write_event('gift', data)
                self._print_stats()
        
        @self.client.on(LikeEvent)
        async def on_like(event: LikeEvent):
            self.stats['likes'] += 1
            self.stats['total'] += 1
            
            data = {
                'user': event.user.nickname if event.user else '匿名',
                'count': event.count
            }
            self._write_event('like', data)
        
        @self.client.on(JoinEvent)
        async def on_join(event: JoinEvent):
            self.stats['joins'] += 1
            self.stats['total'] += 1
            
            data = {
                'user': event.user.nickname,
                'user_id': event.user.user_id
            }
            self._write_event('join', data)
        
        @self.client.on(FollowEvent)
        async def on_follow(event: FollowEvent):
            self.stats['follows'] += 1
            self.stats['total'] += 1
            
            data = {
                'user': event.user.nickname,
                'user_id': event.user.user_id
            }
            self._write_event('follow', data)
            self._print_stats()
        
        @self.client.on(ShareEvent)
        async def on_share(event: ShareEvent):
            self.stats['shares'] += 1
            self.stats['total'] += 1
            
            data = {
                'user': event.user.nickname,
                'user_id': event.user.user_id
            }
            self._write_event('share', data)
    
    def _write_event(self, event_type: str, data: dict):
        """写入事件到文件"""
        record = {
            'timestamp': time.time(),
            'time': datetime.now().isoformat(),
            'type': event_type,
            'data': data
        }
        self.file_handle.write(json.dumps(record, ensure_ascii=False) + '\n')
        self.file_handle.flush()
    
    def _print_stats(self):
        """打印统计信息"""
        print(f"💬 评论: {self.stats['comments']:>4} | "
              f"🎁 礼物: {self.stats['gifts']:>3} | "
              f"👍 点赞: {self.stats['likes']:>5} | "
              f"👥 加入: {self.stats['joins']:>3} | "
              f"📊 总计: {self.stats['total']:>5}",
              end='\r')
    
    def start(self):
        """启动录制"""
        try:
            print("=" * 70)
            print("🎬 抖音弹幕实时录制器（TikTokLive）")
            print("=" * 70)
            print(f"📺 直播间ID: {self.room_id}")
            print(f"📝 输出文件: {self.output_file}")
            print()
            print("🚀 正在连接...")
            print("   按 Ctrl+C 停止录制")
            print("=" * 70)
            print()
            
            # 启动客户端（阻塞）
            self.client.run()
            
        except KeyboardInterrupt:
            print("\n\n⏹️  用户中断...")
            self.stop()
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            self.stop()
    
    def stop(self):
        """停止录制"""
        print()
        print("=" * 70)
        print("✅ 录制完成")
        print("=" * 70)
        print("📊 统计信息:")
        print(f"   💬 评论: {self.stats['comments']} 条")
        print(f"   🎁 礼物: {self.stats['gifts']} 个")
        print(f"   👍 点赞: {self.stats['likes']} 次")
        print(f"   👥 加入: {self.stats['joins']} 人")
        print(f"   ➕ 关注: {self.stats['follows']} 人")
        print(f"   📤 分享: {self.stats['shares']} 次")
        print(f"   📊 总计: {self.stats['total']} 条")
        
        if self.file_handle:
            self.file_handle.close()
            file_size = os.path.getsize(self.output_file) / 1024 / 1024
            print(f"   📝 输出文件: {self.output_file}")
            print(f"   💾 文件大小: {file_size:.2f} MB")
        print()


def main():
    # 配置
    room_id = "83970695603"  # 直播间ID
    anchor_name = "观山"
    output_dir = os.path.expanduser("~/videos/shanshan/抖音直播/观山")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成输出文件名
    date_str = datetime.now().strftime('%Y-%m-%d')
    output_file = os.path.join(output_dir, f"{anchor_name}_{date_str}_danmaku.jsonl")
    
    # 创建录制器并启动
    recorder = RealtimeDanmakuRecorder(room_id=room_id, output_file=output_file)
    recorder.start()


if __name__ == "__main__":
    main()

