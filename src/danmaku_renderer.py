#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
弹幕渲染器

功能：
- 读取弹幕数据
- 时间戳同步
- 智能定位（避开人脸）
- 渲染弹幕到视频
- 生成ASS字幕格式
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import subprocess

logger = logging.getLogger(__name__)


class DanmakuRenderer:
    """弹幕渲染器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 视频参数
        self.video_width = self.config.get('video_width', 1920)
        self.video_height = self.config.get('video_height', 1080)
        
        # 弹幕参数
        self.font_size = self.config.get('font_size', 30)
        self.font_name = self.config.get('font_name', 'Arial')
        self.opacity = self.config.get('opacity', 0.8)  # 透明度
        self.duration = self.config.get('duration', 8)  # 弹幕显示时长（秒）
        self.speed = self.config.get('speed', 150)  # 弹幕速度（像素/秒）
        
        # 弹幕密度控制
        self.max_danmaku_per_second = self.config.get('max_per_second', 10)
        self.min_interval = self.config.get('min_interval', 0.1)  # 最小间隔
        
        # 安全区域（避开人脸/UI）
        self.safe_top = self.config.get('safe_top', 100)  # 顶部安全距离
        self.safe_bottom = self.config.get('safe_bottom', 150)  # 底部安全距离
        self.safe_left = self.config.get('safe_left', 50)
        self.safe_right = self.config.get('safe_right', 50)
        
        # 弹幕轨道
        self.track_height = self.font_size + 10
        self.num_tracks = (
            self.video_height - self.safe_top - self.safe_bottom
        ) // self.track_height
        
        # 颜色配置
        self.color_scheme = self.config.get('color_scheme', 'white')
        self.colors = {
            'white': '&H00FFFFFF',  # 白色
            'cyan': '&H00FFFF00',   # 青色
            'yellow': '&H0000FFFF', # 黄色
            'green': '&H0000FF00',  # 绿色
            'pink': '&H00FF00FF',   # 粉色
        }
    
    def load_danmaku(self, danmaku_file: str) -> List[Dict]:
        """
        加载弹幕数据
        
        Args:
            danmaku_file: 弹幕JSONL文件
        
        Returns:
            弹幕列表
        """
        if not os.path.exists(danmaku_file):
            logger.error(f"弹幕文件不存在: {danmaku_file}")
            return []
        
        danmaku_list = []
        
        try:
            with open(danmaku_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    msg = json.loads(line)
                    
                    # 只处理聊天消息
                    if msg.get('type') == 'chat':
                        danmaku_list.append({
                            'timestamp': msg.get('timestamp', 0),
                            'user': msg.get('user', 'Unknown'),
                            'content': msg.get('content', ''),
                            'color': self._get_color_for_user(msg.get('user', ''))
                        })
            
            logger.info(f"加载了 {len(danmaku_list)} 条弹幕")
            return danmaku_list
            
        except Exception as e:
            logger.error(f"加载弹幕失败: {e}")
            return []
    
    def _get_color_for_user(self, user: str) -> str:
        """根据用户名分配颜色"""
        # 简单的hash分配
        colors = list(self.colors.values())
        index = hash(user) % len(colors)
        return colors[index]
    
    def filter_danmaku(
        self,
        danmaku_list: List[Dict],
        start_time: float = 0,
        end_time: float = None
    ) -> List[Dict]:
        """
        过滤弹幕（时间范围、密度控制）
        
        Args:
            danmaku_list: 弹幕列表
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            过滤后的弹幕列表
        """
        # 时间范围过滤
        filtered = [
            dm for dm in danmaku_list
            if dm['timestamp'] >= start_time and (
                end_time is None or dm['timestamp'] <= end_time
            )
        ]
        
        # 密度控制
        if self.max_danmaku_per_second > 0:
            filtered = self._control_density(filtered)
        
        logger.info(f"过滤后剩余 {len(filtered)} 条弹幕")
        return filtered
    
    def _control_density(self, danmaku_list: List[Dict]) -> List[Dict]:
        """控制弹幕密度"""
        if not danmaku_list:
            return []
        
        result = []
        last_timestamp = -999
        
        for dm in danmaku_list:
            # 检查时间间隔
            if dm['timestamp'] - last_timestamp >= self.min_interval:
                result.append(dm)
                last_timestamp = dm['timestamp']
        
        return result
    
    def generate_ass_subtitle(
        self,
        danmaku_list: List[Dict],
        output_path: str,
        video_start_time: float = 0
    ) -> bool:
        """
        生成ASS字幕文件
        
        Args:
            danmaku_list: 弹幕列表
            output_path: 输出路径
            video_start_time: 视频开始时间（用于同步）
        
        Returns:
            是否成功
        """
        try:
            with open(output_path, 'w', encoding='utf-8-sig') as f:
                # 写入ASS头部
                f.write(self._generate_ass_header())
                
                # 写入弹幕事件
                for i, dm in enumerate(danmaku_list):
                    # 计算显示时间
                    start_time = dm['timestamp'] - video_start_time
                    end_time = start_time + self.duration
                    
                    # 转换为ASS时间格式
                    start_str = self._seconds_to_ass_time(start_time)
                    end_str = self._seconds_to_ass_time(end_time)
                    
                    # 弹幕文本
                    text = dm['content']
                    user = dm['user']
                    color = dm.get('color', self.colors['white'])
                    
                    # 生成移动效果（从右到左）
                    # 使用ASS的\move命令
                    start_x = self.video_width + 100
                    end_x = -200
                    y = self._get_track_y(i)
                    
                    # ASS格式：Dialogue行
                    # Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
                    dialogue = (
                        f"Dialogue: 0,{start_str},{end_str},Danmaku,{user},"
                        f"0,0,0,,"
                        f"{{\\move({start_x},{y},{end_x},{y})}}"
                        f"{{\\c{color}}}"
                        f"{text}\n"
                    )
                    
                    f.write(dialogue)
            
            logger.info(f"✅ ASS字幕生成成功: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成ASS字幕失败: {e}")
            return False
    
    def _generate_ass_header(self) -> str:
        """生成ASS头部"""
        return f"""[Script Info]
