#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频集锦生成器

功能：
- 生成7种视频集锦
- 智能片段选择
- 自动转场
- 多种输出格式
"""

import os
import json
import logging
import subprocess
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import random
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class VideoMontageGenerator:
    """视频集锦生成器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 输出质量
        self.quality = self.config.get('quality', 'high')  # high/medium/low
        self.resolution = self.config.get('resolution', '1080p')
        
        # 转场效果
        self.transition = self.config.get('transition', 'fade')  # fade/dissolve/wipe
        self.transition_duration = self.config.get('transition_duration', 1.0)
        
        # FFmpeg预设
        self.ffmpeg_preset = {
            'high': 'slow',
            'medium': 'medium',
            'low': 'fast'
        }.get(self.quality, 'medium')
    
    def generate_song_montage(
        self,
        video_path: str,
        songs_data: List[Dict],
        output_dir: str,
        version: str = 'full'
    ) -> Dict[str, str]:
        """
        生成唱歌集锦
        
        Args:
            video_path: 原始视频路径
            songs_data: 歌曲数据列表
            output_dir: 输出目录
            version: 版本
                - 'full': 完整版（所有歌曲完整演唱）
                - 'highlight': 高潮版（每首歌只取高潮部分）
                - 'best': 精选版（只选最好的10首）
        
        Returns:
            生成的文件路径
        """
        logger.info(f"生成唱歌集锦 - {version}版本")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 根据版本筛选和处理歌曲
        if version == 'full':
            segments = self._prepare_full_songs(songs_data)
            output_name = "唱歌集锦_完整版.mp4"
            target_duration = None  # 不限制时长
        elif version == 'highlight':
            segments = self._prepare_highlight_songs(songs_data)
            output_name = "唱歌集锦_高潮版.mp4"
            target_duration = 600  # 10分钟
        else:  # best
            segments = self._prepare_best_songs(songs_data, top_n=10)
            output_name = "唱歌集锦_精选版.mp4"
            target_duration = 300  # 5分钟
        
        if not segments:
            logger.warning("没有可用的歌曲片段")
            return {}
        
        output_path = os.path.join(output_dir, output_name)
        
        # 生成集锦
        success = self._concat_segments_with_transition(
            video_path,
            segments,
            output_path
        )
        
        if success:
            return {'path': output_path, 'version': version}
        return {}
    
    def generate_thank_montage(
        self,
        video_path: str,
        gift_data: List[Dict],
        output_dir: str,
        min_value: int = 1000
    ) -> Optional[str]:
        """
        生成感谢集锦
        
        Args:
            video_path: 原始视频路径
            gift_data: 礼物数据列表
            output_dir: 输出目录
            min_value: 最小礼物价值（抖音币）
        
        Returns:
            输出文件路径
        """
        logger.info(f"生成感谢集锦（礼物价值≥{min_value}）")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 筛选高价值礼物
        high_value_gifts = [
            gift for gift in gift_data
            if gift.get('total_value', 0) >= min_value
        ]
        
        if not high_value_gifts:
            logger.warning(f"没有价值≥{min_value}的礼物")
            return None
        
        # 准备片段（每个礼物前后各5秒）
        segments = []
        for gift in high_value_gifts:
            segments.append({
                'start': gift['timestamp'] - 5,
                'duration': 10,
                'description': f"{gift['user']} 送出 {gift['gift_name']}"
            })
        
        output_path = os.path.join(output_dir, "感谢集锦.mp4")
        
        success = self._concat_segments_with_transition(
            video_path,
            segments,
            output_path
        )
        
        return output_path if success else None
    
    def generate_upgrade_montage(
        self,
        upgrade_videos_dir: str,
        output_dir: str
    ) -> Optional[str]:
        """
        生成升级集锦
        
        Args:
            upgrade_videos_dir: 升级视频目录
            output_dir: 输出目录
        
        Returns:
            输出文件路径
        """
        logger.info("生成升级集锦")
        
        if not os.path.exists(upgrade_videos_dir):
            logger.warning(f"升级视频目录不存在: {upgrade_videos_dir}")
            return None
        
        # 查找所有完整版升级视频
        import glob
        upgrade_videos = glob.glob(
            os.path.join(upgrade_videos_dir, "*完整版.mp4")
        )
        
        if not upgrade_videos:
            logger.warning("没有升级视频")
            return None
        
        logger.info(f"找到 {len(upgrade_videos)} 个升级视频")
        
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "升级合集.mp4")
        
        # 直接拼接升级视频
        success = self._concat_video_files(upgrade_videos, output_path)
        
        return output_path if success else None
    
    def generate_chat_montage(
        self,
        video_path: str,
        chat_data: List[Dict],
        output_dir: str,
        max_duration: int = 180
    ) -> Optional[str]:
        """
        生成聊天集锦
        
        Args:
            video_path: 原始视频路径
            chat_data: 聊天数据列表
            output_dir: 输出目录
            max_duration: 最大时长（秒）
        
        Returns:
            输出文件路径
        """
        logger.info("生成聊天集锦")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 选择有趣的聊天片段
        interesting_chats = self._select_interesting_chats(chat_data)
        
        if not interesting_chats:
            logger.warning("没有有趣的聊天片段")
            return None
        
        # 限制总时长
        segments = []
        total_duration = 0
        
        for chat in interesting_chats:
            duration = chat.get('duration', 10)
            if total_duration + duration > max_duration:
                break
            
            segments.append({
                'start': chat['start'],
                'duration': duration,
                'description': chat.get('text', '')[:50]
            })
            total_duration += duration
        
        output_path = os.path.join(output_dir, "聊天集锦.mp4")
        
        success = self._concat_segments_with_transition(
            video_path,
            segments,
            output_path
        )
        
        return output_path if success else None
    
    def generate_daily_montage(
        self,
        video_path: str,
        daily_data: List[Dict],
        output_dir: str,
        max_duration: int = 300
    ) -> Optional[str]:
        """
        生成日常集锦
        
        Args:
            video_path: 原始视频路径
            daily_data: 日常片段数据列表
            output_dir: 输出目录
            max_duration: 最大时长（秒）
        
        Returns:
            输出文件路径
        """
        logger.info("生成日常集锦")
        
        os.makedirs(output_dir, exist_ok=True)
        
        if not daily_data:
            logger.warning("没有日常片段")
            return None
        
        # 选择日常片段（开场、结束、休息等）
        segments = []
        total_duration = 0
        
        # 优先选择开场和结束
        for daily in daily_data:
            text = daily.get('text', '').lower()
            duration = daily.get('duration', 10)
            
            # 如果达到最大时长，停止
            if total_duration + duration > max_duration:
                break
            
            # 开场片段（优先级高）
            if any(k in text for k in ['开始', '来了', '上播', '大家好']):
                segments.insert(0, {  # 插入到开头
                    'start': daily['start'],
                    'duration': min(duration, 15),  # 最多15秒
                    'description': '开场'
                })
                total_duration += min(duration, 15)
            # 结束片段（优先级高）
            elif any(k in text for k in ['下播', '拜拜', '再见', '结束']):
                segments.append({
                    'start': daily['start'],
                    'duration': min(duration, 15),
                    'description': '结束'
                })
                total_duration += min(duration, 15)
            # 其他日常片段
            elif total_duration < max_duration * 0.7:  # 前70%时长可以添加其他日常
                segments.append({
                    'start': daily['start'],
                    'duration': min(duration, 10),
                    'description': text[:20]
                })
                total_duration += min(duration, 10)
        
        if not segments:
            logger.warning("没有可用的日常片段")
            return None
        
        output_path = os.path.join(output_dir, "日常集锦.mp4")
        
        success = self._concat_segments_with_transition(
            video_path,
            segments,
            output_path
        )
        
        return output_path if success else None
    
    def generate_highlight_montage(
        self,
        video_path: str,
        all_materials: Dict,
        output_dir: str,
        max_duration: int = 300
    ) -> Optional[str]:
        """
        生成精彩时刻集锦
        
        综合所有类型的精彩片段
        
        Args:
            video_path: 原始视频路径
            all_materials: 所有素材数据
            output_dir: 输出目录
            max_duration: 最大时长（秒）
        
        Returns:
            输出文件路径
        """
        logger.info("生成精彩时刻集锦")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 收集所有精彩片段
        highlights = []
        
        # 1. 最好的歌曲（前3首）
        if 'songs' in all_materials:
            top_songs = self._prepare_best_songs(all_materials['songs'], top_n=3)
            highlights.extend(top_songs)
        
        # 2. 升级事件
        if 'upgrades' in all_materials:
            for upgrade in all_materials['upgrades']:
                highlights.append({
                    'start': upgrade['timestamp'] - 3,
                    'duration': 8,
                    'score': 10,  # 升级很重要
                    'type': 'upgrade'
                })
        
        # 3. 高价值礼物
        if 'gifts' in all_materials:
            for gift in all_materials['gifts']:
                if gift.get('total_value', 0) >= 3000:  # ≥3000抖音币
                    highlights.append({
                        'start': gift['timestamp'] - 2,
                        'duration': 6,
                        'score': 8,
                        'type': 'gift'
                    })
        
        # 按评分排序
        highlights.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # 限制总时长
        segments = []
        total_duration = 0
        
        for highlight in highlights:
            duration = highlight['duration']
            if total_duration + duration > max_duration:
                break
            
            segments.append(highlight)
            total_duration += duration
        
        if not segments:
            logger.warning("没有精彩片段")
            return None
        
        output_path = os.path.join(output_dir, "精彩时刻.mp4")
        
        success = self._concat_segments_with_transition(
            video_path,
            segments,
            output_path
        )
        
        return output_path if success else None
    
    def generate_daily_essence(
        self,
        video_path: str,
        all_materials: Dict,
        output_dir: str
    ) -> Optional[str]:
        """
        生成每日精华
        
        最精华的3-5分钟内容，适合发朋友圈/微博
        
        Args:
            video_path: 原始视频路径
            all_materials: 所有素材数据
            output_dir: 输出目录
        
        Returns:
            输出文件路径
        """
        logger.info("生成每日精华")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 选择最精华的片段
        segments = []
        
        # 1. 开场（前30秒）
        segments.append({
            'start': 0,
            'duration': 30,
            'description': '开场'
        })
        
        # 2. 最好的一首歌（取高潮部分）
        if 'songs' in all_materials and all_materials['songs']:
            best_song = all_materials['songs'][0]
            # 假设高潮在歌曲中段
            song_start = best_song['start']
            song_duration = best_song.get('duration', 180)
            highlight_start = song_start + song_duration * 0.4
            
            segments.append({
                'start': highlight_start,
                'duration': 60,
                'description': f"歌曲: {best_song.get('name', '未知')}"
            })
        
        # 3. 升级事件（如果有）
        if 'upgrades' in all_materials and all_materials['upgrades']:
            upgrade = all_materials['upgrades'][0]
            segments.append({
                'start': upgrade['timestamp'] - 2,
                'duration': 8,
                'description': f"升级: {upgrade['user']} {upgrade['level']}级"
            })
        
        # 4. 感谢高价值礼物
        if 'gifts' in all_materials:
            top_gift = max(
                all_materials['gifts'],
                key=lambda x: x.get('total_value', 0),
                default=None
            )
            if top_gift and top_gift.get('total_value', 0) >= 5000:
                segments.append({
                    'start': top_gift['timestamp'] - 2,
                    'duration': 6,
                    'description': f"礼物: {top_gift['gift_name']}"
                })
        
        # 5. 结尾（最后20秒）
        # 需要知道视频总时长
        # 这里假设结尾有告别
        
        output_path = os.path.join(output_dir, "每日精华.mp4")
        
        success = self._concat_segments_with_transition(
            video_path,
            segments,
            output_path
        )
        
        return output_path if success else None
    
    def generate_short_videos(
        self,
        video_path: str,
        all_materials: Dict,
        output_dir: str,
        count: int = 5
    ) -> List[str]:
        """
        生成短视频素材
        
        ✅ 竖屏3:4比例，15-60秒，适合抖音/快手/视频号
        （从9:16改为3:4，横向更宽，更适合横屏直播裁剪）
        
        Args:
            video_path: 原始视频路径
            all_materials: 所有素材数据
            output_dir: 输出目录
            count: 生成数量
        
        Returns:
            输出文件路径列表
        """
        logger.info(f"生成 {count} 个短视频素材")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 选择适合短视频的片段
        candidates = []
        
        # 1. 歌曲片段（高潮部分）
        if 'songs' in all_materials:
            for i, song in enumerate(all_materials['songs'][:10]):
                song_start = song['start']
                song_duration = song.get('duration', 180)
                highlight_start = song_start + song_duration * 0.4
                
                candidates.append({
                    'start': highlight_start,
                    'duration': 30,
                    'type': 'song',
                    'score': 10 - i,  # 前面的歌更好
                    'description': song.get('name', f'歌曲{i+1}')
                })
        
        # 2. 升级片段
        if 'upgrades' in all_materials:
            for upgrade in all_materials['upgrades']:
                candidates.append({
                    'start': upgrade['timestamp'] - 3,
                    'duration': 15,
                    'type': 'upgrade',
                    'score': 9,
                    'description': f"升级_{upgrade['level']}级"
                })
        
        # 3. 高价值礼物片段
        if 'gifts' in all_materials:
            high_value_gifts = [
                g for g in all_materials['gifts']
                if g.get('total_value', 0) >= 5000
            ]
            for gift in high_value_gifts:
                candidates.append({
                    'start': gift['timestamp'] - 2,
                    'duration': 15,
                    'type': 'gift',
                    'score': 8,
                    'description': f"礼物_{gift['gift_name']}"
                })
        
        # 按评分排序
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # 生成短视频
        output_files = []
        
        for i, candidate in enumerate(candidates[:count]):
            output_name = f"短视频_{i+1:02d}_{candidate['description']}.mp4"
            output_path = os.path.join(output_dir, output_name)
            
            # 转换为竖屏
            success = self._create_short_video(
                video_path,
                candidate['start'],
                candidate['duration'],
                output_path
            )
            
            if success:
                output_files.append(output_path)
        
        logger.info(f"成功生成 {len(output_files)} 个短视频")
        
        return output_files
    
    def _prepare_full_songs(self, songs_data: List[Dict]) -> List[Dict]:
        """准备完整歌曲片段"""
        segments = []
        for song in songs_data:
            segments.append({
                'start': song['start'],
                'duration': song.get('duration', 180),
                'description': song.get('name', '未知歌曲')
            })
        return segments
    
    def _prepare_highlight_songs(self, songs_data: List[Dict]) -> List[Dict]:
        """准备歌曲高潮片段"""
        segments = []
        for song in songs_data:
            # 高潮通常在歌曲的40%-70%处
            song_start = song['start']
            song_duration = song.get('duration', 180)
            highlight_start = song_start + song_duration * 0.4
            highlight_duration = min(60, song_duration * 0.3)
            
            segments.append({
                'start': highlight_start,
                'duration': highlight_duration,
                'description': song.get('name', '未知歌曲') + '_高潮'
            })
        return segments
    
    def _prepare_best_songs(self, songs_data: List[Dict], top_n: int = 10) -> List[Dict]:
        """准备精选歌曲"""
        # 按某种评分排序（这里简单地取前N首）
        # 实际应该考虑：音准、完整度、观众反应等
        best_songs = songs_data[:top_n]
        return self._prepare_full_songs(best_songs)
    
    def _select_interesting_chats(self, chat_data: List[Dict]) -> List[Dict]:
        """选择有趣的聊天片段"""
        # 简单实现：选择文本较长的聊天
        # 实际应该考虑：互动性、情绪、话题等
        interesting = [
            chat for chat in chat_data
            if len(chat.get('text', '')) > 20
        ]
        return interesting[:20]  # 最多20个
    
    def _concat_segments_with_transition(
        self,
        video_path: str,
        segments: List[Dict],
        output_path: str
    ) -> bool:
        """
        拼接视频片段（带转场）
        
        Args:
            video_path: 原始视频路径
            segments: 片段列表
            output_path: 输出路径
        
        Returns:
            是否成功
        """
        if not segments:
            return False
        
        try:
            # 1. 提取所有片段
            temp_dir = os.path.join(os.path.dirname(output_path), 'temp_segments')
            os.makedirs(temp_dir, exist_ok=True)
            
            segment_files = []
            
            for i, segment in enumerate(segments):
                temp_file = os.path.join(temp_dir, f"segment_{i:03d}.mp4")
                
                # 提取片段
                cmd = [
                    'ffmpeg',
                    '-ss', str(segment['start']),
                    '-i', video_path,
                    '-t', str(segment['duration']),
                    '-c', 'copy',
                    '-y',
                    temp_file
                ]
                
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=300
                )
                
                if result.returncode == 0 and os.path.exists(temp_file):
                    segment_files.append(temp_file)
            
            if not segment_files:
                logger.error("没有成功提取任何片段")
                return False
            
            # 2. 拼接片段（带转场）
            success = self._concat_with_ffmpeg(segment_files, output_path)
            
            # 3. 清理临时文件
            for f in segment_files:
                try:
                    os.remove(f)
                except:
                    pass
            
            try:
                os.rmdir(temp_dir)
            except:
                pass
            
            return success
            
        except Exception as e:
            logger.error(f"拼接片段失败: {e}")
            return False
    
    def _concat_video_files(
        self,
        video_files: List[str],
        output_path: str
    ) -> bool:
        """直接拼接视频文件"""
        try:
            # 创建文件列表
            list_file = output_path + '.filelist.txt'
            
            with open(list_file, 'w', encoding='utf-8') as f:
                for video_file in video_files:
                    f.write(f"file '{os.path.abspath(video_file)}'\n")
            
            # FFmpeg拼接
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file,
                '-c', 'copy',
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=600
            )
            
            # 清理
            if os.path.exists(list_file):
                os.remove(list_file)
            
            return result.returncode == 0 and os.path.exists(output_path)
            
        except Exception as e:
            logger.error(f"拼接视频文件失败: {e}")
            return False
    
    def _concat_with_ffmpeg(
        self,
        video_files: List[str],
        output_path: str
    ) -> bool:
        """使用FFmpeg拼接（简化版，无转场）"""
        # 转场效果需要复杂的FFmpeg filter
        # 这里先实现简单拼接
        return self._concat_video_files(video_files, output_path)
    
    def _detect_face_position(
        self,
        video_path: str,
        start: float,
        duration: float,
        sample_count: int = 5
    ) -> Optional[Tuple[int, int]]:
        """
        检测视频片段中的人脸位置
        
        Args:
            video_path: 视频路径
            start: 开始时间
            duration: 持续时间
            sample_count: 采样帧数
        
        Returns:
            人脸中心位置 (x, y)，如果未检测到则返回None
        """
        try:
            # 加载OpenCV人脸检测器
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            face_positions = []
            
            # 在视频片段中均匀采样
            for i in range(sample_count):
                # 计算采样时间点
                sample_time = start + (duration * i / (sample_count - 1) if sample_count > 1 else 0)
                frame_num = int(sample_time * fps)
                
                # 定位到指定帧
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # 转换为灰度图
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # 检测人脸
                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                
                # 如果检测到人脸，记录最大的人脸中心位置
                if len(faces) > 0:
                    # 选择最大的人脸
                    largest_face = max(faces, key=lambda f: f[2] * f[3])
                    x, y, w, h = largest_face
                    face_center_x = x + w // 2
                    face_center_y = y + h // 2
                    face_positions.append((face_center_x, face_center_y))
            
            cap.release()
            
            # 如果检测到人脸，返回平均位置
            if face_positions:
                avg_x = int(np.mean([pos[0] for pos in face_positions]))
                avg_y = int(np.mean([pos[1] for pos in face_positions]))
                logger.info(f"✅ 检测到人脸位置: ({avg_x}, {avg_y}), 采样 {len(face_positions)}/{sample_count} 帧")
                return (avg_x, avg_y)
            else:
                logger.debug(f"⚠️  未检测到人脸，使用默认中央裁剪")
                return None
                
        except Exception as e:
            logger.warning(f"人脸检测失败: {e}，使用默认中央裁剪")
            return None
    
    def _create_short_video(
        self,
        video_path: str,
        start: float,
        duration: float,
        output_path: str
    ) -> bool:
        """
        创建竖屏短视频（支持人脸跟踪中央定位）
        
        Args:
            video_path: 原始视频路径
            start: 开始时间
            duration: 时长
            output_path: 输出路径
        
        Returns:
            是否成功
        """
        try:
            # 获取视频分辨率
            probe_cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'json',
                video_path
            ]
            
            probe_result = subprocess.run(
                probe_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            
            import json
            probe_data = json.loads(probe_result.stdout)
            width = probe_data['streams'][0]['width']
            height = probe_data['streams'][0]['height']
            
            # ✅ 修复：使用3:4比例（更适合横屏直播裁剪为竖屏）
            # 原9:16太窄（608px），现改为3:4（810px）
            # 目标宽高比: 3:4 = 0.75
            target_ratio = 3 / 4  # ✅ 从9:16改为3:4，增加横向宽度
            source_ratio = width / height
            
            # ✅ 新功能：人脸检测，调整裁剪区域让人脸居中
            face_position = self._detect_face_position(video_path, start, duration, sample_count=3)
            
            if source_ratio > target_ratio:
                # 视频太宽，裁剪左右
                crop_height = height
                crop_width = int(height * target_ratio)
                
                # ✅ 如果检测到人脸，调整crop_x让人脸居中
                if face_position:
                    face_x, face_y = face_position
                    # 理想的crop_x是让人脸在裁剪区域的中央
                    ideal_crop_x = face_x - crop_width // 2
                    # 确保不越界
                    crop_x = max(0, min(ideal_crop_x, width - crop_width))
                    logger.info(f"✅ 人脸跟踪裁剪: crop_x={crop_x} (人脸x={face_x})")
                else:
                    crop_x = (width - crop_width) // 2
                
                crop_y = 0
            else:
                # 视频太高，裁剪上下
                crop_width = width
                crop_height = int(width / target_ratio)
                crop_x = 0
                
                # ✅ 如果检测到人脸，调整crop_y让人脸居中
                if face_position:
                    face_x, face_y = face_position
                    # 理想的crop_y是让人脸在裁剪区域的中央
                    ideal_crop_y = face_y - crop_height // 2
                    # 确保不越界
                    crop_y = max(0, min(ideal_crop_y, height - crop_height))
                    logger.info(f"✅ 人脸跟踪裁剪: crop_y={crop_y} (人脸y={face_y})")
                else:
                    crop_y = (height - crop_height) // 2
            
            # ✅ 裁剪为3:4竖屏（更适合横屏直播）
            cmd = [
                'ffmpeg',
                '-ss', str(start),
                '-i', video_path,
                '-t', str(duration),
                '-vf', f'crop={crop_width}:{crop_height}:{crop_x}:{crop_y}',
                '-c:v', 'libx264',
                '-preset', self.ffmpeg_preset,
                '-crf', '23',
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300
            )
            
            success = result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0
            
            if success:
                logger.info(f"✅ 短视频生成成功: {os.path.basename(output_path)} ({crop_width}x{crop_height})")
            else:
                logger.error(f"❌ 短视频生成失败: returncode={result.returncode}")
                if result.stderr:
                    logger.error(f"FFmpeg错误: {result.stderr.decode()[:500]}")
            
            return success
            
        except Exception as e:
            logger.error(f"创建短视频失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n=== 视频集锦生成系统 ===\n")
    print("功能：")
    print("  • 唱歌集锦（3版本）")
    print("  • 感谢集锦")
    print("  • 升级集锦")
    print("  • 聊天集锦")
    print("  • 精彩时刻")
    print("  • 每日精华")
    print("  • 短视频素材（竖屏3:4，更适合横屏直播）")
    print()



