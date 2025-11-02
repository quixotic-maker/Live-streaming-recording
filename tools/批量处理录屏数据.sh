#!/bin/bash
# 批量处理录屏数据脚本

# 使用方法：
#   bash 批量处理录屏数据.sh <输入目录> <输出目录>

set -e

INPUT_DIR="${1:-/home/liu/app_github/BilibiliDown.v6.39.release/download/夢之初-}"
OUTPUT_DIR="${2:-/home/liu/shanshan_materials/00_录屏预处理}"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          📹 批量处理录屏数据                                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "输入目录: $INPUT_DIR"
echo "输出目录: $OUTPUT_DIR"
echo ""

# 检查输入目录
if [ ! -d "$INPUT_DIR" ]; then
    echo "❌ 输入目录不存在: $INPUT_DIR"
    exit 1
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 统计视频文件
video_count=$(find "$INPUT_DIR" -name "*.mp4" -o -name "*.flv" | wc -l)
echo "找到 $video_count 个视频文件"
echo ""

# 询问是否继续
read -p "是否继续？(y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "开始处理"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

processed=0
failed=0

# 处理每个视频
find "$INPUT_DIR" -name "*.mp4" | sort | while read video; do
    processed=$((processed + 1))
    
    # 获取文件名（不含扩展名）
    basename=$(basename "$video" .mp4)
    
    # 创建输出子目录
    output_subdir="$OUTPUT_DIR/$basename"
    mkdir -p "$output_subdir"
    
    echo "[$processed/$video_count] 处理: $basename"
    
    # 检查是否已处理
    cropped_video="$output_subdir/${basename}_cropped.mp4"
    if [ -f "$cropped_video" ]; then
        echo "  ⏭️  已存在，跳过"
        echo ""
        continue
    fi
    
    # 执行处理（只裁剪，不OCR）
    conda run -n shanshan python /home/liu/app_github/DouyinLiveRecorder/tools/录屏数据预处理.py \
        --input "$video" \
        --output "$output_subdir" \
        --no-danmaku \
        > /dev/null 2>&1
    
    # 检查是否生成了裁剪视频
    if [ -f "$cropped_video" ] && [ -s "$cropped_video" ]; then
        echo "  ✅ 完成"
        file_size=$(du -h "$cropped_video" | cut -f1)
        echo "  📦 大小: $file_size"
    else
        echo "  ❌ 失败"
        failed=$((failed + 1))
    fi
    
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "处理完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "总数: $video_count"
echo "成功: $((video_count - failed))"
echo "失败: $failed"
echo ""
echo "输出目录: $OUTPUT_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

