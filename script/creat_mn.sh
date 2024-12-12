  # 指定目录，可根据实际需求修改
directory="./result"

# 获取当前日期和时间，格式为 "YYYY-MM-DD HH:MM"
datetime=$(date +"%m-%d_%H_%M")

# 拼接生成文件名
filename="${directory}/${datetime}.txt"


# 在指定目录下创建文件并写入 "hello"
touch "${filename}"

sudo cpulimit -l 400 -f -- ./build/Server 1>>"${filename}" 2>&1