#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音弹幕录制器 - 真实实现

基于抖音直播API的弹幕录制
支持WebSocket和HTTP两种方式
"""

import asyncio
import json
import os
import time
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlencode
import threading

logger = logging.getLogger(__name__)

# 尝试导入依赖
try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    logger.warning("websockets库未安装，WebSocket功能不可用")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    logger.warning("requests库未安装，HTTP功能不可用")


class DouyinDanmakuRecorder:
    """
    抖音弹幕录制器 - 真实实现
    
    支持两种模式：
    1. WebSocket实时录制（推荐）
    2. HTTP轮询录制（后备）
    """
    
    def __init__(self, room_url: str, output_dir: str, anchor_name: str = ""):
        """
        初始化
        
        Args:
            room_url: 直播间URL（如：https://live.douyin.com/123456）
            output_dir: 输出目录
            anchor_name: 主播名称
        """
        self.room_url = room_url
        self.room_id = self._extract_room_id(room_url)
        self.output_dir = output_dir
        self.anchor_name = anchor_name or self.room_id
        self.session_id = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # 弹幕缓冲
        self.danmaku_buffer = []
        self.events_buffer = []
        
        # 统计
        self.stats = {
            'total_messages': 0,
            'chat_messages': 0,
            'gift_events': 0,
            'upgrade_events': 0,
            'member_join': 0,
            'like_count': 0,
            'start_time': None,
            'end_time': None,
            'recording_duration': 0
        }
        
        # 运行控制
        self.is_recording = False
        self.record_thread = None
        self.loop = None
        
        # 回调
        self.callbacks = {
            'on_upgrade': None,
            'on_gift': None,
            'on_chat': None
        }
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 输出文件
        date_str = datetime.now().strftime('%Y-%m-%d')
        self.output_base = os.path.join(
            output_dir,
            f"{self.anchor_name}_{date_str}"
        )
        
        self.danmaku_file = f"{self.output_base}_danmaku.jsonl"
        self.events_file = f"{self.output_base}_events.json"
        self.stats_file = f"{self.output_base}_danmaku_stats.json"
        self.timeline_file = f"{self.output_base}_timeline.txt"
    
    def _extract_room_id(self, url: str) -> str:
        """从URL提取房间ID"""
        # https://live.douyin.com/123456
        match = re.search(r'douyin\.com/(\d+)', url)
        if match:
            return match.group(1)
        return url
    
    def start_recording(self, mode: str = 'auto'):
        """
        启动录制
        
        Args:
            mode: 录制模式
                - 'websocket': WebSocket模式
                - 'http': HTTP轮询模式
                - 'auto': 自动选择（默认）
        """
        if self.is_recording:
            logger.warning("弹幕录制已在运行")
            return
        
        self.is_recording = True
        self.stats['start_time'] = time.time()
        
        # 选择录制模式
        if mode == 'auto':
            mode = 'websocket' if HAS_WEBSOCKETS else 'http'
        
        logger.info(f"✅ 启动弹幕录制: {self.anchor_name} (房间ID: {self.room_id})")
        logger.info(f"   录制模式: {mode}")
        logger.info(f"   输出目录: {self.output_dir}")
        
        # 启动录制线程
        if mode == 'websocket':
            self.record_thread = threading.Thread(
                target=self._websocket_record_loop,
                daemon=True
            )
        else:
            self.record_thread = threading.Thread(
                target=self._http_record_loop,
                daemon=True
            )
        
        self.record_thread.start()
    
    def stop_recording(self):
        """停止录制"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        self.stats['end_time'] = time.time()
        self.stats['recording_duration'] = self.stats['end_time'] - self.stats['start_time']
        
        # 保存数据
        self._flush_buffers()
        self._save_final_data()
        
        logger.info(f"✅ 弹幕录制已停止")
        logger.info(f"   录制时长: {self.stats['recording_duration']/60:.1f} 分钟")
        logger.info(f"   总消息数: {self.stats['total_messages']}")
        logger.info(f"   升级事件: {self.stats['upgrade_events']}")
        logger.info(f"   礼物事件: {self.stats['gift_events']}")
    
    def _websocket_record_loop(self):
        """WebSocket录制循环"""
        try:
            logger.info("使用WebSocket模式录制弹幕")
            logger.info("⚠️  注意：需要实现真实的WebSocket连接逻辑")
            logger.info("   建议集成DouyinBarrageGrab项目")
            
            # TODO: 实现真实的WebSocket连接
            # 1. 获取WebSocket URL
            # 2. 建立连接
            # 3. 接收和解析消息
            # 4. 调用相应的处理函数
            
            # 这里是占位代码
            while self.is_recording:
                time.sleep(1)
                
                # 定期刷新缓冲
                if len(self.danmaku_buffer) >= 50:
                    self._flush_buffers()
            
        except Exception as e:
            logger.error(f"WebSocket录制出错: {e}")
        finally:
            self.is_recording = False
    
    def _http_record_loop(self):
        """HTTP轮询录制循环"""
        try:
            logger.info("使用HTTP轮询模式录制弹幕")
            logger.info("⚠️  轮询模式可能丢失部分弹幕")
            
            while self.is_recording:
                try:
                    # TODO: 实现HTTP API轮询
                    # 1. 调用抖音API获取弹幕
                    # 2. 解析返回数据
                    # 3. 处理新消息
                    
                    # 定期刷新缓冲
                    if len(self.danmaku_buffer) >= 50:
                        self._flush_buffers()
                    
                    # 轮询间隔
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"HTTP轮询出错: {e}")
                    time.sleep(5)
            
        except Exception as e:
            logger.error(f"HTTP录制出错: {e}")
        finally:
            self.is_recording = False
    
    def process_message(self, raw_data: Dict):
        """
        处理接收到的消息
        
        这是一个通用的消息处理接口，无论是WebSocket还是HTTP获取的消息
        都应该调用这个方法
        
        Args:
            raw_data: 原始消息数据
        """
        try:
            msg_type = raw_data.get('method', raw_data.get('type', 'unknown'))
            
            # 根据消息类型处理
            if msg_type in ['WebcastChatMessage', 'chat']:
                self._process_chat_message(raw_data)
            elif msg_type in ['WebcastGiftMessage', 'gift']:
                self._process_gift_message(raw_data)
            elif msg_type in ['WebcastMemberMessage', 'member', 'join']:
                self._process_member_message(raw_data)
            elif msg_type in ['WebcastLikeMessage', 'like']:
                self._process_like_message(raw_data)
            elif msg_type in ['WebcastSocialMessage', 'social']:
                self._process_social_message(raw_data)
            else:
                self._process_other_message(raw_data)
            
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
    
    def _process_chat_message(self, data: Dict):
        """处理聊天消息"""
        timestamp = time.time()
        
        # 提取用户信息
        user_info = data.get('user', {})
        nickname = user_info.get('nickname', user_info.get('nickName', 'Unknown'))
        user_id = user_info.get('id', user_info.get('userId', ''))
        
        # 提取消息内容
        content = data.get('content', data.get('Content', ''))
        
        message = {
            'type': 'chat',
            'timestamp': timestamp,
            'time': datetime.fromtimestamp(timestamp).isoformat(),
            'user': nickname,
            'user_id': str(user_id),
            'content': content
        }
        
        self.danmaku_buffer.append(message)
        self.stats['total_messages'] += 1
        self.stats['chat_messages'] += 1
        
        # 检测特殊事件
        self._detect_upgrade_from_chat(message)
        self._detect_gift_from_chat(message)
        
        # 回调
        if self.callbacks['on_chat']:
            self.callbacks['on_chat'](message)
    
    def _process_gift_message(self, data: Dict):
        """处理礼物消息"""
        timestamp = time.time()
        
        user_info = data.get('user', {})
        gift_info = data.get('gift', {})
        
        gift_event = {
            'type': 'gift',
            'timestamp': timestamp,
            'time': datetime.fromtimestamp(timestamp).isoformat(),
            'user': user_info.get('nickname', 'Unknown'),
            'user_id': str(user_info.get('id', '')),
            'gift_name': gift_info.get('name', ''),
            'gift_id': gift_info.get('id', ''),
            'gift_count': data.get('repeatCount', data.get('count', 1)),
            'gift_value': gift_info.get('diamondCount', 0),
            'total_value': 0
        }
        
        gift_event['total_value'] = gift_event['gift_value'] * gift_event['gift_count']
        
        self.danmaku_buffer.append(gift_event)
        self.stats['total_messages'] += 1
        self.stats['gift_events'] += 1
        
        # 记录为事件
        self.events_buffer.append({
            'event_type': 'gift',
            'timestamp': timestamp,
            'time': gift_event['time'],
            'description': f"{gift_event['user']} 送出 {gift_event['gift_name']} x{gift_event['gift_count']}",
            'value': gift_event['total_value'],
            'user': gift_event['user'],
            'gift_name': gift_event['gift_name'],
            'gift_count': gift_event['gift_count']
        })
        
        # 回调
        if self.callbacks['on_gift']:
            self.callbacks['on_gift'](gift_event)
    
    def _process_member_message(self, data: Dict):
        """处理成员消息"""
        timestamp = time.time()
        
        user_info = data.get('user', {})
        action = data.get('action', data.get('actionType', 'join'))
        
        member_event = {
            'type': 'member',
            'timestamp': timestamp,
            'time': datetime.fromtimestamp(timestamp).isoformat(),
            'user': user_info.get('nickname', 'Unknown'),
            'user_id': str(user_info.get('id', '')),
            'action': action
        }
        
        self.danmaku_buffer.append(member_event)
        self.stats['total_messages'] += 1
        self.stats['member_join'] += 1
    
    def _process_like_message(self, data: Dict):
        """处理点赞消息"""
        count = data.get('count', 1)
        self.stats['like_count'] += count
    
    def _process_social_message(self, data: Dict):
        """处理社交消息（关注、分享等）"""
        timestamp = time.time()
        
        user_info = data.get('user', {})
        action = data.get('action', 'unknown')
        
        social_event = {
            'type': 'social',
            'timestamp': timestamp,
            'time': datetime.fromtimestamp(timestamp).isoformat(),
            'user': user_info.get('nickname', 'Unknown'),
            'user_id': str(user_info.get('id', '')),
            'action': action
        }
        
        self.danmaku_buffer.append(social_event)
        self.stats['total_messages'] += 1
    
    def _process_other_message(self, data: Dict):
        """处理其他消息"""
        timestamp = time.time()
        
        message = {
            'type': data.get('method', data.get('type', 'unknown')),
            'timestamp': timestamp,
            'time': datetime.fromtimestamp(timestamp).isoformat(),
            'raw': data
        }
        
        self.danmaku_buffer.append(message)
        self.stats['total_messages'] += 1
    
    def _detect_upgrade_from_chat(self, message: Dict):
        """从聊天消息中检测升级事件"""
        content = message['content'].lower()
        
        # 升级关键词
        upgrade_patterns = [
            (r'升到\s*(\d+)\s*级', '升级'),
            (r'达到\s*(\d+)\s*级', '达到'),
            (r'lv\s*(\d+)', 'LV'),
            (r'(\d+)\s*级.*粉丝', '粉丝等级')
        ]
        
        for pattern, desc in upgrade_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                level = int(match.group(1))
                
                # 只记录16级及以上的升级
                if level >= 16:
                    upgrade_event = {
                        'event_type': 'upgrade',
                        'timestamp': message['timestamp'],
                        'time': message['time'],
                        'user': message['user'],
                        'level': level,
                        'description': f"{message['user']} 升到 {level} 级",
                        'source': 'chat',
                        'original_message': message['content']
                    }
                    
                    self.events_buffer.append(upgrade_event)
                    self.stats['upgrade_events'] += 1
                    
                    logger.info(f"🎉 检测到升级事件: {upgrade_event['description']}")
                    
                    # 回调
                    if self.callbacks['on_upgrade']:
                        self.callbacks['on_upgrade'](upgrade_event)
                    
                    break
    
    def _detect_gift_from_chat(self, message: Dict):
        """从聊天消息中检测礼物事件（辅助）"""
        # 这是一个辅助方法，主要礼物检测应该来自gift消息
        pass
    
    def _flush_buffers(self):
        """刷新缓冲区"""
        if self.danmaku_buffer:
            self._save_danmaku_batch()
        
        if self.events_buffer:
            self._save_events_batch()
    
    def _save_danmaku_batch(self):
        """保存弹幕批次"""
        try:
            with open(self.danmaku_file, 'a', encoding='utf-8') as f:
                for msg in self.danmaku_buffer:
                    f.write(json.dumps(msg, ensure_ascii=False) + '\n')
            
            logger.debug(f"保存弹幕: {len(self.danmaku_buffer)} 条")
            self.danmaku_buffer.clear()
            
        except Exception as e:
            logger.error(f"保存弹幕失败: {e}")
    
    def _save_events_batch(self):
        """保存事件批次"""
        try:
            # 读取现有事件
            existing_events = []
            if os.path.exists(self.events_file):
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    existing_events = json.load(f)
            
            # 合并新事件
            existing_events.extend(self.events_buffer)
            
            # 保存
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(existing_events, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"保存事件: {len(self.events_buffer)} 条")
            self.events_buffer.clear()
            
        except Exception as e:
            logger.error(f"保存事件失败: {e}")
    
    def _save_final_data(self):
        """保存最终数据"""
        # 保存统计信息
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 统计信息已保存: {self.stats_file}")
        except Exception as e:
            logger.error(f"保存统计信息失败: {e}")
        
        # 生成时间线
        self._generate_timeline()
    
    def _generate_timeline(self):
        """生成时间线"""
        try:
            if not os.path.exists(self.events_file):
                return
            
            with open(self.events_file, 'r', encoding='utf-8') as f:
                events = json.load(f)
            
            with open(self.timeline_file, 'w', encoding='utf-8') as f:
                f.write(f"# 弹幕事件时间线 - {self.anchor_name}\n")
                f.write(f"# 录制时间: {datetime.fromtimestamp(self.stats['start_time']).strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 总事件数: {len(events)}\n")
                f.write("\n")
                
                for i, event in enumerate(events, 1):
                    time_str = datetime.fromtimestamp(event['timestamp']).strftime('%H:%M:%S')
                    desc = event['description']
                    
                    if event['event_type'] == 'upgrade':
                        icon = "🎉"
                    elif event['event_type'] == 'gift':
                        icon = "🎁"
                    else:
                        icon = "•"
                    
                    f.write(f"{i:3d}. [{time_str}] {icon} {desc}\n")
            
            logger.info(f"✅ 时间线已生成: {self.timeline_file}")
            
        except Exception as e:
            logger.error(f"生成时间线失败: {e}")
    
    def set_callback(self, event_type: str, callback):
        """设置回调函数"""
        if event_type in self.callbacks:
            self.callbacks[event_type] = callback


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 示例用法
    recorder = DouyinDanmakuRecorder(
        room_url="https://live.douyin.com/123456",
        output_dir="./test_danmaku",
        anchor_name="观山"
    )
    
    def on_upgrade(event):
        print(f"🎉 {event['description']}")
    
    def on_gift(event):
        print(f"🎁 {event['user']} 送出 {event['gift_name']} x{event['gift_count']}")
    
    recorder.set_callback('on_upgrade', on_upgrade)
    recorder.set_callback('on_gift', on_gift)
    
    print("\n=== 抖音弹幕录制器 ===")
    print("注意：这是框架代码，需要集成真实的WebSocket/HTTP连接")
    print("建议方案：集成DouyinBarrageGrab项目")
    print()



