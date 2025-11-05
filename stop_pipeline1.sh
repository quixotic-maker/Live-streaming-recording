#!/bin/bash
# Pipeline 1 (main.py) 停止脚本

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "停止 Pipeline 1 - 抖音直播录制系统"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 从PID文件获取PID
if [ -f /tmp/main_py.pid ]; then
  PID=$(cat /tmp/main_py.pid)
  echo "从PID文件获取: $PID"
  
  if ps -p $PID > /dev/null 2>&1; then
    echo "正在停止进程 $PID..."
    kill $PID
    sleep 2
    
    # 验证是否已停止
    if ps -p $PID > /dev/null 2>&1; then
      echo "进程仍在运行，尝试强制停止..."
      kill -9 $PID
      sleep 1
    fi
    
    if ps -p $PID > /dev/null 2>&1; then
      echo "✗ 停止失败"
      exit 1
    else
      echo "✓ 进程已停止"
      rm /tmp/main_py.pid
    fi
  else
    echo "⚠️  PID文件中的进程不存在"
    rm /tmp/main_py.pid
  fi
else
  echo "⚠️  PID文件不存在"
fi

# 检查是否还有main.py进程
REMAINING=$(ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$REMAINING" ]; then
  echo ""
  echo "发现其他main.py进程: $REMAINING"
  echo "是否停止? (y/n)"
  read -t 10 ANSWER
  
  if [ "$ANSWER" = "y" ]; then
    for PID in $REMAINING; do
      echo "停止进程 $PID..."
      kill $PID
    done
    sleep 2
    echo "✓ 所有main.py进程已停止"
  fi
else
  echo "✓ 没有main.py进程在运行"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Pipeline 1 已停止"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

