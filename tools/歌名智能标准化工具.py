#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
歌名智能标准化工具

功能：
1. 中英文歌名映射
2. 繁简体转换
3. 移除特殊标记（伴奏版、Live等）
4. 优化歌词搜索成功率
"""

import re
import json
import os
from typing import Dict, List, Tuple

class SongNameNormalizer:
    """歌名标准化器"""
    
    def __init__(self):
        # 中英文歌名映射表
        self.name_mapping = {
            # 英文名 → 中文名
            'Love Confession': '告白气球',
            'A Little Bit': '一点点',
            'Lovers': '老伴',
            'Waiting For You': '等你下课',
            'Little Love Song': '小情歌',
            'Faulty Forecast': '错误的天气预报',
            'The Magic of Love': '愛的魔法',
            'Pet Spoiled': '宠坏',
            'Like Sunny Like Rainy': '像晴天像雨天',
            'Obviously': '明明就',
            'I Miss': '我懷念的',
            'Guest': '嘉宾',
            'Frozen': '凍結',
            'Quiet Scarecrow': '安静的稻草人',
            'Cloud Robe Feather Dress Song': '雲裳羽衣曲',
            'Can Be Not You': '可以不是你',
            'Good Person': '好人',
        }
        
        # 繁简体映射（常见字）
        self.traditional_to_simplified = {
            '愛': '爱',
            '說': '说',
            '聽': '听',
            '見': '见',
            '為': '为',
            '來': '来',
            '還': '还',
            '給': '给',
            '個': '个',
            '時': '时',
            '間': '间',
            '會': '会',
            '過': '过',
            '開': '开',
            '關': '关',
            '懷': '怀',
            '經': '经',
            '讓': '让',
            '變': '变',
            '離': '离',
            '難': '难',
            '雲': '云',
            '無': '无',
            '歡': '欢',
            '親': '亲',
            '動': '动',
            '學': '学',
            '長': '长',
            '當': '当',
            '準': '准',
            '從': '从',
            '帶': '带',
            '這': '这',
            '們': '们',
            '對': '对',
            '國': '国',
            '現': '现',
            '夢': '梦',
            '氣': '气',
            '記': '记',
            '點': '点',
            '頭': '头',
            '種': '种',
            '後': '后',
            '認': '认',
            '萬': '万',
            '應': '应',
            '場': '场',
            '機': '机',
            '話': '话',
            '凍': '冻',
            '結': '结',
        }
        
        # 要移除的标记
        self.remove_patterns = [
            r'\(伴奏版\)',
            r'\(伴奏\)',
            r'\(Live\)',
            r'\(live\)',
            r'\(现场版\)',
            r'\(KTV版\)',
            r'\(《.*?》.*?\)',  # 如：(《XXX》主题曲)
            r'《.*?》',  # 书名号及内容
            r'\s*-\s*.*?版$',  # 如：- 电影版
        ]
    
    def normalize(self, song_name: str, artist: str = None) -> List[Tuple[str, str]]:
        """
        标准化歌名，返回多个候选
        
        Args:
            song_name: 原始歌名
            artist: 歌手名（可选）
            
        Returns:
            [(标准化歌名, 歌手名), ...] 按优先级排序
        """
        candidates = []
        
        # 1. 原始名称
        candidates.append((song_name.strip(), artist or ""))
        
        # 2. 英文→中文映射
        if song_name in self.name_mapping:
            candidates.append((self.name_mapping[song_name], artist or ""))
        
        # 3. 移除特殊标记
        cleaned = self._remove_special_marks(song_name)
        if cleaned != song_name:
            candidates.append((cleaned, artist or ""))
        
        # 4. 繁体→简体
        simplified = self._traditional_to_simplified(song_name)
        if simplified != song_name:
            candidates.append((simplified, artist or ""))
        
        # 5. 组合：移除标记 + 繁简转换
        if cleaned != song_name:
            cleaned_simplified = self._traditional_to_simplified(cleaned)
            if cleaned_simplified not in [c[0] for c in candidates]:
                candidates.append((cleaned_simplified, artist or ""))
        
        # 6. 不带歌手名的版本
        if artist:
            for name, _ in list(candidates):
                candidates.append((name, ""))
        
        # 去重
        seen = set()
        unique_candidates = []
        for name, art in candidates:
            key = (name, art)
            if key not in seen:
                seen.add(key)
                unique_candidates.append((name, art))
        
        return unique_candidates
    
    def _remove_special_marks(self, song_name: str) -> str:
        """移除特殊标记"""
        result = song_name
        
        for pattern in self.remove_patterns:
            result = re.sub(pattern, '', result)
        
        # 移除多余空格
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result
    
    def _traditional_to_simplified(self, text: str) -> str:
        """繁体转简体"""
        result = text
        
        for trad, simp in self.traditional_to_simplified.items():
            result = result.replace(trad, simp)
        
        return result
    
    def add_mapping(self, english_name: str, chinese_name: str):
        """添加新的映射"""
        self.name_mapping[english_name] = chinese_name
    
    def save_mapping(self, file_path: str):
        """保存映射表"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.name_mapping, f, ensure_ascii=False, indent=2)
    
    def load_mapping(self, file_path: str):
        """加载映射表"""
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                self.name_mapping.update(json.load(f))


