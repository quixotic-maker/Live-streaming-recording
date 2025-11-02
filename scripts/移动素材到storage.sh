#!/bin/bash
# 移动素材到 /mnt/storage/shanshan/

echo "========================================================================"
echo "移动素材到 /mnt/storage/shanshan/"
echo "========================================================================"

# 源目录
SOURCE_DIR="素材库_重新分类"

# 目标目录
TARGET_DIR="/mnt/storage/shanshan"

# 检查源目录
if [ ! -d "$SOURCE_DIR" ]; then
    echo "错误: 源目录不存在: $SOURCE_DIR"
    exit 1
fi

# 创建目标目录
echo "1. 创建目标目录..."
mkdir -p "$TARGET_DIR"

# 复制文件
echo "2. 复制素材文件..."
cp -r "$SOURCE_DIR"/* "$TARGET_DIR/"

# 验证
echo "3. 验证移动结果..."
ls -lh "$TARGET_DIR"

echo ""
echo "✓ 素材已移动到: $TARGET_DIR"
echo ""
echo "移动的文件："
echo "  - singing_素材.json (219个唱歌片段)"
echo "  - singing_素材.txt"
echo "  - gift_素材.json (74个礼物感谢)"
echo "  - gift_素材.txt"
echo "  - chat_素材.json (207个闲聊)"
echo "  - chat_素材.txt"
echo "  - unknown_素材.json (80个未分类)"
echo "  - unknown_素材.txt"
echo "  - 分类统计报告.txt"
echo ""
echo "使用方法："
echo "  bash 移动素材到storage.sh"

