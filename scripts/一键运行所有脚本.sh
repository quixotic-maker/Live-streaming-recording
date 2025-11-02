#!/bin/bash
# -*- coding: utf-8 -*-
# 一键运行所有素材处理脚本
# 自动完成从原始视频到所有素材的生成

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_DIR="/home/liu/app_github/DouyinLiveRecorder"
MATERIAL_DIR="$HOME/shanshan_materials"

# 日志文件
LOG_FILE="$PROJECT_DIR/logs/batch_processing_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$(dirname "$LOG_FILE")"

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "$LOG_FILE"
}

# 显示横幅
show_banner() {
    echo "======================================================================" | tee -a "$LOG_FILE"
    echo "                观山直播素材一键处理工具" | tee -a "$LOG_FILE"
    echo "======================================================================" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
}

# 检查环境
check_environment() {
    log_info "检查环境..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查FFmpeg
    if ! command -v ffmpeg &> /dev/null; then
        log_error "FFmpeg 未安装"
        exit 1
    fi
    
    # 检查项目目录
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    
    # 检查素材目录
    if [ ! -d "$MATERIAL_DIR" ]; then
        log_warning "素材目录不存在，正在创建: $MATERIAL_DIR"
        mkdir -p "$MATERIAL_DIR"
    fi
    
    log "✓ 环境检查通过"
}

# 处理函数
run_script() {
    local script_name=$1
    local description=$2
    local required=${3:-"yes"}  # yes/no，是否必需
    
    log ""
    log "======================================================================" 
    log "[$description]"
    log "======================================================================" 
    
    if [ ! -f "$PROJECT_DIR/$script_name" ]; then
        if [ "$required" == "yes" ]; then
            log_error "脚本不存在: $script_name"
            exit 1
        else
            log_warning "脚本不存在（跳过）: $script_name"
            return 0
        fi
    fi
    
    cd "$PROJECT_DIR"
    
    # 根据文件扩展名选择运行方式
    if [[ "$script_name" == *.py ]]; then
        python3 "$script_name" 2>&1 | tee -a "$LOG_FILE"
    elif [[ "$script_name" == *.sh ]]; then
        bash "$script_name" 2>&1 | tee -a "$LOG_FILE"
    else
        log_error "不支持的脚本类型: $script_name"
        return 1
    fi
    
    if [ $? -eq 0 ]; then
        log "✓ [$description] 完成"
    else
        log_error "[$description] 失败"
        if [ "$required" == "yes" ]; then
            exit 1
        fi
    fi
}

# 主流程
main() {
    show_banner
    check_environment
    
    log_info "开始批量处理..."
    log_info "日志文件: $LOG_FILE"
    log ""
    
    # 阶段1：内容分类（如果还没做过）
    if [ ! -f "$MATERIAL_DIR/素材库_最新/singing_素材.json" ]; then
        log_info "阶段1：内容分类"
        run_script "重新分类素材.py" "重新分类素材" "yes"
    else
        log_info "素材分类已存在，跳过"
    fi
    
    # 阶段2：歌曲整理（如果还没做过）
    if [ ! -f "$MATERIAL_DIR/歌曲素材库/歌曲列表.json" ]; then
        log_info "阶段2：歌曲整理"
        run_script "整理歌曲素材.py" "整理歌曲素材" "yes"
    else
        log_info "歌曲列表已存在，跳过"
    fi
    
    # 阶段3：提取歌曲音频
    log_info "阶段3：提取歌曲音频"
    run_script "批量提取歌曲音频.py" "批量提取歌曲音频" "no"
    
    # 阶段4：生成歌词字幕
    log_info "阶段4：生成歌词字幕"
    run_script "生成歌词字幕.py" "生成歌词字幕" "no"
    
    # 阶段5：提取关键帧
    log_info "阶段5：提取关键帧"
    run_script "批量提取关键帧.py" "批量提取关键帧" "no"
    
    # 阶段6：生成精彩集锦
    log_info "阶段6：生成精彩集锦"
    run_script "生成精彩集锦.py" "生成精彩集锦" "no"
    
    # 阶段7：生成表情包（可选，耗时较长，需要手动运行）
    # 原因：表情包生成涉及视频逐帧分析，需要10-30分钟
    #       而且可能不是每次都需要生成表情包
    log_warning "阶段7：生成表情包（跳过，如需生成请手动运行 python3 生成表情包素材_优化版.py）"
    log_warning "      原因：耗时10-30分钟，且不是每次都需要"
    # run_script "生成表情包素材_优化版.py" "生成表情包素材" "no"
    
    # 阶段8：生成剪映草稿（可选，需要手动运行）
    # 原因：剪映草稿根据不同需求生成不同类型，用户可按需选择
    log_info "阶段8：生成剪映草稿（可选，如需生成请手动运行相应脚本）"
    log_info "      - 歌曲集锦草稿: python3 生成剪映草稿_歌曲集锦.py"
    log_info "      - 完整分段草稿: python3 生成剪映草稿_完整分段.py"
    # run_script "生成剪映草稿_歌曲集锦.py" "生成剪映草稿（歌曲集锦）" "no"
    
    # 完成
    log ""
    log "======================================================================" 
    log "✅ 所有处理完成！"
    log "======================================================================" 
    log ""
    log "素材位置: $MATERIAL_DIR"
    log "日志文件: $LOG_FILE"
    log ""
    log "生成的素材："
    log "  - 分类素材: $MATERIAL_DIR/素材库_最新/"
    log "  - 歌曲列表: $MATERIAL_DIR/歌曲素材库/"
    log "  - 歌曲音频: $MATERIAL_DIR/歌曲站/音频/"
    log "  - 歌词字幕: $MATERIAL_DIR/歌词字幕/"
    log "  - 关键帧截图: $MATERIAL_DIR/关键帧截图/"
    log "  - 精彩集锦: $MATERIAL_DIR/精彩集锦/"
    log ""
    log "下一步："
    log "  1. 查看各目录的素材"
    log "  2. 运行 'python3 获取网络歌词.py' 获取网络正版歌词（推荐）"
    log "  3. 运行 'python3 生成表情包素材_优化版.py' 生成表情包（可选，耗时10-30分钟）"
    log "  4. 运行 'python3 生成剪映草稿_*.py' 生成剪映草稿（可选）"
    log "  5. 同步素材到网站服务器"
    log ""
}

# 捕获中断信号
trap 'log_error "用户中断"; exit 130' INT

# 运行主程序
main

exit 0

