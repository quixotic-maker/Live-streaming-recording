#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频特征提取器

功能：
1. 提取音频特征（音高、节奏、音色、能量）
2. 辅助内容分类（区分唱歌/说话）
3. 增强歌曲识别准确率
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("⚠️  未安装 librosa，部分功能将不可用")
    print("   安装: pip install librosa")


class AudioFeatureExtractor:
    """音频特征提取器"""
    
    def __init__(self):
        if not LIBROSA_AVAILABLE:
            raise ImportError("需要安装 librosa: pip install librosa")
        
        self.sr = 22050  # 采样率
    
    def extract_from_file(self, audio_file: str, start: float = None, duration: float = None) -> Dict:
        """
        从音频文件提取特征
        
        Args:
            audio_file: 音频文件路径
            start: 起始时间（秒）
            duration: 持续时间（秒）
            
        Returns:
            特征字典
        """
        # 加载音频
        y, sr = librosa.load(audio_file, sr=self.sr, offset=start, duration=duration)
        
        return self.extract_from_array(y, sr)
    
    def extract_from_array(self, y: np.ndarray, sr: int) -> Dict:
        """
        从音频数组提取特征
        
        Args:
            y: 音频数组
            sr: 采样率
            
        Returns:
            特征字典
        """
        features = {}
        
        # 1. 基础特征
        features['duration'] = len(y) / sr
        features['sample_rate'] = sr
        
        # 2. 能量特征
        features['energy'] = self._extract_energy(y)
        
        # 3. 音高特征
        features['pitch'] = self._extract_pitch(y, sr)
        
        # 4. 节奏特征
        features['rhythm'] = self._extract_rhythm(y, sr)
        
        # 5. 音色特征（MFCC）
        features['timbre'] = self._extract_timbre(y, sr)
        
        # 6. 频谱特征
        features['spectral'] = self._extract_spectral(y, sr)
        
        # 7. 综合判断
        features['is_singing'] = self._is_singing(features)
        features['singing_confidence'] = self._singing_confidence(features)
        
        return features
    
    def _extract_energy(self, y: np.ndarray) -> Dict:
        """提取能量特征"""
        rms = librosa.feature.rms(y=y)[0]
        
        return {
            'mean': float(np.mean(rms)),
            'std': float(np.std(rms)),
            'max': float(np.max(rms)),
            'min': float(np.min(rms)),
        }
    
    def _extract_pitch(self, y: np.ndarray, sr: int) -> Dict:
        """提取音高特征"""
        # 使用YIN算法提取音高
        f0 = librosa.yin(y, fmin=50, fmax=2000, sr=sr)
        
        # 过滤掉无效值
        valid_f0 = f0[f0 > 0]
        
        if len(valid_f0) > 0:
            return {
                'mean': float(np.mean(valid_f0)),
                'std': float(np.std(valid_f0)),
                'max': float(np.max(valid_f0)),
                'min': float(np.min(valid_f0)),
                'range': float(np.max(valid_f0) - np.min(valid_f0)),
                'valid_ratio': float(len(valid_f0) / len(f0)),
            }
        else:
            return {
                'mean': 0.0,
                'std': 0.0,
                'max': 0.0,
                'min': 0.0,
                'range': 0.0,
                'valid_ratio': 0.0,
            }
    
    def _extract_rhythm(self, y: np.ndarray, sr: int) -> Dict:
        """提取节奏特征"""
        # 节拍检测
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        
        return {
            'tempo': float(tempo),  # BPM（每分钟节拍数）
            'beat_count': len(beats),
            'beat_strength': float(np.mean(librosa.onset.onset_strength(y=y, sr=sr))),
        }
    
    def _extract_timbre(self, y: np.ndarray, sr: int) -> Dict:
        """提取音色特征（MFCC）"""
        # 梅尔频率倒谱系数
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        return {
            'mfcc_mean': [float(x) for x in np.mean(mfcc, axis=1)],
            'mfcc_std': [float(x) for x in np.std(mfcc, axis=1)],
        }
    
    def _extract_spectral(self, y: np.ndarray, sr: int) -> Dict:
        """提取频谱特征"""
        # 频谱质心
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        
        # 频谱带宽
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        
        # 频谱对比度
        spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        
        return {
            'centroid_mean': float(np.mean(spectral_centroid)),
            'centroid_std': float(np.std(spectral_centroid)),
            'bandwidth_mean': float(np.mean(spectral_bandwidth)),
            'bandwidth_std': float(np.std(spectral_bandwidth)),
            'contrast_mean': float(np.mean(spectral_contrast)),
        }
    
    def _is_singing(self, features: Dict) -> bool:
        """判断是否为唱歌"""
        # 基于多个特征综合判断
        
        # 1. 音高变化范围（唱歌通常有更大的音高变化）
        pitch_range = features['pitch']['range']
        
        # 2. 音高有效比例（唱歌时音高更稳定）
        pitch_valid_ratio = features['pitch']['valid_ratio']
        
        # 3. 能量标准差（唱歌时能量变化更大）
        energy_std = features['energy']['std']
        
        # 4. 节奏强度（唱歌时节奏更明显）
        beat_strength = features['rhythm']['beat_strength']
        
        # 综合判断
        score = 0
        
        if pitch_range > 100:  # 音高变化超过100Hz
            score += 2
        
        if pitch_valid_ratio > 0.5:  # 50%以上有有效音高
            score += 2
        
        if energy_std > 0.05:  # 能量变化较大
            score += 1
        
        if beat_strength > 5.0:  # 节奏明显
            score += 1
        
        return score >= 3
    
    def _singing_confidence(self, features: Dict) -> float:
        """唱歌置信度（0-1）"""
        score = 0.0
        
        # 音高特征权重：40%
        pitch_range = features['pitch']['range']
        pitch_valid = features['pitch']['valid_ratio']
        score += min(pitch_range / 200, 1.0) * 0.2  # 音高范围
        score += pitch_valid * 0.2  # 音高稳定性
        
        # 节奏特征权重：30%
        tempo = features['rhythm']['tempo']
        beat_strength = features['rhythm']['beat_strength']
        score += min(tempo / 180, 1.0) * 0.15  # 节奏速度
        score += min(beat_strength / 10, 1.0) * 0.15  # 节奏强度
        
        # 能量特征权重：30%
        energy_std = features['energy']['std']
        energy_mean = features['energy']['mean']
        score += min(energy_std / 0.1, 1.0) * 0.15  # 能量变化
        score += min(energy_mean / 0.3, 1.0) * 0.15  # 能量大小
        
        return min(score, 1.0)


