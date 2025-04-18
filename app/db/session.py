"""
文件路径: app/db/session.py

数据库会话管理模块

本模块负责创建和管理SQLAlchemy的数据库连接和会话。
提供同步和异步会话工厂、依赖注入函数，以及数据库引擎配置。
适配FastAPI框架，支持异步数据库操作和请求级会话管理。

使用说明:
- 同步操作使用get_db依赖
- 异步操作使用get_async_db依赖
- 通过环境变量配置数据库连接
"""
import os  # 导入os模块，用于访问环境变量
from typing import AsyncGenerator, Generator  # 导入类型提示工具，用于标注生成器类型

from sqlalchemy import create_engine  # 导入SQLAlchemy引擎创建函数，用于创建同步数据库引擎
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # 导入异步SQLAlchemy组件
from sqlalchemy.orm import Session, sessionmaker  # 导入会话工厂和会话类

# 从环境变量获取数据库配置，提供默认值以防环境变量未设置
DB_HOST = os.getenv("DB_HOST", "localhost")  # 数据库主机地址
DB_PORT = os.getenv("DB_PORT", "5432")  # 数据库端口，PostgreSQL默认为5432
DB_USER = os.getenv("DB_USER", "postgres")  # 数据库用户名
DB_PASS = os.getenv("DB_PASS", "postgres")  # 数据库密码
DB_NAME = os.getenv("DB_NAME", "appdb")  # 数据库名称

# 构建同步和异步数据库连接URL
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ASYNC_SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 创建同步引擎，配置连接池选项以优化性能
# pool_pre_ping确保连接有效，避免"连接已关闭"错误
# pool_recycle设置连接在连接池中的最大生存时间，避免因数据库超时策略导致的连接断开
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",  # 根据环境变量决定是否打印SQL语句
)

# 创建异步引擎，用于异步操作数据库
async_engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
)

# 创建同步和异步会话工厂，用于生成数据库会话
# 使用sessionmaker创建会话工厂，指定自动提交和自动刷新行为
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    class_=AsyncSession, autocommit=False, autoflush=False, bind=async_engine
)


def get_db() -> Generator[Session, None, None]:
    """
    提供同步数据库会话的依赖函数
    
    用于FastAPI依赖注入系统，确保请求结束时会话被正确关闭。
    创建一个请求作用域的会话，处理异常并在请求结束时自动关闭会话。
    
    返回:
        Generator[Session, None, None]: 数据库会话生成器
        
    用法示例:
        @app.get("/users/{user_id}")
        def get_user(user_id: str, db: Session = Depends(get_db)):
            return db.query(User).filter(User.id == user_id).first()
    
    异常:
        确保在发生任何异常时会话都被正确关闭
    """
    db = SessionLocal()
    try:
        yield db  # 将会话提供给路由函数使用
    finally:
        db.close()  # 确保会话被关闭，无论是否发生异常


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    提供异步数据库会话的依赖函数
    
    用于FastAPI异步依赖注入，创建异步会话并在请求结束时关闭。
    支持异步上下文中的数据库操作，确保资源被正确释放。
    
    返回:
        AsyncGenerator[AsyncSession, None]: 异步数据库会话生成器
        
    用法示例:
        @app.get("/users/{user_id}")
        async def get_user(user_id: str, db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
    
    异常:
        确保在发生任何异常时异步会话都被正确关闭
    """
    async_session = AsyncSessionLocal()
    try:
        yield async_session  # 将异步会话提供给异步路由函数使用
    finally:
        await async_session.close()  # 异步关闭会话