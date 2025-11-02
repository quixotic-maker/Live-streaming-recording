#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
素材管理器 - 分层存储与索引管理

功能：
1. 创建分层目录结构
2. 文件自动分类存储
3. 生成元数据索引
4. 生成批量处理脚本
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MaterialOrganizer:
    """
    素材管理器
    
    功能：
    - 创建标准化目录结构
    - 自动分类文件
    - 生成索引和元数据
    - 生成批量处理脚本
    """
    
    # 标准目录结构
    DIRECTORY_STRUCTURE = {
        "视频站": {
            "完整直播": {},
            "歌曲视频": {},
            "精选集锦": {}
        },
        "歌曲站": {
            "视频": {},
            "音频": {
                "MP3": {},
                "FLAC": {}
            },
            "歌词": {}
        },
        "表情包站": {
            "抖音专用": {
                "手势舞": {
                    "240x240": {},
                    "300x300": {},
                    "512x512": {}
                },
                "感谢表情": {
                    "240x240": {},
                    "300x300": {},
                    "512x512": {}
                },
                "比心手势": {
                    "240x240": {},
                    "300x300": {},
                    "512x512": {}
                }
            },
            "通用表情包": {
                "大尺寸": {},
                "动画GIF": {}
            },
            "高清截图": {}
        },
        "照片站": {
            "高清截图": {
                "唱歌瞬间": {},
                "感谢时刻": {},
                "闲聊瞬间": {}
            },
            "手势特写": {
                "比心": {},
                "挥手": {},
                "手势舞": {}
            },
            "表情特写": {
                "微笑": {},
                "惊喜": {},
                "开心": {}
            },
            "壁纸": {
                "竖屏": {},
                "横屏": {}
            }
        },
        "元数据库": {}
    }
    
    def __init__(self, base_dir: str):
        """
        初始化素材管理器
        
        Args:
            base_dir: 素材库根目录
        """
        self.base_dir = Path(base_dir)
        self.metadata = {
            "videos": {},
            "songs": {},
            "emojis": {},
            "photos": {}
        }
        logger.info(f"MaterialOrganizer initialized at: {self.base_dir}")
    
    def create_directory_structure(self):
        """
        创建完整的目录结构
        """
        logger.info("创建目录结构...")
        
        def create_dirs(parent_path: Path, structure: Dict):
            """递归创建目录"""
            for name, sub_structure in structure.items():
                dir_path = parent_path / name
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"创建目录: {dir_path}")
                
                if sub_structure:
                    create_dirs(dir_path, sub_structure)
        
        create_dirs(self.base_dir, self.DIRECTORY_STRUCTURE)
        
        logger.info(f"目录结构创建完成: {self.base_dir}")
    
    def classify_emoji(
        self,
        file_path: str,
        metadata: Dict
    ) -> Tuple[str, str]:
        """
        分类表情包文件
        
        Args:
            file_path: 文件路径
            metadata: 元数据
        
        Returns:
            (category, subcategory) 元组
        """
        # 判断文件类型
        ext = Path(file_path).suffix.lower()
        
        # GIF动图
        if ext == '.gif':
            # 提取尺寸信息
            size = metadata.get('size', (0, 0))
            width = size[0] if isinstance(size, (tuple, list)) else size
            
            # 抖音专用规格
            if width in [240, 300, 512]:
                category = "表情包站/抖音专用"
                
                # 根据类型分类
                gesture_type = metadata.get('gesture_type', 'unknown')
                if 'dance' in gesture_type.lower():
                    subcategory = f"手势舞/{width}x{width}"
                elif 'thank' in gesture_type.lower() or 'wave' in gesture_type.lower():
                    subcategory = f"感谢表情/{width}x{width}"
                elif 'heart' in gesture_type.lower():
                    subcategory = f"比心手势/{width}x{width}"
                else:
                    subcategory = f"感谢表情/{width}x{width}"  # 默认
            else:
                # 通用规格
                category = "表情包站/通用表情包"
                subcategory = "动画GIF" if width <= 720 else "大尺寸"
        
        # PNG/JPG静态图
        elif ext in ['.png', '.jpg', '.jpeg']:
            category = "表情包站"
            subcategory = "高清截图"
        
        else:
            category = "表情包站/通用表情包"
            subcategory = "其他"
        
        return category, subcategory
    
    def classify_photo(
        self,
        file_path: str,
        metadata: Dict
    ) -> Tuple[str, str]:
        """
        分类照片文件
        
        Args:
            file_path: 文件路径
            metadata: 元数据
        
        Returns:
            (category, subcategory) 元组
        """
        # 提取元数据
        content_type = metadata.get('content_type', 'unknown')
        feature_type = metadata.get('feature_type', 'unknown')
        size = metadata.get('size', (0, 0))
        
        # 判断是否为壁纸尺寸
        if size[0] >= 1920 or size[1] >= 1920:
            category = "照片站/壁纸"
            subcategory = "竖屏" if size[1] > size[0] else "横屏"
            return category, subcategory
        
        # 按特征分类
        if 'gesture' in feature_type.lower():
            category = "照片站/手势特写"
            if 'heart' in feature_type.lower():
                subcategory = "比心"
            elif 'wave' in feature_type.lower():
                subcategory = "挥手"
            else:
                subcategory = "手势舞"
        
        elif 'emotion' in feature_type.lower() or 'face' in feature_type.lower():
            category = "照片站/表情特写"
            if 'smile' in feature_type.lower():
                subcategory = "微笑"
            elif 'surprise' in feature_type.lower():
                subcategory = "惊喜"
            else:
                subcategory = "开心"
        
        else:
            # 按内容类型分类
            category = "照片站/高清截图"
            if 'singing' in content_type.lower():
                subcategory = "唱歌瞬间"
            elif 'gift' in content_type.lower() or 'thank' in content_type.lower():
                subcategory = "感谢时刻"
            else:
                subcategory = "闲聊瞬间"
        
        return category, subcategory
    
    def move_to_category(
        self,
        src_path: str,
        category: str,
        subcategory: str,
        copy: bool = False
    ) -> str:
        """
        移动文件到指定分类
        
        Args:
            src_path: 源文件路径
            category: 分类（如"表情包站/抖音专用"）
            subcategory: 子分类（如"手势舞/240x240"）
            copy: 是否复制（False为移动）
        
        Returns:
            目标文件路径
        """
        src = Path(src_path)
        
        if not src.exists():
            raise FileNotFoundError(f"源文件不存在: {src_path}")
        
        # 构建目标路径
        target_dir = self.base_dir / category / subcategory
        target_dir.mkdir(parents=True, exist_ok=True)
        
        target_path = target_dir / src.name
        
        # 如果目标文件已存在，添加序号
        if target_path.exists():
            stem = src.stem
            suffix = src.suffix
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{stem}_{counter}{suffix}"
                counter += 1
        
        # 复制或移动
        if copy:
            shutil.copy2(src, target_path)
            logger.debug(f"复制文件: {src} -> {target_path}")
        else:
            shutil.move(str(src), str(target_path))
            logger.debug(f"移动文件: {src} -> {target_path}")
        
        return str(target_path)
    
    def add_to_index(
        self,
        file_path: str,
        metadata: Dict,
        index_type: str
    ):
        """
        添加文件到索引
        
        Args:
            file_path: 文件路径
            metadata: 元数据
            index_type: 索引类型（videos/songs/emojis/photos）
        """
        # 生成唯一ID
        file_id = self._generate_file_id(file_path)
        
        # 添加基本信息
        index_entry = {
            "id": file_id,
            "path": str(file_path),
            "filename": Path(file_path).name,
            "size_bytes": os.path.getsize(file_path),
            "created_at": datetime.now().isoformat(),
            **metadata
        }
        
        self.metadata[index_type][file_id] = index_entry
        logger.debug(f"添加到索引 [{index_type}]: {file_id}")
    
    def save_indexes(self):
        """
        保存所有索引到文件
        """
        metadata_dir = self.base_dir / "元数据库"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        index_files = {
            "videos": "视频索引.json",
            "songs": "歌曲索引.json",
            "emojis": "表情包索引.json",
            "photos": "照片索引.json"
        }
        
        for index_type, filename in index_files.items():
            index_path = metadata_dir / filename
            
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(
                    self.metadata[index_type],
                    f,
                    ensure_ascii=False,
                    indent=2
                )
            
            count = len(self.metadata[index_type])
            logger.info(f"保存索引 [{index_type}]: {count}条记录 -> {index_path}")
    
    def load_indexes(self):
        """
        从文件加载所有索引
        """
        metadata_dir = self.base_dir / "元数据库"
        
        if not metadata_dir.exists():
            logger.warning("元数据目录不存在")
            return
        
        index_files = {
            "videos": "视频索引.json",
            "songs": "歌曲索引.json",
            "emojis": "表情包索引.json",
            "photos": "照片索引.json"
        }
        
        for index_type, filename in index_files.items():
            index_path = metadata_dir / filename
            
            if index_path.exists():
                with open(index_path, 'r', encoding='utf-8') as f:
                    self.metadata[index_type] = json.load(f)
                
                count = len(self.metadata[index_type])
                logger.info(f"加载索引 [{index_type}]: {count}条记录")
            else:
                logger.debug(f"索引文件不存在: {index_path}")
    
    def generate_statistics(self) -> Dict:
        """
        生成统计报告
        
        Returns:
            统计信息字典
        """
        stats = {
            "total_files": 0,
            "total_size_mb": 0,
            "by_type": {},
            "by_category": {},
            "generated_at": datetime.now().isoformat()
        }
        
        for index_type, items in self.metadata.items():
            count = len(items)
            total_size = sum(item.get('size_bytes', 0) for item in items.values())
            
            stats["by_type"][index_type] = {
                "count": count,
                "size_mb": round(total_size / 1024 / 1024, 2)
            }
            
            stats["total_files"] += count
            stats["total_size_mb"] += total_size / 1024 / 1024
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        
        return stats
    
    def generate_download_script(
        self,
        category: str,
        output_path: str,
        script_type: str = "bash"
    ):
        """
        生成批量下载脚本
        
        Args:
            category: 分类（emojis/photos等）
            output_path: 输出脚本路径
            script_type: 脚本类型（bash/python）
        """
        if category not in self.metadata:
            raise ValueError(f"未知分类: {category}")
        
        items = self.metadata[category]
        
        if script_type == "bash":
            self._generate_bash_script(items, output_path)
        elif script_type == "python":
            self._generate_python_script(items, output_path)
        else:
            raise ValueError(f"未知脚本类型: {script_type}")
        
        logger.info(f"生成下载脚本: {output_path}")
    
    def _generate_bash_script(self, items: Dict, output_path: str):
        """生成Bash脚本"""
        lines = [
            "#!/bin/bash",
            "# 批量操作脚本",
            f"# 生成时间: {datetime.now().isoformat()}",
            f"# 文件数量: {len(items)}",
            "",
            "set -e",
            "",
            "echo '开始处理文件...'",
            ""
        ]
        
        for file_id, item in items.items():
            file_path = item.get('path', '')
            filename = item.get('filename', '')
            
            if file_path:
                lines.append(f"# {file_id}: {filename}")
                lines.append(f"# cp '{file_path}' ./")
                lines.append("")
        
        lines.append("echo '处理完成！'")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        # 添加执行权限
        os.chmod(output_path, 0o755)
    
    def _generate_python_script(self, items: Dict, output_path: str):
        """生成Python脚本"""
        lines = [
            "#!/usr/bin/env python3",
            "# -*- coding: utf-8 -*-",
            "# 批量操作脚本",
            f"# 生成时间: {datetime.now().isoformat()}",
            f"# 文件数量: {len(items)}",
            "",
            "import shutil",
            "from pathlib import Path",
            "",
            "files = [",
        ]
        
        for file_id, item in items.items():
            file_path = item.get('path', '')
            if file_path:
                lines.append(f"    '{file_path}',")
        
        lines.extend([
            "]",
            "",
            "output_dir = Path('./downloaded')",
            "output_dir.mkdir(exist_ok=True)",
            "",
            "for i, file_path in enumerate(files, 1):",
            "    src = Path(file_path)",
            "    if src.exists():",
            "        dst = output_dir / src.name",
            "        shutil.copy2(src, dst)",
            "        print(f'{i}/{len(files)}: {src.name}')",
            "",
            "print('处理完成！')"
        ])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        # 添加执行权限
        os.chmod(output_path, 0o755)
    
    def _generate_file_id(self, file_path: str) -> str:
        """
        生成文件唯一ID
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件ID
        """
        # 使用文件路径的MD5哈希前8位
        hash_obj = hashlib.md5(file_path.encode())
        return hash_obj.hexdigest()[:8]
    
    def organize_emojis(
        self,
        source_dir: str,
        metadata_file: Optional[str] = None
    ) -> int:
        """
        整理表情包文件夹
        
        Args:
            source_dir: 源文件夹
            metadata_file: 元数据文件（可选）
        
        Returns:
            整理的文件数量
        """
        logger.info(f"整理表情包: {source_dir}")
        
        # 加载元数据（如果提供）
        file_metadata = {}
        if metadata_file and os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                file_metadata = json.load(f)
        
        source_path = Path(source_dir)
        count = 0
        
        # 遍历所有文件
        for file_path in source_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            # 跳过元数据文件
            if file_path.name.endswith('_metadata.json'):
                continue
            
            # 获取文件元数据
            file_key = file_path.stem
            metadata = file_metadata.get(file_key, {})
            
            # 分类文件
            try:
                category, subcategory = self.classify_emoji(str(file_path), metadata)
                
                # 移动到目标位置
                target_path = self.move_to_category(
                    str(file_path),
                    category,
                    subcategory,
                    copy=False
                )
                
                # 添加到索引
                self.add_to_index(target_path, metadata, "emojis")
                
                count += 1
                
            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")
        
        logger.info(f"表情包整理完成: {count}个文件")
        
        return count


