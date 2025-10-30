#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间窗口功能测试脚本
用于验证时间窗口判断逻辑是否正常工作
"""

import datetime


def is_in_time_window(start_time_str: str, end_time_str: str) -> bool:
    """
    判断当前时间是否在指定的时间窗口内
    :param start_time_str: 开始时间，格式 "HH:MM"
    :param end_time_str: 结束时间，格式 "HH:MM"
    :return: True表示在时间窗口内，False表示不在
    """
    try:
        now = datetime.datetime.now()
        current_time = now.time()
        
        start_time = datetime.datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.datetime.strptime(end_time_str, "%H:%M").time()
        
        # 处理跨天的情况（如 22:00-02:00）
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:
            return current_time >= start_time or current_time <= end_time
    except Exception as e:
        print(f"时间窗口判断错误: {e}")
        return True


def get_seconds_until_time_window(start_time_str: str) -> int:
    """
    计算距离下一个时间窗口开始还有多少秒
    :param start_time_str: 开始时间，格式 "HH:MM"
    :return: 秒数
    """
    try:
        now = datetime.datetime.now()
        start_time = datetime.datetime.strptime(start_time_str, "%H:%M").time()
        
        # 构造今天的开始时间
        today_start = datetime.datetime.combine(now.date(), start_time)
        
        # 如果今天的开始时间已过，则计算明天的
        if now.time() > start_time:
            today_start += datetime.timedelta(days=1)
        
        seconds = int((today_start - now).total_seconds())
        return max(seconds, 0)
    except Exception as e:
        print(f"计算时间窗口等待时间错误: {e}")
        return 3600


def test_time_window():
    """测试时间窗口功能"""
    print("=" * 60)
    print("时间窗口功能测试")
    print("=" * 60)
    
    # 从配置文件读取设置（简化版）
    start_time = "19:01"
    end_time = "23:30"
    
    now = datetime.datetime.now()
    current_time_str = now.strftime("%H:%M:%S")
    
    print(f"\n当前时间: {current_time_str}")
    print(f"监测窗口: {start_time} - {end_time}")
    print("-" * 60)
    
    # 测试是否在时间窗口内
    in_window = is_in_time_window(start_time, end_time)
    
    if in_window:
        print("✅ 当前在监测时间窗口内")
        print("📡 程序将每60秒检测一次直播状态")
    else:
        print("❌ 当前不在监测时间窗口内")
        wait_seconds = get_seconds_until_time_window(start_time)
        wait_hours = wait_seconds // 3600
        wait_minutes = (wait_seconds % 3600) // 60
        wait_secs = wait_seconds % 60
        
        print(f"⏰ 距离下一次监测还有: {wait_hours}小时 {wait_minutes}分钟 {wait_secs}秒")
        
        # 计算下次监测的具体时间
        next_check_time = now + datetime.timedelta(seconds=wait_seconds)
        print(f"📅 下次监测时间: {next_check_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("-" * 60)
    
    # 测试几个特殊时间点
    print("\n测试各个时间点:")
    test_times = [
        ("18:00", "19:01之前"),
        ("19:01", "窗口开始时刻"),
        ("20:00", "窗口中间"),
        ("23:30", "窗口结束时刻"),
        ("23:31", "23:30之后"),
        ("01:00", "凌晨")
    ]
    
    for test_time_str, description in test_times:
        test_time = datetime.datetime.strptime(test_time_str, "%H:%M").time()
        
        # 模拟该时间点的判断
        if start_time <= end_time:
            in_test_window = datetime.datetime.strptime(start_time, "%H:%M").time() <= test_time <= datetime.datetime.strptime(end_time, "%H:%M").time()
        else:
            in_test_window = test_time >= datetime.datetime.strptime(start_time, "%H:%M").time() or test_time <= datetime.datetime.strptime(end_time, "%H:%M").time()
        
        status = "✅ 在窗口内" if in_test_window else "❌ 在窗口外"
        print(f"  {test_time_str} ({description}): {status}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_time_window()

