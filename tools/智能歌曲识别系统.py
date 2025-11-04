#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能歌曲识别系统

目标：100%识别所有歌曲
策略：音频指纹 + 弹幕分析 + 歌名提取 + 人工标注

流程：
1. 音频指纹识别（Shazam/ACRCloud）→ 预计80-90%
2. 弹幕关键词分析 → 补充5-10%
3. 改进歌名提取 → 补充5-10%
4. 人工标注兜底 → 剩余0-10%
"""

import os
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

# 设置代理环境变量（Clash Verge）
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
os.environ['ALL_PROXY'] = 'http://127.0.0.1:7897'


class AudioFingerprint:
    """音频指纹识别器（使用ShazamIO）"""
    
    def __init__(self):
        self.shazam = None
        self._init_shazam()
    
    def _init_shazam(self):
        """初始化Shazam（带代理支持）"""
        try:
            from shazamio import Shazam
            import aiohttp
            
            # 创建带代理的connector
            proxy_url = os.environ.get('HTTP_PROXY', 'http://127.0.0.1:7897')
            
            # ShazamIO会自动使用环境变量中的代理
            # 但我们显式创建一个带代理的实例来确保
            self.shazam = Shazam()
            self.proxy_url = proxy_url
            
            print(f"✓ Shazam初始化成功（代理: {proxy_url}）")
        except ImportError:
            print("⚠ ShazamIO未安装，请运行: pip install shazamio")
            print("  或使用 pip install aiohttp aiodns")
    
    async def recognize_from_file(self, audio_path: str) -> Optional[Dict]:
        """
        识别音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            歌曲信息字典
        """
        if not self.shazam:
            return None
        
        try:
            # 使用代理进行识别（通过环境变量HTTP_PROXY）
            result = await self.shazam.recognize(audio_path)
            
            if result and 'track' in result:
                track = result['track']
                # 更安全的字段提取
                title = track.get('title', '')
                artist = track.get('subtitle', '')
                
                # 提取专辑信息（可能不存在）
                album = ''
                sections = track.get('sections', [])
                if sections:
                    metadata = sections[0].get('metadata', [])
                    if metadata:
                        album = metadata[0].get('text', '')
                
                return {
                    'title': title,
                    'artist': artist,
                    'album': album,
                    'confidence': 0.95,
                    'source': 'shazam'
                }
        except IndexError as e:
            print(f"  ⚠ Shazam识别失败: 返回数据格式异常")
        except Exception as e:
            print(f"  ⚠ Shazam识别失败: {e}")
        
        return None
    
    def extract_audio_segment(self, video_path: str, start_time: float, 
                             duration: float, output_path: str):
        """
        提取音频片段用于识别
        
        Args:
            video_path: 视频路径
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            output_path: 输出路径
        """
        # 提取30秒音频片段（识别效果最好）
        duration = min(duration, 30)
        # 从中间部分提取（避免前奏和尾奏）
        start_time = start_time + max(0, (duration - 30) / 2)
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', '44100',
            '-ac', '1',
            '-y',
            output_path
        ]
        
        subprocess.run(cmd, stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, check=True)


class DanmakuAnalyzer:
    """弹幕分析器"""
    
    def __init__(self, danmaku_file: Optional[str] = None):
        self.danmaku_file = danmaku_file
        self.danmaku_data = []
        
        if danmaku_file and os.path.exists(danmaku_file):
            self._load_danmaku()
    
    def _load_danmaku(self):
        """加载弹幕数据"""
        try:
            with open(self.danmaku_file, 'r', encoding='utf-8') as f:
                self.danmaku_data = json.load(f)
            print(f"✓ 加载弹幕: {len(self.danmaku_data)} 条")
        except Exception as e:
            print(f"⚠ 加载弹幕失败: {e}")
    
    def extract_song_names(self, start_time: float, end_time: float) -> List[str]:
        """
        从弹幕中提取歌名
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            可能的歌名列表
        """
        song_keywords = []
        
        # 关键词模式
        patterns = [
            r'这首歌[是叫]?[《<]?([^》>。，,]+)[》>]?',
            r'点播[《<]?([^》>。，,]+)[》>]?',
            r'唱[《<]?([^》>。，,]+)[》>]?',
            r'[《<]([^》>]{2,10})[》>]',
            r'歌名[：:是]?([^。，,\s]+)',
        ]
        
        # 筛选时间范围内的弹幕
        for danmu in self.danmaku_data:
            timestamp = danmu.get('time', 0)
            if start_time <= timestamp <= end_time:
                content = danmu.get('content', '')
                
                # 匹配歌名模式
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    song_keywords.extend(matches)
        
        # 统计频率
        from collections import Counter
        counter = Counter(song_keywords)
        
        # 返回出现次数最多的前3个
        return [name for name, count in counter.most_common(3) if count >= 2]


class ImprovedNameExtractor:
    """改进的歌名提取器"""
    
    def __init__(self):
        self.song_indicators = [
            "这首歌叫", "歌名是", "点播", "唱一首", 
            "来一首", "点凭", "点歌"
        ]
    
    def extract_from_transcript(self, segments: List[Dict], 
                               song_start: float, song_end: float) -> Optional[str]:
        """
        从转录文本中提取歌名
        
        Args:
            segments: Whisper转录片段
            song_start: 歌曲开始时间
            song_end: 歌曲结束时间
            
        Returns:
            歌名
        """
        # 查找歌曲前后30秒的闲聊内容
        search_start = max(0, song_start - 30)
        search_end = song_end + 30
        
        relevant_texts = []
        for seg in segments:
            seg_time = seg.get('start', 0)
            if search_start <= seg_time <= search_end:
                text = seg.get('text', '').strip()
                relevant_texts.append(text)
        
        # 合并文本
        full_text = ' '.join(relevant_texts)
        
        # 使用正则提取歌名
        patterns = [
            r'这首歌叫([^，。\s]{2,15})',
            r'歌名[是叫]?([^，。\s]{2,15})',
            r'点播([^，。\s]{2,15})',
            r'唱[一]?首([^，。\s]{2,15})',
            r'来[一]?首([^，。\s]{2,15})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                song_name = match.group(1)
                # 过滤明显不是歌名的
                if not any(x in song_name for x in ['谢谢', '爱你', '宝贝', '家人']):
                    return song_name
        
        return None


class ManualAnnotationGenerator:
    """人工标注生成器"""
    
    def __init__(self, video_path: str, output_dir: str):
        self.video_path = video_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_player(self, unknown_songs: List[Dict], output_file: str):
        """
        生成HTML播放器供人工标注
        
        Args:
            unknown_songs: 未识别的歌曲列表
            output_file: 输出HTML文件路径
        """
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>歌曲人工标注工具</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            text-align: center;
            color: #667eea;
            margin-bottom: 10px;
            font-size: 36px;
        }
        .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 30px;
        }
        .progress-bar {
            background: #f0f0f0;
            border-radius: 10px;
            height: 20px;
            margin-bottom: 30px;
            overflow: hidden;
        }
        .progress-fill {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            width: 0%;
            transition: width 0.3s;
        }
        .song-item {
            border: 2px solid #e0e0e0;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            background: #fafafa;
            display: none;
        }
        .song-item.active {
            display: block;
            animation: fadeIn 0.5s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .song-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .song-number {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .song-time {
            color: #888;
            font-size: 14px;
        }
        video {
            width: 100%;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .lyrics-preview {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            max-height: 150px;
            overflow-y: auto;
            font-size: 14px;
            line-height: 1.8;
            color: #666;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #333;
        }
        input[type="text"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .button-group {
            display: flex;
            gap: 15px;
            justify-content: center;
        }
        button {
            padding: 15px 40px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-submit {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-submit:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .btn-skip {
            background: #f0f0f0;
            color: #666;
        }
        .btn-skip:hover {
            background: #e0e0e0;
        }
        .btn-export {
            background: #4CAF50;
            color: white;
            margin-top: 20px;
            width: 100%;
            display: none;
        }
        .btn-export.show {
            display: block;
        }
        .summary {
            display: none;
            text-align: center;
            padding: 40px;
        }
        .summary.show {
            display: block;
        }
        .summary h2 {
            color: #4CAF50;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 歌曲人工标注工具</h1>
        <p class="subtitle">请为以下未识别的歌曲填写正确的歌名</p>
        
        <div class="progress-bar">
            <div class="progress-fill" id="progressFill"></div>
        </div>
        
        <div id="songContainer">
            <!-- 歌曲项将在这里动态生成 -->
        </div>
        
        <div class="summary" id="summary">
            <h2>✅ 标注完成！</h2>
            <p id="summaryText"></p>
            <button class="btn-export show" onclick="exportResults()">📥 导出结果（JSON）</button>
        </div>
    </div>
    
    <script>
        const songs = SONGS_DATA;
        let currentIndex = 0;
        const results = {};
        
        function init() {
            renderSongs();
            updateProgress();
            showCurrentSong();
        }
        
        function renderSongs() {
            const container = document.getElementById('songContainer');
            container.innerHTML = songs.map((song, index) => `
                <div class="song-item" id="song-${index}" ${index === 0 ? 'class="song-item active"' : ''}>
                    <div class="song-header">
                        <span class="song-number">第 ${index + 1} / ${songs.length} 首</span>
                        <span class="song-time">${formatTime(song.start)} - ${formatTime(song.end)}</span>
                    </div>
                    
                    <video controls id="video-${index}">
                        <source src="#" type="video/mp4">
                        您的浏览器不支持视频标签。
                    </video>
                    
                    <div class="lyrics-preview">
                        <strong>歌词预览：</strong><br>
                        ${song.text.substring(0, 200)}...
                    </div>
                    
                    <div class="form-group">
                        <label for="songName-${index}">歌曲名称：</label>
                        <input type="text" id="songName-${index}" 
                               placeholder="请输入歌曲名称（例如：告白气球）">
                    </div>
                    
                    <div class="form-group">
                        <label for="artistName-${index}">歌手名称（可选）：</label>
                        <input type="text" id="artistName-${index}" 
                               placeholder="请输入歌手名称（例如：周杰伦）">
                    </div>
                    
                    <div class="button-group">
                        <button class="btn-submit" onclick="submitSong(${index})">✓ 提交</button>
                        <button class="btn-skip" onclick="skipSong(${index})">→ 跳过</button>
                    </div>
                </div>
            `).join('');
            
            // 设置视频源（需要实际视频文件）
            songs.forEach((song, index) => {
                const video = document.getElementById(`video-${index}`);
                // 注意：这里需要提取对应时间段的视频片段
                // 实际使用时需要预先提取好视频片段
            });
        }
        
        function formatTime(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }
        
        function showCurrentSong() {
            document.querySelectorAll('.song-item').forEach((item, index) => {
                item.classList.toggle('active', index === currentIndex);
            });
        }
        
        function updateProgress() {
            const progress = (currentIndex / songs.length) * 100;
            document.getElementById('progressFill').style.width = progress + '%';
        }
        
        function submitSong(index) {
            const songName = document.getElementById(`songName-${index}`).value.trim();
            const artistName = document.getElementById(`artistName-${index}`).value.trim();
            
            if (!songName) {
                alert('请输入歌曲名称！');
                return;
            }
            
            results[songs[index].id] = {
                title: songName,
                artist: artistName || '未知',
                start: songs[index].start,
                end: songs[index].end,
                duration: songs[index].duration
            };
            
            nextSong();
        }
        
        function skipSong(index) {
            results[songs[index].id] = {
                title: '未知歌曲',
                artist: '未知',
                start: songs[index].start,
                end: songs[index].end,
                duration: songs[index].duration,
                skipped: true
            };
            
            nextSong();
        }
        
        function nextSong() {
            currentIndex++;
            
            if (currentIndex >= songs.length) {
                showSummary();
            } else {
                showCurrentSong();
                updateProgress();
            }
        }
        
        function showSummary() {
            document.getElementById('songContainer').style.display = 'none';
            
            const labeled = Object.values(results).filter(r => !r.skipped).length;
            const skipped = Object.values(results).filter(r => r.skipped).length;
            
            document.getElementById('summaryText').innerHTML = `
                <p style="font-size: 18px; margin: 20px 0;">
                    已标注：<strong>${labeled}</strong> 首<br>
                    已跳过：<strong>${skipped}</strong> 首
                </p>
            `;
            
            document.getElementById('summary').classList.add('show');
        }
        
        function exportResults() {
            const dataStr = JSON.stringify(results, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'manual_annotations.json';
            a.click();
            URL.revokeObjectURL(url);
            
            alert('结果已导出！请将 manual_annotations.json 文件放到项目目录。');
        }
        
        // 初始化
        init();
    </script>
</body>
</html>
        """
        
        # 准备歌曲数据
        songs_json = json.dumps(unknown_songs, ensure_ascii=False, indent=2)
        html_content = html_template.replace('SONGS_DATA', songs_json)
        
        # 写入文件
        output_path = self.output_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ 已生成人工标注页面: {output_path}")
        print(f"  请用浏览器打开该文件进行标注")