def analyze_audio_file(audio_file: str):
    """分析单个音频文件"""
    
    print(f"\n分析: {os.path.basename(audio_file)}")
    print("=" * 70)
    
    extractor = AudioFeatureExtractor()
    features = extractor.extract_from_file(audio_file)
    
    # 打印结果
    print(f"\n基础信息:")
    print(f"  时长: {features['duration']:.2f} 秒")
    print(f"  采样率: {features['sample_rate']} Hz")
    
    print(f"\n能量特征:")
    print(f"  平均: {features['energy']['mean']:.4f}")
    print(f"  标准差: {features['energy']['std']:.4f}")
    
    print(f"\n音高特征:")
    print(f"  平均: {features['pitch']['mean']:.1f} Hz")
    print(f"  范围: {features['pitch']['range']:.1f} Hz")
    print(f"  有效比例: {features['pitch']['valid_ratio']:.2%}")
    
    print(f"\n节奏特征:")
    print(f"  速度: {features['rhythm']['tempo']:.1f} BPM")
    print(f"  节拍数: {features['rhythm']['beat_count']}")
    print(f"  强度: {features['rhythm']['beat_strength']:.2f}")
    
    print(f"\n综合判断:")
    print(f"  是否唱歌: {'✓ 是' if features['is_singing'] else '✗ 否'}")
    print(f"  置信度: {features['singing_confidence']:.2%}")


def batch_analyze(input_dir: str, output_file: str):
    """批量分析音频文件"""
    
    print("=" * 80)
    print("批量音频特征提取")
    print("=" * 80)
    print()
    
    extractor = AudioFeatureExtractor()
    
    # 查找音频文件
    audio_files = []
    for ext in ['.mp3', '.wav', '.flac', '.m4a']:
        audio_files.extend(Path(input_dir).rglob(f'*{ext}'))
    
    if not audio_files:
        print(f"⚠️  未找到音频文件: {input_dir}")
        return
    
    print(f"找到 {len(audio_files)} 个音频文件\n")
    
    results = []
    
    for i, audio_file in enumerate(audio_files, 1):
        try:
            print(f"[{i}/{len(audio_files)}] {audio_file.name}")
            
            features = extractor.extract_from_file(str(audio_file))
            
            results.append({
                'file': str(audio_file),
                'filename': audio_file.name,
                'features': features,
            })
            
            print(f"  ✓ 唱歌: {'是' if features['is_singing'] else '否'} "
                  f"({features['singing_confidence']:.0%})")
        
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            continue
    
    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print()
    print(f"✅ 分析完成！")
    print(f"   结果已保存: {output_file}")
    
    # 统计
    singing_count = sum(1 for r in results if r['features']['is_singing'])
    print()
    print(f"统计:")
    print(f"  总文件: {len(results)}")
    print(f"  识别为唱歌: {singing_count} ({singing_count/len(results):.1%})")
    print(f"  识别为说话: {len(results)-singing_count} ({(len(results)-singing_count)/len(results):.1%})")


def main():
    """主函数"""
    
    if not LIBROSA_AVAILABLE:
        print("✗ 未安装 librosa")
        print("  请运行: pip install librosa")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("=" * 80)
        print("音频特征提取器")
        print("=" * 80)
        print()
        print("功能：")
        print("  1. 提取音频特征（音高、节奏、音色、能量）")
        print("  2. 判断是否为唱歌")
        print("  3. 辅助内容分类")
        print()
        print("使用方法：")
        print("  python3 音频特征提取器.py <音频文件>          # 分析单个文件")
        print("  python3 音频特征提取器.py <目录> <输出JSON>  # 批量分析")
        print()
        print("示例：")
        print("  python3 音频特征提取器.py song.mp3")
        print("  python3 音频特征提取器.py ~/songs features.json")
        return
    
    if len(sys.argv) == 2:
        # 单个文件分析
        audio_file = sys.argv[1]
        if not os.path.exists(audio_file):
            print(f"✗ 文件不存在: {audio_file}")
            sys.exit(1)
        
        analyze_audio_file(audio_file)
    
    elif len(sys.argv) >= 3:
        # 批量分析
        input_dir = sys.argv[1]
        output_file = sys.argv[2]
        
        if not os.path.exists(input_dir):
            print(f"✗ 目录不存在: {input_dir}")
            sys.exit(1)
        
        batch_analyze(input_dir, output_file)


if __name__ == "__main__":
    main()



