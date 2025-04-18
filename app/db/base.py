"""
文件路径: app/db/base.py

数据库模型基类模块

本模块定义了应用程序中所有SQLAlchemy模型的基础类和混入类。
提供了通用功能如ID生成、时间戳跟踪、表名生成、状态管理、软删除和审计跟踪等。
适用于仅在中国境内使用的应用，使用北京时区(UTC+8)处理所有时间。

使用说明:
- 所有模型不应直接从此模块导入，而应通过app.models.base模块导入
- Base类是所有模型的基础类
- 各种Mixin类提供额外功能，可以组合使用
"""
from datetime import datetime  # 导入datetime类，用于处理日期和时间
from typing import Any, Dict, Optional  # 导入类型提示工具，用于增强代码的类型安全性

from sqlalchemy import MetaData, String  # 导入SQLAlchemy核心组件：MetaData用于定义表元数据
from sqlalchemy.ext.declarative import declared_attr  # 导入declared_attr装饰器，用于定义类级别的声明式属性（如表名）
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column  # 导入ORM组件：DeclarativeBase是模型基类，Mapped用于类型注解，mapped_column用于列定义

from app.utils.time import beijing_now  # 导入自定义北京时区时间工具
from app.utils.ulid import generate_ulid  # 导入ULID生成工具，用于生成唯一标识符

# 为约束定义命名约定，以便与alembic迁移良好配合
# 一致的命名约定可以简化数据库迁移和版本控制
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",  # 索引命名格式
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # 唯一约束命名格式
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # 检查约束命名格式
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # 外键约束命名格式
    "pk": "pk_%(table_name)s",  # 主键约束命名格式
}

# 创建元数据对象，应用上述命名约定
metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """
    SQLAlchemy模型的基础类
    
    所有数据库模型都应继承此类，以获得通用功能：
    - 自动生成表名（驼峰转下划线并加复数）
    - ULID主键（26字符长度字符串，按时间排序）
    - 创建和更新时间戳（使用北京时区UTC+8）
    - 模型实例转字典的方法
    - 批量更新属性的实用方法
    
    提供的字段:
    - id: 记录唯一标识符，ULID格式
    - created_at: 记录创建时间
    - updated_at: 记录最后更新时间
    """
    
    # 使用定义的命名约定元数据
    metadata = metadata
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        自动从类名生成表名（驼峰转下划线复数形式）
        
        将驼峰命名的类名转换为下划线形式并添加复数后缀's'
        例如：UserProfile类 -> user_profiles表
        """
        # 将驼峰式命名转换为下划线形式并转为复数
        name = ""
        for i, char in enumerate(cls.__name__):
            if i > 0 and char.isupper():
                name += "_"
            name += char.lower()
        return name + "s"  # 转换为复数形式
    
    # 主键字段，使用ULID类型（26字符字符串），默认自动生成新的ULID
    id: Mapped[str] = mapped_column(
        String(26),
        primary_key=True, 
        default=generate_ulid,
        comment="记录唯一标识符，使用ULID格式（26字符，时间排序）"
    )
    
    # 创建时间字段，自动设置为当前北京时间
    created_at: Mapped[datetime] = mapped_column(
        default=beijing_now,
        nullable=False,
        comment="记录创建时间，使用北京时区(UTC+8)"
    )
    
    # 更新时间字段，创建和更新时自动设置为当前北京时间
    updated_at: Mapped[datetime] = mapped_column(
        default=beijing_now, 
        onupdate=beijing_now, 
        nullable=False,
        comment="记录最后更新时间，使用北京时区(UTC+8)"
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        将模型实例转换为字典
        
        用于API响应或序列化模型数据时，将所有列属性转换为字典格式。
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def update(self, **kwargs: Any) -> None:
        """
        批量更新模型实例属性
        
        提供一种简便的方式更新多个属性，只更新模型中已存在的属性。
        忽略不属于模型的属性，避免错误赋值。
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class StatusMixin:
    """
    状态跟踪混入类
    
    为需要状态管理的模型提供状态字段和状态变更跟踪功能。
    适用于需要状态流转的实体，如订单、配送任务、审核流程等。
    
    提供的字段:
    - status: 状态值（字符串）
    - status_changed_at: 状态最后变更时间
    """
    # 状态字段，用于存储实体当前状态
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,  # 添加索引以优化按状态查询
        comment="记录状态，如'ACTIVE'、'PENDING'、'COMPLETED'等"
    )
    
    # 状态变更时间，用于跟踪状态何时发生变化
    status_changed_at: Mapped[datetime] = mapped_column(
        default=beijing_now,  # 初始创建时使用北京时区的当前时间
        onupdate=beijing_now,  # 更新时自动更新为北京时区的当前时间
        nullable=False,
        comment="状态最后变更时间，用于跟踪状态变更历史，使用北京时区(UTC+8)"
    )
    
    def update_status(self, new_status: str) -> None:
        """
        更新状态并记录变更时间
        
        自动更新status_changed_at为北京时区的当前时间，确保状态变更有准确的时间记录。
        """
        self.status = new_status
        self.status_changed_at = beijing_now()  # 显式设置北京时区的当前时间，确保精确性


class SoftDeleteMixin:
    """
    软删除混入类
    
    为模型添加软删除功能，被"删除"的记录只是标记为已删除，
    不会实际从数据库中移除，便于数据恢复和审计追踪。
    
    适用于重要数据实体，如用户、订单、财务记录等，避免意外删除导致数据丢失。
    
    提供的字段:
    - is_deleted: 删除时间（None表示未删除）
    """
    # 软删除标记，存储删除时间，None表示未删除
    is_deleted: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,  # 可为空，表示未删除
        index=True,  # 添加索引以优化查询未删除的记录
        comment="删除时间，NULL表示未删除；如果有值，表示记录被软删除的时间点"
    )
    
    def soft_delete(self) -> None:
        """
        将记录标记为已删除
        
        设置is_deleted为北京时区的当前时间，而不是实际从数据库删除记录。
        """
        self.is_deleted = beijing_now()
    
    def restore(self) -> None:
        """
        恢复被软删除的记录
        
        清除is_deleted标记，使记录重新可见。
        """
        self.is_deleted = None


class AuditMixin:
    """
    审计跟踪混入类
    
    为模型添加创建者和更新者字段，用于跟踪数据变更责任。
    适用于需要操作审计的敏感业务数据，如用户管理、权限变更、重要配置等。
    
    提供的字段:
    - created_by: 创建者ID
    - updated_by: 最后更新者ID
    """
    # 创建者ID，记录谁创建了这条记录
    created_by: Mapped[Optional[str]] = mapped_column(
        String(26),  # 使用与用户ID相同的类型和长度
        nullable=True,  # 允许为空，兼容系统生成的记录
        comment="创建者ID，关联到users表的id字段，记录创建此记录的用户"
    )
    
    # 最后更新者ID，记录谁最后修改了这条记录
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(26),
        nullable=True,  # 允许为空，兼容系统更新的记录
        comment="最后更新者ID，关联到users表的id字段，记录最后修改此记录的用户"
    )
    
    def set_creator(self, user_id: str) -> None:
        """
        设置创建者ID
        
        仅在created_by为空时设置，避免覆盖原始创建者。
        """
        if not self.created_by:
            self.created_by = user_id
    
    def set_updater(self, user_id: str) -> None:
        """
        设置更新者ID
        
        记录当前执行更新操作的用户ID。
        """
        self.updated_by = user_id