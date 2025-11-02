#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试视频集锦生成

测试7种视频集锦的生成
"""

import sys
import os
import json
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from video_montage import VideoMontageGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_mock_data():
    """创建模拟数据用于测试"""
    return {
        'songs': [
            {
                'name': '测试歌曲1',
                'start': 60,
                'duration': 180
            },
            {
                'name': '测试歌曲2',
                'start': 300,
                'duration': 200
            },
            {
                'name': '测试歌曲3',
                'start': 600,
                'duration': 190
            }
        ],
        'gifts': [
            {
                'user': '用户A',
                'gift_name': '嘉年华',
                'timestamp': 150,
                'total_value': 3000
            },
            {
                'user': '用户B',
                'gift_name': '跑车',
                'timestamp': 450,
                'total_value': 5000
            }
        ],
        'upgrades': [
            {
                'user': '用户C',
                'level': 20,
                'timestamp': 250
            }
        ],
        'chats': [
            {
                'start': 100,
                'duration': 15,
                'text': '这是一段有趣的聊天内容，大家讨论得很热烈'
            },
            {
                'start': 400,
                'duration': 12,
                'text': '主播回答了粉丝的问题，互动很好'
            }
        ]
    }


def test_with_real_video():
    """使用真实视频测试"""
    logger.info("="*80)
    logger.info("测试视频集锦生成系统（真实视频）")
    logger.info("="*80)
    
    # 查找最近的录播视频
    recordings_dir = os.path.expanduser("~/shanshan_materials/01_完整录播")
    
    if not os.path.exists(recordings_dir):
        logger.error(f"录播目录不存在: {recordings_dir}")
        return
    
    # 查找最新的视频
    import glob
    video_files = glob.glob(os.path.join(recordings_dir, "**/*_完整.ts"), recursive=True)
    
    if not video_files:
        logger.error("没有找到录播视频")
        return
    
    # 按修改时间排序，取最新的
    video_files.sort(key=os.path.getmtime, reverse=True)
    video_path = video_files[0]
    
    logger.info(f"使用视频: {video_path}")
    logger.info(f"视频大小: {os.path.getsize(video_path) / (1024**3):.2f} GB")
    
    # 尝试加载真实素材数据
    base_dir = os.path.expanduser("~/shanshan_materials")
    
    # 从视频文件名提取日期
    import re
    match = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(video_path))
    if match:
        date = match.group(1)
        logger.info(f"检测到日期: {date}")
    else:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # 尝试加载真实数据
    materials = {}
    
    # 歌曲数据
    songs_file = os.path.join(base_dir, "歌曲素材库/歌曲列表_优化版.json")
    if os.path.exists(songs_file):
        with open(songs_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            materials['songs'] = data.get('songs', data if isinstance(data, list) else [])
            logger.info(f"✅ 加载歌曲数据: {len(materials['songs'])} 首")
    else:
        logger.warning("⚠️  未找到歌曲数据，使用模拟数据")
        materials['songs'] = create_mock_data()['songs']
    
    # 礼物数据
    gift_file = os.path.join(base_dir, f"03_内容分类/{date}/gift_素材.json")
    if os.path.exists(gift_file):
        with open(gift_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            materials['gifts'] = data.get('segments', data if isinstance(data, list) else [])
            logger.info(f"✅ 加载礼物数据: {len(materials['gifts'])} 个")
    else:
        logger.warning("⚠️  未找到礼物数据，使用模拟数据")
        materials['gifts'] = create_mock_data()['gifts']
    
    # 升级数据
    upgrade_file = os.path.join(base_dir, f"04_素材生成/{date}/upgrades/upgrades_metadata.json")
    if os.path.exists(upgrade_file):
        with open(upgrade_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            materials['upgrades'] = data.get('upgrades', [])
            logger.info(f"✅ 加载升级数据: {len(materials['upgrades'])} 个")
    else:
        logger.warning("⚠️  未找到升级数据，使用模拟数据")
        materials['upgrades'] = create_mock_data()['upgrades']
    
    # 聊天数据
    chat_file = os.path.join(base_dir, f"03_内容分类/{date}/chat_素材.json")
    if os.path.exists(chat_file):
        with open(chat_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            materials['chats'] = data.get('segments', data if isinstance(data, list) else [])
            logger.info(f"✅ 加载聊天数据: {len(materials['chats'])} 条")
    else:
        logger.warning("⚠️  未找到聊天数据，使用模拟数据")
        materials['chats'] = create_mock_data()['chats']
    
    # 创建输出目录
    output_dir = os.path.join(base_dir, f"测试_视频集锦_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"\n输出目录: {output_dir}")
    
    # 创建生成器
    generator = VideoMontageGenerator({
        'quality': 'medium',  # 测试用medium质量
        'resolution': '1080p',
        'transition': 'fade'
    })
    
    # 测试各种集锦
    logger.info("\n" + "="*80)
    logger.info("开始生成测试集锦...")
    logger.info("="*80)
    
    results = {}
    
    # 1. 测试唱歌集锦（只测试best版本）
    if materials.get('songs'):
        logger.info("\n【测试1】生成唱歌集锦（精选版）...")
        result = generator.generate_song_montage(
            video_path,
            materials['songs'],
            output_dir,
            version='best'
        )
        if result:
            results['song_best'] = result
            logger.info(f"✅ 成功: {result}")
        else:
            logger.error("❌ 失败")
    
    # 2. 测试感谢集锦
    if materials.get('gifts'):
        logger.info("\n【测试2】生成感谢集锦...")
        result = generator.generate_thank_montage(
            video_path,
            materials['gifts'],
            output_dir,
            min_value=1000
        )
        if result:
            results['thank'] = result
            logger.info(f"✅ 成功: {result}")
        else:
            logger.error("❌ 失败")
    
    # 3. 测试精彩时刻
    logger.info("\n【测试3】生成精彩时刻...")
    result = generator.generate_highlight_montage(
        video_path,
        materials,
        output_dir,
        max_duration=180  # 测试只生成3分钟
    )
    if result:
        results['highlight'] = result
        logger.info(f"✅ 成功: {result}")
    else:
        logger.error("❌ 失败")
    
    # 4. 测试短视频（只生成2个）
    logger.info("\n【测试4】生成短视频素材...")
    short_videos = generator.generate_short_videos(
        video_path,
        materials,
        os.path.join(output_dir, "短视频"),
        count=2
    )
    if short_videos:
        results['short_videos'] = short_videos
        logger.info(f"✅ 成功: 生成 {len(short_videos)} 个短视频")
    else:
        logger.error("❌ 失败")
    
    # 总结
    logger.info("\n" + "="*80)
    logger.info("测试完成！")
    logger.info("="*80)
    logger.info(f"\n生成的文件:")
    
    for key, value in results.items():
        if isinstance(value, list):
            for v in value:
                logger.info(f"  • {os.path.basename(v)}")
        elif isinstance(value, dict):
            logger.info(f"  • {os.path.basename(value.get('path', ''))}")
        else:
            logger.info(f"  • {os.path.basename(value)}")
    
    logger.info(f"\n输出目录: {output_dir}")
    
    # 保存测试结果
    result_file = os.path.join(output_dir, "测试结果.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"测试结果已保存: {result_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='测试视频集锦生成')
    parser.add_argument('--mock', action='store_true', help='使用模拟数据测试')
    
    args = parser.parse_args()
    
    if args.mock:
        logger.info("暂不支持纯模拟数据测试，请使用真实视频测试")
    else:
        test_with_real_video()


if __name__ == "__main__":
    main()



