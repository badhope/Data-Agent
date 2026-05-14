"""
Skill Manager - 技能管理系统，支持AI一键生成
"""
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime


# ==================== 技能注册表 ====================

class SkillRegistry:
    """技能注册表 - 管理所有可用技能"""
    
    def __init__(self):
        self.skills: Dict[str, Dict[str, Any]] = {}
        self._register_built_in_skills()
    
    def _register_built_in_skills(self):
        """注册内置技能"""
        self.register(
            id="code_reviewer",
            name="代码审查专家",
            description="智能代码审查，发现潜在问题并提供优化建议",
            category="code_analysis",
            icon="🔍",
            type="built_in",
            parameters=[
                {"name": "code", "type": "string", "description": "待审查的代码", "required": True},
                {"name": "language", "type": "string", "description": "编程语言", "required": False}
            ]
        )
        
        self.register(
            id="data_analyzer",
            name="数据分析助手",
            description="执行数据分析和可视化",
            category="data_analysis",
            icon="📊",
            type="built_in",
            parameters=[
                {"name": "data", "type": "string", "description": "数据", "required": True},
                {"name": "analysis_type", "type": "string", "description": "分析类型", "required": True}
            ]
        )
        
        self.register(
            id="document_processor",
            name="文档处理助手",
            description="提取、总结和分析文档内容",
            category="document_processing",
            icon="📄",
            type="built_in",
            parameters=[
                {"name": "content", "type": "string", "description": "文档内容", "required": True},
                {"name": "task", "type": "string", "description": "任务类型", "required": True}
            ]
        )
        
        self.register(
            id="financial_analyzer",
            name="财务分析工具",
            description="财务报表分析和指标计算",
            category="financial",
            icon="💰",
            type="built_in",
            parameters=[
                {"name": "company", "type": "string", "description": "公司名称", "required": True},
                {"name": "year", "type": "int", "description": "年份", "required": False}
            ]
        )
    
    def register(self, id: str, name: str, description: str, 
                 category: str, icon: str, type: str, 
                 parameters: List[Dict[str, str]] = None):
        """
        注册一个新技能
        
        Args:
            id: 技能ID
            name: 显示名称
            description: 描述
            category: 分类
            icon: 图标
            type: 类型
            parameters: 参数列表
        """
        self.skills[id] = {
            "id": id,
            "name": name,
            "description": description,
            "category": category,
            "icon": icon,
            "type": type,
            "parameters": parameters or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def get_all(self) -> List[Dict[str, Any]]:
        """获取所有技能"""
        return list(self.skills.values())
    
    def get(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """通过ID获取技能"""
        return self.skills.get(skill_id)
    
    def delete(self, skill_id: str) -> bool:
        """删除技能"""
        if skill_id in self.skills and self.skills[skill_id]["type"] != "built_in":
            del self.skills[skill_id]
            return True
        return False


# 全局单例
registry = SkillRegistry()


# ==================== AI技能生成器 ====================

class AISkillGenerator:
    """AI技能生成器 - 一键生成自定义Skill"""
    
    def __init__(self):
        pass
    
    async def generate(
        self,
        skill_type: str,
        description: str,
        parameters: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        生成新的Skill
        
        Args:
            skill_type: 技能类型
            description: 技能描述
            parameters: 可选的参数列表
            
        Returns:
            生成的Skill配置
        """
        # 生成唯一ID
        skill_id = f"ai_generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 配置
        config = {
            "name": f"{skill_type}_{skill_id.split('_')[-1]}",
            "display_name": f"AI生成 - {description[:20]}",
            "description": description,
            "category": skill_type,
            "parameters": parameters or [
                {"name": "input", "type": "string", "description": "输入数据", "required": True}
            ]
        }
        
        # 注册新技能
        registry.register(
            id=skill_id,
            name=config["display_name"],
            description=config["description"],
            category=config["category"],
            icon="🤖",
            type="ai_generated",
            parameters=config["parameters"]
        )
        
        return {
            "success": True,
            "skill_id": skill_id,
            "config": config,
            "code": "def skill_function(input_data):\n    return {'result': input_data}\n",
            "created_at": datetime.now().isoformat()
        }


# 全局AI生成器实例
ai_generator = AISkillGenerator()


# ==================== 技能执行器 ====================

class SkillExecutor:
    """技能执行器"""
    
    def __init__(self):
        self.executors = {}
        self._register_default_executors()
    
    def _register_default_executors(self):
        """注册默认执行器"""
        # 这里只是示例，实际执行逻辑可以按需实现
        pass
    
    async def execute(self, skill_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            skill_id: 技能ID
            params: 执行参数
            
        Returns:
            执行结果
        """
        skill = registry.get(skill_id)
        if not skill:
            return {
                "success": False,
                "error": f"Skill not found: {skill_id}"
            }
        
        # 简单的示例执行逻辑
        if skill_id == "code_reviewer":
            return await self._code_reviewer_executor(params)
        elif skill_id == "data_analyzer":
            return await self._data_analyzer_executor(params)
        elif skill_id == "financial_analyzer":
            return await self._financial_analyzer_executor(params)
        else:
            return self._default_executor(skill, params)
    
    async def _code_reviewer_executor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """代码审查执行器"""
        code = params.get("code", "")
        issues = []
        suggestions = []
        
        if len(code) > 0 and "print" in code:
            issues.append("建议使用日志系统而非print")
        if "eval(" in code:
            issues.append("eval函数存在安全风险，建议避免使用")
        
        suggestions.append("遵循PEP 8代码风格")
        suggestions.append("添加函数文档字符串")
        
        return {
            "success": True,
            "review": {
                "issues": issues,
                "suggestions": suggestions,
                "score": 75 if not issues else 60
            }
        }
    
    async def _data_analyzer_executor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """数据分析执行器"""
        data = params.get("data", "")
        
        return {
            "success": True,
            "analysis": {
                "length": len(str(data)),
                "type": str(type(data)),
                "sample": str(data)[:100]
            }
        }
    
    async def _financial_analyzer_executor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """财务分析执行器"""
        try:
            from web.tidycup.nl2sql_engine import FullNL2SQLPipeline
            db_path = Path.cwd() / "data" / "skill_test.db"
            pipeline = FullNL2SQLPipeline(db_path)
            pipeline.initialize()
            
            result = await pipeline.process_query(
                params.get("company", "")
            )
            
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _default_executor(self, skill: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """默认执行器"""
        return {
            "success": True,
            "message": f"Executed {skill['name']}",
            "params_received": params,
            "skill": skill
        }


# 全局执行器实例
executor = SkillExecutor()


# ==================== 辅助函数 ====================

def get_all_skills() -> List[Dict[str, Any]]:
    """获取所有技能"""
    return registry.get_all()


def get_skill_by_id(skill_id: str) -> Optional[Dict[str, Any]]:
    """通过ID获取技能"""
    return registry.get(skill_id)


async def execute_skill(skill_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """执行技能"""
    return await executor.execute(skill_id, params)


async def generate_ai_skill(
    skill_type: str,
    description: str,
    parameters: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """AI生成技能"""
    return await ai_generator.generate(skill_type, description, parameters)
