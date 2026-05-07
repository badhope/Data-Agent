"""
Office Agent Tools - Document Module
文档处理工具集
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from langchain_core.tools import tool
from langchain_core.pydantic_v1 import BaseModel, Field


# ==================== Tool Input Schemas ====================

class ReadDocumentInput(BaseModel):
    """读取文档输入参数"""
    file_path: str = Field(description="文件路径")
    max_lines: Optional[int] = Field(default=None, description="最大读取行数")


class SearchDocumentInput(BaseModel):
    """搜索文档输入参数"""
    keyword: str = Field(description="搜索关键词")
    folder: str = Field(default="./documents", description="文档文件夹")
    file_type: Optional[str] = Field(default=None, description="文件类型，如 .txt, .md, .docx")


class SummarizeDocumentInput(BaseModel):
    """总结文档输入参数"""
    file_path: str = Field(description="文件路径")
    max_points: int = Field(default=5, description="最大要点数量")


class CreateDocumentInput(BaseModel):
    """创建文档输入参数"""
    file_path: str = Field(description="文件路径")
    content: str = Field(description="文档内容")
    file_type: str = Field(default="md", description="文件类型")


class ListDocumentsInput(BaseModel):
    """列出文档输入参数"""
    folder: str = Field(default="./documents", description="文件夹路径")
    file_type: Optional[str] = Field(default=None, description="文件类型过滤")


# ==================== Mock Document Store ====================

class MockDocumentStore:
    """模拟文档存储"""
    
    def __init__(self):
        self.documents = {
            "documents/project_report.md": """# 项目进度报告

## 一、项目概述
本项目旨在开发一套企业级办公自动化系统。

## 二、当前进度
- 前端开发：80%
- 后端开发：65%
- 测试：30%

## 三、存在问题
1. 人员紧张
2. 需求变更频繁

## 四、下一步计划
1. 完成核心功能开发
2. 进行系统集成测试
3. 准备上线部署
""",
            "documents/meeting_notes_2025.txt": """会议纪要 - 2025年1月15日

参会人员：张总、李经理、王工

议题：
1. Q1产品规划评审
2. 技术方案讨论

决议：
- 3月底完成MVP版本
- 技术方案采用微服务架构

待办事项：
- [ ] 张总：确认需求优先级
- [ ] 李经理：安排开发资源
- [ ] 王工：输出技术方案文档
""",
            "documents/company_policy.md": """# 公司政策手册

## 考勤制度
- 上班时间：9:00
- 下班时间：18:00
- 弹性工作制：核心时间10:00-16:00

## 请假制度
- 年假：10天起步
- 病假：需提供证明
- 事假：提前3天申请

