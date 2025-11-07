#!/bin/bash
# 启动弹幕录制 - 清除代理环境变量

# 清除代理设置（抖音直播国内可直连，不需要代理）
unset HTTP_PROXY
unset HTTPS_PROXY
unset ALL_PROXY
unset http_proxy
unset https_proxy
unset all_proxy

# 启动弹幕录制
cd /home/liu/app_github/DouyinLiveRecorder
python3 -u realtime_danmaku_recorder.py "$@"

