# 输出以下内容：
# 1. 每个文件的存活时间，按照compaction的间隔来计算
# 2. compaction的占比，不同层级的compaction占比




def count_compaction(filename):
    count = 0
    with open(filename, 'r') as file:
        for line in file:
            count += line.lower().count('file')
    return count

if __name__ == "__main__":
    filename = '/home/gkl/dLSM/result/12-09_18_26good.txt'  # 替换为你的txt文件名
    compaction_count = count_compaction(filename)
    print(f"The word 'compaction' appears {compaction_count} times in the file.")