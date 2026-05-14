#!/bin/bash

echo "=========================================="
echo "测试页面路由"
echo "=========================================="

echo -e "\n[1] 测试主页..."
curl -s -o /dev/null -w "状态码: %{http_code}\n" http://localhost:8080/

echo -e "\n[2] 测试功能页面..."
curl -s -o /dev/null -w "状态码: %{http_code}\n" http://localhost:8080/features

echo -e "\n[3] 测试日志页面..."
curl -s -o /dev/null -w "状态码: %{http_code}\n" http://localhost:8080/logs

echo -e "\n[4] 测试WebSocket..."
curl -s -o /dev/null -w "状态码: %{http_code}\n" --include --no-buffer http://localhost:8080/ws

