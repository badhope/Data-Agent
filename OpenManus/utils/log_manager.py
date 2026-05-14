#!/usr/bin/env python3
"""
系统日志管理模块
提供操作日志、错误日志、访问日志的查看和管理功能
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import re


class LogManager:
    """日志管理器"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # 日志类型定义
        self.log_types = {
            "system": "系统日志",
            "operation": "操作日志",
            "error": "错误日志",
            "access": "访问日志",
            "agent": "Agent日志",
            "api": "API日志",
            "tool": "工具日志"
        }

    def get_log_files(self) -> List[Dict]:
        """获取所有日志文件列表"""
        files = []
        if self.log_dir.exists():
            for file in sorted(self.log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True):
                stat = file.stat()
                files.append({
                    "name": file.name,
                    "path": str(file),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "type": self._classify_log(file.name)
                })
        return files

    def _classify_log(self, filename: str) -> str:
        """根据文件名分类日志"""
        filename_lower = filename.lower()
        for key, name in self.log_types.items():
            if key in filename_lower:
                return name
        return "其他日志"

    def read_log_content(self, filename: str, lines: int = 100, level: Optional[str] = None) -> List[Dict]:
        """读取日志内容"""
        log_path = self.log_dir / filename
        if not log_path.exists():
            return []

        result = []
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()

            # 倒序读取最新日志
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

            for line_num, line in enumerate(recent_lines, start=max(0, len(all_lines) - lines) + 1):
                line = line.strip()
                if not line:
                    continue

                # 解析日志行
                parsed = self._parse_log_line(line, line_num)

                # 按级别过滤
                if level and parsed['level'] != level:
                    continue

                result.append(parsed)

        except Exception as e:
            result.append({
                "line": 0,
                "time": datetime.now().isoformat(),
                "level": "ERROR",
                "message": f"读取日志失败: {str(e)}",
                "source": "system"
            })

        return result

    def _parse_log_line(self, line: str, line_num: int) -> Dict:
        """解析单行日志"""
        # 匹配格式: 2026-05-14 10:30:45 [INFO] module: message
        pattern = r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}),?\s*\[(\w+)\]\s*(?:(\w+)[:\s]+)?(.*)'
        match = re.match(pattern, line)

        if match:
            time_str, level, source, message = match.groups()
            return {
                "line": line_num,
                "time": time_str,
                "level": level.upper(),
                "source": source or "system",
                "message": message.strip()
            }

        # 简单格式
        return {
            "line": line_num,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": self._detect_level(line),
            "source": "unknown",
            "message": line
        }

    def _detect_level(self, line: str) -> str:
        """检测日志级别"""
        line_upper = line.upper()
        if 'ERROR' in line_upper or '❌' in line:
            return "ERROR"
        elif 'WARNING' in line_upper or 'WARN' in line_upper or '⚠️' in line:
            return "WARNING"
        elif 'DEBUG' in line_upper:
            return "DEBUG"
        elif 'SUCCESS' in line_upper or '✅' in line:
            return "SUCCESS"
        return "INFO"

    def search_logs(self, keyword: str, log_type: Optional[str] = None) -> List[Dict]:
        """搜索日志内容"""
        results = []
        files = self.get_log_files()

        for file_info in files:
            if log_type and file_info['type'] != log_type:
                continue

            try:
                with open(file_info['path'], 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, start=1):
                        if keyword.lower() in line.lower():
                            parsed = self._parse_log_line(line.strip(), line_num)
                            parsed['file'] = file_info['name']
                            results.append(parsed)
            except Exception:
                continue

        return results

    def get_log_stats(self) -> Dict:
        """获取日志统计信息"""
        stats = {
            "total_files": 0,
            "total_size": 0,
            "by_type": {},
            "recent_errors": 0,
            "last_updated": None
        }

        files = self.get_log_files()
        stats["total_files"] = len(files)

        for file_info in files:
            stats["total_size"] += file_info["size"]
            log_type = file_info["type"]
            stats["by_type"][log_type] = stats["by_type"].get(log_type, 0) + 1

            # 统计错误
            try:
                with open(file_info['path'], 'r', encoding='utf-8') as f:
                    for line in f:
                        if 'ERROR' in line.upper() or '❌' in line:
                            stats["recent_errors"] += 1
            except Exception:
                pass

        if files:
            stats["last_updated"] = files[0]["modified"]

        return stats


# 全局实例
log_manager = LogManager()


if __name__ == "__main__":
    # 测试日志管理器
    manager = LogManager()
    print("日志统计信息:")
    print(json.dumps(manager.get_log_stats(), indent=2, ensure_ascii=False))
    print("\n日志文件列表:")
    print(json.dumps(manager.get_log_files(), indent=2, ensure_ascii=False))