# ============================================================
# 主函数 - 示例用法
# ============================================================

def main():
    """示例：如何使用素材管理器"""
    
    print("=" * 60)
    print("素材管理器 - 示例")
    print("=" * 60)
    
    # 创建管理器
    organizer = MaterialOrganizer("素材库_测试")
    
    # ========== 示例1: 创建目录结构 ==========
    print("\n[示例1] 创建目录结构")
    print("-" * 60)
    
    organizer.create_directory_structure()
    print("目录结构创建完成")
    
    # ========== 示例2: 分类文件 ==========
    print("\n[示例2] 分类表情包")
    print("-" * 60)
    
    # 模拟表情包元数据
    emoji_metadata = {
        "size": (240, 240),
        "gesture_type": "dance",
        "confidence": 0.85
    }
    
    category, subcategory = organizer.classify_emoji(
        "emoji_001_240x240.gif",
        emoji_metadata
    )
    print(f"分类结果: {category}/{subcategory}")
    
    # ========== 示例3: 添加到索引 ==========
    print("\n[示例3] 添加到索引")
    print("-" * 60)
    
    # 模拟添加文件到索引
    organizer.add_to_index(
        "素材库_测试/表情包站/抖音专用/手势舞/240x240/emoji_001.gif",
        emoji_metadata,
        "emojis"
    )
    print("已添加到表情包索引")
    
    # ========== 示例4: 生成统计 ==========
    print("\n[示例4] 生成统计")
    print("-" * 60)
    
    stats = organizer.generate_statistics()
    print(f"总文件数: {stats['total_files']}")
    print(f"总大小: {stats['total_size_mb']}MB")
    print("\n按类型统计:")
    for type_name, type_stats in stats['by_type'].items():
        print(f"  {type_name}: {type_stats['count']}个文件, {type_stats['size_mb']}MB")
    
    # ========== 示例5: 保存索引 ==========
    print("\n[示例5] 保存索引")
    print("-" * 60)
    
    organizer.save_indexes()
    print("索引已保存")
    
    # ========== 示例6: 生成脚本 ==========
    print("\n[示例6] 生成下载脚本")
    print("-" * 60)
    
    if organizer.metadata['emojis']:
        organizer.generate_download_script(
            "emojis",
            "下载表情包.sh",
            "bash"
        )
        print("Bash脚本已生成: 下载表情包.sh")
        
        organizer.generate_download_script(
            "emojis",
            "下载表情包.py",
            "python"
        )
        print("Python脚本已生成: 下载表情包.py")
    
    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    main()



