#!/bin/bash

# 指定目录，可根据实际需求修改
directory="./result"

# 获取当前日期和时间，格式为 "YYYY-MM-DD HH:MM"
datetime=$(date +"%m-%d_%H_%M")

# 拼接生成文件名
filename="${directory}/${datetime}.txt"

# 在指定目录下创建文件并写入 "hello"
touch "${filename}"


benchmarks="fillrandom,readrandom,readrandom,,readrandomwriterandom"
#benchmarks="fillrandom,readrandom,readrandomwriterandom"
#benchmarks="fillrandom,readrandom"

# 定义threads参数
threads=16

# 定义value_size参数
value_size=400

# 定义num参数
kv_num=100000000

kv_num_per_thread=$((kv_num/threads))


# 定义bloom_bits参数
bloom_bits=10

# 定义readwritepercent参数
readwritepercent=5

# 定义compute_node_id参数
compute_node_id=0

# 定义fixed_compute_shards_num参数
fixed_compute_shards_num=0


# 将参数信息写入文件
echo "Parameters:" >>"${filename}"
echo "benchmarks: ${benchmarks}" >>"${filename}"
echo "threads: ${threads}" >>"${filename}"
echo "value_size: ${value_size}" >>"${filename}"
echo "num: ${kv_num}" >>"${filename}"
echo "kv_num_per_thread: ${kv_num_per_thread}" >>"${filename}"
echo "bloom_bits: ${bloom_bits}" >> "${filename}"
echo "readwritepercent: ${readwritepercent}" >>"${filename}"
echo "compute_node_id: ${compute_node_id}" >>"${filename}"
echo "fixed_compute_shards_num: ${fixed_compute_shards_num}" >>"${filename}"


# 执行db_bench命令并将标准输出重定向到文件
sudo ./build/db_bench --benchmarks="${benchmarks}" --threads="${threads}" --value_size="${value_size}" --num="${kv_num_per_thread}" --bloom_bits="${bloom_bits}" --readwritepercent="${readwritepercent}" --compute_node_id="${compute_node_id}" --fixed_compute_shards_num="${fixed_compute_shards_num}" 1>>"${filename}"

