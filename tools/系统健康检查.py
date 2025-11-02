#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统健康检查工具

功能：
1. 检查环境依赖
2. 验证素材完整性
3. 检查磁盘空间
4. 验证配置文件
5. 生成健康报告
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


class HealthChecker:
    """系统健康检查器"""
    
    def __init__(self):
        """初始化检查器"""
        self.project_dir = Path(__file__).parent
        self.material_dir = Path.home() / "shanshan_materials"
        self.results = {
            "environment": {},
            "materials": {},
            "disk_space": {},
            "configs": {},
            "recommendations": []
        }
    
    def check_all(self) -> Dict:
        """运行所有检查"""
        print("=" * 70)
        print("系统健康检查")
        print("=" * 70)
        print()
        
        self.check_environment()
        self.check_materials()
        self.check_disk_space()
        self.check_configs()
        self.generate_recommendations()
        
        return self.results
    
    def check_environment(self):
        """检查环境依赖"""
        print("[1] 检查环境依赖")
        print("-" * 70)
        
        checks = {
            "python": ["python3", "--version"],
            "ffmpeg": ["ffmpeg", "-version"],
            "git": ["git", "--version"],
        }
        
        for name, cmd in checks.items():
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.split('\n')[0]
                    self.results["environment"][name] = {
                        "installed": True,
                        "version": version
                    }
                    print(f"  ✓ {name}: {version}")
                else:
                    self.results["environment"][name] = {
                        "installed": False,
                        "error": result.stderr
                    }
                    print(f"  ✗ {name}: 未安装或出错")
            except Exception as e:
                self.results["environment"][name] = {
                    "installed": False,
                    "error": str(e)
                }
                print(f"  ✗ {name}: {e}")
        
        # 检查Python包
        print("\n  Python包:")
        packages = ["numpy", "opencv-python", "pillow", "whisper"]
        for pkg in packages:
            try:
                __import__(pkg.replace("-", "_"))
                print(f"    ✓ {pkg}")
                self.results["environment"][f"python_{pkg}"] = {"installed": True}
            except ImportError:
                print(f"    ✗ {pkg} (未安装)")
                self.results["environment"][f"python_{pkg}"] = {"installed": False}
        
        print()
    
    def check_materials(self):
        """检查素材完整性"""
        print("[2] 检查素材完整性")
        print("-" * 70)
        
        # 检查主目录
        if not self.material_dir.exists():
            print(f"  ✗ 素材目录不存在: {self.material_dir}")
            self.results["materials"]["main_dir"] = False
            return
        
        print(f"  ✓ 素材目录: {self.material_dir}")
        self.results["materials"]["main_dir"] = True
        
        # 检查子目录
        expected_dirs = {
            "素材库_最新": "分类素材",
            "歌曲素材库": "歌曲数据",
            "关键帧截图": "截图",
            "精彩集锦": "视频集锦",
            "歌词字幕": "字幕文件"
        }
        
        for dir_name, description in expected_dirs.items():
            dir_path = self.material_dir / dir_name
            exists = dir_path.exists()
            self.results["materials"][dir_name] = {
                "exists": exists,
                "path": str(dir_path)
            }
            
            status = "✓" if exists else "✗"
            print(f"  {status} {description}: {dir_name}")
            
            # 统计文件数量
            if exists:
                file_count = len(list(dir_path.rglob("*")))
                self.results["materials"][dir_name]["file_count"] = file_count
                print(f"     文件数: {file_count}")
        
        # 检查关键JSON文件
        print("\n  关键数据文件:")
        key_files = [
            "素材库_最新/singing_素材.json",
            "素材库_最新/gift_素材.json",
            "素材库_最新/chat_素材.json",
            "歌曲素材库/歌曲列表.json"
        ]
        
        for file_path in key_files:
            full_path = self.material_dir / file_path
            exists = full_path.exists()
            status = "✓" if exists else "✗"
            print(f"    {status} {file_path}")
            
            if exists:
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 获取统计信息
                    if "total_count" in data:
                        print(f"       片段数: {data['total_count']}")
                    elif "total_songs" in data:
                        print(f"       歌曲数: {data['total_songs']}")
                    
                    self.results["materials"][file_path] = {
                        "exists": True,
                        "valid": True,
                        "data": data.get("total_count") or data.get("total_songs")
                    }
                except Exception as e:
                    print(f"       ⚠ 读取失败: {e}")
                    self.results["materials"][file_path] = {
                        "exists": True,
                        "valid": False,
                        "error": str(e)
                    }
            else:
                self.results["materials"][file_path] = {"exists": False}
        
        print()
    
    def check_disk_space(self):
        """检查磁盘空间"""
        print("[3] 检查磁盘空间")
        print("-" * 70)
        
        # 检查系统磁盘
        try:
            import shutil
            
            # 素材目录所在磁盘
            total, used, free = shutil.disk_usage(self.material_dir)
            
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            used_percent = (used / total) * 100
            
            print(f"  磁盘: {self.material_dir}")
            print(f"  总容量: {total_gb:.1f} GB")
            print(f"  已使用: {used_gb:.1f} GB ({used_percent:.1f}%)")
            print(f"  可用: {free_gb:.1f} GB")
            
            self.results["disk_space"] = {
                "path": str(self.material_dir),
                "total_gb": round(total_gb, 1),
                "used_gb": round(used_gb, 1),
                "free_gb": round(free_gb, 1),
                "used_percent": round(used_percent, 1)
            }
            
            # 警告
            if free_gb < 50:
                print(f"  ⚠ 警告: 可用空间不足50GB")
                self.results["recommendations"].append(
                    "磁盘空间不足，建议清理或扩容"
                )
            elif free_gb < 100:
                print(f"  ⚠ 提示: 可用空间较少")
            else:
                print(f"  ✓ 空间充足")
            
            # 检查素材大小
            print("\n  素材占用:")
            if self.material_dir.exists():
                total_size = sum(
                    f.stat().st_size for f in self.material_dir.rglob('*') 
                    if f.is_file()
                )
                size_gb = total_size / (1024**3)
                print(f"  总大小: {size_gb:.2f} GB")
                self.results["disk_space"]["material_size_gb"] = round(size_gb, 2)
        
        except Exception as e:
            print(f"  ✗ 检查失败: {e}")
            self.results["disk_space"]["error"] = str(e)
        
        print()
    
    def check_configs(self):
        """检查配置文件"""
        print("[4] 检查配置文件")
        print("-" * 70)
        
        config_file = self.project_dir / "config" / "config.ini"
        
        if config_file.exists():
            print(f"  ✓ 配置文件存在: {config_file}")
            self.results["configs"]["config.ini"] = {"exists": True}
            
            # 读取关键配置
            try:
                import configparser
                config = configparser.ConfigParser()
                config.read(config_file, encoding='utf-8')
                
                print("\n  关键配置:")
                key_settings = [
                    ("直播配置", "是否启用时间窗口监测(是/否)"),
                    ("直播配置", "监测开始时间"),
                    ("直播配置", "监测结束时间"),
                    ("录制配置", "自动合并分段视频(是/否)"),
                ]
                
                for section, key in key_settings:
                    try:
                        value = config.get(section, key)
                        print(f"    {key}: {value}")
                    except:
                        pass
            
            except Exception as e:
                print(f"  ⚠ 读取配置失败: {e}")
        else:
            print(f"  ✗ 配置文件不存在")
            self.results["configs"]["config.ini"] = {"exists": False}
            self.results["recommendations"].append(
                "配置文件不存在，请检查 config/config.ini"
            )
        
        print()
    
    def generate_recommendations(self):
        """生成建议"""
        print("[5] 系统建议")
        print("-" * 70)
        
        # 基于检查结果生成建议
        if not self.results["environment"].get("ffmpeg", {}).get("installed"):
            self.results["recommendations"].append(
                "安装FFmpeg: sudo apt install ffmpeg"
            )
        
        if not self.material_dir.exists():
            self.results["recommendations"].append(
                f"创建素材目录: mkdir -p {self.material_dir}"
            )
        
        if not self.results["materials"].get("素材库_最新", {}).get("exists"):
            self.results["recommendations"].append(
                "运行 '重新分类素材.py' 生成分类素材"
            )
        
        if not self.results["materials"].get("歌曲素材库", {}).get("exists"):
            self.results["recommendations"].append(
                "运行 '整理歌曲素材.py' 生成歌曲列表"
            )
        
        # 显示建议
        if self.results["recommendations"]:
            for i, rec in enumerate(self.results["recommendations"], 1):
                print(f"  {i}. {rec}")
        else:
            print("  ✓ 系统状态良好，无特别建议")
        
        print()
    
    def save_report(self, output_file: str = None):
        """保存健康报告"""
        if output_file is None:
            output_file = self.project_dir / f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        self.results["check_time"] = datetime.now().isoformat()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 健康报告已保存: {output_file}")
        
        # 也生成文本版
        txt_file = str(output_file).replace('.json', '.txt')
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("系统健康检查报告\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"检查时间: {self.results['check_time']}\n\n")
            
            f.write("环境依赖:\n")
            for name, info in self.results["environment"].items():
                status = "✓" if info.get("installed") else "✗"
                f.write(f"  {status} {name}\n")
            
            f.write("\n素材完整性:\n")
            for name, info in self.results["materials"].items():
                if isinstance(info, dict):
                    status = "✓" if info.get("exists", info.get("main_dir")) else "✗"
                    f.write(f"  {status} {name}\n")
            
            f.write("\n磁盘空间:\n")
            if "free_gb" in self.results["disk_space"]:
                f.write(f"  可用: {self.results['disk_space']['free_gb']} GB\n")
                f.write(f"  使用率: {self.results['disk_space']['used_percent']}%\n")
            
            if self.results["recommendations"]:
                f.write("\n建议:\n")
                for i, rec in enumerate(self.results["recommendations"], 1):
                    f.write(f"  {i}. {rec}\n")
        
        print(f"✓ 文本报告已保存: {txt_file}")
    
    def get_summary(self) -> str:
        """获取摘要"""
        total_checks = 0
        passed_checks = 0
        
        # 环境检查
        for info in self.results["environment"].values():
            total_checks += 1
            if info.get("installed"):
                passed_checks += 1
        
        # 素材检查
        for info in self.results["materials"].values():
            if isinstance(info, dict):
                total_checks += 1
                if info.get("exists") or info.get("main_dir"):
                    passed_checks += 1
        
        pass_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        status_emoji = "✅" if pass_rate >= 80 else "⚠️" if pass_rate >= 60 else "❌"
        
        return f"{status_emoji} 系统健康度: {passed_checks}/{total_checks} ({pass_rate:.0f}%)"


def main():
    """主函数"""
    try:
        checker = HealthChecker()
        results = checker.check_all()
        
        # 保存报告
        checker.save_report()
        
        # 显示摘要
        print("=" * 70)
        print(checker.get_summary())
        print("=" * 70)
        print()
        
        # 退出码
        if len(results["recommendations"]) > 0:
            sys.exit(1)  # 有建议 = 需要改进
        else:
            sys.exit(0)  # 完美
    
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()



