# DouyinLiveRecorder 快速导航 🚀

> **最后更新**: 2025-11-02  
> **项目状态**: 已完成文件整理，结构清晰，可直接使用

---

## 📁 目录结构一览

```
DouyinLiveRecorder/
├── main.py              ⭐ 主程序：直播录制
├── demo.py              示例程序
├── ffmpeg_install.py    FFmpeg安装工具
├── i18n.py              国际化模块
├── msg_push.py          消息推送模块
│
├── src/                 📦 核心模块（18个文件）
│   ├── content_classifier.py      内容分类
│   ├── danmaku_recorder.py        弹幕录制
│   ├── danmaku_manager.py         弹幕管理
│   ├── danmaku_renderer.py        弹幕渲染
│   ├── emoji_generator_v2.py      表情包生成V2
│   ├── multimodal_detector.py     多模态检测
│   ├── upgrade_detector.py        升级检测
│   ├── video_montage.py           视频集锦
│   ├── song_identifier.py         歌曲识别
│   └── ... (更多模块)
│
├── tools/               🔧 工具脚本（28个）
│   ├── 批量提取歌曲音频.py
│   ├── 完整语音分析.py
│   ├── 字幕校对工具.py
│   ├── 批量提取关键帧.py
│   ├── 修复表情包生成.py
│   └── ... (23个工具)
│
├── tests/               🧪 测试脚本（13个）
│   ├── 测试多模态检测.py
│   ├── 测试弹幕录制.py
│   ├── 测试视频集锦.py
│   ├── 测试表情包优化.py
│   └── outputs/               测试输出文件
│       ├── highlights_*.json
│       ├── timeline_*.txt
│       └── speech_analysis_*
│
├── docs/                📚 技术文档（39个）
│   ├── README_完整指南.md         👈 详细使用指南
│   ├── 项目完成情况_最终版.md
│   ├── 完整项目规划书.md
│   ├── 多模态检测使用说明.md
│   ├── 表情包生成系统说明.md
│   └── quick_start/             快速开始指南
│       ├── 多模态检测快速开始.txt
│       ├── 表情识别快速开始.txt
│       ├── 完整链路流程图.txt
│       └── 快速参考卡片.txt
│
├── scripts/             🎬 Shell脚本
│   ├── 启动直播录制.sh
│   ├── 一键运行所有脚本.sh
│   ├── 同步到storage定时任务.sh
│   ├── 移动素材到storage.sh
│   └── windows/
│       └── StopRecording.vbs
│
├── requirements/        📦 依赖文件
│   ├── requirements.txt           主要依赖
│   ├── requirements_emoji.txt     表情包依赖
│   ├── requirements_multimodal.txt 多模态依赖
│   ├── requirements_emotion.txt   情绪识别依赖
│   └── requirements_recognition.txt 识别依赖
│
├── web/                 🌐 网页文件
│   └── index.html
│
├── config/              ⚙️ 配置文件
│   ├── config.ini
│   ├── URL_config.ini
│   └── anchors/              主播配置
│
└── logs/                📝 日志文件
```

---

## 🚀 快速开始

### 1. 启动直播录制

```bash
cd /home/liu/app_github/DouyinLiveRecorder
conda activate shanshan
python main.py
```

### 2. 安装依赖

```bash
# 安装所有依赖
cd /home/liu/app_github/DouyinLiveRecorder
conda activate shanshan

# 主要依赖
pip install -r requirements/requirements.txt

# 可选：表情包功能
pip install -r requirements/requirements_emoji.txt

# 可选：多模态检测
pip install -r requirements/requirements_multimodal.txt
```

### 3. 使用工具脚本

```bash
cd /home/liu/app_github/DouyinLiveRecorder
conda activate shanshan

# 提取歌曲音频
python tools/批量提取歌曲音频.py

# 完整语音分析
python tools/完整语音分析.py

# 字幕校对
python tools/字幕校对工具.py

# 提取关键帧
python tools/批量提取关键帧.py
```

### 4. 运行测试

```bash
cd /home/liu/app_github/DouyinLiveRecorder
conda activate shanshan

# 测试多模态检测
python tests/测试多模态检测.py

# 测试弹幕录制
python tests/测试弹幕录制.py

# 测试视频集锦
python tests/测试视频集锦.py
```

---

## 📖 常用文档

### 新手必读

| 文档 | 路径 | 说明 |
|------|------|------|
| **完整使用指南** | `docs/README_完整指南.md` | 系统完整使用说明 ⭐⭐⭐ |
| **项目完成情况** | `docs/项目完成情况_最终版.md` | 项目状态和完成度 |
| **快速参考卡片** | `docs/quick_start/快速参考卡片.txt` | 常用命令速查 |

### 功能说明

| 文档 | 说明 |
|------|------|
| `docs/多模态检测使用说明.md` | 升级检测系统 |
| `docs/表情包生成系统说明.md` | 表情包生成功能 |
| `docs/弹幕录制_集成指南.md` | 弹幕录制功能 |
| `docs/视频自动合并说明.md` | 视频合并功能 |

### 快速开始

| 文档 | 说明 |
|------|------|
| `docs/quick_start/多模态检测快速开始.txt` | 快速使用多模态检测 |
| `docs/quick_start/表情识别快速开始.txt` | 快速使用表情识别 |
| `docs/quick_start/完整链路流程图.txt` | 完整处理流程 |

---

## 🔧 常用工具

### 音频处理

