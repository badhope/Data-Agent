"""
DataAgent - 技能路由
包含技能 CRUD、生成、使用、测试、导入导出、模板等端点
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from database import skills, save_skills, current_settings
from config import OPENAI_AVAILABLE
from models import Skill
import json, uuid, datetime, re

router = APIRouter()


async def call_llm(prompt: str, settings) -> str:
    if not OPENAI_AVAILABLE:
        return "错误: 未安装 openai 库，请运行 pip install openai"
    if not settings.llm.get("api_key"):
        return "请先在设置中配置 API Key"
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.llm["api_key"],
            base_url=settings.llm["base_url"]
        )
        response = await client.chat.completions.create(
            model=settings.llm["model"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.llm["max_tokens"],
            temperature=settings.llm["temperature"],
            top_p=settings.llm["top_p"]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM调用失败: {str(e)}"


# ==================== 技能 CRUD ====================

@router.get("/api/skills")
async def list_skills():
    return JSONResponse([skill.model_dump() for skill in skills.values()])


@router.post("/api/skills/generate")
async def generate_skill(request: Request):
    data = await request.json()
    purpose = data.get("purpose", "")

    if not purpose:
        raise HTTPException(status_code=400, detail="请提供技能用途描述")

    if not current_settings.llm.get("api_key"):
        raise HTTPException(status_code=400, detail="请先在设置中配置API Key")

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=current_settings.llm["api_key"],
            base_url=current_settings.llm.get("base_url", "https://api.openai.com/v1")
        )

        prompt = f"""基于以下需求，生成一个AI技能的建议：

需求：{purpose}

请生成一个JSON对象，包含以下字段：
- name: 技能名称（中文，不超过30字）
- icon: 表情符号图标（一个emoji）
- description: 详细描述（中文，100字以内）
- category: 分类（代码/数据/文档/翻译/写作/学习/创意/其他）

