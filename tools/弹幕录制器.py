#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音弹幕录制器

功能：
1. 同步录制直播弹幕
2. 保存弹幕数据（JSON格式）
3. 实时统计弹幕信息
4. 与视频录制时间同步

依赖：
需要先安装并配置 DouyinBarrageGrab 项目
"""

import os
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional
from collections import Counter

class DouyinDanmakuRecorder:
    """抖音弹幕录制器"""
    
    def __init__(self, room_url: str, output_file: str):
        """
        Args:
            room_url: 直播间URL
            output_file: 输出文件路径
        """
        self.room_url = room_url
        self.output_file = output_file
        self.danmaku_list = []
        self.start_time = None
        self.is_recording = False
        
        # 统计数据
        self.stats = {
            'total_danmaku': 0,
            'total_gifts': 0,
            'unique_users': set(),
            'gift_types': Counter(),
        }
    
    async def start_recording(self):
        """开始录制弹幕"""
        
        try:
            # 尝试导入弹幕抓取模块
            from DouyinBarrageGrab import DouyinBarrage
        except ImportError:
            print("⚠️  未找到 DouyinBarrageGrab 模块")
            print("   请先克隆项目: git clone https://github.com/ape-byte/DouyinBarrageGrab")
            print("   并安装依赖: pip install -r requirements.txt")
            return
        
        self.start_time = datetime.now()
        self.is_recording = True
        
        print(f"\n开始录制弹幕...")
        print(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"直播间: {self.room_url}")
        print()
        
        try:
            # 创建弹幕抓取器
            barrage = DouyinBarrage(self.room_url)
            
            # 接收弹幕
            async for danmaku in barrage.receive():
                if not self.is_recording:
                    break
                
                # 计算相对时间（秒）
                relative_time = (datetime.now() - self.start_time).total_seconds()
                
                # 解析弹幕数据
                danmaku_data = {
                    'time': relative_time,
                    'timestamp': datetime.now().isoformat(),
                    'type': danmaku.get('type', 'unknown'),
                    'user': danmaku.get('user', {}).get('nickname', '未知'),
                    'user_id': danmaku.get('user', {}).get('id', ''),
                    'content': danmaku.get('content', ''),
                }
                
                # 礼物信息
                if danmaku.get('type') == 'gift':
                    danmaku_data['gift'] = {
                        'name': danmaku.get('gift_name', ''),
                        'count': danmaku.get('gift_count', 1),
                        'value': danmaku.get('gift_value', 0),
                    }
                    self.stats['total_gifts'] += danmaku_data['gift']['count']
                    self.stats['gift_types'][danmaku_data['gift']['name']] += danmaku_data['gift']['count']
                
                # 添加到列表
                self.danmaku_list.append(danmaku_data)
                self.stats['total_danmaku'] += 1
                self.stats['unique_users'].add(danmaku_data['user_id'])
                
                # 实时显示
                self._print_danmaku(danmaku_data)
                
                # 每100条保存一次
                if len(self.danmaku_list) % 100 == 0:
                    self.save()
                    print(f"  💾 已保存 {len(self.danmaku_list)} 条弹幕")
        
        except KeyboardInterrupt:
            print("\n⚠️  用户中断录制")
        except Exception as e:
            print(f"\n✗ 录制出错: {e}")
        finally:
            self.stop_recording()
    
    def _print_danmaku(self, danmaku: Dict):
        """打印弹幕信息"""
        
        time_str = f"{int(danmaku['time'] // 60):02d}:{int(danmaku['time'] % 60):02d}"
        
        if danmaku['type'] == 'chat':
            print(f"  [{time_str}] 💬 {danmaku['user']}: {danmaku['content']}")
        elif danmaku['type'] == 'gift':
            gift = danmaku['gift']
            print(f"  [{time_str}] 🎁 {danmaku['user']} 送出 {gift['name']} x{gift['count']}")
        elif danmaku['type'] == 'like':
            print(f"  [{time_str}] ❤️  {danmaku['user']} 点赞")
        elif danmaku['type'] == 'enter':
            print(f"  [{time_str}] 👋 {danmaku['user']} 进入直播间")
    
    def stop_recording(self):
        """停止录制"""
        
        self.is_recording = False
        
        # 最后保存一次
        self.save()
        
        # 打印统计
        self.print_stats()
    
    def save(self):
        """保存弹幕数据"""
        
        data = {
            'metadata': {
                'room_url': self.room_url,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': datetime.now().isoformat(),
                'duration': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                'total_danmaku': len(self.danmaku_list),
            },
            'danmaku_list': self.danmaku_list,
        }
        
        # 保存为JSON
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def print_stats(self):
        """打印统计信息"""
        
        print()
        print("=" * 70)
        print("弹幕录制统计")
        print("=" * 70)
        print(f"总弹幕数: {self.stats['total_danmaku']} 条")
        print(f"总礼物数: {self.stats['total_gifts']} 个")
        print(f"互动人数: {len(self.stats['unique_users'])} 人")
        
        if self.stats['gift_types']:
            print()
            print("热门礼物 TOP 5:")
            for gift_name, count in self.stats['gift_types'].most_common(5):
                print(f"  {gift_name}: {count} 个")
        
        print()
        print(f"数据已保存: {self.output_file}")
        print("=" * 70)


class DanmakuAnalyzer:
    """弹幕数据分析器"""
    
    def __init__(self, danmaku_file: str):
        """
        Args:
            danmaku_file: 弹幕JSON文件路径
        """
        self.danmaku_file = danmaku_file
        self.data = None
    
    def load(self):
        """加载弹幕数据"""
        
        with open(self.danmaku_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        print(f"✓ 加载了 {len(self.data['danmaku_list'])} 条弹幕")
    
    def extract_song_mentions(self) -> List[Dict]:
        """提取歌曲相关的弹幕"""
        
        song_keywords = ['歌', '唱', '好听', '这首', '什么歌', '歌名']
        song_mentions = []
        
        for danmaku in self.data['danmaku_list']:
            content = danmaku['content']
            
            # 检查是否包含歌曲关键词
            if any(kw in content for kw in song_keywords):
                song_mentions.append({
                    'time': danmaku['time'],
                    'content': content,
                    'user': danmaku['user'],
                })
        
        return song_mentions
    
    def find_emotion_peaks(self) -> List[Dict]:
        """找出弹幕密度高峰（情绪高涨时刻）"""
        
        # 按10秒窗口统计弹幕密度
        window_size = 10  # 秒
        max_time = max(d['time'] for d in self.data['danmaku_list'])
        
        density_timeline = []
        
        for t in range(0, int(max_time) + 1, window_size):
            # 计算该窗口内的弹幕数
            count = len([
                d for d in self.data['danmaku_list']
                if t <= d['time'] < t + window_size
            ])
            
            density_timeline.append({
                'time': t,
                'count': count,
            })
        
        # 找出高密度时段（超过平均值+标准差）
        import numpy as np
        counts = [d['count'] for d in density_timeline]
        mean = np.mean(counts)
        std = np.std(counts)
        threshold = mean + std
        
        peaks = [d for d in density_timeline if d['count'] > threshold]
        
        return peaks
    
    def get_gift_timeline(self) -> List[Dict]:
        """获取礼物时间线"""
        
        gifts = []
        
        for danmaku in self.data['danmaku_list']:
            if danmaku['type'] == 'gift':
                gifts.append({
                    'time': danmaku['time'],
                    'gift_name': danmaku['gift']['name'],
                    'count': danmaku['gift']['count'],
                    'user': danmaku['user'],
                })
        
        return gifts
    
    def generate_report(self, output_file: str):
        """生成分析报告"""
        
        song_mentions = self.extract_song_mentions()
        emotion_peaks = self.find_emotion_peaks()
        gifts = self.get_gift_timeline()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("弹幕数据分析报告\n")
            f.write("=" * 80 + "\n\n")
            
            # 基本统计
            f.write("## 基本统计\n\n")
            f.write(f"总弹幕数: {len(self.data['danmaku_list'])} 条\n")
            f.write(f"礼物数: {len(gifts)} 个\n")
            f.write(f"歌曲提及: {len(song_mentions)} 次\n")
            f.write(f"情绪高峰: {len(emotion_peaks)} 个\n\n")
            
            # 歌曲提及
            if song_mentions:
                f.write("## 歌曲相关弹幕\n\n")
                for mention in song_mentions[:20]:  # 只显示前20个
                    time_str = f"{int(mention['time'] // 60):02d}:{int(mention['time'] % 60):02d}"
                    f.write(f"[{time_str}] {mention['user']}: {mention['content']}\n")
                f.write("\n")
            
            # 情绪高峰
            if emotion_peaks:
                f.write("## 情绪高峰时刻\n\n")
                f.write("（弹幕密度高的时段，可能是精彩片段）\n\n")
                for peak in emotion_peaks:
                    time_str = f"{int(peak['time'] // 60):02d}:{int(peak['time'] % 60):02d}"
                    f.write(f"{time_str} - 弹幕数: {peak['count']} 条\n")
                f.write("\n")
            
            # 礼物时间线
            if gifts:
                f.write("## 礼物时间线\n\n")
                for gift in gifts[:30]:  # 只显示前30个
                    time_str = f"{int(gift['time'] // 60):02d}:{int(gift['time'] % 60):02d}"
                    f.write(f"[{time_str}] {gift['user']}: {gift['gift_name']} x{gift['count']}\n")
                f.write("\n")
        
        print(f"✓ 报告已生成: {output_file}")


def main():
    """主函数"""
    import sys
    
    print("=" * 80)
    print("抖音弹幕录制器")
    print("=" * 80)
    print()
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print()
        print("1. 录制弹幕:")
        print("   python3 弹幕录制器.py record <直播间URL>")
        print()
        print("2. 分析弹幕:")
        print("   python3 弹幕录制器.py analyze <弹幕JSON文件>")
        print()
        print("示例:")
        print("   python3 弹幕录制器.py record https://live.douyin.com/123456")
        print("   python3 弹幕录制器.py analyze ~/shanshan_materials/观山_弹幕.json")
        return
    
    mode = sys.argv[1]
    
    if mode == 'record':
        if len(sys.argv) < 3:
            print("✗ 请提供直播间URL")
            return
        
        room_url = sys.argv[2]
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = os.path.expanduser(f"~/shanshan_materials/观山_{timestamp}_弹幕.json")
        
        # 创建录制器
        recorder = DouyinDanmakuRecorder(room_url, output_file)
        
        # 开始录制
        asyncio.run(recorder.start_recording())
    
    elif mode == 'analyze':
        if len(sys.argv) < 3:
            print("✗ 请提供弹幕JSON文件路径")
            return
        
        danmaku_file = sys.argv[2]
        
        if not os.path.exists(danmaku_file):
            print(f"✗ 文件不存在: {danmaku_file}")
            return
        
        # 创建分析器
        analyzer = DanmakuAnalyzer(danmaku_file)
        analyzer.load()
        
        # 生成报告
        report_file = danmaku_file.replace('.json', '_分析报告.txt')
        analyzer.generate_report(report_file)
        
        print()
        print("✅ 分析完成！")
    
    else:
        print(f"✗ 未知模式: {mode}")
        print("   支持的模式: record, analyze")


if __name__ == "__main__":
    main()



