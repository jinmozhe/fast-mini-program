"""
文件路径: app/db/init_db.py

数据库初始化模块

本模块负责数据库表结构创建和初始数据填充功能。
提供开发、测试和生产环境中数据库的初始化操作。
支持创建表、删除表和初始管理员账户设置。

使用说明:
- create_tables(): 创建所有数据库表
- drop_tables(): 删除所有表（仅用于测试环境）
- init_db(): 填充初始数据，如系统管理员账户
"""
import logging  # 导入logging模块，用于记录初始化过程信息
from typing import List  # 导入类型提示工具

from sqlalchemy import select  # 导入SQLAlchemy 2.0查询函数
from sqlalchemy.orm import Session  # 导入SQLAlchemy会话类，用于数据库操作

from app.core.config import settings  # 导入应用配置，获取初始管理员设置
from app.db.base import Base  # 导入ORM基类，用于表结构管理
from app.db.session import engine  # 导入数据库引擎
import app.models.models  # 导入所有模型，确保它们被注册到SQLAlchemy元数据

# 配置模块级别日志记录器
logger = logging.getLogger(__name__)


def create_tables() -> None:
    """
    创建所有数据库表
    
    使用SQLAlchemy元数据创建定义的所有表结构。
    适用于应用首次部署或开发环境中重建表结构。
    
    注意:
        此操作不会删除现有数据，但可能因表已存在而报错。
        生产环境应使用迁移工具而非此函数。
    
    用法示例:
        from app.db.init_db import create_tables
        create_tables()  # 创建所有表
    """
    logger.info("创建数据库表...")
    # 导入models.py确保所有模型已注册到元数据
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建完成")


def drop_tables() -> None:
    """
    删除所有数据库表
    
    危险操作，将删除所有表结构和数据。
    仅用于测试环境或开发阶段的完全重置。
    
    警告:
        此操作会永久删除所有数据，无法恢复。
        严禁在生产环境中使用。
    
    用法示例:
        from app.db.init_db import drop_tables
        # 仅在测试环境中使用
        if settings.ENVIRONMENT == "test":
            drop_tables()
    """
    logger.warning("删除所有数据库表...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("数据库表删除完成")


def init_db(db: Session) -> None:
    """
    初始化数据库，填充初始数据
    
    在数据库中创建必要的初始数据，如超级管理员账户。
    根据应用配置进行条件初始化，避免重复创建。
    
    参数:
        db (Session): 数据库会话对象，用于执行数据操作
    
    用法示例:
        from app.db.init_db import init_db
        from app.db.session import SessionLocal
        
        with SessionLocal() as db:
            init_db(db)
    
    注意:
        需要在配置中设置FIRST_SUPERUSER_EMAIL和FIRST_SUPERUSER_PASSWORD
    """
    # 检查必要的配置参数
    if settings.ENVIRONMENT != "test" and not settings.FIRST_SUPERUSER_PASSWORD:
        logger.warning("未设置初始管理员密码，跳过数据库初始化")
        return
        
    # 导入User模型用于创建超级管理员
    from app.models.user import User
    
    # 检查管理员是否已存在 (使用SQLAlchemy 2.0语法)
    admin_user = db.execute(
        select(User).where(User.email == settings.FIRST_SUPERUSER_EMAIL)
    ).scalar_one_or_none()
    
    if not admin_user:
        logger.info(f"创建超级管理员: {settings.FIRST_SUPERUSER_EMAIL}")
        
        # 创建新的管理员用户实例
        admin_user = User(
            email=settings.FIRST_SUPERUSER_EMAIL,
            username=settings.FIRST_SUPERUSER_USERNAME,
            full_name="系统管理员",
            is_active=True,
            is_verified=True,
            email_verified=True,
            is_admin=True,
            user_type="ADMIN",
            status="ACTIVE"
        )
        # 设置安全密码
        admin_user.set_password(settings.FIRST_SUPERUSER_PASSWORD)
        
        # 保存到数据库
        db.add(admin_user)
        db.commit()
        logger.info("超级管理员创建成功")
    else:
        logger.info("超级管理员已存在，跳过创建")