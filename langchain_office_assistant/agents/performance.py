"""
并发控制器和性能监控
限制并发请求，防止系统过载
"""
from typing import Dict, Any, Optional
import asyncio
import time
import threading
from dataclasses import dataclass, field
from collections import defaultdict
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RequestMetrics:
    """请求指标"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration_ms: float = 0
    avg_duration_ms: float = 0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0
    requests_per_minute: float = 0


class ConcurrencyLimiter:
    """并发限制器"""

    def __init__(self, max_concurrent: int = 10, max_requests_per_minute: int = 60):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._max_requests_per_minute = max_requests_per_minute
        self._request_times = []
        self._lock = threading.Lock()

    async def acquire(self):
        """获取执行许可"""
        await self._semaphore.acquire()
        self._clean_old_requests()

        if len(self._request_times) >= self._max_requests_per_minute:
            wait_time = 60 - (time.time() - self._request_times[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                self._clean_old_requests()

        self._request_times.append(time.time())

    def release(self):
        """释放执行许可"""
        self._semaphore.release()

    def _clean_old_requests(self):
        """清理超过1分钟的请求记录"""
        current_time = time.time()
        self._request_times = [
            t for t in self._request_times
            if current_time - t < 60
        ]

    @property
    def available_slots(self) -> int:
        """可用并发槽位数"""
        return self._semaphore._value


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self._metrics: Dict[str, RequestMetrics] = defaultdict(
            lambda: RequestMetrics()
        )
        self._start_time = time.time()
        self._lock = threading.Lock()

    def record_request(
        self,
        component: str,
        success: bool,
        duration_ms: float
    ):
        """记录请求"""
        with self._lock:
            metrics = self._metrics[component]
            metrics.total_requests += 1

            if success:
                metrics.successful_requests += 1
            else:
                metrics.failed_requests += 1

            metrics.total_duration_ms += duration_ms
            metrics.avg_duration_ms = (
                metrics.total_duration_ms / metrics.total_requests
            )
            metrics.min_duration_ms = min(
                metrics.min_duration_ms, duration_ms
            )
            metrics.max_duration_ms = max(
                metrics.max_duration_ms, duration_ms
            )

    def get_metrics(self, component: str = None) -> Dict[str, Any]:
        """获取指标"""
        with self._lock:
            if component:
                return self._get_component_metrics(component)
            return self._get_all_metrics()

    def _get_component_metrics(self, component: str) -> Dict[str, Any]:
        """获取单个组件的指标"""
        metrics = self._metrics.get(component, RequestMetrics())

        success_rate = (
            metrics.successful_requests / metrics.total_requests * 100
            if metrics.total_requests > 0 else 0
        )

        return {
            "component": component,
            "total_requests": metrics.total_requests,
            "successful_requests": metrics.successful_requests,
            "failed_requests": metrics.failed_requests,
            "success_rate": f"{success_rate:.1f}%",
            "avg_duration_ms": f"{metrics.avg_duration_ms:.2f}",
            "min_duration_ms": f"{metrics.min_duration_ms:.2f}" if metrics.min_duration_ms != float('inf') else "N/A",
            "max_duration_ms": f"{metrics.max_duration_ms:.2f}",
        }

    def _get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        uptime = time.time() - self._start_time

        total_requests = sum(
            m.total_requests for m in self._metrics.values()
        )
        total_success = sum(
            m.successful_requests for m in self._metrics.values()
        )

        return {
            "uptime_seconds": f"{uptime:.2f}",
            "total_requests": total_requests,
            "overall_success_rate": f"{total_success/total_requests*100:.1f}%" if total_requests > 0 else "N/A",
            "components": {
                name: self._get_component_metrics(name)
                for name in self._metrics.keys()
            }
        }

    def reset(self):
        """重置指标"""
        with self._lock:
            self._metrics.clear()
            self._start_time = time.time()

    def get_health_status(self) -> str:
        """获取健康状态"""
        all_metrics = self._get_all_metrics()

        if not all_metrics["components"]:
            return "🟢 HEALTHY - No requests recorded"

        unhealthy_components = []

        for component, metrics in all_metrics["components"].items():
            success_rate = float(metrics["success_rate"].replace("%", ""))

            if success_rate < 80:
                unhealthy_components.append(f"{component} (success: {success_rate:.1f}%)")

        if unhealthy_components:
            return f"🔴 UNHEALTHY - Low success rate in: {', '.join(unhealthy_components)}"

        return "🟢 HEALTHY - All components operating normally"


_performance_monitor = None
_concurrency_limiter = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_concurrency_limiter(
    max_concurrent: int = 10,
    max_requests_per_minute: int = 60
) -> ConcurrencyLimiter:
    """获取全局并发限制器"""
    global _concurrency_limiter
    if _concurrency_limiter is None:
        _concurrency_limiter = ConcurrencyLimiter(max_concurrent, max_requests_per_minute)
    return _concurrency_limiter
