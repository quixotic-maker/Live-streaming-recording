#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音弹幕录制器

功能：
- 实时录制弹幕
- 检测升级事件
- 检测礼物事件
- 保存弹幕数据
- 生成事件时间线
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pathlib import Path
import threading
import websocket
import logging

logger = logging.getLogger(__name__)


class DanmakuRecorder:
    """抖音弹幕录制器"""
    
    def __init__(self, room_id: str, output_dir: str, anchor_name: str = ""):
        """
        初始化弹幕录制器
        
        Args:
            room_id: 直播间ID
            output_dir: 输出目录
            anchor_name: 主播名称
        """
        self.room_id = room_id
        self.output_dir = output_dir
        self.anchor_name = anchor_name or room_id
        self.session_id = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # 弹幕缓冲区
        self.danmaku_buffer = []
        self.events_buffer = []
        
        # 统计信息
        self.stats = {
            'total_messages': 0,
            'chat_messages': 0,
            'gift_events': 0,
            'upgrade_events': 0,
            'like_count': 0,
            'start_time': None,
            'end_time': None
        }
        
        # 升级关键词
        self.upgrade_keywords = [
            '升级', '升到', '等级', 'level', 'lv', '级',
            '恭喜', '成为', '粉丝团'
        ]
        
        # 礼物关键词
        self.gift_keywords = [
            '送出', '礼物', '火箭', '跑车', '嘉年华',
            'gift', '打赏', '支持'
        ]
        
        # 运行标志
        self.is_recording = False
        self.ws = None
        self.record_thread = None
        
        # 回调函数
        self.on_upgrade_callback: Optional[Callable] = None
        self.on_gift_callback: Optional[Callable] = None
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 输出文件路径
        self.danmaku_file = os.path.join(
            output_dir, 
            f"{self.anchor_name}_{self.session_id}_danmaku.json"
        )
        self.events_file = os.path.join(
            output_dir,
            f"{self.anchor_name}_{self.session_id}_events.json"
        )
        self.stats_file = os.path.join(
            output_dir,
            f"{self.anchor_name}_{self.session_id}_stats.json"
        )
    
    def start_recording(self):
        """启动弹幕录制（非阻塞）"""
        if self.is_recording:
            logger.warning("弹幕录制已在运行")
            return
        
        self.is_recording = True
        self.stats['start_time'] = datetime.now().isoformat()
        
        # 在新线程中启动录制
        self.record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.record_thread.start()
        
        logger.info(f"✅ 弹幕录制已启动: {self.room_id}")
        logger.info(f"   输出目录: {self.output_dir}")
    
    def stop_recording(self):
        """停止弹幕录制"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        self.stats['end_time'] = datetime.now().isoformat()
        
        # 关闭WebSocket连接
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
        
        # 保存最终数据
        self._save_all_data()
        
        logger.info(f"✅ 弹幕录制已停止: {self.room_id}")
        logger.info(f"   总消息数: {self.stats['total_messages']}")
        logger.info(f"   升级事件: {self.stats['upgrade_events']}")
        logger.info(f"   礼物事件: {self.stats['gift_events']}")
    
    def _record_loop(self):
        """录制循环（在单独线程中运行）"""
        try:
            # 注意：这里使用简化的WebSocket连接
            # 实际应用中需要获取真实的WebSocket URL和签名
            ws_url = self._get_websocket_url()
            
            if not ws_url:
                logger.error("❌ 无法获取弹幕WebSocket URL")
                return
            
            # 创建WebSocket连接
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # 运行WebSocket（阻塞）
            self.ws.run_forever()
            
        except Exception as e:
            logger.error(f"❌ 弹幕录制出错: {e}")
        finally:
            self.is_recording = False
    
    def _get_websocket_url(self) -> Optional[str]:
        """
        获取WebSocket URL
        
        注意：实际实现需要：
        1. 获取直播间信息
        2. 获取WebSocket服务器地址
        3. 生成签名和参数
        
        这里返回一个占位URL，实际使用时需要替换
        """
        # TODO: 集成DouyinBarrageGrab的URL获取逻辑
        # 或者使用抖音直播API获取真实的WebSocket URL
        
        # 占位实现
        logger.warning("⚠️  使用占位WebSocket URL，需要集成真实的弹幕服务")
        return None
    
    def _on_open(self, ws):
        """WebSocket连接打开"""
        logger.info("✅ WebSocket连接已建立")
    
    def _on_message(self, ws, message):
        """接收到弹幕消息"""
        try:
            # 解析消息
            data = json.loads(message) if isinstance(message, str) else message
            
            # 处理不同类型的消息
            msg_type = data.get('type', 'unknown')
            
            if msg_type == 'chat':
                self._handle_chat_message(data)
            elif msg_type == 'gift':
                self._handle_gift_message(data)
            elif msg_type == 'like':
                self._handle_like_message(data)
            elif msg_type == 'member':
                self._handle_member_message(data)
            else:
                self._handle_other_message(data)
            
            # 定期保存数据
            if len(self.danmaku_buffer) >= 100:
                self._save_danmaku_batch()
            
            if len(self.events_buffer) >= 10:
                self._save_events_batch()
            
        except Exception as e:
            logger.error(f"处理弹幕消息失败: {e}")
    
    def _on_error(self, ws, error):
        """WebSocket错误"""
        logger.error(f"WebSocket错误: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket关闭"""
        logger.info(f"WebSocket连接关闭: {close_status_code} - {close_msg}")
    
    def _handle_chat_message(self, data: Dict):
        """处理聊天消息"""
        timestamp = time.time()
        
        message = {
            'type': 'chat',
            'timestamp': timestamp,
            'time': datetime.fromtimestamp(timestamp).isoformat(),
            'user': data.get('user', {}).get('nickname', 'Unknown'),
            'user_id': data.get('user', {}).get('id', ''),
            'content': data.get('content', ''),
            'raw': data
        }
        
        self.danmaku_buffer.append(message)
        self.stats['total_messages'] += 1
        self.stats['chat_messages'] += 1
        
        # 检测升级事件
        if self._is_upgrade_message(message['content']):
            self._handle_upgrade_event(message)
        
        # 检测礼物事件（从聊天消息中）
        if self._is_gift_message(message['content']):
            self._handle_gift_event_from_chat(message)
    
    def _handle_gift_message(self, data: Dict):
        """处理礼物消息"""
        timestamp = time.time()
        
        gift_event = {
            'type': 'gift',
            'timestamp': timestamp,
            'time': datetime.fromtimestamp(timestamp).isoformat(),
            'user': data.get('user', {}).get('nickname', 'Unknown'),
            'user_id': data.get('user', {}).get('id', ''),
            'gift_name': data.get('gift', {}).get('name', ''),
            'gift_count': data.get('count', 1),
            'gift_value': data.get('gift', {}).get('coin_price', 0),
            'total_value': data.get('gift', {}).get('coin_price', 0) * data.get('count', 1),
            'raw': data
        }
        
        self.danmaku_buffer.append(gift_event)
        self.events_buffer.append({
            'event_type': 'gift',
            'timestamp': timestamp,
            'time': gift_event['time'],
            'description': f"{gift_event['user']} 送出 {gift_event['gift_name']} x{gift_event['gift_count']}",
            'value': gift_event['total_value'],
            'data': gift_event
        })
        
        self.stats['total_messages'] += 1
        self.stats['gift_events'] += 1
        
        # 触发回调
        if self.on_gift_callback:
            try:
                self.on_gift_callback(gift_event)
            except Exception as e:
                logger.error(f"礼物回调执行失败: {e}")
    
    def _handle_like_message(self, data: Dict):
        """处理点赞消息"""
        self.stats['like_count'] += data.get('count', 1)
    
    def _handle_member_message(self, data: Dict):
        """处理成员消息（升级、进入等）"""
        timestamp = time.time()
        
        member_event = {
            'type': 'member',
            'timestamp': timestamp,
            'time': datetime.fromtimestamp(timestamp).isoformat(),
            'user': data.get('user', {}).get('nickname', 'Unknown'),
            'user_id': data.get('user', {}).get('id', ''),
            'action': data.get('action', ''),
            'level': data.get('level', 0),
            'raw': data
        }
        
        self.danmaku_buffer.append(member_event)
        self.stats['total_messages'] += 1
        
        # 检测升级事件
        if member_event['action'] in ['upgrade', 'level_up']:
            self._handle_upgrade_event(member_event)
    
    def _handle_other_message(self, data: Dict):
        """处理其他类型消息"""
        timestamp = time.time()
        
        message = {
            'type': data.get('type', 'unknown'),
            'timestamp': timestamp,
            'time': datetime.fromtimestamp(timestamp).isoformat(),
            'raw': data
        }
        
        self.danmaku_buffer.append(message)
        self.stats['total_messages'] += 1
    
    def _is_upgrade_message(self, content: str) -> bool:
        """判断是否是升级消息"""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.upgrade_keywords)
    
    def _is_gift_message(self, content: str) -> bool:
        """判断是否是礼物消息"""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.gift_keywords)
    
    def _handle_upgrade_event(self, message: Dict):
        """处理升级事件"""
        # 提取升级信息
        user = message.get('user', 'Unknown')
        content = message.get('content', '')
        level = self._extract_level(content)
        
        upgrade_event = {
            'event_type': 'upgrade',
            'timestamp': message['timestamp'],
            'time': message['time'],
            'user': user,
            'level': level,
            'description': f"{user} 升到 {level} 级",
            'source_message': message
        }
        
        self.events_buffer.append(upgrade_event)
        self.stats['upgrade_events'] += 1
        
        logger.info(f"🎉 检测到升级事件: {upgrade_event['description']}")
        
        # 触发回调
        if self.on_upgrade_callback:
            try:
                self.on_upgrade_callback(upgrade_event)
            except Exception as e:
                logger.error(f"升级回调执行失败: {e}")
    
    def _handle_gift_event_from_chat(self, message: Dict):
        """从聊天消息中提取礼物事件"""
        # 这是一个后备方法，如果没有收到gift类型消息
        # 可以从聊天消息中尝试提取礼物信息
        pass
    
    def _extract_level(self, text: str) -> int:
        """从文本中提取等级"""
        import re
        
        # 匹配各种等级格式
        patterns = [
            r'(\d+)\s*级',
            r'lv\s*(\d+)',
            r'level\s*(\d+)',
            r'升到\s*(\d+)',
            r'达到\s*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 0
    
    def _save_danmaku_batch(self):
        """保存弹幕批次"""
        if not self.danmaku_buffer:
            return
        
        try:
            # 追加模式保存
            mode = 'a' if os.path.exists(self.danmaku_file) else 'w'
            
            with open(self.danmaku_file, mode, encoding='utf-8') as f:
                for msg in self.danmaku_buffer:
                    f.write(json.dumps(msg, ensure_ascii=False) + '\n')
            
            logger.debug(f"保存弹幕批次: {len(self.danmaku_buffer)} 条")
            self.danmaku_buffer.clear()
            
        except Exception as e:
            logger.error(f"保存弹幕批次失败: {e}")
    
    def _save_events_batch(self):
        """保存事件批次"""
        if not self.events_buffer:
            return
        
        try:
            # 追加模式保存
            mode = 'a' if os.path.exists(self.events_file) else 'w'
            
            with open(self.events_file, mode, encoding='utf-8') as f:
                for event in self.events_buffer:
                    f.write(json.dumps(event, ensure_ascii=False) + '\n')
            
            logger.debug(f"保存事件批次: {len(self.events_buffer)} 条")
            self.events_buffer.clear()
            
        except Exception as e:
            logger.error(f"保存事件批次失败: {e}")
    
    def _save_all_data(self):
        """保存所有数据"""
        # 保存剩余的弹幕和事件
        if self.danmaku_buffer:
            self._save_danmaku_batch()
        
        if self.events_buffer:
            self._save_events_batch()
        
        # 保存统计信息
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 统计信息已保存: {self.stats_file}")
        except Exception as e:
            logger.error(f"保存统计信息失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def set_upgrade_callback(self, callback: Callable):
        """设置升级事件回调"""
        self.on_upgrade_callback = callback
    
    def set_gift_callback(self, callback: Callable):
        """设置礼物事件回调"""
        self.on_gift_callback = callback


class SimpleDanmakuRecorder:
    """
    简化的弹幕录制器
    
    适用于：
    1. 没有WebSocket连接时的模拟录制
    2. 基于HTTP API的弹幕获取
    3. 文件导入弹幕数据
    """
    
    def __init__(self, output_dir: str, anchor_name: str = ""):
        self.output_dir = output_dir
        self.anchor_name = anchor_name
        self.session_id = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        os.makedirs(output_dir, exist_ok=True)
        
        self.danmaku_file = os.path.join(
            output_dir,
            f"{anchor_name}_{self.session_id}_danmaku_simple.json"
        )
    
    def save_message(self, message: Dict):
        """保存单条消息"""
        try:
            with open(self.danmaku_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(message, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"保存消息失败: {e}")
    
    def import_from_file(self, file_path: str):
        """从文件导入弹幕数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        message = json.loads(line)
                        self.save_message(message)
            
            logger.info(f"✅ 弹幕数据导入完成: {file_path}")
        except Exception as e:
            logger.error(f"导入弹幕数据失败: {e}")


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 创建录制器
    recorder = DanmakuRecorder(
        room_id="test_room",
        output_dir="./test_danmaku",
        anchor_name="观山"
    )
    
    # 设置回调
    def on_upgrade(event):
        print(f"🎉 升级事件: {event['description']}")
    
    def on_gift(event):
        print(f"🎁 礼物事件: {event['user']} 送出 {event['gift_name']}")
    
    recorder.set_upgrade_callback(on_upgrade)
    recorder.set_gift_callback(on_gift)
    
    # 启动录制
    print("启动弹幕录制...")
    print("注意：需要集成真实的WebSocket连接才能工作")
    print("当前版本是框架代码")





















