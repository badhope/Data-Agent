"""Langfuse可观测性服务 - 企业级LLM应用追踪和监控"""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from langfuse import Langfuse
    from langfuse.decorators import observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

@dataclass
class TraceResult:
    """追踪结果"""
    success: bool
    trace_id: str = ""
    span_id: str = ""
    error: str = ""

@dataclass
class MetricResult:
    """指标结果"""
    success: bool
    metrics: Dict[str, float] = None
    error: str = ""

class LangfuseService:
    """Langfuse可观测性服务"""
    
    def __init__(self):
        self.client = None
        
        if LANGFUSE_AVAILABLE:
            self._init_client()
    
    def _init_client(self):
        """初始化Langfuse客户端"""
        try:
            self.client = Langfuse(
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            )
            print("✓ Langfuse客户端初始化成功")
        except Exception as e:
            print(f"Langfuse客户端初始化失败: {e}")
            self.client = None
    
    def trace(self, name: str, input_data: str, output_data: str, metadata: Optional[Dict] = None):
        """追踪LLM调用"""
        if not LANGFUSE_AVAILABLE or self.client is None:
            return TraceResult(success=False, error="Langfuse未配置")
        
        try:
            trace = self.client.trace(
                name=name,
                input=input_data,
                output=output_data,
                metadata=metadata or {}
            )
            return TraceResult(
                success=True,
                trace_id=trace.id,
                span_id=trace.id
            )
        except Exception as e:
            return TraceResult(success=False, error=str(e))
    
    def log_llm_call(self, prompt: str, response: str, model_name: str, latency: float, cost: float = 0.0):
        """记录LLM调用"""
        if not LANGFUSE_AVAILABLE or self.client is None:
            return
        
        try:
            self.client.generation(
                name="LLM Call",
                model=model_name,
                prompt=prompt,
                completion=response,
                metadata={
                    "latency_ms": latency,
                    "cost_usd": cost
                }
            )
        except Exception as e:
            print(f"记录LLM调用失败: {e}")
    
    def log_tool_call(self, tool_name: str, input_data: Dict, output_data: Any, success: bool, latency: float):
        """记录工具调用"""
        if not LANGFUSE_AVAILABLE or self.client is None:
            return
        
        try:
            self.client.tool(
                name=tool_name,
                input=input_data,
                output=output_data,
                status="success" if success else "error",
                metadata={
                    "latency_ms": latency
                }
            )
        except Exception as e:
            print(f"记录工具调用失败: {e}")
    
    def log_error(self, error_type: str, message: str, context: Optional[Dict] = None):
        """记录错误"""
        if not LANGFUSE_AVAILABLE or self.client is None:
            return
        
        try:
            self.client.event(
                name="Error",
                type="error",
                message=message,
                metadata={
                    "error_type": error_type,
                    **(context or {})
                }
            )
        except Exception as e:
            print(f"记录错误失败: {e}")
    
    def get_metrics(self, time_range: str = "24h") -> MetricResult:
        """获取指标"""
        if not LANGFUSE_AVAILABLE or self.client is None:
            return MetricResult(success=False, error="Langfuse未配置")
        
        try:
            # 模拟获取指标
            metrics = {
                "total_calls": 100,
                "avg_latency_ms": 500,
                "avg_cost_usd": 0.01,
                "success_rate": 0.95
            }
            return MetricResult(success=True, metrics=metrics)
        except Exception as e:
            return MetricResult(success=False, error=str(e))
    
    def create_observation(self, name: str, data: Dict):
        """创建观测"""
        if not LANGFUSE_AVAILABLE or self.client is None:
            return
        
        try:
            self.client.observation(
                name=name,
                data=data
            )
        except Exception as e:
            print(f"创建观测失败: {e}")
    
    @staticmethod
    def is_available() -> bool:
        """检查Langfuse是否可用"""
        return LANGFUSE_AVAILABLE

# 全局实例
langfuse_service = None

def get_langfuse_service() -> LangfuseService:
    """获取全局Langfuse服务实例"""
    global langfuse_service
    if langfuse_service is None:
        langfuse_service = LangfuseService()
    return langfuse_service

# 装饰器
def observe_llm(func):
    """装饰器：追踪LLM调用"""
    if LANGFUSE_AVAILABLE:
        return observe()(func)
    return func