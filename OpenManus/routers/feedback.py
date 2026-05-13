"""
DataAgent - 用户反馈与学习系统
支持消息评分、偏好学习、Prompt自动优化
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pathlib import Path
import json
import datetime
from typing import Dict, List, Any

router = APIRouter()

FEEDBACK_FILE = Path("data/feedback.json")
PREFERENCES_FILE = Path("data/preferences.json")


def _load_json(filepath: Path, default: dict = None) -> dict:
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return default or {}


def _save_json(filepath: Path, data: dict):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.post("/api/feedback")
async def submit_feedback(request: Request):
    """提交消息反馈"""
    data = await request.json()
    message_id = data.get("message_id", "")
    conversation_id = data.get("conversation_id", "")
    rating = data.get("rating")  # "up" or "down"
    category = data.get("category", "general")  # general, code, analysis, writing, knowledge
    comment = data.get("comment", "")
    message_preview = data.get("message_preview", "")[:200]

    if rating not in ("up", "down"):
        raise HTTPException(status_code=400, detail="rating 必须是 'up' 或 'down'")

    feedback_data = _load_json(FEEDBACK_FILE, {"feedbacks": [], "stats": {"total": 0, "up": 0, "down": 0}})

    feedback_id = f"fb_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    feedback = {
        "id": feedback_id,
        "message_id": message_id,
        "conversation_id": conversation_id,
        "rating": rating,
        "category": category,
        "comment": comment,
        "message_preview": message_preview,
        "created_at": datetime.datetime.now().isoformat()
    }

    feedback_data["feedbacks"].append(feedback)
    feedback_data["stats"]["total"] += 1
    feedback_data["stats"][rating] += 1

    _save_json(FEEDBACK_FILE, feedback_data)

    # Update preferences based on feedback
    _update_preferences(rating, category, message_preview)

    return JSONResponse({"success": True, "id": feedback_id})


@router.get("/api/feedback/stats")
async def get_feedback_stats():
    """获取反馈统计"""
    feedback_data = _load_json(FEEDBACK_FILE, {"feedbacks": [], "stats": {"total": 0, "up": 0, "down": 0}})
    preferences = _load_json(PREFERENCES_FILE, {"categories": {}, "keywords": {}, "style": {}})

    return JSONResponse({
        "stats": feedback_data["stats"],
        "satisfaction_rate": round(feedback_data["stats"]["up"] / max(feedback_data["stats"]["total"], 1) * 100, 1),
        "preferences": preferences,
        "recent_feedbacks": feedback_data["feedbacks"][-20:]  # 最近20条
    })


@router.get("/api/feedback/preferences")
async def get_preferences():
    """获取学习到的用户偏好"""
    preferences = _load_json(PREFERENCES_FILE, {"categories": {}, "keywords": {}, "style": {}})
    return JSONResponse(preferences)


@router.post("/api/feedback/preferences/reset")
async def reset_preferences():
    """重置学习到的偏好"""
    _save_json(PREFERENCES_FILE, {"categories": {}, "keywords": {}, "style": {}})
    return JSONResponse({"success": True, "message": "偏好已重置"})


@router.get("/api/feedback/prompt-suggestion")
async def get_prompt_suggestion():
    """基于用户偏好生成系统提示词建议"""
    preferences = _load_json(PREFERENCES_FILE, {"categories": {}, "keywords": {}, "style": {}})

    suggestions = []

    # 基于类别偏好
    categories = preferences.get("categories", {})
    if categories:
        top_categories = sorted(categories.items(), key=lambda x: x[1].get("score", 0), reverse=True)[:3]
        for cat, data in top_categories:
            if data.get("score", 0) > 0:
                suggestions.append(f"用户偏好 {cat} 类任务（满意度 {data.get('score', 0):.0%}），应优先考虑相关工具和方法")

    # 基于风格偏好
    style = preferences.get("style", {})
    if style.get("detail_level") == "detailed":
        suggestions.append("用户偏好详细的回复，应提供充分的解释和代码注释")
    elif style.get("detail_level") == "concise":
        suggestions.append("用户偏好简洁的回复，应直接给出答案，减少冗余说明")

    if style.get("code_preference") == "with_explanation":
        suggestions.append("用户偏好带解释的代码，应在代码前后添加说明")

    # 基于关键词偏好
    keywords = preferences.get("keywords", {})
    positive_keywords = [k for k, v in keywords.items() if v.get("sentiment", 0) > 0]
    negative_keywords = [k for k, v in keywords.items() if v.get("sentiment", 0) < 0]

    if positive_keywords:
        suggestions.append(f"用户喜欢涉及以下主题的内容: {', '.join(positive_keywords[:5])}")
    if negative_keywords:
        suggestions.append(f"用户不喜欢涉及以下主题的内容: {', '.join(negative_keywords[:5])}")

    return JSONResponse({
        "suggestions": suggestions,
        "has_enough_data": len(suggestions) > 0
    })


def _update_preferences(rating: str, category: str, message_preview: str):
    """根据反馈更新用户偏好"""
    preferences = _load_json(PREFERENCES_FILE, {"categories": {}, "keywords": {}, "style": {}})

    # 更新类别偏好
    if category and category != "general":
        if category not in preferences["categories"]:
            preferences["categories"][category] = {"up": 0, "down": 0, "score": 0.5}

        cat_data = preferences["categories"][category]
        cat_data[rating] = cat_data.get(rating, 0) + 1
        total = cat_data.get("up", 0) + cat_data.get("down", 0)
        cat_data["score"] = cat_data.get("up", 0) / max(total, 1)

    # 从消息预览中提取关键词偏好
    if message_preview:
        import re
        # 简单的关键词提取（中文和英文）
        words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', message_preview)
        for word in set(words[:10]):
            if word not in preferences["keywords"]:
                preferences["keywords"][word] = {"sentiment": 0, "count": 0}

            kw_data = preferences["keywords"][word]
            kw_data["count"] += 1
            kw_data["sentiment"] += (1 if rating == "up" else -1)
            # 归一化
            kw_data["sentiment"] = round(kw_data["sentiment"] / max(kw_data["count"], 1), 2)

    # 更新风格偏好
    style = preferences["style"]
    if len(message_preview) > 100 and rating == "up":
        current = style.get("detail_level", {})
        current["detailed"] = current.get("detailed", 0) + 1
        style["detail_level"] = current
    elif len(message_preview) < 100 and rating == "up":
        current = style.get("detail_level", {})
        current["concise"] = current.get("concise", 0) + 1
        style["detail_level"] = current

    if "```" in message_preview and rating == "up":
        style["code_preference"] = "with_explanation"

    _save_json(PREFERENCES_FILE, preferences)


def get_learned_system_prompt_suffix() -> str:
    """获取基于用户偏好学习的系统提示词后缀"""
    preferences = _load_json(PREFERENCES_FILE, {"categories": {}, "keywords": {}, "style": {}})

    suffix_parts = []

    # 类别偏好
    categories = preferences.get("categories", {})
    top_categories = sorted(categories.items(), key=lambda x: x[1].get("score", 0), reverse=True)[:3]
    for cat, data in top_categories:
        if data.get("score", 0) > 0.6:
            suffix_parts.append(f"- 用户经常使用{cat}相关功能，优先考虑相关方案")

    # 风格偏好
    style = preferences.get("style", {})
    detail = style.get("detail_level", {})
    if detail.get("detailed", 0) > detail.get("concise", 0) * 2:
        suffix_parts.append("- 用户偏好详细的回复风格，提供充分的解释")
    elif detail.get("concise", 0) > detail.get("detailed", 0) * 2:
        suffix_parts.append("- 用户偏好简洁的回复风格，直接给出答案")

    if not suffix_parts:
        return ""

    return "\n\n## 用户偏好（基于历史反馈自动学习）\n" + "\n".join(suffix_parts)
