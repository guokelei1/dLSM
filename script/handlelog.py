# 输出以下内容：
# 1. 每个文件的存活时间，按照compaction的间隔来计算
# 2. compaction的占比，不同层级的compaction占比

from dataclasses import dataclass, field
import os
import sys
import time
from typing import List, Dict
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


@dataclass
class FileMetaData:
    file_number: int
    file_size: int

@dataclass
class Level:
    level_number: int
    files: List[FileMetaData] = field(default_factory=list)

@dataclass
class Version:
    levels: Dict[int, Level] = field(default_factory=dict)

def parse_log(filename):
    versions = []
    current_version = None
    current_level = None

    with open(filename, 'r') as file:
        count =0
        for line in file:
            stripped_line = line.strip()

            # 忽略空行
            if not stripped_line:
                continue

            # 识别LSM Tree Information的开始
            if stripped_line.startswith("LSM Tree Information:"):
                if current_version:
                    versions.append(current_version)
                    count += 1
                current_version = Version()
                continue

            # 识别Version content行
            if stripped_line.startswith("Version content:"):
                continue

            # 识别Level行
            level_match = re.match(r"Level (\d+):", stripped_line)
            if level_match:
                level_number = int(level_match.group(1))
                current_level = Level(level_number=level_number)
                current_version.levels[level_number] = current_level
                continue

            # 识别File Number行
            file_match = re.match(r"File Number: (\d+), File Size: (\d+)", stripped_line)
            if file_match:
                file_number = int(file_match.group(1))
                file_size = int(file_match.group(2))
                file_meta = FileMetaData(file_number=file_number, file_size=file_size)
                if current_level:
                    current_level.files.append(file_meta)
                continue

    # 添加最后一个版本
    if current_version:
        versions.append(current_version)
        count += 1

    return count,versions


@dataclass
class Compaction:
    compact_level: int
    count: int 
    time: int
    files: List[List[int]] = field(default_factory=lambda: [[], []])

def parse_neardata(filename,compactions):
    pattern = re.compile(r"NearDataCompaction (\d+)\s+(\d+)")
    with open(filename, 'r') as file:
        for line in file:
            match = re.match(pattern,line)
            if match:
                seg = int(match.group(1))
                time  = int(match.group(2))
                compactions[seg].time = time
        
def parse_compactions(filename):
    compaction_count = 0
    compactions = []
    with open(filename, 'r') as file:
        while True:
            line = file.readline()
            # 如果文件读完了，就退出
            if line == '':
                break
            # 去除行首和行尾的空白字符
            stripped_line = line.strip()
            # 如果line为空行，跳过
            if not stripped_line:
                continue
            # 如果line以Compaction开头，计数
            if stripped_line.startswith('Compaction'):
                compaction = parse_compaction_line(stripped_line)
                if compaction:
                    compactions.append(compaction)
                    compaction_count += 1
    return compaction_count,compactions

def parse_compaction_line(line):
    # 使用正则表达式解析行内容
    pattern = r"Compaction level (\d)  (\d+) Input \d+ level:\s+([\d\s]+) Input \d+ level:\s+([\d\s]+)"
    match = re.match(pattern, line)
    
    if match:
        level = int(match.group(1))
        count_ = int(match.group(2))
        input_0_files = list(map(int, match.group(3).split()))
        input_1_files = list(map(int, match.group(4).split()))
        
        return Compaction(compact_level=level,count=count_,time=0, files=[input_0_files, input_1_files])
    else:
        return None
 
def compute_compact(compactions: List[Compaction]) -> Dict[int, Dict[str, float]]:
    level_counts = {}
    input_0_counts = {}
    input_1_counts = {}
    level_compaction_times = {}
    level_compaction_counts = {}
    time_els = 0
    ccnt = 0
    for compaction in compactions:
        level = compaction.compact_level
        if compaction.count > 0:
            ccnt += 1
            time_els += compaction.time
            if level not in level_compaction_times:
                level_compaction_times[level] = 0
            if level not in level_compaction_counts:
                level_compaction_counts[level] = 0
            level_compaction_times[level] += compaction.time
            level_compaction_counts[level] += 1
        if level in level_counts:
            level_counts[level] += 1
            input_0_counts[level].append(len(compaction.files[0]))
            input_1_counts[level].append(len(compaction.files[1]))
        else:
            level_counts[level] = 1
            input_0_counts[level] = [len(compaction.files[0])]
            input_1_counts[level] = [len(compaction.files[1])]

    result = {}
    for level, count in level_counts.items():
        avg_input_0 = sum(input_0_counts[level]) / len(input_0_counts[level])
        avg_input_1 = sum(input_1_counts[level]) / len(input_1_counts[level])
        result[level] = {
            "count": count,
            "avg_input_0": avg_input_0,
            "avg_input_1": avg_input_1,
            "avg_time": level_compaction_times[level]/level_compaction_counts[level]
        }
    print(f"compaction count: {ccnt}, average time: {time_els/ccnt}")

    return result
   
