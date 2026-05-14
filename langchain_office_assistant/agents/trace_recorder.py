from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import json
import os
from ..utils.logger import get_logger

logger = get_logger(__name__)

class TraceStep(BaseModel):
    step_id: str = Field(description="步骤唯一标识")
    timestamp: str = Field(description="时间戳")
    action: str = Field(description="执行的动作")
    tool_name: Optional[str] = Field(description="调用的工具名称", default=None)
    input_params: Dict[str, Any] = Field(description="输入参数", default={})
    output: Optional[str] = Field(description="输出结果", default=None)
    duration_ms: Optional[int] = Field(description="执行耗时(毫秒)", default=None)
    error: Optional[str] = Field(description="错误信息", default=None)
    confidence: Optional[float] = Field(description="置信度", default=None)
    reasoning: Optional[str] = Field(description="推理过程", default=None)

class TraceRecord(BaseModel):
    trace_id: str = Field(description="追踪记录唯一标识")
    session_id: str = Field(description="会话ID")
    user_input: str = Field(description="用户输入")
    intent: str = Field(description="识别的意图")
    steps: List[TraceStep] = Field(description="执行步骤列表", default=[])
    final_response: Optional[str] = Field(description="最终响应", default=None)
    total_duration_ms: Optional[int] = Field(description="总耗时(毫秒)", default=None)
    created_at: str = Field(description="创建时间")

class TraceRecorder:
    def __init__(self, storage_path: str = "./traces"):
        self.storage_path = storage_path
        self._ensure_storage()
    
    def _ensure_storage(self):
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
    
    def create_trace(self, session_id: str, user_input: str, intent: str) -> str:
        trace_id = f"{session_id}_{int(datetime.now().timestamp())}"
        record = TraceRecord(
            trace_id=trace_id,
            session_id=session_id,
            user_input=user_input,
            intent=intent,
            created_at=datetime.now().isoformat()
        )
        self._save_record(record)
        return trace_id
    
    def add_step(self, trace_id: str, action: str, tool_name: Optional[str] = None,
                 input_params: Dict[str, Any] = None, output: Optional[str] = None,
                 duration_ms: Optional[int] = None, error: Optional[str] = None,
                 confidence: Optional[float] = None, reasoning: Optional[str] = None) -> None:
        record = self._load_record(trace_id)
        if not record:
            logger.warning(f"Trace record not found: {trace_id}")
            return
        
        step = TraceStep(
            step_id=f"step_{len(record.steps) + 1}",
            timestamp=datetime.now().isoformat(),
            action=action,
            tool_name=tool_name,
            input_params=input_params or {},
            output=output,
            duration_ms=duration_ms,
            error=error,
            confidence=confidence,
            reasoning=reasoning
        )
        record.steps.append(step)
        self._save_record(record)
    
    def finalize_trace(self, trace_id: str, final_response: str, total_duration_ms: int) -> None:
        record = self._load_record(trace_id)
        if record:
            record.final_response = final_response
            record.total_duration_ms = total_duration_ms
            self._save_record(record)
    
    def get_trace(self, trace_id: str) -> Optional[TraceRecord]:
        return self._load_record(trace_id)
    
    def get_traces_by_session(self, session_id: str) -> List[TraceRecord]:
        traces = []
        for filename in os.listdir(self.storage_path):
            if filename.startswith(session_id):
                filepath = os.path.join(self.storage_path, filename)
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        traces.append(TraceRecord(**data))
                except Exception as e:
                    logger.error(f"Failed to load trace file: {e}")
        return sorted(traces, key=lambda x: x.created_at)
    
    def visualize_trace(self, trace_id: str) -> str:
        record = self._load_record(trace_id)
        if not record:
            return f"❌ Trace not found: {trace_id}"
        
        output = f"📋 Trace Report: {record.trace_id}\n"
        output += "=" * 60 + "\n\n"
        output += f"📅 Created: {record.created_at}\n"
        output += f"🔗 Session: {record.session_id}\n"
        output += f"👤 Input: {record.user_input}\n"
        output += f"🎯 Intent: {record.intent}\n\n"
        
        output += "📝 Execution Steps:\n"
        output += "-" * 40 + "\n"
        
        for step in record.steps:
            output += f"\n[{step.step_id}] {step.timestamp}\n"
            output += f"   Action: {step.action}\n"
            if step.tool_name:
                output += f"   Tool: {step.tool_name}\n"
            if step.input_params:
                output += f"   Input: {json.dumps(step.input_params, ensure_ascii=False)}\n"
            if step.output:
                output += f"   Output: {step.output[:200]}..." if len(step.output) > 200 else f"   Output: {step.output}\n"
            if step.duration_ms:
                output += f"   Duration: {step.duration_ms}ms\n"
            if step.error:
                output += f"   ❌ Error: {step.error}\n"
        
        if record.final_response:
            output += "\n" + "=" * 40 + "\n"
            output += f"✅ Final Response:\n{record.final_response}\n"
        
        if record.total_duration_ms:
            output += f"\n⏱️ Total Duration: {record.total_duration_ms}ms\n"
        
        return output
    
    def _save_record(self, record: TraceRecord):
        filepath = os.path.join(self.storage_path, f"{record.trace_id}.json")
        try:
            with open(filepath, "w") as f:
                json.dump(record.dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save trace record: {e}")
    
    def _load_record(self, trace_id: str) -> Optional[TraceRecord]:
        filepath = os.path.join(self.storage_path, f"{trace_id}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    return TraceRecord(**data)
            except Exception as e:
                logger.error(f"Failed to load trace record: {e}")
        return None