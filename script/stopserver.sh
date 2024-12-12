#!/bin/bash

# 查找 Server 程序的 PID
SERVER_PID=$(pgrep -f './build/Server')

# 如果找到了 PID，则终止该进程
if [ -n "$SERVER_PID" ]; then
  sudo kill $SERVER_PID
  echo "Server (PID $SERVER_PID) has been terminated."
else
  echo "Server is not running."
fi