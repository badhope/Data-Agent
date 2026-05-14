"""公共验证工具函数"""
import re

def validate_table_name(name: str) -> str:
    """验证SQL表名，防止SQL注入"""
    if not name or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"无效的表名: {name}")
    return name

def validate_id(id_str: str, name: str = "ID") -> str:
    """验证通用ID格式"""
    if not id_str or not re.match(r'^[a-zA-Z0-9_-]+$', id_str):
        raise ValueError(f"无效的{name}: {id_str}")
    return id_str

def validate_share_id(share_id: str) -> str:
    """验证分享ID格式"""
    if not share_id or not re.match(r'^[a-zA-Z0-9]+$', share_id):
        raise ValueError(f"无效的分享ID: {share_id}")
    return share_id

def validate_schema_type(schema_type: str) -> str:
    """验证Schema类型"""
    if not schema_type or not re.match(r'^[a-zA-Z0-9_-]+$', schema_type):
        raise ValueError(f"无效的Schema类型: {schema_type}")
    return schema_type
