#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表情包素材生成 - 优化版（降低检测阈值）

优化内容：
1. 降低运动检测阈值：0.15 → 0.08
2. 降低推荐阈值：0.7 → 0.4
3. 缩短检测时长：60分钟 → 30分钟（加快测试）
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from gesture_detector import MotionDetector, PoseDetector, MultimodalDetector
from emoji_generator import EmojiGenerator
# ✅ 移除MaterialOrganizer - 改用简单目录创建
# from material_organizer import MaterialOrganizer


# ✅ 并行生成单个表情包的独立函数
def _generate_single_emoji(task: Dict) -> Dict:
    """
    在独立进程中生成单个表情包
    
    Args:
        task: 包含所有必要参数的字典
    
    Returns:
        生成结果字典
    """
    try:
        # 导入所需模块（在子进程中需要重新导入）
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
        from emoji_generator import EmojiGenerator
        
        # 创建生成器实例
        generator = EmojiGenerator()
        
        # 生成表情包
        result = generator.generate_multi_specs(
            video_path=task['video_path'],
            start=task['start'],
            end=task['end'],
            output_dir=task['output_dir'],
            base_name=task['base_name']
        )
        
        return result
        
    except Exception as e:
        # 返回None表示失败
        return None


def _get_memory_usage():
    """获取当前内存使用情况（MB）"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        return {
            'total': memory.total / (1024**3),      # GB
            'used': memory.used / (1024**3),        # GB
            'available': memory.available / (1024**3),  # GB
            'percent': memory.percent
        }
    except:
        return None


# 配置参数
config = {
    "video_path": "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4",
    "output_dir": os.path.expanduser("~/shanshan_materials/表情包素材库"),
    "temp_dir": "temp_emojis",
    
    # 优化参数
    "motion_config": {
        "motion_threshold": 0.03,      # ✅ 进一步降低: 0.05→0.03（更敏感）
        "min_duration": 1.5,            # 最短1.5秒
        "merge_gap": 2.0                # 合并间隔2秒
    },
    
    "multimodal_config": {
        "recommend_threshold": 0.2,     # ✅ 进一步降低: 0.3→0.2（更宽松）
        "gesture_weight": 0.5,          # 增加手势权重
        "effect_weight": 0.3            # 增加特效权重
    },
    
    # 测试参数
    "test_duration": None,              # ✅ 修复: 默认分析全视频（不限制时长）
    "max_dance_moments": 999999,        # ✅ 不限制数量（供人工标注）
    "max_thank_moments": 999999,        # ✅ 不限制数量（供人工标注）
    "max_sing_moments": 999999,         # ✅ 新增：唱歌表情包
    "max_chat_moments": 999999,         # ✅ 新增：聊天表情包
    "max_upgrade_moments": 999999       # ✅ 新增：升级表情包
}


class EmojiMaterialGenerator:
    """表情包素材生成器 - 优化版"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.video_path = config["video_path"]
        self.output_dir = config["output_dir"]
        self.temp_dir = config.get("temp_dir", "temp_emojis")
        self.fingerprint = config.get("fingerprint")
        
        if not os.path.exists(self.video_path):
            raise FileNotFoundError(f"视频文件不存在: {self.video_path}")
        
        # 创建检测器（使用优化参数）
        self.motion_detector = MotionDetector(config.get("motion_config", {}))
        self.pose_detector = PoseDetector()
        self.multimodal_detector = MultimodalDetector(config.get("multimodal_config", {}))
        
        self.emoji_generator = EmojiGenerator()
        # ✅ 移除MaterialOrganizer，改用简单目录创建
        # self.organizer = MaterialOrganizer(self.output_dir)
        
        # 创建简化的输出目录结构
        self._create_simple_structure()
        
        self.dance_moments = []
        self.thank_moments = []
        self.sing_moments = []      # ✅ 新增：唱歌表情包
        self.chat_moments = []      # ✅ 新增：聊天表情包
        self.upgrade_moments = []   # ✅ 新增：升级表情包
        self.all_emojis = []
        
        print("=" * 70)
        print("表情包素材生成系统（优化版）已初始化")
        print("=" * 70)
        print(f"视频路径: {self.video_path}")
        print(f"输出目录: {self.output_dir}")
        print(f"\n优化配置:")
        print(f"  运动阈值: {config['motion_config']['motion_threshold']}")
        print(f"  推荐阈值: {config['multimodal_config']['recommend_threshold']}")
        if config.get('test_duration'):
            print(f"  分析时长: {config['test_duration']/60:.0f}分钟")
        else:
            print(f"  分析时长: 全部视频")
        print()
    
    def _create_simple_structure(self):
        """创建简化的目录结构（不使用MaterialOrganizer）"""
        output_path = Path(self.output_dir)
        
        # 创建基础目录
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 无需创建复杂的"站"结构，只创建实际需要的
        # 表情包会直接保存在output_dir下
        print("✅ 使用简化目录结构（无MaterialOrganizer）")
    
    def _write_completion_marker(self, output_path: Path):
        """写入完成标记，便于上层跳过逻辑"""
        if not self.fingerprint:
            return
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            # 清理旧的完成标记
            for marker in output_path.glob(".emoji_done_*"):
                if marker.is_file():
                    marker.unlink()
            marker_file = output_path / f".emoji_done_{self.fingerprint}"
            marker_file.write_text(f"done {datetime.now().isoformat()}", encoding="utf-8")
            print(f"✓ 写入完成标记: {marker_file.name}")
        except Exception as e:
            print(f"⚠️ 写入完成标记失败: {e}")
    
    def load_data(self):
        """加载已有数据"""
        print("\n[步骤1] 加载已有数据")
        print("-" * 70)
        
        # ✅ 修复: 健壮的gift数据查找 - 使用所有片段
        gift_data_loaded = self._find_gift_data_robust()
        
        if gift_data_loaded:
            segments = gift_data_loaded.get("segments", []) if isinstance(gift_data_loaded, dict) else gift_data_loaded
            # ✅ 使用所有gift片段，不再限制只有"谢谢"的
            for item in segments:
                if isinstance(item, dict):
                    self.thank_moments.append({
                        "time": item["start"],
                        "keyword": "礼物/感谢",
                        "text": item.get("text", "")
                    })
            
            print(f"✓ 加载礼物感谢数据: {len(self.thank_moments)}个时刻 (所有gift片段)")
        else:
            print(f"⚠ 未找到礼物数据，将仅依赖运动检测")
            self.thank_moments = []
        
        # ✅ 新增：加载唱歌数据 - 使用所有片段
        singing_data = self._load_singing_data()
        if singing_data:
            segments = singing_data.get("segments", []) if isinstance(singing_data, dict) else singing_data
            # ✅ 使用所有唱歌片段，不再限制前20个
            for item in segments:
                if isinstance(item, dict):
                    self.sing_moments.append({
                        "start": item.get("start", 0),
                        "end": item.get("end", item.get("start", 0) + 3),
                        "song": item.get("title", "unknown")
                    })
            print(f"✓ 加载唱歌数据: {len(self.sing_moments)}个时刻 (所有singing片段)")
        else:
            print(f"⚠ 未找到唱歌数据")
        
        # ✅ 新增：加载聊天数据（从Whisper转录）
        chat_data = self._load_chat_data()
        if chat_data:
            print(f"✓ 加载聊天数据: {len(chat_data)}个时刻")
            self.chat_moments = chat_data[:50]  # 取前50个有趣对话
        else:
            print(f"⚠ 未找到聊天数据")
        
        # ✅ 新增：加载升级数据
        upgrade_data = self._load_upgrade_data()
        if upgrade_data:
            segments = upgrade_data.get("segments", []) if isinstance(upgrade_data, dict) else upgrade_data
            for item in segments:
                if isinstance(item, dict):
                    self.upgrade_moments.append({
                        "start": item.get("start", 0),
                        "end": item.get("end", item.get("start", 0) + 3),
                        "level": item.get("level", "unknown")
                    })
            print(f"✓ 加载升级数据: {len(self.upgrade_moments)}个时刻")
        else:
            print(f"⚠ 未找到升级数据")
        
        print(f"\n数据加载完成:")
        print(f"  感谢时刻: {len(self.thank_moments)}个")
        print(f"  唱歌时刻: {len(self.sing_moments)}个")
        print(f"  聊天时刻: {len(self.chat_moments)}个")
        print(f"  升级时刻: {len(self.upgrade_moments)}个")
    
    def _find_gift_data_robust(self):
        """健壮的礼物数据查找方法"""
        import re
        from pathlib import Path
        
        # 从视频路径提取日期
        match = re.search(r'(\d{4}-\d{2}-\d{2})', self.video_path)
        if not match:
            print(f"⚠ 无法从视频路径提取日期: {self.video_path}")
            date = None
        else:
            date = match.group(1)
            print(f"✓ 提取日期: {date}")
        
        base_dir = Path.home() / "shanshan_materials"
        
        # 优先级1: 当前日期目录
        if date:
            priority1_paths = [
                base_dir / f"03_内容分类/{date}/gift_素材.json",
                base_dir / f"04_素材生成/{date}/gift/gift_素材.json",
            ]
            
            for path in priority1_paths:
                if path.exists():
                    print(f"✓ 找到礼物数据: {path}")
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
        
        # 优先级2: 全局素材库（兜底）
        priority2_paths = [
            base_dir / "素材库_最新/gift_素材.json",
            base_dir / "歌曲素材库/gift_素材.json",
        ]
        
        for path in priority2_paths:
            if path.exists():
                print(f"⚠ 使用全局素材库: {path}")
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        # 优先级3: 无数据
        print(f"❌ 未找到任何礼物数据文件")
        print(f"   尝试过的路径:")
        if date:
            print(f"     • 03_内容分类/{date}/gift_素材.json")
            print(f"     • 04_素材生成/{date}/gift/gift_素材.json")
        print(f"     • 素材库_最新/gift_素材.json")
        print(f"     • 歌曲素材库/gift_素材.json")
        return None
    
    def _load_singing_data(self):
        """加载唱歌数据"""
        import re
        from pathlib import Path
        
        # 从视频路径提取日期
        match = re.search(r'(\d{4}-\d{2}-\d{2})', self.video_path)
        if not match:
            return None
        
        date = match.group(1)
        base_dir = Path.home() / "shanshan_materials"
        
        # 查找singing_素材.json
        paths = [
            base_dir / f"03_内容分类/{date}/singing_素材.json",
            base_dir / f"03_内容分类/{date}/singing_素材_fingerprint.json",
        ]
        
        for path in paths:
            if path.exists():
                print(f"✓ 找到唱歌数据: {path}")
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
        
        return None
    
    def _load_chat_data(self):
        """加载聊天数据（从Whisper转录提取有趣对话）"""
        import re
        from pathlib import Path
        
        # 从视频路径提取日期
        match = re.search(r'(\d{4}-\d{2}-\d{2})', self.video_path)
        if not match:
            return []
        
        date = match.group(1)
        base_dir = Path.home() / "shanshan_materials"
        
        # 查找Whisper转录文件
        transcript_path = base_dir / f"02_转文字结果/{date}"
        if not transcript_path.exists():
            return []
        
        # 查找json文件
        json_files = list(transcript_path.glob("*_transcript.json"))
        if not json_files:
            return []
        
        try:
            with open(json_files[0], 'r', encoding='utf-8') as f:
                transcript = json.load(f)
            
            # 提取包含问号、感叹号的对话（可能是有趣互动）
            chat_moments = []
            for segment in transcript.get("segments", []):
                text = segment.get("text", "")
                if ("?" in text or "？" in text or "!" in text or "！" in text) and len(text) > 5:
                    chat_moments.append({
                        "start": segment.get("start", 0),
                        "end": segment.get("end", segment.get("start", 0) + 3),
                        "text": text
                    })
            
            return chat_moments[:50]  # 返回前50个
        except:
            return []
    
    def _load_upgrade_data(self):
        """加载升级数据"""
        import re
        from pathlib import Path
        
        # 从视频路径提取日期
        match = re.search(r'(\d{4}-\d{2}-\d{2})', self.video_path)
        if not match:
            return None
        
        date = match.group(1)
        base_dir = Path.home() / "shanshan_materials"
        
        # 查找upgrade_素材.json
        paths = [
            base_dir / f"03_内容分类/{date}/upgrade_素材.json",
            base_dir / f"04_素材生成/{date}/upgrade/upgrade_素材.json",
        ]
        
        for path in paths:
            if path.exists():
                print(f"✓ 找到升级数据: {path}")
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
        
        return None
    
    def detect_dance_moments(self):
        """方案A: 检测手势舞"""
        print("\n[步骤2] 方案A: 运动检测 - 查找手势舞")
        print("-" * 70)
        
        test_duration = self.config.get("test_duration")
        if test_duration:
            print(f"分析时间范围: 0-{test_duration/60:.0f}分钟")
        else:
            print(f"分析时间范围: 全部视频")
        print(f"运动阈值: {self.config['motion_config']['motion_threshold']}")
        print("这可能需要几分钟...")
        
        detect_kwargs = {"video_path": self.video_path, "start_time": 0}
        if test_duration:
            detect_kwargs["end_time"] = test_duration
        self.dance_moments = self.motion_detector.detect_dance_moments(**detect_kwargs)
        
        print(f"\n✓ 找到 {len(self.dance_moments)} 个手势舞候选片段")
        
        if len(self.dance_moments) > 0:
            print("\n前5个候选:")
            for i, moment in enumerate(self.dance_moments[:5], 1):
                print(f"  {i}. {moment['start']:.2f}s - {moment['end']:.2f}s, "
                      f"得分: {moment['motion_score']:.3f}, 置信度: {moment['confidence']:.2f}")
            
            if len(self.dance_moments) > 5:
                print(f"  ... 还有{len(self.dance_moments) - 5}个")
        else:
            print("⚠ 未找到手势舞候选，建议:")
            print("  1. 进一步降低阈值（当前0.08）")
            print("  2. 检查视频前30分钟是否有大幅度动作")
            print("  3. 可以手动指定时间段进行测试")
    
    def analyze_thank_moments(self):
        """方案E: 保留所有候选（跳过多模态推荐过滤）"""
        print("\n[步骤3] 方案E: 保留所有候选时刻（供人工标注和AI学习）")
        print("-" * 70)
        
        max_moments = self.config.get("max_thank_moments", 50)
        moments_to_use = self.thank_moments[:max_moments]
        
        print(f"✅ 保留 {len(moments_to_use)} 个候选时刻（共{len(self.thank_moments)}个）")
        print(f"💡 理念: 不进行AI预筛选，保留所有候选供人工标注")
        print(f"   → 人工标注 + AI学习 = 更好的质量模型")
        
        # 将thank_moments转换为统一格式
        analyzed_moments = []
        for moment in moments_to_use:
            analyzed_moments.append({
                "start": moment.get("start", moment.get("time", 0)),
                "end": moment.get("end", moment.get("start", moment.get("time", 0)) + 3),
                "score": 1.0,  # 所有候选初始得分为1.0
                "gesture_type": "thank",
                "features": {"source": moment.get("keyword", "interval_sampling")}
            })
        
        print(f"\n✓ 已准备 {len(analyzed_moments)} 个表情包候选")
        print(f"   - 关键词匹配: ~{len([m for m in self.thank_moments if 'keyword' in m])}个")
        print(f"   - 固定间隔: ~{len([m for m in self.thank_moments if 'keyword' not in m])}个")
        
        self.thank_moments = analyzed_moments
    
    def generate_emojis(self):
        """生成表情包（直接输出到output_dir）"""
        print("\n[步骤4] 生成表情包")
        print("-" * 70)
        
        # ✅ 直接使用output_dir，不再使用temp_dir
        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        all_candidates = []
        
        # 添加手势舞
        max_dance = self.config.get("max_dance_moments", 15)
        for moment in self.dance_moments[:max_dance]:
            all_candidates.append({
                "start": moment["start"],
                "end": moment["end"],
                "type": "cute",  # 改用"cute"分类，更通用
                "gesture_type": moment.get("gesture_type", "dance")
            })
        
        # 添加感谢表情
        max_thank = self.config.get("max_thank_moments", 50)
        for moment in self.thank_moments[:max_thank]:
            all_candidates.append({
                "start": moment["start"],
                "end": moment["end"],
                "type": "thank",
                "gesture_type": "thank"
            })
        
        # ✅ 新增：添加唱歌表情
        max_sing = self.config.get("max_sing_moments", 999999)
        for moment in self.sing_moments[:max_sing]:
            all_candidates.append({
                "start": moment["start"],
                "end": moment["end"],
                "type": "sing",
                "gesture_type": "sing"
            })
        
        # ✅ 新增：添加聊天表情
        max_chat = self.config.get("max_chat_moments", 999999)
        for moment in self.chat_moments[:max_chat]:
            all_candidates.append({
                "start": moment["start"],
                "end": moment["end"],
                "type": "chat",
                "gesture_type": "chat"
            })
        
        # ✅ 新增：添加升级表情
        max_upgrade = self.config.get("max_upgrade_moments", 999999)
        for moment in self.upgrade_moments[:max_upgrade]:
            all_candidates.append({
                "start": moment["start"],
                "end": moment["end"],
                "type": "upgrade",
                "gesture_type": "upgrade"
            })
        
        if len(all_candidates) == 0:
            print("⚠ 没有找到候选片段，无法生成表情包")
            print("  建议调整检测参数后重新运行")
            return
        
        print(f"准备生成 {len(all_candidates)} 个表情包")
        print("每个表情包生成3种规格（240x240, 300x300, 512x512）+ 1个静态图")
        print(f"预计生成 {len(all_candidates) * 4} 个文件")
        print()
        
        # ✅ 并行生成表情包
        import multiprocessing
        from concurrent.futures import ProcessPoolExecutor, as_completed
        import os
        
        cpu_count = multiprocessing.cpu_count()
        
        # 检查是否手动指定并行度
        if self.config.get('max_workers'):
            max_workers = self.config['max_workers']
            print(f"🚀 并行模式: 使用 {max_workers} 个进程 (手动指定, CPU: {cpu_count}核)")
        else:
            # ⚠️ 内存限制：每个进程约需4-6GB内存
            # 64GB内存 → 最多8-10个进程安全
            
            # 优先考虑内存限制（假设可用内存50GB，每进程5GB）
            memory_limited_workers = 10  # 保守估计
            cpu_limited_workers = max(1, int(cpu_count * 0.5))  # 降低到50%
            
            max_workers = min(memory_limited_workers, cpu_limited_workers)
            max_workers = max(1, min(max_workers, 6))  # 硬性上限：6个进程
            
            print(f"🚀 并行模式: 使用 {max_workers} 个进程 (自动检测, CPU: {cpu_count}核)")
            print(f"⚠️  内存保护: 限制并发数以避免OOM (建议: 2-6个进程)")
        
        print()
        
        # 准备任务（支持断点续传）
        tasks = []
        skipped_count = 0
        
        for i, candidate in enumerate(all_candidates, 1):
            emoji_type = candidate["type"]
            base_name = f"emoji_{emoji_type}_{i:03d}"
            
            # ✅ 断点续传：检查元数据文件是否已存在
            metadata_file = output_path / f"{base_name}_metadata.json"
            if metadata_file.exists():
                skipped_count += 1
                # 读取已有的元数据，添加到all_emojis
                try:
                    import json
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        existing_result = json.load(f)
                        existing_result["gesture_type"] = candidate["gesture_type"]
                        existing_result["category"] = emoji_type
                        self.all_emojis.append(existing_result)
                except Exception as e:
                    print(f"⚠️  读取已有元数据失败: {base_name}, {e}")
                continue  # 跳过已生成的
            
            task = {
                'index': i,
                'total': len(all_candidates),
                'video_path': self.video_path,
                'start': candidate["start"],
                'end': candidate["end"],
                'output_dir': str(output_path),
                'base_name': base_name,
                'emoji_type': emoji_type,
                'gesture_type': candidate["gesture_type"]
            }
            tasks.append(task)
        
        if skipped_count > 0:
            print(f"✓ 断点续传: 跳过 {skipped_count} 个已生成的表情包")
            print(f"✓ 剩余任务: {len(tasks)} 个\n")
        
        # ✅ 如果所有任务都已完成，直接返回
        if len(tasks) == 0:
            self._write_completion_marker(output_path)
            print("✅ 所有表情包已生成完成，无需继续处理")
            print(f"📦 总计: {len(self.all_emojis)} 个表情包\n")
            return
        
        # 并行执行（带实时内存监控）
        success_count = 0
        fail_count = 0
        
        # 初始内存状态
        mem_start = _get_memory_usage()
        if mem_start:
            print(f"📊 初始内存: {mem_start['used']:.1f}GB / {mem_start['total']:.1f}GB ({mem_start['percent']:.1f}%)")
            print()
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = {executor.submit(_generate_single_emoji, task): task for task in tasks}
            
            # 收集结果（按完成顺序）
            last_mem_check = 0
            for i, future in enumerate(as_completed(futures), 1):
                task = futures[future]
                try:
                    result = future.result()
                    if result:
                        result["gesture_type"] = task["gesture_type"]
                        result["category"] = task["emoji_type"]
                        self.all_emojis.append(result)
                        
                        # 每10个任务检查一次内存
                        if i % 10 == 0:
                            mem = _get_memory_usage()
                            if mem:
                                mem_delta = mem['used'] - (mem_start['used'] if mem_start else 0)
                                status = "🟢" if mem['percent'] < 80 else "🟡" if mem['percent'] < 90 else "🔴"
                                print(f"[{task['index']}/{task['total']}] ✓ {task['base_name']} {status} {mem['percent']:.1f}% (+{mem_delta:.1f}GB)")
                            else:
                                print(f"[{task['index']}/{task['total']}] ✓ {task['base_name']}")
                        else:
                            print(f"[{task['index']}/{task['total']}] ✓ {task['base_name']}")
                        
                        success_count += 1
                    else:
                        print(f"[{task['index']}/{task['total']}] ✗ {task['base_name']} (生成失败)")
                        fail_count += 1
                except Exception as e:
                    print(f"[{task['index']}/{task['total']}] ✗ {task['base_name']} (错误: {e})")
                    fail_count += 1
        
        # 最终内存状态
        mem_end = _get_memory_usage()
        print()
        if mem_end and mem_start:
            mem_delta = mem_end['used'] - mem_start['used']
            print(f"📊 最终内存: {mem_end['used']:.1f}GB / {mem_end['total']:.1f}GB ({mem_end['percent']:.1f}%)")
            print(f"   内存增量: +{mem_delta:.1f}GB")
        
        print()
        print(f"✓ 表情包生成完成: {success_count} 个成功, {fail_count} 个失败")
        print(f"   输出目录: {output_path}")
        self._write_completion_marker(output_path)
    
    def organize_emojis(self):
        """分类存储表情包（已禁用 - 使用简化结构）"""
        print("\n[步骤5] 分类存储")
        print("-" * 70)
        print("⚠️  MaterialOrganizer已禁用，表情包直接保存在输出目录")
        print("✓ 跳过分类存储步骤")
        return
        
        # ❌ 以下代码已禁用（依赖MaterialOrganizer）
        # self.organizer.create_directory_structure()
        
        print(f"整理 {len(self.all_emojis)} 个表情包...")
        
        organized_count = 0
        
        for emoji_result in self.all_emojis:
            for spec_name, gif_info in emoji_result.get("gifs", {}).items():
                try:
                    metadata = {
                        "size": gif_info["size"],
                        "gesture_type": emoji_result.get("gesture_type", "unknown"),
                        "duration": gif_info["duration"],
                        "frames": gif_info["frames"],
                        "file_size_kb": gif_info["file_size_kb"],
                        "source_time": emoji_result["source"]["start"]
                    }
                    
                    category, subcategory = self.organizer.classify_emoji(
                        gif_info["path"],
                        metadata
                    )
                    
                    target_path = self.organizer.move_to_category(
                        gif_info["path"],
                        category,
                        subcategory,
                        copy=False
                    )
                    
                    self.organizer.add_to_index(target_path, metadata, "emojis")
                    organized_count += 1
                    
                except Exception as e:
                    print(f"  ⚠ 整理失败: {e}")
            
            if emoji_result.get("static"):
                try:
                    static_info = emoji_result["static"]
                    metadata = {
                        "size": static_info["size"],
                        "gesture_type": emoji_result.get("gesture_type", "unknown"),
                        "file_size_kb": static_info["file_size_kb"],
                        "source_time": emoji_result["source"]["start"]
                    }
                    
                    target_path = self.organizer.move_to_category(
                        static_info["path"],
                        "表情包站",
                        "高清截图",
                        copy=False
                    )
                    
                    self.organizer.add_to_index(target_path, metadata, "photos")
                    organized_count += 1
                    
                except Exception as e:
                    print(f"  ⚠ 整理失败: {e}")
        
        print(f"✓ 整理完成: {organized_count}个文件")
        
        # 显示输出位置
        print(f"\n📁 素材输出位置:")
        print(f"   {os.path.abspath(self.output_dir)}/表情包站/")
    
    def generate_reports(self):
        """生成报告（已禁用 - 使用简化结构）"""
        print("\n[步骤6] 生成报告和索引")
        print("-" * 70)
        print("⚠️  MaterialOrganizer已禁用，跳过报告生成")
        print("✓ 跳过报告步骤")
        return
        
        # ❌ 以下代码已禁用（依赖MaterialOrganizer）
        # self.organizer.save_indexes()
        # stats = self.organizer.generate_statistics()
        
        print("\n📊 统计报告:")
        print(f"  总文件数: {stats['total_files']}")
        print(f"  总大小: {stats['total_size_mb']:.2f}MB")
        print("\n按类型统计:")
        for type_name, type_stats in stats['by_type'].items():
            if type_stats['count'] > 0:
                print(f"  {type_name}: {type_stats['count']}个, {type_stats['size_mb']:.2f}MB")
        
        stats_path = Path(self.output_dir) / "元数据库" / "统计报告.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n统计报告已保存: {stats_path}")
    
    def run(self):
        """运行完整流程"""
        print("\n" + "=" * 70)
        print("开始表情包素材生成流程（优化版）")
        print("=" * 70)
        
        start_time = datetime.now()
        
        try:
            self.load_data()
            self.detect_dance_moments()
            # self.identify_gestures()  # 跳过姿态估计，加快速度
            self.analyze_thank_moments()
            self.generate_emojis()
            
            if len(self.all_emojis) > 0:
                self.organize_emojis()
                self.generate_reports()
            else:
                print("\n⚠ 未生成任何表情包")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("\n" + "=" * 70)
            print("✓ 表情包素材生成完成！")
            print("=" * 70)
            print(f"总用时: {duration/60:.1f}分钟")
            print(f"输出目录: {os.path.abspath(self.output_dir)}")
            print("\n查看结果:")
            print(f"  1. 表情包文件: {self.output_dir}/表情包站/")
            print(f"  2. 元数据索引: {self.output_dir}/元数据库/表情包索引.json")
            print()
        
        except Exception as e:
            print(f"\n✗ 错误: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='表情包素材生成 - 优化版')
    parser.add_argument('--video', type=str, help='视频文件路径')
    parser.add_argument('--output', type=str, help='输出目录')
    parser.add_argument('--max_emojis', type=int, default=20, help='最大表情包数量')
    parser.add_argument('--duration', type=int, help='分析时长（秒），不指定则分析全部')
    parser.add_argument('--motion_threshold', type=float, help='运动检测阈值（默认0.03，越小越敏感）')
    parser.add_argument('--recommend_threshold', type=float, help='推荐阈值（默认0.2，越小越宽松）')
    parser.add_argument('--max_workers', type=int, help='并行进程数（默认自动检测，建议2-6）')
    parser.add_argument('--fingerprint', type=str, help='输入数据指纹（用于完成标记）')
    args = parser.parse_args()
    
    # 使用命令行参数覆盖配置
    if args.video:
        config["video_path"] = args.video
    if args.output:
        config["output_dir"] = args.output
    if args.duration:
        config["test_duration"] = args.duration
    else:
        # 如果没有指定duration，移除限制（分析全部）
        config["test_duration"] = None
    
    # ✅ 阈值参数覆盖
    if args.motion_threshold is not None:
        config["motion_config"]["motion_threshold"] = args.motion_threshold
    if args.recommend_threshold is not None:
        config["multimodal_config"]["recommend_threshold"] = args.recommend_threshold
    
    # ✅ 并行度参数覆盖
    if args.max_workers is not None:
        config["max_workers"] = args.max_workers
    if args.fingerprint:
        config["fingerprint"] = args.fingerprint
    
    # ✅ 方案E: 不限制候选数量，生成尽可能多的候选供标注
    config["max_dance_moments"] = 999999  # 不限制cute/dance数量
    config["max_thank_moments"] = 999999  # 不限制thank数量
    config["max_sing_moments"] = 999999   # 不限制sing数量
    config["max_chat_moments"] = 999999   # 不限制chat数量
    config["max_upgrade_moments"] = 999999  # 不限制upgrade数量
    
    if not os.path.exists(config["video_path"]):
        print(f"错误: 视频文件不存在: {config['video_path']}")
        return
    
    generator = EmojiMaterialGenerator(config)
    success = generator.run()
    
    if success:
        print("✓ 全部完成！")
    else:
        print("✗ 生成过程中出现错误")


if __name__ == "__main__":
    main()

