"""
文件路径: app/models/models.py

SQLAlchemy 模型注册模块

本模块负责导入并注册所有数据库模型，
确保模型正确加载到 SQLAlchemy 元数据中以用于迁移和表创建。
此模块主要供 Alembic 和数据库初始化程序使用。
"""

# 导入所有模型，注册到 SQLAlchemy 元数据
from app.models.user import User
from app.models.user_address import UserAddress
from app.models.user_preference import UserPreference
# 导入其他模型...

# 可选：提供一个注册函数，使导入意图更明确
def register_all_models():
    """
    确保所有模型已被导入并注册到 SQLAlchemy 元数据。
    
    注意:
        仅仅导入此模块就足够注册所有模型，
        此函数仅为显式调用提供更清晰的代码意图。
    """
    # 模型已通过上面的导入语句注册
    pass