## 报销制度
- 差旅费：实报实销
- 餐费：每天上限100元
"""
        }
    
    def exists(self, file_path: str) -> bool:
        return file_path in self.documents or Path(file_path).exists()
    
    def read(self, file_path: str, max_lines: Optional[int] = None) -> str:
        if file_path in self.documents:
            content = self.documents[file_path]
        else:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except FileNotFoundError:
                return f"❌ 文件不存在: {file_path}"
            except Exception as e:
                return f"❌ 读取失败: {str(e)}"
        
        if max_lines:
            lines = content.split('\n')
            if len(lines) > max_lines:
                content = '\n'.join(lines[:max_lines])
                content += f"\n\n... (共 {len(lines)} 行，已显示前 {max_lines} 行)"
        
        return content
    
    def write(self, file_path: str, content: str) -> bool:
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.documents[file_path] = content
            return True
        except Exception as e:
            return False
    
    def search(self, keyword: str, folder: str = "./documents") -> List[Dict]:
        results = []
        for path, content in self.documents.items():
            if folder not in path:
                continue
            if keyword.lower() in content.lower():
                # 找到关键词附近的内容作为预览
                lines = content.split('\n')
                preview_lines = []
                for i, line in enumerate(lines):
                    if keyword.lower() in line.lower():
                        start = max(0, i - 1)
                        end = min(len(lines), i + 2)
                        preview_lines.extend(lines[start:end])
                        break
                
                results.append({
                    "path": path,
                    "preview": ' '.join(preview_lines)[:150],
                    "size": len(content)
                })
        return results
    
    def list_files(self, folder: str = "./documents", 
                   file_type: Optional[str] = None) -> List[Dict]:
        files = []
        for path in self.documents:
            if folder not in path:
                continue
            if file_type and not path.endswith(file_type):
                continue
            files.append({
                "path": path,
                "name": Path(path).name,
                "size": len(self.documents[path])
            })
        return files


# 全局文档存储实例
_doc_store = MockDocumentStore()


# ==================== Document Tools ====================

@tool(args_schema=ReadDocumentInput, return_direct=False)
def read_document(file_path: str, max_lines: Optional[int] = None) -> str:
    """
    读取文档内容。
    
    当用户要查看某个文档的内容时使用此工具。
    
    Args:
        file_path: 文件路径
        max_lines: 最大读取行数（可选）
    
    Returns:
        文档内容
    """
    content = _doc_store.read(file_path, max_lines)
    return content


@tool(args_schema=SearchDocumentInput, return_direct=False)
def search_documents(
    keyword: str,
    folder: str = "./documents",
    file_type: Optional[str] = None
) -> str:
    """
    搜索包含关键词的文档。
    
    当用户需要在文档库中查找包含特定内容的文档时使用此工具。
    
    Args:
        keyword: 搜索关键词
        folder: 搜索的文件夹
        file_type: 文件类型过滤（如 .md, .txt）
    
    Returns:
        搜索结果列表
    """
    results = _doc_store.search(keyword, folder)
    
    if file_type:
        results = [r for r in results if r["path"].endswith(file_type)]
    
    if not results:
        return f"🔍 没有找到包含「{keyword}」的文档"
    
    output = f"🔍 找到 {len(results)} 篇相关文档：\n\n"
    
    for i, doc in enumerate(results, 1):
        size_kb = doc["size"] / 1024
        output += f"""【{i}】📄 {doc['path']}
   📝 预览: {doc['preview']}...
   📊 大小: {size_kb:.1f} KB

"""
    
    return output.strip()


@tool(args_schema=SummarizeDocumentInput, return_direct=False)
def summarize_document(file_path: str, max_points: int = 5) -> str:
    """
    总结文档要点。
    
    当用户需要快速了解文档的主要内容时使用此工具。
    
    Args:
        file_path: 文件路径
        max_points: 最大要点数量
    
    Returns:
        文档摘要
    """
    content = _doc_store.read(file_path)
    
    if content.startswith("❌"):
        return content
    
    # 简单模拟摘要生成（实际应使用 LLM）
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    
    # 提取标题和关键行
    key_points = []
    headers = [l for l in lines if l.startswith('#')]
    
    for line in lines:
        if line.startswith('## ') or line.startswith('- '):
            key_points.append(line)
            if len(key_points) >= max_points:
                break
    
    result = f"""📄 文档摘要: {Path(file_path).name}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 文档结构：\n"""
    
    for h in headers[:5]:
        result += f"   {h}\n"
    
    if key_points:
        result += f"\n📝 关键内容：\n"
        for point in key_points[:max_points]:
            clean = point.replace('## ', '• ').replace('- ', '• ')
            result += f"   {clean}\n"
    
    result += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 文档总行数: {len(lines)}"""
    
    return result


