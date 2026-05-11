import pytest
from langchain_office_assistant.plugins import (
    EmailPlugin,
    CalendarPlugin,
    TaskPlugin,
    DocumentPlugin,
    PPTPlugin,
    KnowledgePlugin,
    ChartPlugin,
    CalcPlugin,
)

class TestEmailPlugin:
    @pytest.fixture
    def plugin(self):
        plugin = EmailPlugin()
        plugin.initialize({})
        return plugin
    
    @pytest.mark.asyncio
    async def test_search_emails(self, plugin):
        result = await plugin.execute("search_emails", keyword="项目")
        assert "项目" in result
    
    @pytest.mark.asyncio
    async def test_send_email(self, plugin):
        result = await plugin.execute("send_email", to=["test@example.com"], subject="Test", body="Test body")
        assert "Email sent successfully" in result

class TestCalendarPlugin:
    @pytest.fixture
    def plugin(self):
        plugin = CalendarPlugin()
        plugin.initialize({})
        return plugin
    
    @pytest.mark.asyncio
    async def test_list_events(self, plugin):
        result = await plugin.execute("list_events", date="2025-01-15")
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_create_event(self, plugin):
        result = await plugin.execute("create_event", title="Test Meeting", start_time="2025-01-15 14:00", end_time="2025-01-15 15:00")
        assert "created successfully" in result

class TestTaskPlugin:
    @pytest.fixture
    def plugin(self):
        plugin = TaskPlugin()
        plugin.initialize({})
        return plugin
    
    @pytest.mark.asyncio
    async def test_create_task(self, plugin):
        result = await plugin.execute("create_task", title="Test Task", description="Test description")
        assert "created successfully" in result
    
    @pytest.mark.asyncio
    async def test_list_tasks(self, plugin):
        result = await plugin.execute("list_tasks")
        assert isinstance(result, str)

class TestCalcPlugin:
    @pytest.fixture
    def plugin(self):
        plugin = CalcPlugin()
        plugin.initialize({})
        return plugin
    
    @pytest.mark.asyncio
    async def test_calculate(self, plugin):
        result = await plugin.execute("calculate", expression="2 + 3 * 4")
        assert "14" in result
    
    @pytest.mark.asyncio
    async def test_statistics(self, plugin):
        result = await plugin.execute("statistics", numbers=[1, 2, 3, 4, 5])
        assert "mean" in result.lower()
    
    @pytest.mark.asyncio
    async def test_currency_convert(self, plugin):
        result = await plugin.execute("currency_convert", amount=100, from_currency="USD", to_currency="CNY")
        assert "CNY" in result

class TestChartPlugin:
    @pytest.fixture
    def plugin(self):
        plugin = ChartPlugin()
        plugin.initialize({})
        return plugin
    
    @pytest.mark.asyncio
    async def test_create_bar_chart(self, plugin):
        result = await plugin.execute("create_bar_chart", data={"A": 10, "B": 20, "C": 30}, title="Test Chart")
        assert "saved" in result.lower()
    
    @pytest.mark.asyncio
    async def test_create_line_chart(self, plugin):
        result = await plugin.execute("create_line_chart", data={"Jan": 10, "Feb": 20, "Mar": 15}, title="Line Chart")
        assert "saved" in result.lower()

class TestKnowledgePlugin:
    @pytest.fixture
    def plugin(self):
        plugin = KnowledgePlugin()
        plugin.initialize({})
        return plugin
    
    @pytest.mark.asyncio
    async def test_add_document(self, plugin):
        result = await plugin.execute("add_document", content="Test content", title="Test Document")
        assert "added successfully" in result
    
    @pytest.mark.asyncio
    async def test_search_knowledge(self, plugin):
        result = await plugin.execute("search_knowledge", query="test")
        assert isinstance(result, str)

class TestPPTPlugin:
    @pytest.fixture
    def plugin(self):
        plugin = PPTPlugin()
        plugin.initialize({})
        return plugin
    
    @pytest.mark.asyncio
    async def test_create_ppt(self, plugin):
        result = await plugin.execute("create_ppt", title="Test Presentation")
        assert "created successfully" in result

class TestDocumentPlugin:
    @pytest.fixture
    def plugin(self):
        plugin = DocumentPlugin()
        plugin.initialize({})
        return plugin
    
    @pytest.mark.asyncio
    async def test_write_document(self, plugin):
        result = await plugin.execute("write_document", file_path="test.txt", content="Test content")
        assert "saved" in result.lower()