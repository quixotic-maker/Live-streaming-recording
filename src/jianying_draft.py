#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映草稿生成器核心模块

功能：
1. 生成剪映草稿JSON结构
2. 支持视频片段、音频、字幕、转场
3. 自动生成草稿ID和时间线
"""

import json
import os
import uuid
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class JianYingDraft:
    """剪映草稿生成器"""
    
    def __init__(self, project_name: str, output_dir: str):
        """
        初始化草稿生成器
        
        Args:
            project_name: 项目名称
            output_dir: 输出目录
        """
        self.project_name = project_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化草稿结构
        self.draft = {
            "canvas_config": {
                "height": 1080,
                "width": 1920,
                "ratio": "16:9"
            },
            "color_space": 0,
            "create_time": int(datetime.now().timestamp() * 1000000),
            "duration": 0,
            "id": self._generate_id(),
            "materials": {
                "audios": [],
                "images": [],
                "texts": [],
                "videos": []
            },
            "name": project_name,
            "tracks": [],
            "version": "6.0.0"
        }
        
        # 时间线偏移（微秒）
        self.current_time = 0
        
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return str(uuid.uuid4())
    
    def _micros_to_duration(self, micros: int) -> int:
        """
        微秒转持续时间
        
        Args:
            micros: 微秒
            
        Returns:
            持续时间
        """
        return micros
    
    def _seconds_to_micros(self, seconds: float) -> int:
        """
        秒转微秒
        
        Args:
            seconds: 秒数
            
        Returns:
            微秒
        """
        return int(seconds * 1000000)
    
    def add_video_material(self, video_path: str, start: float = 0, 
                          duration: float = None) -> str:
        """
        添加视频素材
        
        Args:
            video_path: 视频文件路径
            start: 起始时间（秒）
            duration: 持续时间（秒），None表示全部
            
        Returns:
            素材ID
        """
        material_id = self._generate_id()
        
        # 获取视频信息（这里简化，实际需要用ffprobe）
        video_path = str(Path(video_path).absolute())
        
        material = {
            "create_time": int(datetime.now().timestamp() * 1000000),
            "duration": self._seconds_to_micros(duration) if duration else 0,
            "extra_info": {
                "audio_fade": None,
                "audio_length": 0,
                "enable_color_curves": True,
                "enable_color_wheels": True,
                "enable_lut": True,
                "enable_smart_color_adjust": False,
                "video_algorithm": {
                    "algorithms": [],
                    "beauty_mode": False,
                    "enable_ai_enhance": False
                }
            },
            "file_Path": video_path,
            "height": 1080,
            "id": material_id,
            "import_time": int(datetime.now().timestamp() * 1000000),
            "import_time_ms": int(datetime.now().timestamp() * 1000),
            "item_source": 1,
            "md5": "",
            "metetype": "video",
            "roughcut_time_range": {
                "duration": -1,
                "start": 0
            },
            "source_platform": 0,
            "type": 0,
            "width": 1920
        }
        
        self.draft["materials"]["videos"].append(material)
        return material_id
    
    def add_audio_material(self, audio_path: str, duration: float) -> str:
        """
        添加音频素材
        
        Args:
            audio_path: 音频文件路径
            duration: 持续时间（秒）
            
        Returns:
            素材ID
        """
        material_id = self._generate_id()
        audio_path = str(Path(audio_path).absolute())
        
        material = {
            "create_time": int(datetime.now().timestamp() * 1000000),
            "duration": self._seconds_to_micros(duration),
            "extra_info": "",
            "file_Path": audio_path,
            "id": material_id,
            "import_time": int(datetime.now().timestamp() * 1000000),
            "import_time_ms": int(datetime.now().timestamp() * 1000),
            "metetype": "audio",
            "name": Path(audio_path).stem,
            "path": audio_path,
            "roughcut_time_range": {
                "duration": -1,
                "start": 0
            },
            "source_platform": 0,
            "type": 0
        }
        
        self.draft["materials"]["audios"].append(material)
        return material_id
    
    def add_video_segment(self, material_id: str, duration: float,
                          track_index: int = 0) -> Dict:
        """
        添加视频片段到轨道
        
        Args:
            material_id: 素材ID
            duration: 持续时间（秒）
            track_index: 轨道索引
            
        Returns:
            片段对象
        """
        segment = {
            "cartoon": False,
            "clip": {
                "alpha": 1.0,
                "flip": {
                    "horizontal": False,
                    "vertical": False
                },
                "rotation": 0.0,
                "scale": {
                    "x": 1.0,
                    "y": 1.0
                },
                "transform": {
                    "x": 0.0,
                    "y": 0.0
                }
            },
            "common_keyframes": [],
            "enable_adjust": True,
            "enable_color_curves": True,
            "enable_color_match_adjust": False,
            "enable_color_wheels": True,
            "enable_lut": True,
            "enable_smart_color_adjust": False,
            "extra_material_refs": [],
            "group_id": "",
            "hdr_settings": {
                "intensity": 1.0,
                "mode": 1,
                "nits": 1000
            },
            "id": self._generate_id(),
            "intensifies_audio": False,
            "is_placeholder": False,
            "is_tone_modify": False,
            "keyframe_refs": [],
            "last_nonzero_volume": 1.0,
            "material_id": material_id,
            "render_index": 0,
            "reverse": False,
            "source_timerange": {
                "duration": self._seconds_to_micros(duration),
                "start": 0
            },
            "speed": 1.0,
            "target_timerange": {
                "duration": self._seconds_to_micros(duration),
                "start": self.current_time
            },
            "template_id": "",
            "template_scene": "default",
            "track_attribute": 0,
            "track_render_index": 0,
            "uniform_scale": {
                "on": True,
                "value": 1.0
            },
            "visible": True,
            "volume": 1.0
        }
        
        # 确保有足够的轨道
        while len(self.draft["tracks"]) <= track_index:
            self.draft["tracks"].append({
                "attribute": 0,
                "flag": 0,
                "id": self._generate_id(),
                "segments": [],
                "type": "video"
            })
        
        self.draft["tracks"][track_index]["segments"].append(segment)
        
        # 更新时间线
        self.current_time += self._seconds_to_micros(duration)
        
        return segment
    
    def add_text_segment(self, text: str, start: float, duration: float,
                        style: Dict = None) -> Dict:
        """
        添加文字片段
        
        Args:
            text: 文字内容
            start: 起始时间（秒）
            duration: 持续时间（秒）
            style: 文字样式
            
        Returns:
            片段对象
        """
        if style is None:
            style = {
                "font": "默认",
                "font_size": 24.0,
                "color": [255, 255, 255],  # 白色
                "bold": False,
                "italic": False
            }
        
        # 创建文字素材
        text_material_id = self._generate_id()
        
        text_material = {
            "animations": [],
            "content": text,
            "create_time": int(datetime.now().timestamp() * 1000000),
            "font_category_id": "",
            "font_category_name": "",
            "font_id": "",
            "font_name": style["font"],
            "font_path": "",
            "font_resource_id": "",
            "font_size": style["font_size"],
            "font_source_platform": 0,
            "font_team_id": "",
            "font_title": style["font"],
            "font_url": "",
            "id": text_material_id,
            "italic": style.get("italic", False),
            "letter_spacing": 0.0,
            "line_spacing": 0.02,
            "name": text[:20],
            "preset_category": "",
            "preset_category_id": "",
            "preset_has_set_alignment": False,
            "preset_id": "",
            "preset_index": 0,
            "preset_name": "",
            "recognize_task_id": "",
            "recognize_type": 0,
            "relevance_segment": [],
            "style_name": "默认",
            "sub_type": 0,
            "subtitle_keywords": None,
            "subtitle_template_original_fontsize": 0.0,
            "text_alpha": 1.0,
            "text_color": style.get("color", [255, 255, 255]),
            "text_curve": None,
            "text_preset_resource_id": "",
            "text_size": 24,
            "text_to_audio_ids": [],
            "type": "text",
            "underline": False,
            "underline_offset": 0.0,
            "underline_width": 0.05,
            "use_effect_default_color": True,
            "words": {
                "end_time": [],
                "start_time": [],
                "text": [text]
            }
        }
        
        self.draft["materials"]["texts"].append(text_material)
        
        # 创建文字片段
        segment = {
            "caption_template_info": {
                "category_id": "",
                "category_name": "",
                "effect_id": "",
                "is_new": False,
                "path": "",
                "request_id": "",
                "resource_id": "",
                "resource_name": "",
                "source_platform": 0
            },
            "clip": {
                "alpha": 1.0,
                "flip": {
                    "horizontal": False,
                    "vertical": False
                },
                "rotation": 0.0,
                "scale": {
                    "x": 1.0,
                    "y": 1.0
                },
                "transform": {
                    "x": 0.0,
                    "y": 0.0
                }
            },
            "common_keyframes": [],
            "enable_adjust": True,
            "extra_material_refs": [],
            "group_id": "",
            "hdr_settings": None,
            "id": self._generate_id(),
            "intensifies_audio": False,
            "is_placeholder": False,
            "is_tone_modify": False,
            "keyframe_refs": [],
            "last_nonzero_volume": 1.0,
            "material_id": text_material_id,
            "render_index": 0,
            "reverse": False,
            "source_timerange": None,
            "speed": 1.0,
            "target_timerange": {
                "duration": self._seconds_to_micros(duration),
                "start": self._seconds_to_micros(start)
            },
            "template_id": "",
            "template_scene": "",
            "track_attribute": 0,
            "track_render_index": 0,
            "uniform_scale": None,
            "visible": True,
            "volume": 1.0
        }
        
        # 添加到文字轨道
        text_track = None
        for track in self.draft["tracks"]:
            if track.get("type") == "text":
                text_track = track
                break
        
        if text_track is None:
            text_track = {
                "attribute": 0,
                "flag": 0,
                "id": self._generate_id(),
                "segments": [],
                "type": "text"
            }
            self.draft["tracks"].append(text_track)
        
        text_track["segments"].append(segment)
        
        return segment
    
    def set_duration(self):
        """设置草稿总时长"""
        if self.current_time > 0:
            self.draft["duration"] = self.current_time
    
    def save(self, draft_name: str = None) -> str:
        """
        保存草稿
        
        Args:
            draft_name: 草稿名称（可选）
            
        Returns:
            草稿文件路径
        """
        if draft_name is None:
            draft_name = self.project_name
        
        # 设置总时长
        self.set_duration()
        
        # 创建草稿目录结构
        draft_dir = self.output_dir / draft_name
        draft_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存draft_content.json
        content_file = draft_dir / "draft_content.json"
        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump(self.draft, f, ensure_ascii=False, indent=2)
        
        # 保存draft_info.json
        info_file = draft_dir / "draft_info.json"
        info_data = {
            "draft_cloud_capcut_purchase": {},
            "draft_cloud_last_action_time": 0,
            "draft_cloud_purchase": {},
            "draft_cover": "",
            "draft_feature_tag": "",
            "draft_fold_path": "",
            "draft_id": self.draft["id"],
            "draft_is_ai_dynamic_cover": False,
            "draft_is_invisible": False,
            "draft_materials": {},
            "draft_name": draft_name,
            "draft_new_version": "6.0.0",
            "draft_removable_storage_device": "",
            "draft_root_path": str(draft_dir.absolute()),
            "draft_timeline_materials": {},
            "tm_draft_create_time": int(datetime.now().timestamp() * 1000),
            "tm_draft_modified_time": int(datetime.now().timestamp() * 1000)
        }
        
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(info_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 剪映草稿已保存: {draft_dir}")
        return str(draft_dir)
    
    def get_total_duration(self) -> float:
        """
        获取总时长（秒）
        
        Returns:
            总时长
        """
        return self.current_time / 1000000.0


def create_simple_draft_example():
    """创建一个简单的草稿示例"""
    
    print("=" * 70)
    print("剪映草稿生成器 - 示例")
    print("=" * 70)
    
    # 创建草稿
    draft = JianYingDraft(
        project_name="示例项目",
        output_dir=os.path.expanduser("~/shanshan_materials/剪映草稿")
    )
    
    # 添加视频素材（这里用占位路径）
    video_id = draft.add_video_material(
        video_path="/path/to/video.mp4",
        duration=10.0
    )
    
    # 添加视频片段
    draft.add_video_segment(video_id, duration=10.0)
    
    # 添加文字
    draft.add_text_segment(
        text="这是一个示例文字",
        start=1.0,
        duration=5.0
    )
    
    # 保存草稿
    draft_path = draft.save("示例草稿")
    
    print(f"\n总时长: {draft.get_total_duration():.1f}秒")
    print(f"草稿路径: {draft_path}")
    
    return draft_path


if __name__ == "__main__":
    create_simple_draft_example()





