@tool(args_schema=CreateDocumentInput, return_direct=True)
def create_document(file_path: str, content: str, file_type: str = "md") -> str:
    """
    创建新文档。
    
    当用户需要创建新的文档、报告或笔记时使用此工具。
    
    Args:
        file_path: 文件路径
        content: 文档内容
        file_type: 文件类型（默认 .md）
    
    Returns:
        创建结果
    """
    if not file_path.endswith(f".{file_type}"):
        file_path = f"{file_path}.{file_type}"
    
    if _doc_store.write(file_path, content):
        return f"""✅ 文档创建成功！

📄 文件路径: {file_path}
📊 内容长度: {len(content)} 字符
🕐 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

您可以随时通过 read_document 工具查看或修改此文档。"""
    else:
        return f"❌ 创建文档失败"


@tool(args_schema=ListDocumentsInput, return_direct=False)
def list_documents(folder: str = "./documents", file_type: Optional[str] = None) -> str:
    """
    列出文件夹中的所有文档。
    
    当用户想了解某个文件夹下有哪些文档时使用此工具。
    
    Args:
        folder: 文件夹路径
        file_type: 文件类型过滤（如 .md, .txt）
    
    Returns:
        文档列表
    """
    files = _doc_store.list_files(folder, file_type)
    
    if not files:
        return f"📁 文件夹为空: {folder}"
    
    total_size = sum(f["size"] for f in files)
    
    output = f"📁 {folder} 文档列表\n"
    output += "=" * 50 + "\n"
    output += f"共 {len(files)} 个文件，总大小: {total_size/1024:.1f} KB\n\n"
    
    for i, f in enumerate(files, 1):
        size_kb = f["size"] / 1024
        output += f"{i}. 📄 {f['name']} ({size_kb:.1f} KB)\n"
        output += f"   路径: {f['path']}\n\n"
    
    return output.strip()


@tool(return_direct=False)
def extract_action_items(file_path: str) -> str:
    """
    从文档中提取待办事项和行动项。
    
    当用户需要从会议纪要或任务文档中提取待办列表时使用此工具。
    
    Args:
        file_path: 文件路径
    
    Returns:
        提取的待办事项列表
    """
    content = _doc_store.read(file_path)
    
    if content.startswith("❌"):
        return content
    
    # 查找待办项（Markdown 格式的 checkbox 或 [] 格式）
    lines = content.split('\n')
    action_items = []
    
    for line in lines:
        stripped = line.strip()
        if '[ ]' in stripped or '- [ ]' in stripped or '☐' in stripped:
            # 未完成的待办
            item = stripped.replace('- [ ]', '').replace('[ ]', '').replace('☐', '').strip()
            action_items.append(("pending", item))
        elif '[x]' in stripped or '- [x]' in stripped or '☑' in stripped:
            # 已完成的待办
            item = stripped.replace('- [x]', '').replace('[x]', '').replace('☑', '').strip()
            action_items.append(("done", item))
    
    if not action_items:
        return """📋 未找到待办事项

此文档中没有使用标准格式标记的待办事项。

标准格式：
- [ ] 未完成的任务
- [x] 已完成的任务"""
    
    pending = [a for a in action_items if a[0] == "pending"]
    done = [a for a in action_items if a[0] == "done"]
    
    result = f"""📋 待办事项提取: {Path(file_path).name}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    
    if pending:
        result += f"⏳ 待完成 ({len(pending)}项)\n"
        for i, (_, item) in enumerate(pending, 1):
            result += f"   {i}. □ {item}\n"
        result += "\n"
    
    if done:
        result += f"✅ 已完成 ({len(done)}项)\n"
        for i, (_, item) in enumerate(done, 1):
            result += f"   {i}. ■ {item}\n"
    
    result += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
总计: {len(pending)} 项待办，{len(done)} 项完成"""
    
    return result


# ==================== Tool Exports ====================

DOCUMENT_TOOLS = [
    read_document,
    search_documents,
    summarize_document,
    create_document,
    list_documents,
    extract_action_items
]

__all__ = [
    "read_document",
    "search_documents",
    "summarize_document",
    "create_document",
    "list_documents",
    "extract_action_items",
    "DOCUMENT_TOOLS"
]
