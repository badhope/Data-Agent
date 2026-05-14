#!/bin/bash

echo "=========================================="
echo "测试静态文件"
echo "=========================================="

echo -e "\n[1] 测试CSS文件..."
curl -s -o /dev/null -w "chat.css: %{http_code}\n" http://localhost:8080/static/css/chat.css
curl -s -o /dev/null -w "thinking.css: %{http_code}\n" http://localhost:8080/static/css/thinking.css
curl -s -o /dev/null -w "style.css: %{http_code}\n" http://localhost:8080/static/css/style.css

echo -e "\n[2] 测试JavaScript文件..."
curl -s -o /dev/null -w "app.js: %{http_code}\n" http://localhost:8080/static/js/app.js
curl -s -o /dev/null -w "utils.js: %{http_code}\n" http://localhost:8080/static/js/utils.js

