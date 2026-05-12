"""Simple logging module for the Data Agent application."""

import os
import json
from datetime import datetime
from typing import Optional
from pathlib import Path


class SimpleLogger:
    """A simple logger that writes to both file and keeps in-memory logs."""
    
    def __init__(self, name: str = "DataAgent", log_file: Optional[str] = None):
        self.name = name
        self.log_file = log_file or "./logs/data_agent.log"
        self.in_memory_logs = []
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Ensure log directory exists."""
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def _write_to_file(self, level: str, message: str):
        """Write log to file."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{level}] [{self.name}] {message}\n"
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass
    
    def _add_to_memory(self, level: str, message: str, details: Optional[dict] = None):
        """Add log to in-memory storage."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "details": details
        }
        self.in_memory_logs.append(log_entry)
        
        if len(self.in_memory_logs) > 100:
            self.in_memory_logs = self.in_memory_logs[-100:]
    
    def debug(self, message: str, details: Optional[dict] = None):
        """Log debug message."""
        self._write_to_file("DEBUG", message)
        self._add_to_memory("DEBUG", message, details)
    
    def info(self, message: str, details: Optional[dict] = None):
        """Log info message."""
        self._write_to_file("INFO", message)
        self._add_to_memory("INFO", message, details)
    
    def warning(self, message: str, details: Optional[dict] = None):
        """Log warning message."""
        self._write_to_file("WARNING", message)
        self._add_to_memory("WARNING", message, details)
    
    def error(self, message: str, details: Optional[dict] = None):
        """Log error message."""
        self._write_to_file("ERROR", message)
        self._add_to_memory("ERROR", message, details)
    
    def get_logs(self, level: Optional[str] = None, limit: int = 50) -> list:
        """Get logs, optionally filtered by level."""
        logs = self.in_memory_logs
        
        if level:
            logs = [log for log in logs if log["level"] == level]
        
        return logs[-limit:]
    
    def get_recent_logs(self, count: int = 20) -> list:
        """Get recent logs."""
        return self.in_memory_logs[-count:]
    
    def clear_logs(self):
        """Clear in-memory logs."""
        self.in_memory_logs = []


_logger = None


def get_logger() -> SimpleLogger:
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        _logger = SimpleLogger()
    return _logger


def log_agent_action(action: str, details: Optional[dict] = None):
    """Log an agent action."""
    logger = get_logger()
    logger.info(f"[AGENT] {action}", details)


def log_tool_call(tool_name: str, args: dict, result: str):
    """Log a tool call."""
    logger = get_logger()
    logger.info(f"[TOOL] {tool_name} called", {
        "args": args,
        "result_preview": result[:200] if len(result) > 200 else result
    })


def log_error(context: str, error: Exception):
    """Log an error with context."""
    logger = get_logger()
    logger.error(f"[ERROR] {context}", {
        "error_type": type(error).__name__,
        "error_message": str(error)
    })
