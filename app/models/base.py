"""
文件路径: app/models/base.py

模型基础模块 - 为所有模型提供统一的导入点

为所有模型文件提供一个统一的导入模块，简化导入语句，
确保所有模型使用一致的基础设施，如时间处理、ID生成等。

使用说明:
- 所有模型文件应从此模块导入所需的基础类和工具
- 包含了常用的数据库模型基类、混入类和工具函数
"""
# 从数据库基础模块导出基础类
from app.db.base import (
    Base,
    StatusMixin,
    SoftDeleteMixin,
    AuditMixin,
    metadata,
)

# 从时间工具模块导入所有时间相关的类和函数
from app.utils.time import *  # 导入datetime, timedelta, timezone, beijing_now等

# 从 ID 生成工具导出
from app.utils.ulid import generate_ulid

# 从 SQLAlchemy 导出常用组件，方便模型定义
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Enum,
    UniqueConstraint,
    Index,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    Type,
)

# 创建全面的导出列表
__all__ = [
    # 基础类
    "Base", "StatusMixin", "SoftDeleteMixin", "AuditMixin", "metadata",
    
    # 从time.py导入的类和函数 - 已通过*导入
    "datetime", "timedelta", "timezone", "BEIJING_TIMEZONE",
    "beijing_now", "format_datetime", "localize_datetime", "parse_datetime",
    
    # ID生成
    "generate_ulid",
    
    # SQLAlchemy类型
    "Boolean", "Column", "DateTime", "Float", "ForeignKey", "Integer", "String", 
    "Text", "JSON", "Enum", "UniqueConstraint", "Index", "func",
    
    # SQLAlchemy ORM
    "Mapped", "mapped_column", "relationship",
    
    # 类型提示
    "Any", "Dict", "List", "Optional", "Union", "Type",
]