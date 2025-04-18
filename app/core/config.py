"""
配置管理模块

此模块负责加载和验证应用配置，使用Pydantic进行环境变量解析和类型验证。
配置分为不同部分便于管理，如安全配置、数据库配置等。
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置设置
    
    使用Pydantic的BaseSettings自动从环境变量加载配置
    配置项按功能分组，方便管理和文档化
    """
    
    # API配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "外卖配送系统API"
    DEBUG: bool = False
    
    # 安全配置
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    ALGORITHM: str = "HS256"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = []

    @field_validator("BACKEND_CORS_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """验证并处理CORS来源配置"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # 数据库配置
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DATABASE_URI: Optional[str] = None

    @field_validator("DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info: Dict[str, Any]) -> Any:
        """构建数据库连接URI"""
        if isinstance(v, str):
            return v
        
        # 获取数据，使用info.data来访问其他字段
        data = info.data
        
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=data.get("POSTGRES_USER"),
                password=data.get("POSTGRES_PASSWORD"),
                host=data.get("POSTGRES_SERVER"),
                port=data.get("POSTGRES_PORT"),
                path=f"/{data.get('POSTGRES_DB') or ''}",
            )
        )

    # 国际化配置
    DEFAULT_LOCALE: str = "zh"
    SUPPORTED_LOCALES: List[str] = ["zh", "en"]
    LOCALE_DIR: str = "locale"
    
    # 其他系统配置
    LOGGING_LEVEL: str = "INFO"
    
    # 将图片和静态文件的URL基础路径
    STATIC_FILES_BASE_URL: str = "/static/"
    
    # 用户配置
    USERS_OPEN_REGISTRATION: bool = True  # 是否允许开放注册
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "gif"]
    UPLOAD_DIR: str = "uploads"  # 文件上传保存的目录

    # Pydantic设置
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_file_encoding="utf-8",
        extra="ignore"
    )


# 创建全局设置实例
settings = Settings()