class EnhancedLyricFetcher:
    """增强的歌词获取器（带智能标准化）"""
    
    def __init__(self):
        from 获取网络歌词 import LyricFetcher
        
        self.fetcher = LyricFetcher()
        self.normalizer = SongNameNormalizer()
    
    def fetch_lyrics_smart(self, song_name: str, artist: str = None) -> Tuple[bool, str, str]:
        """
        智能获取歌词（尝试多个候选）
        
        Args:
            song_name: 歌名
            artist: 歌手
            
        Returns:
            (成功?, 歌词LRC, 使用的歌名)
        """
        # 获取所有候选
        candidates = self.normalizer.normalize(song_name, artist)
        
        print(f"\n尝试获取: {song_name}")
        print(f"  生成 {len(candidates)} 个候选:")
        for i, (name, art) in enumerate(candidates[:5], 1):  # 只显示前5个
            print(f"    {i}. {name}" + (f" - {art}" if art else ""))
        
        # 依次尝试
        for i, (candidate_name, candidate_artist) in enumerate(candidates, 1):
            try:
                # 尝试网易云
                song_info = self.fetcher.search_netease(
                    f"{candidate_name} {candidate_artist}".strip()
                )
                
                if song_info:
                    lyrics = self.fetcher.get_netease_lyric(song_info['id'])
                    if lyrics:
                        print(f"  ✓ 成功 (候选#{i}: {candidate_name})")
                        return True, lyrics, candidate_name
                
                # 尝试QQ音乐
                song_info = self.fetcher.search_qq(
                    f"{candidate_name} {candidate_artist}".strip()
                )
                
                if song_info:
                    lyrics = self.fetcher.get_qq_lyric(song_info['id'])
                    if lyrics:
                        print(f"  ✓ 成功 (候选#{i}: {candidate_name}, QQ音乐)")
                        return True, lyrics, candidate_name
            
            except Exception as e:
                continue
        
        print(f"  ✗ 所有候选都失败")
        return False, "", song_name


def test_normalizer():
    """测试标准化器"""
    
    print("=" * 80)
    print("歌名智能标准化工具 - 测试")
    print("=" * 80)
    print()
    
    normalizer = SongNameNormalizer()
    
    test_cases = [
        ("Love Confession", "周杰伦"),
        ("愛的魔法", None),
        ("宠坏 (伴奏版)", "薛之谦"),
        ("我懷念的", "孙燕姿"),
        ("明明就《电影主题曲》", None),
    ]
    
    for song_name, artist in test_cases:
        print(f"原始: {song_name}" + (f" - {artist}" if artist else ""))
        candidates = normalizer.normalize(song_name, artist)
        print(f"候选数: {len(candidates)}")
        for i, (name, art) in enumerate(candidates[:5], 1):
            print(f"  {i}. {name}" + (f" - {art}" if art else ""))
        print()


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_normalizer()
    else:
        print("=" * 80)
        print("歌名智能标准化工具")
        print("=" * 80)
        print()
        print("功能：")
        print("  1. 中英文歌名映射")
        print("  2. 繁简体转换")
        print("  3. 移除特殊标记")
        print("  4. 生成多个候选名称")
        print()
        print("使用方法：")
        print("  python3 歌名智能标准化工具.py test  # 运行测试")
        print()
        print("集成到其他脚本：")
        print("  from 歌名智能标准化工具 import SongNameNormalizer")
        print("  normalizer = SongNameNormalizer()")
        print("  candidates = normalizer.normalize('Love Confession', '周杰伦')")
        print()


if __name__ == "__main__":
    main()



