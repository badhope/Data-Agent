"""
润色服务 - 处理文本润色请求
支持多阶段状态反馈和动画效果
"""
import logging
import asyncio

logger = logging.getLogger(__name__)

async def handle_polish_request(text: str, style: str, websocket):
    """
    处理润色请求
    支持多阶段状态反馈，实现有层次感的动画效果
    """
    if not text or not text.strip():
        await websocket.send_json({
            "type": "error",
            "content": "润色文本不能为空"
        })
        return
    
    try:
        # 阶段1: 开始处理
        await websocket.send_json({
            "type": "thinking",
            "title": "✨ 开始处理",
            "content": "正在分析文本内容...",
            "progress": 10,
            "stage": "analyzing"
        })
        await asyncio.sleep(0.3)
        
        # 阶段2: 语法检查
        await websocket.send_json({
            "type": "thinking",
            "title": "🔍 语法分析",
            "content": "正在检查语法和拼写错误...",
            "progress": 25,
            "stage": "grammar_check"
        })
        await asyncio.sleep(0.2)
        
        # 阶段3: 风格转换
        style_names = {
            "academic": "学术",
            "formal": "正式",
            "concise": "简洁",
            "casual": "随意"
        }
        style_name = style_names.get(style, "专业")
        
        await websocket.send_json({
            "type": "thinking",
            "title": "🎨 风格转换",
            "content": f"正在将文本转换为{style_name}风格...",
            "progress": 50,
            "stage": "style_conversion"
        })
        await asyncio.sleep(0.2)
        
        # 阶段4: 优化表达
        await websocket.send_json({
            "type": "thinking",
            "title": "💡 表达优化",
            "content": "正在优化用词和句式...",
            "progress": 75,
            "stage": "expression_optimization"
        })
        await asyncio.sleep(0.2)
        
        # 阶段5: 最终检查
        await websocket.send_json({
            "type": "thinking",
            "title": "✅ 最终检查",
            "content": "正在进行最终质量检查...",
            "progress": 90,
            "stage": "final_check"
        })
        await asyncio.sleep(0.1)
        
        # 构建润色提示词
        prompt = f"""请将以下文本润色为更{style_name}的表达，保持原意，但优化语法、表达和用词。

原文：
{text}

润色后的文本（只输出润色后的内容，不要其他说明）："""
        
        # 阶段6: 调用AI
        await websocket.send_json({
            "type": "thinking",
            "title": "🤖 AI处理中",
            "content": "正在调用AI进行智能润色...",
            "progress": 95,
            "stage": "ai_processing"
        })
        
        # 调用LLM获取润色结果
        from services.llm_service import call_llm
        from config import get_settings
        settings = get_settings()
        
        polished_text = await call_llm(prompt, settings)
        
        # 检查结果
        if not polished_text or polished_text.strip() == "":
            logger.error(f"润色失败: 结果为空")
            await websocket.send_json({
                "type": "error",
                "content": "润色失败：未能获取润色结果",
                "error_type": "empty_result"
            })
            return
        
        if "错误" in polished_text or "失败" in polished_text or "Error" in polished_text or "error" in polished_text:
            logger.error(f"润色失败: {polished_text}")
            await websocket.send_json({
                "type": "error",
                "content": f"润色失败：{polished_text[:100]}",
                "error_type": "llm_error"
            })
            return
        
        # 阶段7: 完成
        await websocket.send_json({
            "type": "thinking",
            "title": "🎉 完成",
            "content": "润色完成！",
            "progress": 100,
            "stage": "completed"
        })
        await asyncio.sleep(0.2)
        
        # 返回润色结果
        await websocket.send_json({
            "type": "polished",
            "content": polished_text.strip(),
            "original": text,
            "style": style,
            "style_name": style_name,
            "original_length": len(text),
            "polished_length": len(polished_text.strip())
        })
        
    except Exception as e:
        logger.error(f"润色处理出错: {e}")
        await websocket.send_json({
            "type": "error",
            "content": f"润色失败：{str(e)}",
            "error_type": "internal_error"
        })