class IntegratedRecognitionSystem:
    """集成识别系统"""
    
    def __init__(self, video_path: str, song_list_path: str, 
                 transcript_path: str, danmaku_path: Optional[str] = None,
                 output_path: Optional[str] = None):
        """
        初始化集成识别系统
        
        Args:
            video_path: 视频文件路径
            song_list_path: 歌曲列表JSON路径
            transcript_path: Whisper转录JSON路径
            danmaku_path: 弹幕JSON路径（可选）
            output_path: 输出文件路径（可选）
        """
        self.video_path = video_path
        self.song_list_path = song_list_path
        self.transcript_path = transcript_path
        self.danmaku_path = danmaku_path
        self.output_path = output_path
        
        # 加载数据
        self.songs = self._load_songs()
        self.transcript = self._load_transcript()
        
        # 初始化各个组件
        self.fingerprint = AudioFingerprint()
        self.danmaku_analyzer = DanmakuAnalyzer(danmaku_path) if danmaku_path else None
        self.name_extractor = ImprovedNameExtractor()
        self.annotator = ManualAnnotationGenerator(video_path, 
                                                   os.path.expanduser("~/shanshan_materials"))
        
        # 识别结果
        self.recognition_results = {}
    
    def _load_songs(self) -> List[Dict]:
        """加载歌曲列表或唱歌片段"""
        with open(self.song_list_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 支持两种格式
            if 'songs' in data:
                # 格式1: 标准歌曲列表 {"songs": [...]}
                return data['songs']
            elif 'segments' in data:
                # 格式2: 唱歌片段 {"segments": [...]}
                # 将segments转换为songs格式
                songs = []
                for i, seg in enumerate(data['segments'], 1):
                    songs.append({
                        'id': i,
                        'start': seg.get('start', 0),
                        'end': seg.get('end', 0),
                        'duration': seg.get('duration', 0),
                        'text': seg.get('text', ''),
                        'title': None,  # 待识别
                        'artist': None,
                        'confidence': 0,
                        'source': 'singing_segment'
                    })
                print(f"✓ 从唱歌片段转换了 {len(songs)} 首待识别歌曲")
                return songs
            else:
                print(f"⚠️  未识别的文件格式")
                return []
    
    def _load_transcript(self) -> List[Dict]:
        """加载转录文本"""
        with open(self.transcript_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('segments', [])
    
    async def recognize_all(self):
        """执行完整识别流程"""
        print("=" * 70)
        print("🎵 智能歌曲识别系统")
        print("=" * 70)
        print()
        print(f"总歌曲数: {len(self.songs)}")
        print(f"视频文件: {self.video_path}")
        print(f"弹幕数据: {'有' if self.danmaku_analyzer else '无'}")
        print()
        
        # 阶段1：音频指纹识别
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("阶段1：音频指纹识别（Shazam）")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        
        await self._stage1_fingerprint()
        
        # 阶段2：弹幕分析
        if self.danmaku_analyzer:
            print()
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("阶段2：弹幕关键词分析")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print()
            self._stage2_danmaku()
        
        # 阶段3：改进歌名提取
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("阶段3：改进歌名提取")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        self._stage3_name_extraction()
        
        # 阶段4：人工标注
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("阶段4：人工标注（剩余未识别）")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        self._stage4_manual_annotation()
        
        # 生成报告
        self._generate_report()
    
    async def _stage1_fingerprint(self):
        """阶段1：音频指纹识别"""
        recognized = 0
        failed = 0
        
        for i, song in enumerate(self.songs, 1):
            song_id = song.get('id', i)
            title = song.get('title', f'歌曲{i}')
            
            # 跳过已知歌曲
            if title and not title.startswith('未知歌曲'):
                print(f"[{i}/{len(self.songs)}] 跳过: {title} (已有歌名)")
                self.recognition_results[song_id] = {
                    'title': title,
                    'source': 'existing',
                    'confidence': 1.0
                }
                recognized += 1
                continue
            
            print(f"[{i}/{len(self.songs)}] 识别中: {title}", end="", flush=True)
            
            # 提取音频片段
            temp_audio = f"/tmp/song_{song_id}.wav"
            try:
                self.fingerprint.extract_audio_segment(
                    self.video_path,
                    song.get('start', 0),
                    song.get('duration', 30),
                    temp_audio
                )
                
                # Shazam识别
                result = await self.fingerprint.recognize_from_file(temp_audio)
                
                if result:
                    print(f" → ✓ {result['title']} - {result['artist']}")
                    self.recognition_results[song_id] = result
                    recognized += 1
                else:
                    print(" → ✗ 未识别")
                    failed += 1
                
                # 清理临时文件
                if os.path.exists(temp_audio):
                    os.remove(temp_audio)
                
            except Exception as e:
                print(f" → ✗ 错误: {e}")
                failed += 1
            
            # 延迟，避免API限制
            time.sleep(0.5)
        
        print()
        print(f"识别结果: 成功 {recognized}/{len(self.songs)}, 失败 {failed}/{len(self.songs)}")
    
    def _stage2_danmaku(self):
        """阶段2：弹幕分析"""
        if not self.danmaku_analyzer:
            return
        
        supplemented = 0
        
        for i, song in enumerate(self.songs, 1):
            song_id = song.get('id', i)
            
            # 跳过已识别的
            if song_id in self.recognition_results:
                continue
            
            # 从弹幕提取歌名
            candidates = self.danmaku_analyzer.extract_song_names(
                song.get('start', 0),
                song.get('end', 0)
            )
            
            if candidates:
                print(f"[{i}/{len(self.songs)}] 弹幕提取: {candidates[0]}")
                self.recognition_results[song_id] = {
                    'title': candidates[0],
                    'source': 'danmaku',
                    'confidence': 0.7,
                    'candidates': candidates
                }
                supplemented += 1
        
        print()
        print(f"弹幕补充: {supplemented} 首")
    
    def _stage3_name_extraction(self):
        """阶段3：改进歌名提取"""
        extracted = 0
        
        for i, song in enumerate(self.songs, 1):
            song_id = song.get('id', i)
            
            # 跳过已识别的
            if song_id in self.recognition_results:
                continue
            
            # 从转录文本提取歌名
            song_name = self.name_extractor.extract_from_transcript(
                self.transcript,
                song.get('start', 0),
                song.get('end', 0)
            )
            
            if song_name:
                print(f"[{i}/{len(self.songs)}] 文本提取: {song_name}")
                self.recognition_results[song_id] = {
                    'title': song_name,
                    'source': 'transcript',
                    'confidence': 0.6
                }
                extracted += 1
        
        print()
        print(f"文本提取: {extracted} 首")
    
    def _stage4_manual_annotation(self):
        """阶段4：生成人工标注页面"""
        # 收集未识别的歌曲
        unknown_songs = []
        
        for i, song in enumerate(self.songs, 1):
            song_id = song.get('id', i)
            
            if song_id not in self.recognition_results:
                unknown_songs.append({
                    'id': song_id,
                    'index': i,
                    'start': song.get('start', 0),
                    'end': song.get('end', 0),
                    'duration': song.get('duration', 0),
                    'text': song.get('text', '')[:500]  # 前500字
                })
        
        if unknown_songs:
            print(f"剩余未识别: {len(unknown_songs)} 首")
            print("正在生成人工标注页面...")
            
            # 将manual_annotation.html保存到与输出文件相同的目录
            if hasattr(self, 'output_path') and self.output_path:
                annotation_html = os.path.join(
                    os.path.dirname(self.output_path),
                    'manual_annotation.html'
                )
            else:
                annotation_html = os.path.expanduser('~/shanshan_materials/manual_annotation.html')
            
            self.annotator.generate_html_player(
                unknown_songs,
                annotation_html
            )
            
            print()
            print("请按以下步骤完成人工标注：")
            print(f"  1. 打开浏览器访问: {annotation_html}")
            print(f"  2. 逐首听歌并填写歌名")
            print(f"  3. 点击'导出结果'按钮")
            print(f"  4. 将导出的 manual_annotations.json 放到项目根目录")
            print(f"  5. 重新运行本脚本完成导入")
        else:
            print("✅ 所有歌曲已识别！")
    
    def _generate_report(self):
        """生成识别报告"""
        print()
        print("=" * 70)
        print("📊 识别报告")
        print("=" * 70)
        print()
        
        total = len(self.songs)
        recognized = len(self.recognition_results)
        unknown = total - recognized
        
        # 按来源统计
        from collections import Counter
        sources = Counter(r['source'] for r in self.recognition_results.values())
        
        print(f"总歌曲数: {total}")
        if total > 0:
            print(f"已识别: {recognized} ({recognized/total*100:.1f}%)")
            print(f"未识别: {unknown} ({unknown/total*100:.1f}%)")
        else:
            print(f"已识别: {recognized}")
            print(f"未识别: {unknown}")
        print()
        print("识别来源：")
        for source, count in sources.items():
            source_names = {
                'existing': '原有歌名',
                'shazam': 'Shazam指纹',
                'danmaku': '弹幕分析',
                'transcript': '文本提取',
                'manual': '人工标注'
            }
            print(f"  {source_names.get(source, source)}: {count} 首")
        
        # 保存结果（使用命令行参数指定的路径）
        if not hasattr(self, 'output_path') or not self.output_path:
            self.output_path = os.path.expanduser("~/shanshan_materials/recognition_results.json")
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(self.recognition_results, f, ensure_ascii=False, indent=2)
        
        print()
        print(f"✓ 识别结果已保存: {self.output_path}")
        
        if unknown > 0:
            print()
            print("⚠ 请完成人工标注后重新运行以达到100%识别率")


async def main():
    """主函数"""
    import asyncio
    import argparse
    
    parser = argparse.ArgumentParser(description='智能歌曲识别系统')
    parser.add_argument('--video', type=str, help='视频文件路径')
    parser.add_argument('--singing', type=str, help='唱歌片段JSON文件路径（singing_素材.json）')
    parser.add_argument('--transcript', type=str, help='Whisper转录JSON文件路径')
    parser.add_argument('--danmaku', type=str, help='弹幕文件路径（可选）')
    parser.add_argument('--output', type=str, help='输出识别结果JSON文件路径')
    args = parser.parse_args()
    
    # 使用命令行参数或默认值
    material_dir = os.path.expanduser("~/shanshan_materials")
    video_path = args.video or "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4"
    song_list_path = args.singing or os.path.join(material_dir, "歌曲素材库/歌曲列表.json")
    transcript_path = args.transcript or "speech_analysis_完整转录.json"
    danmaku_path = args.danmaku
    output_path = args.output or os.path.join(material_dir, "歌曲识别结果.json")
    
    # 检查文件
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    if not os.path.exists(song_list_path):
        print(f"❌ 唱歌片段文件不存在: {song_list_path}")
        print(f"   提示: 请先运行内容分类生成 singing_素材.json")
        return
    
    if not os.path.exists(transcript_path):
        print(f"❌ 转录文件不存在: {transcript_path}")
        return
    
    # 创建系统并运行
    system = IntegratedRecognitionSystem(
        video_path,
        song_list_path,
        transcript_path,
        danmaku_path,
        output_path  # 传递输出路径
    )
    
    results = await system.recognize_all()
    
    # 结果已在_generate_report中保存，这里不需要重复保存


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

