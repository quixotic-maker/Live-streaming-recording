#!/bin/bash
# 启动直播录制 - 快速启动脚本

echo "========================================================================"
echo "启动抖音直播录制系统"
echo "========================================================================"
echo ""
echo "配置检查："
echo "  ⏰ 监测时间：19:01 - 23:30"
echo "  📹 自动录制：开启"
echo "  🔄 视频合并：开启"
echo "  📁 保存路径：/home/liu/videos/shanshan/抖音直播/"
echo ""
echo "开始启动..."
echo ""

cd /home/liu/app_github/DouyinLiveRecorder
python main.py