只返回JSON，不要其他内容。"""

        response = await client.chat.completions.create(
            model=current_settings.llm.get("model", "gpt-4o"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )

        result_text = response.choices[0].message.content.strip()

        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return JSONResponse(result)
        else:
            raise HTTPException(status_code=500, detail="AI返回格式错误")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI生成失败: {str(e)}")


@router.post("/api/skills")
async def create_skill(request: Request):
    data = await request.json()
    skill_id = data.get("id", str(uuid.uuid4()))
    now = datetime.datetime.now().isoformat()
    skill = Skill(
        id=skill_id,
        name=data.get("name", "未命名技能"),
        description=data.get("description", ""),
        version=data.get("version", "1.0.0"),
        author=data.get("author", ""),
        category=data.get("category", "custom"),
        type=data.get("type", "custom"),
        icon=data.get("icon", "⚡"),
        created_at=now,
        updated_at=now,
        parameters=data.get("parameters", []),
        prompts=data.get("prompts", {}),
        tools=data.get("tools", [])
    )
    skills[skill_id] = skill
    save_skills()
    return JSONResponse(skill.model_dump())


@router.get("/api/skills/{skill_id}")
async def get_skill(skill_id: str):
    if skill_id not in skills:
        raise HTTPException(status_code=404, detail="技能不存在")
    return JSONResponse(skills[skill_id].model_dump())


@router.post("/api/skills/{skill_id}/use")
async def use_skill(skill_id: str, request: Request):
    if skill_id not in skills:
        raise HTTPException(status_code=404, detail="技能不存在")
    skill = skills[skill_id]
    data = await request.json()
    params = data.get("parameters", {})
    prompt = ""
    if skill.prompts.get("system_prompt"):
        prompt += skill.prompts["system_prompt"] + "\n\n"
    template = skill.prompts.get("user_prompt_template", "{{input}}")
    user_input = params.get("input", str(params))
    prompt += template.replace("{{input}}", user_input)
    for key, value in params.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
    response = await call_llm(prompt, current_settings)
    return JSONResponse({"response": response, "skill": skill.name})


@router.put("/api/skills/{skill_id}")
async def update_skill(skill_id: str, request: Request):
    if skill_id not in skills:
        raise HTTPException(status_code=404, detail="技能不存在")
    data = await request.json()
    skill = skills[skill_id]
    skill.name = data.get("name", skill.name)
    skill.description = data.get("description", skill.description)
    skill.prompts = data.get("prompts", skill.prompts)
    skill.updated_at = datetime.datetime.now().isoformat()
    save_skills()
    return JSONResponse(skill.model_dump())


@router.delete("/api/skills/{skill_id}")
async def delete_skill(skill_id: str):
    if skill_id not in skills:
        raise HTTPException(status_code=404, detail="技能不存在")
    del skills[skill_id]
    save_skills()
    return JSONResponse({"success": True, "message": "技能已删除"})


# ==================== 技能导入导出 ====================

@router.post("/api/skills/import")
async def import_skill(request: Request):
    data = await request.json()
    skill_id = data.get("id", str(uuid.uuid4()))
    if skill_id in skills:
        skill_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    skill = Skill(
        id=skill_id,
        name=data.get("name", "导入技能"),
        description=data.get("description", ""),
        icon=data.get("icon", "🔧"),
        category=data.get("category", "other"),
        version=data.get("version", "1.0.0"),
        parameters=data.get("parameters", []),
        prompts=data.get("prompts", {}),
        tools=data.get("tools", []),
        created_at=data.get("created_at", now),
        updated_at=now
    )
    skills[skill_id] = skill
    save_skills()
    return JSONResponse(skill.model_dump())


@router.get("/api/skills/{skill_id}/export")
async def export_skill(skill_id: str):
    if skill_id not in skills:
        raise HTTPException(status_code=404, detail="技能不存在")
    skill = skills[skill_id]
    return JSONResponse(skill.model_dump())


# ==================== 技能模板 ====================

@router.get("/api/skills/templates")
async def get_skill_templates():
    templates = [
        {
            "id": "code-review",
            "name": "代码审查专家",
            "icon": "🔍",
            "description": "专业的代码审查和质量分析",
            "category": "code",
            "prompts": {
                "system_prompt": "你是一位资深代码审查专家，擅长发现代码中的问题并提供改进建议。",
                "user_prompt_template": "请审查以下代码：\n\n{{input}}"
            }
        },
        {
            "id": "data-analyst",
            "name": "数据分析助手",
            "icon": "📊",
            "description": "数据分析和可视化专家",
            "category": "data",
            "prompts": {
                "system_prompt": "你是一位数据分析专家，擅长数据清洗、统计分析和可视化。",
                "user_prompt_template": "请分析以下数据：\n\n{{input}}"
            }
        },
        {
            "id": "translator",
            "name": "多语言翻译",
            "icon": "🌐",
            "description": "专业的多语言翻译服务",
            "category": "translation",
            "prompts": {
                "system_prompt": "你是一位专业翻译，精通多种语言，确保翻译准确、自然。",
                "user_prompt_template": "请将以下内容翻译成{{target_language}}：\n\n{{input}}"
            },
            "parameters": [
                {"name": "target_language", "type": "string", "default": "英文", "description": "目标语言"}
            ]
        },
        {
            "id": "writer",
            "name": "写作助手",
            "icon": "✍️",
            "description": "专业的文案写作和润色",
            "category": "writing",
            "prompts": {
                "system_prompt": "你是一位专业写作助手，擅长各类文案创作和文字润色。",
                "user_prompt_template": "请帮我{{action}}以下内容：\n\n{{input}}"
            },
            "parameters": [
                {"name": "action", "type": "select", "options": ["润色", "扩写", "缩写", "改写"], "default": "润色"}
            ]
        },
        {
            "id": "summarizer",
            "name": "内容摘要",
            "icon": "📝",
            "description": "智能内容摘要和要点提取",
            "category": "document",
            "prompts": {
                "system_prompt": "你是一位摘要专家，擅长提取关键信息，生成简洁准确的摘要。",
                "user_prompt_template": "请总结以下内容的要点：\n\n{{input}}"
            }
        }
    ]
    return JSONResponse(templates)


# ==================== 技能测试 ====================

@router.post("/api/skills/{skill_id}/test")
async def test_skill(skill_id: str, request: Request):
    if skill_id not in skills:
        raise HTTPException(status_code=404, detail="技能不存在")
    skill = skills[skill_id]
    data = await request.json()
    test_input = data.get("input", "测试输入")

    prompt = ""
    if skill.prompts.get("system_prompt"):
        prompt += skill.prompts["system_prompt"] + "\n\n"
    template = skill.prompts.get("user_prompt_template", "{{input}}")
    prompt += template.replace("{{input}}", test_input)

    try:
        response = await call_llm(prompt, current_settings)
        return JSONResponse({"success": True, "response": response})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
