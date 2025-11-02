#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试抖音表情包规格

功能：
1. 生成测试矩阵（不同尺寸、时长、帧率、压缩组合）
2. 测试文件大小和质量
3. 生成推荐报告
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from emoji_generator import EmojiGenerator


class EmojiSpecTester:
    """抖音表情包规格测试器"""
    
    # 测试参数矩阵
    TEST_SIZES = [(240, 240), (300, 300), (512, 512), (720, 720)]
    TEST_DURATIONS = [1.0, 2.0, 3.0, 5.0]
    TEST_FPS_LIST = [10, 15, 30]
    TEST_QUALITY = ["high", "medium", "low"]
    
    def __init__(self, video_path: str, test_time: float = 132.5):
        """
        初始化测试器
        
        Args:
            video_path: 测试视频路径
            test_time: 测试时间点（秒）
        """
        self.video_path = video_path
        self.test_time = test_time
        self.results = []
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        print(f"初始化测试器:")
        print(f"  视频: {video_path}")
        print(f"  测试时间: {test_time}秒")
    
    def run_full_test(self, output_dir: str = "抖音规格测试"):
        """
        运行完整测试矩阵
        
        Args:
            output_dir: 输出目录
        """
        print("\n" + "=" * 70)
        print("开始抖音表情包规格测试")
        print("=" * 70)
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 计算总测试数
        total_tests = len(self.TEST_SIZES) * len(self.TEST_DURATIONS) * len(self.TEST_FPS_LIST)
        
        print(f"\n测试矩阵:")
        print(f"  尺寸: {len(self.TEST_SIZES)}种")
        print(f"  时长: {len(self.TEST_DURATIONS)}种")
        print(f"  帧率: {len(self.TEST_FPS_LIST)}种")
        print(f"  总计: {total_tests}个测试用例")
        print()
        
        test_num = 0
        
        # 遍历所有组合
        for size in self.TEST_SIZES:
            for duration in self.TEST_DURATIONS:
                for fps in self.TEST_FPS_LIST:
                    test_num += 1
                    
                    print(f"[{test_num}/{total_tests}] 测试: {size[0]}x{size[1]}, {duration}s, {fps}fps")
                    
                    try:
                        result = self._test_single_spec(
                            size=size,
                            duration=duration,
                            fps=fps,
                            output_dir=output_path
                        )
                        
                        self.results.append(result)
                        
                        # 显示结果
                        file_size = result["file_size_kb"]
                        quality_status = "✓" if file_size <= 1000 else "✗"
                        print(f"  {quality_status} 文件大小: {file_size:.2f}KB")
                        
                    except Exception as e:
                        print(f"  ✗ 测试失败: {e}")
                        self.results.append({
                            "size": size,
                            "duration": duration,
                            "fps": fps,
                            "error": str(e),
                            "success": False
                        })
        
        print("\n" + "=" * 70)
        print("测试完成！")
        print("=" * 70)
        
        # 生成报告
        self._generate_report(output_path)
    
    def _test_single_spec(
        self,
        size: tuple,
        duration: float,
        fps: int,
        output_dir: Path
    ) -> dict:
        """
        测试单个规格
        
        Args:
            size: 尺寸 (width, height)
            duration: 时长（秒）
            fps: 帧率
            output_dir: 输出目录
        
        Returns:
            测试结果字典
        """
        # 创建生成器
        generator = EmojiGenerator({
            "default_fps": fps
        })
        
        # 提取帧
        start_time = self.test_time
        end_time = self.test_time + duration
        
        frames = generator.extract_frames(
            self.video_path,
            start_time,
            end_time,
            fps=fps
        )
        
        # 生成GIF文件名
        filename = f"test_{size[0]}x{size[1]}_{duration}s_{fps}fps.gif"
        output_path = output_dir / filename
        
        # 创建GIF
        gif_info = generator.create_gif(
            frames=frames,
            output_path=str(output_path),
            size=size,
            max_size_kb=1000,
            fps=fps
        )
        
        # 评估质量
        quality_score = self._evaluate_quality(gif_info, size, duration, fps)
        
        return {
            "size": size,
            "duration": duration,
            "fps": fps,
            "frames": gif_info["frames"],
            "file_size_kb": gif_info["file_size_kb"],
            "file_path": str(output_path),
            "quality_score": quality_score,
            "success": True,
            "meets_douyin_requirements": gif_info["file_size_kb"] <= 1000
        }
    
    def _evaluate_quality(
        self,
        gif_info: dict,
        size: tuple,
        duration: float,
        fps: int
    ) -> float:
        """
        评估GIF质量
        
        评分标准：
        - 文件大小适中（不超过1MB）: 40分
        - 尺寸合适（240-512px）: 20分
        - 帧率合适（10-15fps）: 20分
        - 时长合适（2-3秒）: 20分
        
        Args:
            gif_info: GIF信息
            size: 尺寸
            duration: 时长
            fps: 帧率
        
        Returns:
            质量得分 (0-100)
        """
        score = 0
        
        # 1. 文件大小评分（40分）
        file_size = gif_info["file_size_kb"]
        if file_size <= 500:
            score += 40
        elif file_size <= 800:
            score += 30
        elif file_size <= 1000:
            score += 20
        else:
            score += 10
        
        # 2. 尺寸评分（20分）
        width = size[0]
        if width >= 240 and width <= 512:
            score += 20
        elif width == 720:
            score += 10
        
        # 3. 帧率评分（20分）
        if fps == 15:
            score += 20
        elif fps == 10:
            score += 15
        elif fps == 30:
            score += 10
        
        # 4. 时长评分（20分）
        if duration >= 2.0 and duration <= 3.0:
            score += 20
        elif duration == 1.0 or duration == 5.0:
            score += 10
        
        return score
    
    def _generate_report(self, output_dir: Path):
        """
        生成测试报告
        
        Args:
            output_dir: 输出目录
        """
        report_path = output_dir / "抖音规格测试报告.txt"
        json_path = output_dir / "测试结果.json"
        
        # 保存JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # 生成文本报告
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("抖音表情包规格测试报告\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"测试视频: {self.video_path}\n")
            f.write(f"测试时间点: {self.test_time}秒\n")
            f.write(f"总测试数: {len(self.results)}\n\n")
            
            # 统计
            success_count = sum(1 for r in self.results if r.get("success"))
            meets_requirements = sum(1 for r in self.results if r.get("meets_douyin_requirements"))
            
            f.write("测试统计:\n")
            f.write(f"  成功: {success_count}/{len(self.results)}\n")
            f.write(f"  符合抖音要求(<1MB): {meets_requirements}/{len(self.results)}\n\n")
            
            # 推荐规格（按质量得分排序）
            successful_results = [r for r in self.results if r.get("success")]
            sorted_results = sorted(
                successful_results,
                key=lambda x: x.get("quality_score", 0),
                reverse=True
            )
            
            f.write("=" * 70 + "\n")
            f.write("推荐规格（TOP 10）\n")
            f.write("=" * 70 + "\n\n")
            
            for i, result in enumerate(sorted_results[:10], 1):
                size = result["size"]
                f.write(f"{i}. {size[0]}x{size[1]}, {result['duration']}s, {result['fps']}fps\n")
                f.write(f"   文件大小: {result['file_size_kb']:.2f}KB\n")
                f.write(f"   质量得分: {result['quality_score']}/100\n")
                f.write(f"   符合要求: {'是' if result['meets_douyin_requirements'] else '否'}\n")
                f.write(f"   文件路径: {result['file_path']}\n\n")
            
            # 详细结果
            f.write("=" * 70 + "\n")
            f.write("详细测试结果\n")
            f.write("=" * 70 + "\n\n")
            
            # 按尺寸分组
            for size in self.TEST_SIZES:
                f.write(f"\n尺寸: {size[0]}x{size[1]}\n")
                f.write("-" * 70 + "\n")
                
                size_results = [r for r in self.results if r.get("size") == size and r.get("success")]
                
                for result in size_results:
                    status = "✓" if result["meets_douyin_requirements"] else "✗"
                    f.write(f"  {status} {result['duration']}s, {result['fps']}fps - ")
                    f.write(f"{result['file_size_kb']:.2f}KB (得分: {result['quality_score']})\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("测试完成！\n")
            f.write("=" * 70 + "\n")
        
        print(f"\n报告已生成:")
        print(f"  文本报告: {report_path}")
        print(f"  JSON数据: {json_path}")
        
        # 显示推荐规格
        if sorted_results:
            print(f"\n🏆 推荐规格:")
            top_result = sorted_results[0]
            size = top_result["size"]
            print(f"  尺寸: {size[0]}x{size[1]}")
            print(f"  时长: {top_result['duration']}秒")
            print(f"  帧率: {top_result['fps']}fps")
            print(f"  文件大小: {top_result['file_size_kb']:.2f}KB")
            print(f"  质量得分: {top_result['quality_score']}/100")


def main():
    """主函数"""
    
    print("\n" + "=" * 70)
    print("抖音表情包规格测试工具")
    print("=" * 70 + "\n")
    
    # 视频路径
    video_path = "/home/liu/videos/shanshan/抖音直播/观山/观山_2025-10-30.mp4"
    
    if not os.path.exists(video_path):
        print(f"错误: 视频文件不存在: {video_path}")
        print("\n请修改video_path变量为实际的视频路径")
        return
    
    # 创建测试器
    tester = EmojiSpecTester(
        video_path=video_path,
        test_time=132.5  # 使用一个感谢时刻作为测试点
    )
    
    # 运行测试
    tester.run_full_test()
    
    print("\n✓ 所有测试完成！")
    print("\n查看测试结果:")
    print("  1. 查看测试GIF文件: ls 抖音规格测试/")
    print("  2. 查看测试报告: cat 抖音规格测试/抖音规格测试报告.txt")
    print()


if __name__ == "__main__":
    main()



