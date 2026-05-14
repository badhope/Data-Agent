"""
Skills API Router
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import uuid
from datetime import datetime

from web.models import Skill
from web.storage import get_skills, save_skills
from web.skill_manager import generate_ai_skill as ai_gen_skill, execute_skill as exec_skill

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])

@router.get("")
async def list_skills():
    """获取所有技能"""
    skills = get_skills()
    return JSONResponse({
        "success": True,
        "skills": [s.model_dump() for s in skills.values()],
        "total": len(skills)
    })

@router.get("/{skill_id}")
async def get_skill(skill_id: str):
    """获取单个技能"""
    skills = get_skills()
    if skill_id not in skills:
        raise HTTPException(status_code=404, detail="技能不存在")
    return JSONResponse({"success": True, "skill": skills[skill_id].model_dump()})

@router.post("")
async def create_skill(request: Dict[str, Any]):
    """创建技能"""
    name = request.get("name")
    description = request.get("description", "")
    icon = request.get("icon", "⚡")
    parameters = request.get("parameters", [])
    prompts = request.get("prompts", {})
    code = request.get("code", "")
    
    if not name:
        raise HTTPException(status_code=400, detail="技能名称不能为空")
    
    skill = Skill(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        icon=icon,
        type="custom",
        parameters=parameters,
        prompts=prompts,
        code=code,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    skills = get_skills()
    skills[skill.id] = skill
    save_skills(skills)
    
    return JSONResponse({"success": True, "skill": skill.model_dump()})

@router.post("/generate-ai")
async def generate_ai_skill(request: Dict[str, Any]):
    """AI一键生成技能"""
    try:
        skill_type = request.get("skill_type", "data_analysis")
        description = request.get("description", "")
        
        if not description:
            raise HTTPException(status_code=400, detail="请提供技能描述")
        
        result = await ai_gen_skill(skill_type, description)
        return JSONResponse(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{skill_id}/execute")
async def execute_skill_endpoint(skill_id: str, request: Dict[str, Any]):
    """执行技能"""
    try:
        params = request.get("params", {})
        result = await exec_skill(skill_id, params)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{skill_id}")
async def delete_skill(skill_id: str):
    """删除技能"""
    skills = get_skills()
    if skill_id not in skills:
        raise HTTPException(status_code=404, detail="技能不存在")
    
    # 不允许删除内置技能
    if skills[skill_id].type == "built_in":
        raise HTTPException(status_code=403, detail="不能删除内置技能")
    
    del skills[skill_id]
    save_skills(skills)
    
    return JSONResponse({"success": True})
