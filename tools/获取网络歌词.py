#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从网络获取原版歌词

功能：
1. 读取歌曲列表
2. 通过歌曲识别API获取正版歌词
3. 生成准确的字幕文件（SRT/ASS）

支持的API：
- 网易云音乐
- QQ音乐
- 酷狗音乐
- 酷我音乐
- 咪咕音乐
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, List, Tuple


class LyricFetcher:
    """歌词获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_netease(self, song_name: str) -> Optional[Dict]:
        """
        从网易云音乐搜索歌曲
        
        Args:
            song_name: 歌曲名
            
        Returns:
            歌曲信息（包含ID）
        """
        try:
            # 网易云音乐搜索API
            url = "https://music.163.com/api/search/get/web"
            params = {
                's': song_name,
                'type': '1',  # 单曲
                'limit': '1'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('result') and data['result'].get('songs'):
                song = data['result']['songs'][0]
                return {
                    'id': song['id'],
                    'name': song['name'],
                    'artist': ','.join([ar['name'] for ar in song['artists']]),
                    'album': song['album']['name']
                }
        except Exception as e:
            print(f"  ⚠ 网易云搜索失败: {e}")
        
        return None
    
    def get_netease_lyric(self, song_id: int) -> Optional[str]:
        """
        从网易云音乐获取歌词
        
        Args:
            song_id: 歌曲ID
            
        Returns:
            LRC格式歌词
        """
        try:
            url = f"https://music.163.com/api/song/lyric"
            params = {
                'id': song_id,
                'lv': 1,
                'tv': -1
            }
            
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('lrc') and data['lrc'].get('lyric'):
                return data['lrc']['lyric']
        except Exception as e:
            print(f"  ⚠ 获取歌词失败: {e}")
        
        return None
    
    def search_qq(self, song_name: str) -> Optional[Dict]:
        """
        从QQ音乐搜索歌曲
        
        Args:
            song_name: 歌曲名
            
        Returns:
            歌曲信息
        """
        try:
            url = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp"
            params = {
                'w': song_name,
                'format': 'json',
                'n': '1'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('data') and data['data'].get('song'):
                songs = data['data']['song']['list']
                if songs:
                    song = songs[0]
                    return {
                        'id': song['songmid'],
                        'name': song['songname'],
                        'artist': ','.join([s['name'] for s in song['singer']]),
                        'album': song['albumname']
                    }
        except Exception as e:
            print(f"  ⚠ QQ音乐搜索失败: {e}")
        
        return None
    
    def get_qq_lyric(self, song_id: str) -> Optional[str]:
        """
        从QQ音乐获取歌词
        
        Args:
            song_id: 歌曲ID
            
        Returns:
            LRC格式歌词
        """
        try:
            url = "https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg"
            params = {
                'songmid': song_id,
                'format': 'json'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('lyric'):
                import base64
                return base64.b64decode(data['lyric']).decode('utf-8')
        except Exception as e:
            print(f"  ⚠ 获取QQ歌词失败: {e}")
        
        return None
    
    def search_kugou(self, song_name: str) -> Optional[Dict]:
        """
        从酷狗音乐搜索歌曲
        
        Args:
            song_name: 歌曲名
            
        Returns:
            歌曲信息
        """
        try:
            url = "http://mobilecdn.kugou.com/api/v3/search/song"
            params = {
                'format': 'json',
                'keyword': song_name,
                'page': '1',
                'pagesize': '1'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('data') and data['data'].get('info'):
                songs = data['data']['info']
                if songs:
                    song = songs[0]
                    return {
                        'hash': song.get('hash', ''),
                        'album_id': song.get('album_id', ''),
                        'name': song.get('songname', ''),
                        'artist': song.get('singername', ''),
                        'album': song.get('album_name', '')
                    }
        except Exception as e:
            print(f"  ⚠ 酷狗音乐搜索失败: {e}")
        
        return None
    
    def get_kugou_lyric(self, song_hash: str, album_id: str) -> Optional[str]:
        """
        从酷狗音乐获取歌词
        
        Args:
            song_hash: 歌曲hash
            album_id: 专辑ID
            
        Returns:
            LRC格式歌词
        """
        try:
            url = "http://www.kugou.com/yy/index.php"
            params = {
                'r': 'play/getdata',
                'hash': song_hash,
                'album_id': album_id
            }
            
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('data') and data['data'].get('lyrics'):
                import base64
                lyrics_b64 = data['data']['lyrics']
                return base64.b64decode(lyrics_b64).decode('utf-8')
        except Exception as e:
            print(f"  ⚠ 获取酷狗歌词失败: {e}")
        
        return None
    
    def search_kuwo(self, song_name: str) -> Optional[Dict]:
        """
        从酷我音乐搜索歌曲
        
        Args:
            song_name: 歌曲名
            
        Returns:
            歌曲信息
        """
        try:
            url = "http://www.kuwo.cn/api/www/search/searchMusicBykeyWord"
            params = {
                'key': song_name,
                'pn': '1',
                'rn': '1'
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'http://www.kuwo.cn/'
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if data.get('data') and data['data'].get('list'):
                songs = data['data']['list']
                if songs:
                    song = songs[0]
                    return {
                        'id': song.get('rid', ''),
                        'name': song.get('name', ''),
                        'artist': song.get('artist', ''),
                        'album': song.get('album', '')
                    }
        except Exception as e:
            print(f"  ⚠ 酷我音乐搜索失败: {e}")
        
        return None
    
    def get_kuwo_lyric(self, song_id: str) -> Optional[str]:
        """
        从酷我音乐获取歌词
        
        Args:
            song_id: 歌曲ID
            
        Returns:
            LRC格式歌词
        """
        try:
            url = f"http://m.kuwo.cn/newh5/singles/songinfoandlrc"
            params = {
                'musicId': song_id
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
                'Referer': 'http://m.kuwo.cn/'
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if data.get('data') and data['data'].get('lrclist'):
                # 将酷我格式转换为LRC格式
                lrc_list = data['data']['lrclist']
                lrc_lines = []
                for item in lrc_list:
                    time_str = item.get('time', '')
                    lyric = item.get('lineLyric', '')
                    if time_str and lyric:
                        lrc_lines.append(f"[{time_str}]{lyric}")
                return '\n'.join(lrc_lines)
        except Exception as e:
            print(f"  ⚠ 获取酷我歌词失败: {e}")
        
        return None
    
    def search_migu(self, song_name: str) -> Optional[Dict]:
        """
        从咪咕音乐搜索歌曲
        
        Args:
            song_name: 歌曲名
            
        Returns:
            歌曲信息
        """
        try:
            url = "https://m.music.migu.cn/migu/remoting/scr_search_tag"
            params = {
                'keyword': song_name,
                'type': '2',  # 歌曲
                'rows': '1',
                'pgc': '1'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('musics'):
                songs = data['musics']
                if songs:
                    song = songs[0]
                    return {
                        'id': song.get('id', ''),
                        'copyrightId': song.get('copyrightId', ''),
                        'name': song.get('title', ''),
                        'artist': song.get('singerName', ''),
                        'album': song.get('albumName', '')
                    }
        except Exception as e:
            print(f"  ⚠ 咪咕音乐搜索失败: {e}")
        
        return None
    
    def get_migu_lyric(self, copyright_id: str) -> Optional[str]:
        """
        从咪咕音乐获取歌词
        
        Args:
            copyright_id: 版权ID
            
        Returns:
            LRC格式歌词
        """
        try:
            url = f"https://music.migu.cn/v3/api/music/audioPlayer/getLyric"
            params = {
                'copyrightId': copyright_id
            }
            
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('lyric'):
                return data['lyric']
        except Exception as e:
            print(f"  ⚠ 获取咪咕歌词失败: {e}")
        
        return None
    
    def parse_lrc(self, lrc_text: str) -> List[Tuple[float, str]]:
        """
        解析LRC格式歌词
        
        Args:
            lrc_text: LRC格式歌词文本
            
        Returns:
            [(时间戳, 歌词), ...]
        """
        import re
        
        lines = []
        pattern = r'\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)'
        
        for line in lrc_text.split('\n'):
            match = re.match(pattern, line)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                milliseconds = int(match.group(3))
                text = match.group(4).strip()
                
                # 转换为秒
                timestamp = minutes * 60 + seconds + milliseconds / 1000
                
                if text:  # 跳过空行
                    lines.append((timestamp, text))
        
        return sorted(lines, key=lambda x: x[0])
    
    def lrc_to_srt(self, lrc_lines: List[Tuple[float, str]], output_path: str):
        """
        将LRC转换为SRT格式
        
        Args:
            lrc_lines: [(时间戳, 歌词), ...]
            output_path: 输出路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, (start_time, text) in enumerate(lrc_lines, 1):
                # 计算结束时间（下一句开始或+5秒）
                end_time = lrc_lines[i][0] if i < len(lrc_lines) else start_time + 5
                
                # 格式化时间
                start_str = self._format_srt_time(start_time)
                end_str = self._format_srt_time(end_time)
                
                # 写入SRT格式
                f.write(f"{i}\n")
                f.write(f"{start_str} --> {end_str}\n")
                f.write(f"{text}\n")
                f.write("\n")
    
    def lrc_to_ass(self, lrc_lines: List[Tuple[float, str]], output_path: str):
        """
        将LRC转换为ASS格式
        
        Args:
            lrc_lines: [(时间戳, 歌词), ...]
            output_path: 输出路径
        """
        # ASS文件头
        header = """[Script Info]
Title: 歌词字幕
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,微软雅黑,24,&H00FFFFFF,&H000088EF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header)
            
            for i, (start_time, text) in enumerate(lrc_lines):
                # 计算结束时间
                end_time = lrc_lines[i][0] if i < len(lrc_lines) else start_time + 5
                
                # 格式化时间
                start_str = self._format_ass_time(start_time)
                end_str = self._format_ass_time(end_time)
                
                # 写入ASS格式
                f.write(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}\n")
    
    def _format_srt_time(self, seconds: float) -> str:
        """格式化为SRT时间格式 (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_ass_time(self, seconds: float) -> str:
        """格式化为ASS时间格式 (H:MM:SS.cc)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def main():
    """主函数"""
    print("=" * 70)
    print("网络歌词获取工具")
    print("=" * 70)
    print()
    
    # 配置
    material_dir = os.path.expanduser("~/shanshan_materials")
    # 使用优化后的歌曲列表（40首唯一歌曲）
    song_list_path = os.path.join(material_dir, "歌曲列表_优化版.json")
    output_dir = os.path.join(material_dir, "歌词字幕_网络版")
    
    # 检查文件
    if not os.path.exists(song_list_path):
        print(f"❌ 歌曲列表不存在: {song_list_path}")
        return
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载歌曲列表
    with open(song_list_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        songs = data.get("songs", [])
    
    print(f"已加载 {len(songs)} 首歌曲")
    print(f"输出目录: {output_dir}")
    print()
    
    # 询问处理范围
    print("选择处理范围：")
    print("  1. 仅处理前10首（测试）")
    print("  2. 处理所有歌曲")
    print("  3. 自定义范围")
    
    choice = input("\n请选择 (1/2/3，默认1): ").strip() or "1"
    
    if choice == "1":
        songs_to_process = songs[:10]
    elif choice == "2":
        songs_to_process = songs
    else:
        try:
            start_idx = int(input("起始索引 (0开始): "))
            end_idx = int(input("结束索引: "))
            songs_to_process = songs[start_idx:end_idx]
        except:
            print("❌ 输入错误")
            return
    
    print()
    print("=" * 70)
    print(f"开始获取歌词（共 {len(songs_to_process)} 首）")
    print("=" * 70)
    print()
    
    # 创建获取器
    fetcher = LyricFetcher()
    
    # 统计
    success_count = 0
    fail_count = 0
    
    # 处理每首歌
    for i, song in enumerate(songs_to_process, 1):
        song_name = song.get("title", f"未知歌曲{i}")
        
        print(f"[{i}/{len(songs_to_process)}] {song_name}")
        
        # 跳过"未知歌曲"
        if song_name.startswith("未知歌曲"):
            print("  ⚠ 跳过未知歌曲")
            fail_count += 1
            continue
        
        # 尝试从网易云获取
        song_info = fetcher.search_netease(song_name)
        lyric_text = None
        source = None
        
        if song_info:
            print(f"  ✓ [网易云] {song_info['name']} - {song_info['artist']}")
            lyric_text = fetcher.get_netease_lyric(song_info['id'])
            if lyric_text:
                source = "网易云"
        
        # 如果网易云失败，尝试QQ音乐
        if not lyric_text:
            print("  → 尝试QQ音乐...")
            song_info = fetcher.search_qq(song_name)
            if song_info:
                print(f"  ✓ [QQ音乐] {song_info['name']} - {song_info['artist']}")
                lyric_text = fetcher.get_qq_lyric(song_info['id'])
                if lyric_text:
                    source = "QQ音乐"
        
        # 如果QQ音乐失败，尝试酷狗
        if not lyric_text:
            print("  → 尝试酷狗...")
            song_info = fetcher.search_kugou(song_name)
            if song_info:
                print(f"  ✓ [酷狗] {song_info['name']} - {song_info['artist']}")
                lyric_text = fetcher.get_kugou_lyric(song_info['hash'], song_info['album_id'])
                if lyric_text:
                    source = "酷狗"
        
        # 如果酷狗失败，尝试酷我
        if not lyric_text:
            print("  → 尝试酷我...")
            song_info = fetcher.search_kuwo(song_name)
            if song_info:
                print(f"  ✓ [酷我] {song_info['name']} - {song_info['artist']}")
                lyric_text = fetcher.get_kuwo_lyric(song_info['id'])
                if lyric_text:
                    source = "酷我"
        
        # 如果酷我失败，尝试咪咕
        if not lyric_text:
            print("  → 尝试咪咕...")
            song_info = fetcher.search_migu(song_name)
            if song_info:
                print(f"  ✓ [咪咕] {song_info['name']} - {song_info['artist']}")
                lyric_text = fetcher.get_migu_lyric(song_info['copyrightId'])
                if lyric_text:
                    source = "咪咕"
        
        # 处理歌词
        if lyric_text:
            try:
                # 解析LRC
                lrc_lines = fetcher.parse_lrc(lyric_text)
                
                if lrc_lines:
                    # 生成文件名
                    safe_name = "".join(c for c in song_name if c.isalnum() or c in "_ -")
                    srt_path = os.path.join(output_dir, f"{i:03d}_{safe_name}.srt")
                    ass_path = os.path.join(output_dir, f"{i:03d}_{safe_name}.ass")
                    
                    # 转换为SRT和ASS
                    fetcher.lrc_to_srt(lrc_lines, srt_path)
                    fetcher.lrc_to_ass(lrc_lines, ass_path)
                    
                    print(f"  ✓ 来源: {source}")
                    print(f"  ✓ 歌词行数: {len(lrc_lines)}")
                    print(f"  ✓ SRT: {os.path.basename(srt_path)}")
                    print(f"  ✓ ASS: {os.path.basename(ass_path)}")
                    
                    success_count += 1
                else:
                    print("  ⚠ 歌词解析失败")
                    fail_count += 1
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
                fail_count += 1
        else:
            print("  ❌ 未找到歌词")
            fail_count += 1
        
        print()
        
        # 延迟，避免请求过快
        time.sleep(0.5)
    
    # 完成
    print("=" * 70)
    print("✅ 歌词获取完成！")
    print("=" * 70)
    print()
    print(f"输出目录: {output_dir}")
    print(f"  成功: {success_count} 首")
    print(f"  失败: {fail_count} 首")
    print()
    print("💡 使用提示:")
    print("  - 网络歌词比Whisper转录准确度高")
    print("  - 但时间轴需要根据实际录播微调")
    print("  - 建议使用Aegisub等工具调整时间轴")
    print()


if __name__ == "__main__":
    main()

