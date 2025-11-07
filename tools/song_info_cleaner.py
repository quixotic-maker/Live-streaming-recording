#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
歌曲信息清洗器 - 使用JSON配置

功能：
1. 从JSON加载歌曲/艺术家名映射
2. 支持粤语→普通话转换
3. 去除括号内容和特殊标签
4. 生成多种搜索变体
"""

import re
import os
import json
from typing import List, Tuple


class SongInfoCleaner:
    """歌曲信息清洗器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化清洗器，加载JSON配置
        
        Args:
            config_path: JSON配置文件路径（可选）
        """
        # 默认配置路径
        if not config_path:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'config', 'song_name_mapping.json'
            )
        
        # 加载配置
        self.SONG_NAME_MAPPING = {}
        self.ARTIST_NAME_MAPPING = {}
        self.CANTONESE_TO_MANDARIN = {}
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.SONG_NAME_MAPPING = config.get('song_name_mapping', {})
                    self.ARTIST_NAME_MAPPING = config.get('artist_name_mapping', {})
                    self.CANTONESE_TO_MANDARIN = config.get('cantonese_to_mandarin', {})
                # print(f"✓ 加载配置: {len(self.SONG_NAME_MAPPING)}个歌名, {len(self.ARTIST_NAME_MAPPING)}个艺术家")
            except Exception as e:
                print(f"⚠️  无法加载配置文件 {config_path}: {e}")
                self._load_default_mappings()
        else:
            # print(f"⚠️  配置文件不存在: {config_path}，使用默认映射")
            self._load_default_mappings()
    
    def _load_default_mappings(self):
        """加载默认映射（向后兼容）"""
        self.SONG_NAME_MAPPING = {
            'Love Confession': '告白气球',
            'Simple Love': '简单爱',
            'Waiting For You': '等你下课',
            'Pink Ocean': '粉色海洋',
            'Girl': '女孩',
            'Silence': '沉默',
        }
        
        self.ARTIST_NAME_MAPPING = {
            'Jay Chou': '周杰伦',
            'JJ Lin': '林俊杰',
            'Eason Chan': '陈奕迅',
            'Silence Wang': '汪苏泷',
        }
        
        self.CANTONESE_TO_MANDARIN = {
            '愛情轉移': '爱情转移',
            '富士山下': '富士山下',
        }
    
    def clean_song_name(self, song_name: str) -> str:
        """
        清洗歌曲名
        
        Args:
            song_name: 原始歌曲名
            
        Returns:
            清洗后的歌曲名
        """
        if not song_name:
            return ""
        
        # 0. 英文名 → 中文名映射（优先）
        if song_name in self.SONG_NAME_MAPPING:
            return self.SONG_NAME_MAPPING[song_name]
        
        # 0.5. 粤语 → 普通话转换
        if song_name in self.CANTONESE_TO_MANDARIN:
            return self.CANTONESE_TO_MANDARIN[song_name]
        
        # 1. 去除括号及其内容（中英文括号）
        # 例如: "宠坏 (伴奏版)" → "宠坏"
        song_name = re.sub(r'\s*[\(（].*?[\)）]\s*', '', song_name)
        song_name = re.sub(r'\s*\[.*?\]\s*', '', song_name)
        
        # 2. 去除特殊标签
        # 例如: "歌名 - Live", "歌名 (feat. xxx)"
        tags_to_remove = [
            r'\s*-\s*Live\s*$',
            r'\s*-\s*live\s*$',
            r'\s*-\s*伴奏\s*$',
            r'\s*-\s*Remix\s*$',
            r'\s*-\s*国语版\s*$',
            r'\s*-\s*粤语版\s*$',
        ]
        for pattern in tags_to_remove:
            song_name = re.sub(pattern, '', song_name, flags=re.IGNORECASE)
        
        # 3. 去除前后空白
        song_name = song_name.strip()
        
        return song_name
    
    def clean_artist_name(self, artist_name: str) -> str:
        """
        清洗艺术家名
        
        Args:
            artist_name: 原始艺术家名
            
        Returns:
            清洗后的艺术家名
        """
        if not artist_name:
            return ""
        
        # 英文 → 中文映射
        if artist_name in self.ARTIST_NAME_MAPPING:
            return self.ARTIST_NAME_MAPPING[artist_name]
        
        # 处理多艺术家分隔符
        # 例如: "A, B & C" → "A"（取第一个）
        artist_name = re.split(r'[,，&/、]', artist_name)[0].strip()
        
        return artist_name
    
    def generate_search_queries(self, song_title: str, artist_name: str) -> List[Tuple[str, str]]:
        """
        生成多个搜索查询变体
        
        Args:
            song_title: 歌曲名
            artist_name: 艺术家名
            
        Returns:
            查询变体列表 [(title, artist), ...]
        """
        queries = []
        
        # 1. 原始查询
        queries.append((song_title, artist_name))
        
        # 2. 清洗后的歌名 + 艺术家
        cleaned_title = self.clean_song_name(song_title)
        cleaned_artist = self.clean_artist_name(artist_name)
        
        if cleaned_title != song_title or cleaned_artist != artist_name:
            queries.append((cleaned_title, cleaned_artist))
        
        # 3. 如果英文歌名有映射，添加中文版本
        if song_title in self.SONG_NAME_MAPPING:
            cn_title = self.SONG_NAME_MAPPING[song_title]
            if artist_name in self.ARTIST_NAME_MAPPING:
                cn_artist = self.ARTIST_NAME_MAPPING[artist_name]
                queries.append((cn_title, cn_artist))
            else:
                queries.append((cn_title, cleaned_artist))
        
        # 4. 只用歌名搜索（泛化搜索）
        if cleaned_title:
            queries.append((cleaned_title, ""))
        
        # 5. 如果有英文映射，只用中文歌名搜索
        if song_title in self.SONG_NAME_MAPPING:
            queries.append((self.SONG_NAME_MAPPING[song_title], ""))
        
        # 去重（保持顺序）
        seen = set()
        unique_queries = []
        for q in queries:
            key = f"{q[0]}|||{q[1]}"
            if key not in seen:
                seen.add(key)
                unique_queries.append(q)
        
        return unique_queries
    
    def format_search_string(self, title: str, artist: str) -> str:
        """
        格式化搜索字符串
        
        Args:
            title: 歌曲名
            artist: 艺术家名
            
        Returns:
            搜索字符串
        """
        if artist:
            return f"{title} {artist}"
        else:
            return title


if __name__ == '__main__':
    # 测试
    cleaner = SongInfoCleaner()
    
    test_cases = [
        ("Love Confession", "Jay Chou"),
        ("宠坏 (伴奏版)", "李俊佑"),
        ("素颜 (with 何曼婷)", "Vae Xu"),
        ("愛情轉移 (國)", "Eason Chan"),
    ]
    
    print("=" * 70)
    print("歌曲信息清洗测试")
    print("=" * 70)
    
    for title, artist in test_cases:
        print(f"\n原始: {title} - {artist}")
        print(f"清洗后歌名: {cleaner.clean_song_name(title)}")
        print(f"清洗后艺术家: {cleaner.clean_artist_name(artist)}")
        queries = cleaner.generate_search_queries(title, artist)
        print(f"搜索变体:")
        for i, (t, a) in enumerate(queries, 1):
            print(f"  {i}. {cleaner.format_search_string(t, a)}")
