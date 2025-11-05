#!/bin/bash
# Pipeline 1 (main.py) 启动脚本
# 用途: 启动抖音直播录制系统

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "启动 Pipeline 1 - 抖音直播录制系统"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 切换到项目目录
cd /home/liu/app_github/DouyinLiveRecorder

# 检查是否已在运行
if [ -f /tmp/main_py.pid ]; then
  OLD_PID=$(cat /tmp/main_py.pid)
  if ps -p $OLD_PID > /dev/null 2>&1; then
    echo "⚠️  Pipeline 1 已在运行 (PID: $OLD_PID)"
    echo "   如需重启，请先停止: kill $OLD_PID"
    exit 1
  else
    echo "清理旧的PID文件..."
    rm /tmp/main_py.pid
  fi
fi

# 检查是否有其他main.py进程
EXISTING=$(ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$EXISTING" ]; then
  echo "⚠️  发现运行中的main.py进程: $EXISTING"
  echo "   请先停止: kill $EXISTING"
  exit 1
fi

# 创建日志目录
mkdir -p logs

# 创建日志文件名
LOG_FILE="logs/main_$(date +%Y%m%d_%H%M%S).log"

echo "启动参数:"
echo "  工作目录: $(pwd)"
echo "  Python环境: conda shanshan"
echo "  日志文件: $LOG_FILE"
echo ""

# 启动main.py
nohup conda run -n shanshan python -u main.py > "$LOG_FILE" 2>&1 &

# 保存PID
PID=$!
echo $PID > /tmp/main_py.pid

echo "✓ Pipeline 1 已启动"
echo "  PID: $PID"
echo "  PID文件: /tmp/main_py.pid"
echo ""

# 等待10秒验证启动
echo "等待10秒，验证启动状态..."
sleep 10

# 检查进程
if ps -p $PID > /dev/null 2>&1; then
  echo "✓ 进程运行正常"
else
  echo "✗ 进程启动失败"
  echo ""
  echo "查看日志:"
  tail -30 "$LOG_FILE"
  exit 1
fi

# 查看PlayURL.log最新内容
if [ -f logs/PlayURL.log ]; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "PlayURL.log 最新内容:"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  tail -10 logs/PlayURL.log
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "监控命令:"
echo "  tail -f logs/PlayURL.log"
echo ""
echo "停止命令:"
echo "  kill $PID"
echo "  或: kill \$(cat /tmp/main_py.pid)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