- `tools/批量提取歌曲音频.py` - 提取视频中的歌曲音频
- `tools/完整语音分析.py` - 完整的语音转文字分析
- `tools/分析语音关键词.py` - 分析语音中的关键词

### 视频处理

- `tools/批量提取关键帧.py` - 提取视频关键帧
- `tools/批量提取单人镜头.py` - 提取单人镜头片段
- `tools/视频内容分类.py` - 自动分类视频内容

### 表情包

- `tools/修复表情包生成.py` - 修复表情包生成问题
- `tools/提取可爱表情.py` - 提取可爱表情

### 字幕处理

- `tools/字幕校对工具.py` - 校对字幕准确性
- `tools/弹幕字幕合成.py` - 合成弹幕字幕

### 数据分析

- `tools/统计分析工具.py` - 统计数据分析
- `tools/查看分类结果.py` - 查看内容分类结果

---

## 🧪 测试功能

### 核心功能测试

```bash
# 多模态检测（升级检测）
python tests/测试多模态检测.py
python tests/快速测试多模态.py
python tests/演示多模态检测.py

# 弹幕功能
python tests/测试弹幕录制.py
python tests/测试弹幕渲染.py

# 视频功能
python tests/测试视频集锦.py
python tests/测试视频合并.py

# 表情包
python tests/测试表情包优化.py
python tests/测试表情识别.py
```

---

## 📊 素材生成（配合 shanshan_materials）

录制完成后，使用 `~/shanshan_materials/` 中的脚本进行自动化处理：

```bash
cd ~/shanshan_materials
conda activate shanshan

# 每日自动处理（推荐）
python 每日自动处理.py --date 2025-11-01

# 单独生成功能
python 生成所有视频集锦.py --video xxx.mp4 --date 2025-11-01
python 生成表情包_V2优化版.py --video xxx.mp4 --date 2025-11-01
python 生成弹幕素材.py --video xxx.mp4 --date 2025-11-01
```

详见：`~/shanshan_materials/目录结构说明_完整版.md`

---

## ⚙️ 配置文件

### 主配置

- `config/config.ini` - 主要配置（录制参数、路径等）
- `config/URL_config.ini` - 直播间URL配置

### 主播配置

- `config/anchors/` - 各主播的个性化配置

---

## 🆘 常见问题

### 1. 导入模块失败

```bash
# 确保在正确的环境
conda activate shanshan

# 确保在项目根目录
cd /home/liu/app_github/DouyinLiveRecorder
```

### 2. 找不到配置文件

配置文件在 `config/` 目录下，不在根目录。

### 3. 测试输出在哪里？

测试输出文件在 `tests/outputs/` 目录。

### 4. 如何安装特定功能的依赖？

```bash
# 根据需要安装
pip install -r requirements/requirements_<功能名>.txt
```

---

## 📚 相关文档

### 本项目（DouyinLiveRecorder/）

- 完整文档：`docs/` 目录
- 快速开始：`docs/quick_start/` 目录

### 素材系统（~/shanshan_materials/）

- `~/shanshan_materials/目录结构说明_完整版.md` - 整体架构
- `~/shanshan_materials/开始使用_文件整理.md` - 快速开始
- `~/shanshan_materials/文件整理完成报告.md` - 整理报告

---

## 🎯 目录职责

| 目录 | 职责 | 何时使用 |
|------|------|----------|
| **根目录** | 核心程序（5个文件） | 启动主程序 |
| **src/** | 核心模块 | 开发核心功能 |
| **tools/** | 工具脚本 | 处理素材、分析数据 |
| **tests/** | 测试脚本 | 测试功能 |
| **docs/** | 技术文档 | 查阅使用说明 |
| **scripts/** | Shell脚本 | 批量操作、定时任务 |
| **requirements/** | 依赖管理 | 安装依赖 |
| **config/** | 配置文件 | 修改配置 |

---

## 💡 最佳实践

### 文件组织

- ✅ **新工具脚本** → 放到 `tools/`
- ✅ **新测试脚本** → 放到 `tests/`
- ✅ **新文档** → 放到 `docs/`
- ✅ **不要在根目录堆积文件**

### 开发流程

1. 修改代码 → 在 `src/` 中修改核心模块
2. 测试功能 → 在 `tests/` 中创建测试脚本
3. 编写工具 → 在 `tools/` 中创建工具脚本
4. 更新文档 → 在 `docs/` 中更新说明文档

---

## 🔗 项目关系

```
DouyinLiveRecorder/          ←→          ~/shanshan_materials/
    (开发工具箱)                              (素材仓库)
    
   录制 + 开发                              数据 + 自动化
   
   ├── 直播录制程序                         ├── 原始录像
   ├── 核心功能模块                         ├── 语音转文字
   ├── 开发工具脚本                         ├── 内容分类
   ├── 功能测试脚本                         ├── 素材生成
   └── 技术开发文档                         ├── 最终成品
                                           ├── 自动化脚本
                                           └── 使用文档
```

**数据流**：录制 → 转码 → 分类 → 生成素材 → 输出成品

---

## 📞 获取帮助

1. **查看文档**：`docs/` 目录
2. **快速参考**：`docs/quick_start/快速参考卡片.txt`
3. **完整指南**：`docs/README_完整指南.md`
4. **整理报告**：`~/shanshan_materials/文件整理完成报告.md`

---

**版本**: v2.0（已完成文件整理）  
**更新日期**: 2025-11-02  
**项目状态**: ✅ 生产就绪

