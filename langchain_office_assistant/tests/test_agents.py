import pytest
from langchain_office_assistant.agents import (
    OfficeAgent,
    create_office_agent,
    IntentRecognizer,
    TraceRecorder,
    IntentType,
)

class TestIntentRecognizer:
    @pytest.fixture
    def recognizer(self):
        return IntentRecognizer()
    
    def test_recognize_email_intent(self, recognizer):
        result = recognizer.recognize("帮我发送一封邮件给张三")
        assert result.intent == IntentType.EMAIL.value
        assert result.confidence > 0.5
    
    def test_recognize_calc_intent(self, recognizer):
        result = recognizer.recognize("计算 2 + 3 * 4")
        assert result.intent == IntentType.CALC.value
        assert result.confidence > 0.5
    
    def test_recognize_chat_intent(self, recognizer):
        result = recognizer.recognize("你好，今天天气怎么样？")
        assert result.intent == IntentType.CHAT.value
    
    def test_recognize_knowledge_intent(self, recognizer):
        result = recognizer.recognize("在知识库中搜索项目管理相关内容")
        assert result.intent == IntentType.KNOWLEDGE.value
        assert result.confidence > 0.5

class TestTraceRecorder:
    @pytest.fixture
    def recorder(self):
        return TraceRecorder()
    
    def test_create_trace(self, recorder):
        trace_id = recorder.create_trace("test_session", "test input", "test_intent")
        assert trace_id is not None
        assert "test_session" in trace_id
    
    def test_add_step(self, recorder):
        trace_id = recorder.create_trace("test_session", "test input", "test_intent")
        recorder.add_step(trace_id, "test_action", "test_tool", {"param": "value"}, "output", 100)
        
        record = recorder.get_trace(trace_id)
        assert len(record.steps) == 1
        assert record.steps[0].action == "test_action"
    
    def test_visualize_trace(self, recorder):
        trace_id = recorder.create_trace("test_session", "test input", "test_intent")
        recorder.add_step(trace_id, "test_action", "test_tool", {"param": "value"}, "output", 100)
        recorder.finalize_trace(trace_id, "final response", 200)
        
        report = recorder.visualize_trace(trace_id)
        assert "Trace Report" in report
        assert "test input" in report
        assert "test_intent" in report

class TestOfficeAgent:
    @pytest.fixture
    def agent(self):
        return create_office_agent({"agent_model": "gpt-3.5-turbo"})
    
    @pytest.mark.asyncio
    async def test_agent_run(self, agent):
        result = await agent.run("你好")
        assert "response" in result
        assert "session_id" in result
        assert "trace_id" in result
    
    def test_get_available_tools(self, agent):
        tools = agent.get_available_tools()
        assert len(tools) > 0
        assert isinstance(tools, list)
    
    def test_get_trace_report(self, agent):
        report = agent.get_trace_report("invalid_trace_id")
        assert "Trace not found" in report

class TestAgentIntegration:
    @pytest.mark.asyncio
    async def test_calc_integration(self):
        agent = create_office_agent({"agent_model": "gpt-3.5-turbo"})
        result = await agent.run("计算 10 + 20")
        
        assert "response" in result
        assert result["intent"] == IntentType.CALC.value
    
    @pytest.mark.asyncio
    async def test_knowledge_integration(self):
        agent = create_office_agent({"agent_model": "gpt-3.5-turbo"})
        result = await agent.run("搜索知识库")
        
        assert "response" in result
        assert result["intent"] == IntentType.KNOWLEDGE.value