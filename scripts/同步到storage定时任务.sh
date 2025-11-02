#!/bin/bash
# 定时同步素材到 /mnt/storage/shanshan/
# 使用方法: 
#   1. chmod +x 同步到storage定时任务.sh
#   2. crontab -e
#   3. 添加: */30 * * * * /home/liu/app_github/DouyinLiveRecorder/同步到storage定时任务.sh

SOURCE_DIR="$HOME/shanshan_materials"
TARGET_DIR="/mnt/storage/shanshan"
LOG_FILE="$HOME/sync_to_storage.log"

echo "================================================" >> "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始同步" >> "$LOG_FILE"

# 检查源目录
if [ ! -d "$SOURCE_DIR" ]; then
    echo "错误: 源目录不存在 $SOURCE_DIR" >> "$LOG_FILE"
    exit 1
fi

# 检查目标目录（尝试创建或需要管理员权限）
if [ ! -d "$TARGET_DIR" ]; then
    echo "警告: 目标目录不存在，尝试创建: $TARGET_DIR" >> "$LOG_FILE"
    mkdir -p "$TARGET_DIR" 2>> "$LOG_FILE" || {
        echo "错误: 无法创建目标目录（需要管理员权限）" >> "$LOG_FILE"
        exit 1
    }
fi

# 使用 rsync 同步（更高效，支持增量）
if command -v rsync &> /dev/null; then
    rsync -av --delete \
        "$SOURCE_DIR/" \
        "$TARGET_DIR/" \
        >> "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✓ 同步成功" >> "$LOG_FILE"
    else
        echo "✗ 同步失败（可能是权限问题）" >> "$LOG_FILE"
        exit 1
    fi
else
    # 备用方案: cp
    cp -ru "$SOURCE_DIR"/* "$TARGET_DIR"/ >> "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✓ 同步成功 (cp)" >> "$LOG_FILE"
    else
        echo "✗ 同步失败（可能是权限问题）" >> "$LOG_FILE"
        exit 1
    fi
fi

# 统计
TOTAL_SIZE=$(du -sh "$SOURCE_DIR" | cut -f1)
echo "总大小: $TOTAL_SIZE" >> "$LOG_FILE"

echo "$(date '+%Y-%m-%d %H:%M:%S') - 同步完成" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"