Title: 弹幕字幕
ScriptType: v4.00+
PlayResX: {self.video_width}
PlayResY: {self.video_height}
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Danmaku,{self.font_name},{self.font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    def _seconds_to_ass_time(self, seconds: float) -> str:
        """将秒数转换为ASS时间格式 (H:MM:SS.CC)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)
        
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
    
    def _get_track_y(self, index: int) -> int:
        """获取弹幕轨道的Y坐标"""
        track = index % self.num_tracks
        return self.safe_top + track * self.track_height + self.font_size
    
    def render_video_with_danmaku(
        self,
        video_path: str,
        danmaku_file: str,
        output_path: str,
        video_start_time: float = 0
    ) -> bool:
        """
        渲染带弹幕的视频
        
        Args:
            video_path: 原始视频路径
            danmaku_file: 弹幕文件路径
            output_path: 输出视频路径
            video_start_time: 视频开始时间（用于同步）
        
        Returns:
            是否成功
        """
        if not os.path.exists(video_path):
            logger.error(f"视频文件不存在: {video_path}")
            return False
        
        # 1. 加载弹幕
        logger.info("步骤1: 加载弹幕数据...")
        danmaku_list = self.load_danmaku(danmaku_file)
        
        if not danmaku_list:
            logger.warning("没有弹幕数据，跳过渲染")
            return False
        
        # 2. 过滤弹幕
        logger.info("步骤2: 过滤弹幕...")
        filtered_danmaku = self.filter_danmaku(danmaku_list)
        
        # 3. 生成ASS字幕
        logger.info("步骤3: 生成ASS字幕...")
        ass_path = output_path.replace('.mp4', '_danmaku.ass')
        
        if not self.generate_ass_subtitle(
            filtered_danmaku,
            ass_path,
            video_start_time
        ):
            return False
        
        # 4. 使用FFmpeg渲染
        logger.info("步骤4: 渲染视频（这可能需要一些时间）...")
        
        success = self._render_with_ffmpeg(
            video_path,
            ass_path,
            output_path
        )
        
        # 5. 清理临时文件
        if os.path.exists(ass_path):
            os.remove(ass_path)
        
        if success:
            logger.info(f"✅ 弹幕视频生成成功: {output_path}")
        else:
            logger.error(f"❌ 弹幕视频生成失败")
        
        return success
    
    def _render_with_ffmpeg(
        self,
        video_path: str,
        ass_path: str,
        output_path: str
    ) -> bool:
        """使用FFmpeg渲染弹幕"""
        try:
            # 创建输出目录
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # FFmpeg命令
            # 使用libass滤镜烧录弹幕
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"ass='{ass_path}'",
                '-c:v', 'libx264',  # 视频编码
                '-preset', 'medium',  # 编码速度
                '-crf', '23',  # 质量
                '-c:a', 'copy',  # 音频直接复制
                '-y',
                output_path
            ]
            
            logger.debug(f"FFmpeg命令: {' '.join(cmd)}")
            
            # 执行
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                timeout=3600  # 1小时超时
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                return True
            else:
                logger.error(f"FFmpeg错误: {result.stderr[-500:]}")  # 只显示最后500字符
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg渲染超时")
            return False
        except Exception as e:
            logger.error(f"FFmpeg渲染出错: {e}")
            return False


class DanmakuAligner:
    """
    弹幕对齐器
    
    负责同步视频和弹幕的时间戳
    """
    
    def __init__(self):
        self.video_start_time = None
        self.danmaku_start_time = None
    
    def sync_timestamps(
        self,
        video_start_time: float,
        danmaku_file: str
    ) -> float:
        """
        同步时间戳
        
        Args:
            video_start_time: 视频录制开始时间（Unix时间戳）
            danmaku_file: 弹幕文件
        
        Returns:
            时间偏移量（秒）
        """
        self.video_start_time = video_start_time
        
        # 读取第一条弹幕的时间戳
        try:
            with open(danmaku_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        msg = json.loads(line)
                        self.danmaku_start_time = msg.get('timestamp', 0)
                        break
        except Exception as e:
            logger.error(f"读取弹幕时间戳失败: {e}")
            return 0
        
        # 计算偏移
        offset = self.danmaku_start_time - self.video_start_time
        
        logger.info(f"时间戳同步:")
        logger.info(f"  视频开始: {datetime.fromtimestamp(video_start_time)}")
        logger.info(f"  弹幕开始: {datetime.fromtimestamp(self.danmaku_start_time)}")
        logger.info(f"  偏移: {offset:.2f} 秒")
        
        return offset
    
    def adjust_danmaku_timestamps(
        self,
        danmaku_file: str,
        output_file: str,
        offset: float
    ):
        """
        调整弹幕时间戳
        
        Args:
            danmaku_file: 输入弹幕文件
            output_file: 输出弹幕文件
            offset: 时间偏移量
        """
        try:
            with open(danmaku_file, 'r', encoding='utf-8') as f_in:
                with open(output_file, 'w', encoding='utf-8') as f_out:
                    for line in f_in:
                        if not line.strip():
                            continue
                        
                        msg = json.loads(line)
                        
                        # 调整时间戳
                        if 'timestamp' in msg:
                            msg['timestamp'] -= offset
                        
                        f_out.write(json.dumps(msg, ensure_ascii=False) + '\n')
            
            logger.info(f"✅ 弹幕时间戳已调整: {output_file}")
            
        except Exception as e:
            logger.error(f"调整弹幕时间戳失败: {e}")


def generate_three_versions(
    video_path: str,
    danmaku_file: str,
    subtitle_file: str,
    output_dir: str,
    base_name: str
) -> Dict[str, str]:
    """
    生成三个版本的视频
    
    1. 原始版（无字幕无弹幕）
    2. 字幕版（有字幕无弹幕）
    3. 弹幕版（有字幕有弹幕）
    
    Args:
        video_path: 原始视频
        danmaku_file: 弹幕文件
        subtitle_file: 字幕文件（SRT或ASS）
        output_dir: 输出目录
        base_name: 基础文件名
    
    Returns:
        生成的文件路径字典
    """
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    # 1. 原始版（直接复制或软链接）
    logger.info("生成版本1: 原始版...")
    original_path = os.path.join(output_dir, f"{base_name}_原始版.mp4")
    
    if video_path != original_path:
        try:
            # 使用软链接节省空间
            if os.path.exists(original_path):
                os.remove(original_path)
            os.symlink(os.path.abspath(video_path), original_path)
            results['original'] = original_path
            logger.info(f"✅ 原始版已链接: {original_path}")
        except Exception as e:
            logger.error(f"创建原始版失败: {e}")
    
    # 2. 字幕版
    logger.info("生成版本2: 字幕版...")
    subtitle_path = os.path.join(output_dir, f"{base_name}_字幕版.mp4")
    
    if subtitle_file and os.path.exists(subtitle_file):
        if _burn_subtitle(video_path, subtitle_file, subtitle_path):
            results['subtitle'] = subtitle_path
            logger.info(f"✅ 字幕版已生成: {subtitle_path}")
    else:
        logger.warning("字幕文件不存在，跳过字幕版生成")
    
    # 3. 弹幕版（字幕+弹幕）
    logger.info("生成版本3: 弹幕版...")
    danmaku_path = os.path.join(output_dir, f"{base_name}_弹幕版.mp4")
    
    if danmaku_file and os.path.exists(danmaku_file):
        renderer = DanmakuRenderer()
        if renderer.render_video_with_danmaku(
            subtitle_path if subtitle_path in results else video_path,
            danmaku_file,
            danmaku_path
        ):
            results['danmaku'] = danmaku_path
            logger.info(f"✅ 弹幕版已生成: {danmaku_path}")
    else:
        logger.warning("弹幕文件不存在，跳过弹幕版生成")
    
    return results


def _burn_subtitle(
    video_path: str,
    subtitle_file: str,
    output_path: str
) -> bool:
    """烧录字幕到视频"""
    try:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f"subtitles='{subtitle_file}'",
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3600
        )
        
        return result.returncode == 0 and os.path.exists(output_path)
        
    except Exception as e:
        logger.error(f"烧录字幕失败: {e}")
        return False


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n=== 弹幕渲染系统 ===\n")
    print("功能：")
    print("  • 加载弹幕数据")
    print("  • 生成ASS字幕格式")
    print("  • 渲染弹幕到视频")
    print("  • 生成3个版本（原始+字幕+弹幕）")
    print()
    print("使用方法:")
    print("  from src.danmaku_renderer import generate_three_versions")
    print("  ")
    print("  generate_three_versions(")
    print("      video_path='完整录播.mp4',")
    print("      danmaku_file='弹幕.jsonl',")
    print("      subtitle_file='字幕.ass',")
    print("      output_dir='./output',")
    print("      base_name='观山_2025-10-31'")
    print("  )")
    print()



