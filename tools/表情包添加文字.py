#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表情包文字添加工具

功能：
1. 自动添加预设文字
2. 半自动模式（从候选列表选择）
3. 自定义文字
4. 支持多种文字样式和位置
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import json


class EmojiTextAdder:
    """表情包文字添加器"""
    
    def __init__(self):
        """初始化"""
        # 预设文字库（根据表情包类型）
        self.preset_texts = {
            "dance": [
                "手势舞", "来跳舞", "舞起来", 
                "666", "太强了", "会跳舞",
                "学会了", "教我", "跟着跳"
            ],
            "thanks": [
                "谢谢", "谢谢老板", "爱你们",
                "感谢支持", "么么哒", "比心",
                "谢谢宝宝", "爱了爱了", "感恩"
            ],
            "gift_effect": [
                "哇", "豪气", "大气",
                "土豪", "壕无人性", "厉害了",
                "感谢送礼", "谢谢礼物", "爱你"
            ]
        }
        
        # 常用字体（按优先级）
        self.font_candidates = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # 文泉驿微米黑
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",  # Noto Sans
            "/System/Library/Fonts/PingFang.ttc",  # macOS
            "C:/Windows/Fonts/msyh.ttc",  # Windows 微软雅黑
        ]
        
        self.font_path = self._find_font()
    
    def _find_font(self) -> str:
        """查找可用字体"""
        for font_path in self.font_candidates:
            if os.path.exists(font_path):
                return font_path
        
        # 如果都没找到，使用PIL默认字体
        print("⚠ 未找到中文字体，将使用默认字体（可能不支持中文）")
        return None
    
    def add_text_to_static_image(self, image_path: str, text: str,
                                  position: str = "bottom",
                                  font_size: int = 32,
                                  text_color: tuple = (255, 255, 255),
                                  outline_color: tuple = (0, 0, 0),
                                  outline_width: int = 2) -> Image:
        """
        为静态图片添加文字
        
        Args:
            image_path: 图片路径
            text: 文字内容
            position: 位置 (top/center/bottom)
            font_size: 字体大小
            text_color: 文字颜色 RGB
            outline_color: 描边颜色 RGB
            outline_width: 描边宽度
            
        Returns:
            处理后的图片
        """
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        # 加载字体
        try:
            if self.font_path:
                font = ImageFont.truetype(self.font_path, font_size)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
            print("⚠ 字体加载失败，使用默认字体")
        
        # 计算文字位置
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        img_width, img_height = img.size
        
        if position == "top":
            x = (img_width - text_width) // 2
            y = 20
        elif position == "center":
            x = (img_width - text_width) // 2
            y = (img_height - text_height) // 2
        else:  # bottom
            x = (img_width - text_width) // 2
            y = img_height - text_height - 20
        
        # 绘制描边（多次绘制产生描边效果）
        for offset_x in range(-outline_width, outline_width + 1):
            for offset_y in range(-outline_width, outline_width + 1):
                if offset_x != 0 or offset_y != 0:
                    draw.text((x + offset_x, y + offset_y), text, 
                             font=font, fill=outline_color)
        
        # 绘制主文字
        draw.text((x, y), text, font=font, fill=text_color)
        
        return img
    
    def add_text_to_gif(self, gif_path: str, text: str,
                       position: str = "bottom",
                       font_size: int = 28,
                       text_color: tuple = (255, 255, 255),
                       outline_color: tuple = (0, 0, 0),
                       outline_width: int = 2) -> list:
        """
        为GIF添加文字
        
        Args:
            gif_path: GIF路径
            text: 文字内容
            其他参数同 add_text_to_static_image
            
        Returns:
            处理后的帧列表
        """
        img = Image.open(gif_path)
        frames = []
        
        # 加载字体
        try:
            if self.font_path:
                font = ImageFont.truetype(self.font_path, font_size)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # 处理每一帧
        for frame in ImageSequence.Iterator(img):
            # 转换为RGBA模式
            frame = frame.convert("RGBA")
            
            # 创建一个用于绘制的图层
            txt_layer = Image.new("RGBA", frame.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_layer)
            
            # 计算文字位置
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            img_width, img_height = frame.size
            
            if position == "top":
                x = (img_width - text_width) // 2
                y = 15
            elif position == "center":
                x = (img_width - text_width) // 2
                y = (img_height - text_height) // 2
            else:  # bottom
                x = (img_width - text_width) // 2
                y = img_height - text_height - 15
            
            # 绘制描边
            for offset_x in range(-outline_width, outline_width + 1):
                for offset_y in range(-outline_width, outline_width + 1):
                    if offset_x != 0 or offset_y != 0:
                        draw.text((x + offset_x, y + offset_y), text,
                                 font=font, fill=outline_color + (255,))
            
            # 绘制主文字
            draw.text((x, y), text, font=font, fill=text_color + (255,))
            
            # 合并图层
            result = Image.alpha_composite(frame, txt_layer)
            frames.append(result.convert("RGB"))
        
        return frames
    
    def save_gif(self, frames: list, output_path: str, duration: int = 50):
        """
        保存GIF
        
        Args:
            frames: 帧列表
            output_path: 输出路径
            duration: 每帧持续时间（毫秒）
        """
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,
            optimize=True
        )
    
    def batch_add_text(self, input_dir: str, output_dir: str,
                      mode: str = "auto", category: str = None):
        """
        批量添加文字
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            mode: 模式 (auto/semi_auto/custom)
            category: 表情包类别 (dance/thanks/gift_effect)
        """
        print(f"\n批量添加文字")
        print(f"输入目录: {input_dir}")
        print(f"输出目录: {output_dir}")
        print(f"模式: {mode}")
        print("-" * 70)
        
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 获取所有图片文件
        image_files = list(input_path.glob("*.gif")) + list(input_path.glob("*.jpg")) + list(input_path.glob("*.png"))
        
        if not image_files:
            print("⚠ 未找到图片文件")
            return
        
        print(f"找到 {len(image_files)} 个文件\n")
        
        # 获取预设文字
        if mode == "auto" and category:
            texts = self.preset_texts.get(category, [""])
        else:
            texts = []
        
        for i, img_file in enumerate(image_files):
            print(f"[{i+1}/{len(image_files)}] 处理: {img_file.name}")
            
            # 确定文字
            if mode == "auto":
                # 自动模式：循环使用预设文字
                if texts:
                    text = texts[i % len(texts)]
                else:
                    text = ""
                    print(f"  跳过（无预设文字）")
                    continue
            
            elif mode == "semi_auto":
                # 半自动模式：显示候选，用户选择
                print(f"\n  候选文字:")
                if category and category in self.preset_texts:
                    for j, t in enumerate(self.preset_texts[category], 1):
                        print(f"    {j}. {t}")
                    print(f"    0. 自定义")
                    print(f"    s. 跳过")
                    
                    choice = input(f"  选择 (1-{len(self.preset_texts[category])}/0/s): ").strip()
                    
                    if choice == 's':
                        print(f"  跳过")
                        continue
                    elif choice == '0':
                        text = input(f"  输入文字: ").strip()
                    else:
                        try:
                            idx = int(choice) - 1
                            text = self.preset_texts[category][idx]
                        except:
                            print(f"  无效选择，跳过")
                            continue
                else:
                    text = input(f"  输入文字 (回车跳过): ").strip()
                    if not text:
                        continue
            
            else:  # custom
                text = input(f"  输入文字 (回车跳过): ").strip()
                if not text:
                    continue
            
            # 处理文件
            try:
                output_file = output_path / img_file.name
                
                if img_file.suffix.lower() == '.gif':
                    # GIF处理
                    frames = self.add_text_to_gif(str(img_file), text)
                    self.save_gif(frames, str(output_file))
                else:
                    # 静态图处理
                    result_img = self.add_text_to_static_image(str(img_file), text)
                    result_img.save(str(output_file))
                
                print(f"  ✓ 已添加文字: '{text}'")
            
            except Exception as e:
                print(f"  ✗ 处理失败: {e}")
        
        print(f"\n✓ 批量处理完成")
        print(f"输出目录: {output_dir}")