def calculate_file_lifetimes(versions: List[Version]) -> (Dict[int, int], Dict[int, List[int]]):
    file_lifetimes = {}
    file_levels = {}

    for version in versions:
        for level in version.levels.values():
            for file in level.files:
                if file.file_number in file_lifetimes:
                    file_lifetimes[file.file_number] += 1
                else:
                    file_lifetimes[file.file_number] = 1
                    file_levels[file.file_number] = level.level_number

    level_lifetimes = {}
    for file_number, lifetime in file_lifetimes.items():
        level = file_levels[file_number]
        if level not in level_lifetimes:
            level_lifetimes[level] = []
        level_lifetimes[level].append(lifetime)

    return file_lifetimes, level_lifetimes

def plot_lifetime_distribution(dir_name,file_lifetimes: Dict[int, int]):
    lifetimes = list(file_lifetimes.values())
    plt.hist(lifetimes, bins=range(1, max(lifetimes) + 2), edgecolor='black')
    plt.xlabel('File Lifetime (number of versions)')
    plt.ylabel('Number of Files')
    plt.title('File Lifetime Distribution')
    file_name = dir_name + '/lifetime_distribution.png'
    plt.savefig(file_name)  # 保存图像文件
    
def plot_level_lifetime_distribution(dir_name,level_lifetimes: Dict[int, List[int]]):
    for level, lifetimes in level_lifetimes.items():
        file_name = dir_name + f'/level_{level}_lifetime_distribution.png'
        # 计算生命周期分布
        lifetime_counts = {}
        for lifetime in lifetimes:
            if lifetime in lifetime_counts:
                lifetime_counts[lifetime] += 1
            else:
                lifetime_counts[lifetime] = 1

        # 排序生命周期
        sorted_lifetimes = sorted(lifetime_counts.items())
        x = [item[0] for item in sorted_lifetimes]
        y = [item[1] for item in sorted_lifetimes]

        plt.figure(figsize=(10, 6))
        plt.plot(x, y, marker='o', linestyle='-', color='b', label=f'Level {level}')
        plt.xlabel('File Lifetime (number of versions)')
        plt.ylabel('Number of Files')
        plt.title(f'File Lifetime Distribution for Level {level}')
        
        # 标注大部分节点上的生命周期
        for i, txt in enumerate(y):
            if txt > 1:  # 只标注数量大于1的节点
                plt.annotate(txt, (x[i], y[i]), textcoords="offset points", xytext=(0,10), ha='center')

        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        plt.savefig(file_name)  # 保存图像文件
   
if __name__ == "__main__":
    dirname = '/home/gkl/dLSM/result/'  # 替换为你的txt文件名
    filename = '/home/gkl/dLSM/result/cnode/12-10_17_14.txt'  # 替换为你的txt文件名
    # 目录名称为日志名称，即去掉后缀以及前缀目录
    dirname += filename.split('/')[-1].split('.')[0]
    #创建目录 dirname 如果目录不存在
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    print(dirname)

    compaction_count,compactions = parse_compactions(filename)
    parse_neardata(filename,compactions)
    
    result = compute_compact(compactions)
    result_name = dirname + '/result.txt'
    with open(result_name, 'a') as file:
        for level, stats in result.items():
            file.write(f"Level {level}: {stats['count']} times, "
                    f"average 0 : {stats['avg_input_0']}, "
                    f"average 1 : {stats['avg_input_1']}, "
                    f"average time : {stats['avg_time']}\n")
    count,versions = parse_log(filename)
    
    assert count == compaction_count
    
    file_lifetimes,level_lifetimes = calculate_file_lifetimes(versions)
    
    plot_lifetime_distribution(dirname,file_lifetimes)
    plot_level_lifetime_distribution(dirname,level_lifetimes)
    time.sleep(1)
   