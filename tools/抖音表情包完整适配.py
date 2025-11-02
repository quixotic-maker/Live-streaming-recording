#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音表情包完整适配工具

严格按照抖音官方规范：
- GIF大小：≤1MB（推荐500KB）
- 尺寸：240x240 / 480x480 / 720x720
- 时长：≤5秒
- 帧数：≤100帧
- 帧率：10-30fps
"""

import os
import sys
from PIL import Image
import imageio
import numpy as np
from pathlib import Path

class DouyinEmojiAdapter:
    """抖音表情包适配器"""
    
    SPECS = {
        'max_file_size': 1024 * 1024,      # 1MB
        'recommended_size': 500 * 1024,     # 500KB
        'dimensions': [(240, 240), (480, 480), (720, 720)],
        'max_duration': 5.0,
        'max_frames': 100,
        'fps_range': (10, 30),
    }
    
    def adapt_gif(self, input_path, output_dir):
        """适配GIF到抖音规格"""
        
        print(f"\n📝 处理: {os.path.basename(input_path)}")
        
        # 读取原始GIF
        try:
            frames = imageio.mimread(input_path)
        except Exception as e:
            print(f"  ✗ 读取失败: {e}")
            return {}
        
        if not frames:
            print(f"  ✗ GIF为空")
            return {}
        
        print(f"  原始: {len(frames)}帧, {os.path.getsize(input_path) / 1024:.1f}KB")
        
        results = {}
        
        for size in self.SPECS['dimensions']:
            size_name = f"{size[0]}x{size[1]}"
            output_path = os.path.join(
                output_dir,
                f"{Path(input_path).stem}_{size_name}.gif"
            )
            
            try:
                # 1. 控制帧数（不超过100帧）
                if len(frames) > self.SPECS['max_frames']:
                    step = len(frames) // self.SPECS['max_frames']
                    selected_frames = frames[::step]
                else:
                    selected_frames = frames
                
                # 2. 调整尺寸
                resized_frames = []
                for frame in selected_frames:
                    img = Image.fromarray(frame)
                    img = img.resize(size, Image.Resampling.LANCZOS)
                    resized_frames.append(np.array(img))
                
                # 3. 颜色量化（减小文件大小）
                quantized_frames = self._quantize_frames(resized_frames, colors=128)
                
                # 4. 生成GIF
                duration = self.SPECS['max_duration'] / len(quantized_frames)
                duration = max(duration, 1/30)  # 不超过30fps
                
                imageio.mimsave(
                    output_path,
                    quantized_frames,
                    duration=duration,
                    loop=0
                )
                
                # 5. 检查文件大小
                file_size = os.path.getsize(output_path)
                
                # 6. 如果过大，进一步压缩
                compression_level = 0
                while file_size > self.SPECS['max_file_size'] and compression_level < 3:
                    compression_level += 1
                    self._compress_further(output_path, quantized_frames, compression_level)
                    file_size = os.path.getsize(output_path)
                
                # 7. 验证
                is_valid = file_size <= self.SPECS['max_file_size']
                
                size_mb = file_size / 1024 / 1024
                status = '✓' if is_valid else '✗ 超过1MB'
                
                print(f"  {size_name}: {size_mb:.2f}MB ({file_size / 1024:.1f}KB) {status}")
                
                results[size_name] = {
                    'path': output_path,
                    'size': file_size,
                    'size_mb': round(size_mb, 2),
                    'size_kb': round(file_size / 1024, 1),
                    'valid': is_valid,
                    'frames': len(quantized_frames),
                    'status': status
                }
                
            except Exception as e:
                print(f"  ✗ {size_name} 生成失败: {e}")
                continue
        
        return results
    
    def _quantize_frames(self, frames, colors=128):
        """颜色量化"""
        quantized = []
        
        for frame in frames:
            img = Image.fromarray(frame)
            # 转换为调色板模式（减少颜色数）
            img = img.convert('P', palette=Image.ADAPTIVE, colors=colors)
            quantized.append(img)
        
        return quantized
    
    def _compress_further(self, gif_path, frames, level):
        """进一步压缩"""
        
        # 根据压缩级别调整颜色数
        colors_map = {1: 96, 2: 64, 3: 32}
        colors = colors_map.get(level, 64)
        
        # 更激进的颜色量化
        compressed_frames = self._quantize_frames(frames, colors=colors)
        
        # 重新保存
        imageio.mimsave(gif_path, compressed_frames, duration=0.1, loop=0)
    
    def batch_adapt(self, input_dir, output_dir):
        """批量适配"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 查找所有GIF文件
        gif_files = []
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                if file.lower().endswith('.gif'):
                    gif_files.append(os.path.join(root, file))
        
        if not gif_files:
            print("⚠️  未找到GIF文件")
            return {}
        
        print(f"\n📊 找到 {len(gif_files)} 个GIF文件")
        
        all_results = {}
        success_count = 0
        
        for gif_file in gif_files:
            results = self.adapt_gif(gif_file, output_dir)
            
            if results:
                all_results[os.path.basename(gif_file)] = results
                # 统计成功的规格数
                success_count += sum(1 for r in results.values() if r['valid'])
        
        return all_results, success_count
    
    def generate_report(self, results, output_file):
        """生成详细报告"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("抖音表情包适配报告\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("## 抖音官方规范\n\n")
            f.write(f"- 最大文件大小: {self.SPECS['max_file_size'] / 1024 / 1024}MB\n")
            f.write(f"- 推荐文件大小: {self.SPECS['recommended_size'] / 1024}KB\n")
            f.write(f"- 支持尺寸: {', '.join([f'{w}x{h}' for w, h in self.SPECS['dimensions']])}\n")
            f.write(f"- 最大时长: {self.SPECS['max_duration']}秒\n")
            f.write(f"- 最大帧数: {self.SPECS['max_frames']}帧\n")
            f.write(f"- 帧率范围: {self.SPECS['fps_range'][0]}-{self.SPECS['fps_range'][1]}fps\n\n")
            
            f.write("## 适配结果\n\n")
            
            total_files = len(results)
            total_valid = 0
            
            for gif_name, sizes in results.items():
                f.write(f"### {gif_name}\n\n")
                f.write("| 规格 | 文件大小 | 帧数 | 状态 |\n")
                f.write("|------|----------|------|------|\n")
                
                for size_name, info in sizes.items():
                    f.write(f"| {size_name} | {info['size_kb']}KB | {info['frames']} | {info['status']} |\n")
                    if info['valid']:
                        total_valid += 1
                
                f.write("\n")
            
            f.write("## 统计\n\n")
            f.write(f"- 处理文件: {total_files} 个\n")
            f.write(f"- 成功规格: {total_valid} 个\n")
            f.write(f"- 总规格数: {total_files * 3} 个\n")
            f.write(f"- 成功率: {total_valid / (total_files * 3) * 100:.1f}%\n")

def main():
    """主函数"""
    print("=" * 80)
    print("抖音表情包完整适配工具")
    print("=" * 80)
    print()
    print("功能：")
    print("  - 生成 240x240、480x480、720x720 三种规格")
    print("  - 自动压缩至 ≤1MB")
    print("  - 控制帧数 ≤100 帧")
    print("  - 优化颜色以减小文件大小")
    print()
    
    # 默认路径
    input_dir = os.path.expanduser("~/shanshan_materials/表情包素材库")
    output_dir = os.path.expanduser("~/shanshan_materials/表情包_抖音适配版")
    
    # 检查输入目录
    if not os.path.exists(input_dir):
        print(f"⚠️  输入目录不存在: {input_dir}")
        print()
        print("请指定输入目录（包含GIF文件）:")
        input_dir = input().strip()
        
        if not os.path.exists(input_dir):
            print("✗ 目录不存在，退出")
            sys.exit(1)
    
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print()
    
    # 创建适配器
    adapter = DouyinEmojiAdapter()
    
    # 批量适配
    results, success_count = adapter.batch_adapt(input_dir, output_dir)
    
    if results:
        # 生成报告
        report_file = os.path.join(output_dir, "适配报告.txt")
        adapter.generate_report(results, report_file)
        
        print()
        print("=" * 80)
        print("✅ 适配完成！")
        print("=" * 80)
        print()
        print(f"📁 输出目录: {output_dir}")
        print(f"📊 处理文件: {len(results)} 个")
        print(f"✓ 成功规格: {success_count} 个")
        print(f"📄 详细报告: {report_file}")
        print()
    else:
        print()
        print("⚠️  没有成功适配的文件")

if __name__ == "__main__":
    main()



