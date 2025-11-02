#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
未识别歌曲清单生成器

功能：
1. 找出所有未被Shazam识别的歌曲
2. 生成人工标注清单（HTML+JSON）
3. 提供音频试听和歌词参考
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

class UnrecognizedSongLister:
    """未识别歌曲清单生成器"""
    
    def __init__(self):
        self.material_dir = os.path.expanduser("~/shanshan_materials")
        self.video_file = None
        self.unrecognized_songs = []
    
    def find_video_file(self):
        """查找录播视频文件"""
        downloads_dir = "/home/liu/app_github/DouyinLiveRecorder/downloads"
        
        # 查找最新的观山视频
        video_files = []
        if os.path.exists(downloads_dir):
            for file in os.listdir(downloads_dir):
                if file.startswith("观山") and file.endswith(".mp4"):
                    video_path = os.path.join(downloads_dir, file)
                    video_files.append((video_path, os.path.getmtime(video_path)))
        
        if video_files:
            # 返回最新的
            self.video_file = max(video_files, key=lambda x: x[1])[0]
            return True
        
        return False
    
    def load_recognition_results(self):
        """加载识别结果"""
        results_file = os.path.join(self.material_dir, "recognition_results.json")
        
        if not os.path.exists(results_file):
            print("⚠️  未找到 recognition_results.json")
            print("   请先运行: python3 智能歌曲识别系统.py")
            return False
        
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 找出未识别的歌曲
        for song in data.get('songs', []):
            if not song.get('recognized', False):
                self.unrecognized_songs.append(song)
        
        print(f"\n找到 {len(self.unrecognized_songs)} 首未识别歌曲")
        return True
    
    def extract_audio_clips(self, output_dir):
        """提取未识别歌曲的音频片段"""
        
        if not self.video_file:
            print("⚠️  未找到视频文件")
            return False
        
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n开始提取音频片段...")
        
        for i, song in enumerate(self.unrecognized_songs, 1):
            start_time = song['start_time']
            duration = min(song['duration'], 45)  # 最多45秒
            
            output_file = os.path.join(output_dir, f"未识别_{i:03d}.mp3")
            
            # 使用FFmpeg提取
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-i', self.video_file,
                '-t', str(duration),
                '-vn',  # 不要视频
                '-acodec', 'libmp3lame',
                '-ab', '192k',
                '-y',
                output_file
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                song['audio_file'] = f"未识别_{i:03d}.mp3"
                print(f"  ✓ {i}/{len(self.unrecognized_songs)}: {output_file}")
            except Exception as e:
                print(f"  ✗ {i}/{len(self.unrecognized_songs)}: 提取失败")
                song['audio_file'] = None
        
        return True
    
    def generate_html_list(self, output_file, audio_dir):
        """生成HTML标注清单"""
        
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>未识别歌曲人工标注清单</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .stats {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        .song-item {
            background: white;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .song-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .song-number {
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
        }
        .song-time {
            color: #666;
            font-size: 14px;
        }
        .lyrics-preview {
            background: #f9f9f9;
            padding: 15px;
            border-left: 4px solid #4CAF50;
            margin: 15px 0;
            font-family: monospace;
            white-space: pre-wrap;
            max-height: 150px;
            overflow-y: auto;
        }
        .input-section {
            margin-top: 15px;
        }
        .input-section label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .input-section input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        .input-section input:focus {
            outline: none;
            border-color: #4CAF50;
        }
        audio {
            width: 100%;
            margin: 10px 0;
        }
        .export-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            padding: 15px 30px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 18px;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            z-index: 1000;
        }
        .export-btn:hover {
            background: #45a049;
        }
        .progress {
            position: fixed;
            bottom: 100px;
            right: 30px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            z-index: 1000;
        }
    </style>
</head>
<body>
    <h1>🎵 未识别歌曲人工标注清单</h1>
    
    <div class="stats">
        <h2>统计信息</h2>
        <p><strong>未识别歌曲数：</strong>""" + str(len(self.unrecognized_songs)) + """首</p>
        <p><strong>生成时间：</strong>""" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        <p style="color: #666; font-size: 14px;">提示：请仔细听每首歌，填写正确的歌名和歌手</p>
    </div>
    
    <div id="song-list">
"""
        
        for i, song in enumerate(self.unrecognized_songs, 1):
            # 格式化时间
            start_min = int(song['start_time'] // 60)
            start_sec = int(song['start_time'] % 60)
            duration_sec = int(song['duration'])
            
            # 歌词预览（前200字符）
            lyrics_preview = song.get('text', '暂无歌词')[:200]
            if len(song.get('text', '')) > 200:
                lyrics_preview += "..."
            
            # 音频路径
            audio_path = ""
            if song.get('audio_file'):
                audio_path = f"未识别歌曲音频/{song['audio_file']}"
            
            html += f"""
        <div class="song-item">
            <div class="song-header">
                <span class="song-number">#{i:03d}</span>
                <span class="song-time">
                    ⏱ 时间: {start_min:02d}:{start_sec:02d} | 时长: {duration_sec}秒
                </span>
            </div>
            
            {"<audio controls><source src='" + audio_path + "' type='audio/mpeg'>您的浏览器不支持音频播放</audio>" if audio_path else "<p style='color: #999;'>⚠️ 音频文件未生成</p>"}
            
            <div class="lyrics-preview">
                <strong>歌词参考：</strong><br>
                {lyrics_preview}
            </div>
            
            <div class="input-section">
                <label>歌曲名：</label>
                <input type="text" id="song_name_{i}" placeholder="请填写歌曲名">
            </div>
            
            <div class="input-section">
                <label>歌手名：</label>
                <input type="text" id="artist_{i}" placeholder="请填写歌手名（可选）">
            </div>
        </div>
"""
        
        html += """
    </div>
    
    <div class="progress">
        <strong>标注进度：</strong><br>
        <span id="progress-text">0 / """ + str(len(self.unrecognized_songs)) + """</span>
    </div>
    
    <button class="export-btn" onclick="exportResults()">💾 导出结果</button>
    
    <script>
        // 监听输入变化，更新进度
        const totalSongs = """ + str(len(self.unrecognized_songs)) + """;
        let completedCount = 0;
        
        for (let i = 1; i <= totalSongs; i++) {
            const input = document.getElementById(`song_name_${i}`);
            if (input) {
                input.addEventListener('input', updateProgress);
            }
        }
        
        function updateProgress() {
            completedCount = 0;
            for (let i = 1; i <= totalSongs; i++) {
                const input = document.getElementById(`song_name_${i}`);
                if (input && input.value.trim()) {
                    completedCount++;
                }
            }
            document.getElementById('progress-text').textContent = 
                `${completedCount} / ${totalSongs}`;
        }
        
        function exportResults() {
            const results = [];
            
            for (let i = 1; i <= totalSongs; i++) {
                const songName = document.getElementById(`song_name_${i}`).value.trim();
                const artist = document.getElementById(`artist_${i}`).value.trim();
                
                if (songName) {
                    results.push({
                        index: i,
                        song_name: songName,
                        artist: artist || "未知"
                    });
                }
            }
            
            if (results.length === 0) {
                alert('请至少标注一首歌曲！');
                return;
            }
            
            // 生成JSON
            const json = JSON.stringify(results, null, 2);
            
            // 下载文件
            const blob = new Blob([json], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'manual_annotations.json';
            a.click();
            
            alert(`成功导出 ${results.length} 首歌曲标注！\\n文件已保存为：manual_annotations.json`);
        }
    </script>
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✅ HTML清单已生成: {output_file}")
    
    def generate_text_list(self, output_file):
        """生成纯文本清单"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("未识别歌曲清单\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"未识别数量: {len(self.unrecognized_songs)} 首\n\n")
            
            for i, song in enumerate(self.unrecognized_songs, 1):
                start_min = int(song['start_time'] // 60)
                start_sec = int(song['start_time'] % 60)
                duration = int(song['duration'])
                
                f.write(f"【{i:03d}】\n")
                f.write(f"时间: {start_min:02d}:{start_sec:02d}\n")
                f.write(f"时长: {duration}秒\n")
                f.write(f"歌词: {song.get('text', '暂无')[:100]}...\n")
                f.write(f"歌名: _________________\n")
                f.write(f"歌手: _________________\n")
                f.write("\n")
        
        print(f"✅ 文本清单已生成: {output_file}")

def main():
    """主函数"""
    print("=" * 80)
    print("未识别歌曲清单生成器")
    print("=" * 80)
    print()
    
    lister = UnrecognizedSongLister()
    
    # 1. 加载识别结果
    if not lister.load_recognition_results():
        return
    
    if len(lister.unrecognized_songs) == 0:
        print("✅ 所有歌曲都已识别，无需人工标注！")
        return
    
    # 2. 查找视频文件
    print("\n查找视频文件...")
    if not lister.find_video_file():
        print("⚠️  未找到视频文件，将生成不含音频的清单")
    else:
        print(f"✓ 找到视频: {lister.video_file}")
    
    # 3. 提取音频片段
    audio_dir = os.path.expanduser("~/shanshan_materials/未识别歌曲音频")
    if lister.video_file:
        lister.extract_audio_clips(audio_dir)
    
    # 4. 生成HTML清单
    html_file = os.path.expanduser("~/shanshan_materials/未识别歌曲标注清单.html")
    lister.generate_html_list(html_file, audio_dir)
    
    # 5. 生成文本清单
    text_file = os.path.expanduser("~/shanshan_materials/未识别歌曲清单.txt")
    lister.generate_text_list(text_file)
    
    print()
    print("=" * 80)
    print("✅ 清单生成完成！")
    print("=" * 80)
    print()
    print("📄 文件位置：")
    print(f"   HTML清单: {html_file}")
    print(f"   文本清单: {text_file}")
    if lister.video_file:
        print(f"   音频片段: {audio_dir}/")
    print()
    print("📝 使用说明：")
    print("   1. 用浏览器打开HTML清单")
    print("   2. 听每首歌，填写歌名和歌手")
    print("   3. 点击"导出结果"保存为 manual_annotations.json")
    print("   4. 将JSON文件用于后续歌词获取")
    print()

if __name__ == "__main__":
    main()



