#!/bin/bash

echo "=========================================="
echo "测试API端点"
echo "=========================================="

echo -e "\n[1] 测试文档处理API..."
curl -s -o /dev/null -w "POST /documents/summarize: %{http_code}\n" \
  -X POST http://localhost:8080/api/documents/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "测试文本"}'

curl -s -o /dev/null -w "POST /documents/ppt/generate: %{http_code}\n" \
  -X POST http://localhost:8080/api/documents/ppt/generate \
  -H "Content-Type: application/json" \
  -d '{"title": "测试PPT", "slides": [{"title": "测试", "content": "测试内容"}]}'

echo -e "\n[2] 测试设置API..."
curl -s -o /dev/null -w "GET /api/settings: %{http_code}\n" \
  -X GET http://localhost:8080/api/settings

curl -s -o /dev/null -w "POST /api/settings: %{http_code}\n" \
  -X POST http://localhost:8080/api/settings \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen-plus-latest"}'

echo -e "\n[3] 测试日志API..."
curl -s -o /dev/null -w "GET /api/logs/stats: %{http_code}\n" \
  -X GET http://localhost:8080/api/logs/stats

curl -s -o /dev/null -w "GET /api/logs/files: %{http_code}\n" \
  -X GET http://localhost:8080/api/logs/files