def main():
    """主函数"""
    print("=" * 70)
    print("表情包文字添加工具")
    print("=" * 70)
    
    adder = EmojiTextAdder()
    
    # 检查字体
    if adder.font_path:
        print(f"✓ 使用字体: {adder.font_path}\n")
    else:
        print("⚠ 未找到中文字体，文字可能显示异常\n")
    
    # 选择模式
    print("请选择模式:")
    print("  1. 自动模式（使用预设文字）")
    print("  2. 半自动模式（从候选列表选择）")
    print("  3. 自定义模式（手动输入每个文字）")
    
    try:
        mode_choice = input("\n选择 (1-3): ").strip()
        
        if mode_choice == "1":
            mode = "auto"
        elif mode_choice == "2":
            mode = "semi_auto"
        elif mode_choice == "3":
            mode = "custom"
        else:
            print("无效选择")
            return
        
        # 选择类别
        print("\n请选择表情包类别:")
        print("  1. 手势舞 (dance)")
        print("  2. 感谢手势 (thanks)")
        print("  3. 礼物特效 (gift_effect)")
        
        category_choice = input("\n选择 (1-3): ").strip()
        
        if category_choice == "1":
            category = "dance"
            category_name = "手势舞"
        elif category_choice == "2":
            category = "thanks"
            category_name = "感谢手势"
        elif category_choice == "3":
            category = "gift_effect"
            category_name = "礼物特效"
        else:
            print("无效选择")
            return
        
        # 设置目录
        material_dir = Path.home() / "shanshan_materials" / "表情包素材库"
        input_dir = material_dir / category_name
        output_dir = material_dir / f"{category_name}_带文字"
        
        if not input_dir.exists():
            print(f"\n错误: 输入目录不存在: {input_dir}")
            print("请先运行表情包生成工具")
            return
        
        # 批量处理
        adder.batch_add_text(
            str(input_dir),
            str(output_dir),
            mode=mode,
            category=category
        )
        
        print("\n" + "=" * 70)
        print("✅ 处理完成！")
        print("=" * 70)
        print(f"\n输出目录: {output_dir}")
    
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()



