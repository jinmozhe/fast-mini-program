"""
文件路径: app/models/user_preference.py

用户偏好设置模型模块

定义用户个性化偏好设置的数据模型，包括通知选项、内容偏好和应用设置。
支持用户自定义体验，管理订阅选项和个性化推荐设置。
使用北京时区(UTC+8)处理时间字段。
"""
from __future__ import annotations  # 启用延迟类型评估，解决循环引用
from typing import TYPE_CHECKING

# 从中央导入点获取所需组件
from app.models.base import (
    Base,
    Boolean, ForeignKey, JSON, String, Text,
    Mapped, mapped_column, relationship,
    List, Optional, Dict, Any
)

# 处理循环引用
if TYPE_CHECKING:
    from app.models.user import User


class UserPreference(Base):
    """
    用户偏好设置模型
    
    存储用户的个性化设置和偏好选项，支持通知、内容和隐私等多种设置。
    使用user_id作为主键，实现与用户的一对一关系。
    
    字段组:
    - 关联信息: 与用户的一对一关系(user_id)
    - 通知设置: 各种通知渠道和类型的开关(email_notifications等)
    - 内容偏好: 用户对内容的个性化选择(diet_preferences等)
    - 隐私安全: 数据共享和个性化的控制选项(share_order_history等)
    - 默认设置: 用户的默认选项(default_payment_method等)
    
    关联关系:
    - user: 偏好设置所属的用户(一对一)
    """
    
    # 表名设置
    __tablename__ = "user_preferences"
    
    # 关联信息 - 使用user_id作为主键，实现一对一关系
    user_id: Mapped[str] = mapped_column(
        String(26), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        primary_key=True,
        comment="所属用户ID，外键关联users表，同时作为主键"
    )
    
    # 通知渠道偏好
    email_notifications: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="是否接收电子邮件通知"
    )
    push_notifications: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="是否接收推送通知"
    )
    sms_notifications: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="是否接收短信通知"
    )
    
    # 通知类型偏好
    notify_order_status: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="是否接收订单状态变更通知"
    )
    notify_delivery_status: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="是否接收配送状态通知"
    )
    notify_promotions: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="是否接收营销和促销信息"
    )
    notify_system: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="是否接收系统通知"
    )
    
    # 饮食偏好 (使用JSON类型存储列表数据)
    diet_preferences: Mapped[Optional[List[str]]] = mapped_column(
        JSON, 
        nullable=True,
        comment="饮食偏好列表，如['素食', '低碳水化合物']等"
    )
    allergies: Mapped[Optional[List[str]]] = mapped_column(
        JSON, 
        nullable=True,
        comment="过敏原列表，如['花生', '乳制品']等"
    )
    favorite_cuisines: Mapped[Optional[List[str]]] = mapped_column(
        JSON, 
        nullable=True,
        comment="喜爱的菜系列表，如['中餐', '意大利菜']等"
    )
    
    # 隐私设置
    share_order_history: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="是否允许分享订单历史用于改进服务"
    )
    allow_recommendations: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="是否允许基于历史行为的个性化推荐"
    )
    
    # 应用设置
    default_payment_method: Mapped[Optional[str]] = mapped_column(
        String(26), 
        nullable=True,
        comment="默认支付方式ID"
    )
    default_address: Mapped[Optional[str]] = mapped_column(
        String(26), 
        nullable=True,
        comment="默认地址ID"
    )
    
    # 杂项设置
    special_instructions: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="用户的特殊说明或要求"
    )
    
    # 关系 - 使用字符串类型标注避免循环引用
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="preferences",
        comment="该偏好设置所属的用户"
    )
    
    def __repr__(self) -> str:
        """
        返回用户偏好对象的字符串表示
        
        返回:
            str: 用户偏好的字符串表示
        """
        return f"<UserPreference for user_id={self.user_id}>"
    
    def update_diet_preferences(self, preferences: List[str]) -> None:
        """
        更新饮食偏好
        
        更新用户的饮食偏好列表，如素食、低碳水化合物等。
        
        参数:
            preferences: 饮食偏好字符串列表
            
        示例:
            user_pref.update_diet_preferences(["素食", "低碳水化合物"])
        """
        self.diet_preferences = preferences
    
    def update_allergies(self, allergies: List[str]) -> None:
        """
        更新过敏信息
        
        更新用户的食物过敏原列表，用于过滤不适宜的食品。
        
        参数:
            allergies: 过敏原字符串列表
            
        示例:
            user_pref.update_allergies(["花生", "乳制品"])
        """
        self.allergies = allergies
        
    def get_all_preferences(self) -> Dict[str, Any]:
        """
        获取所有用户偏好设置
        
        将用户的所有偏好设置整合为一个字典返回，
        便于前端一次性获取所有设置。
        
        返回:
            Dict[str, Any]: 包含所有偏好设置的字典
        """
        return {
            "notification": {
                "channels": {
                    "email": self.email_notifications,
                    "push": self.push_notifications,
                    "sms": self.sms_notifications
                },
                "types": {
                    "order_status": self.notify_order_status,
                    "delivery_status": self.notify_delivery_status,
                    "promotions": self.notify_promotions,
                    "system": self.notify_system
                }
            },
            "diet": {
                "preferences": self.diet_preferences,
                "allergies": self.allergies,
                "favorite_cuisines": self.favorite_cuisines
            },
            "privacy": {
                "share_order_history": self.share_order_history,
                "allow_recommendations": self.allow_recommendations
            },
            "defaults": {
                "payment_method": self.default_payment_method,
                "address": self.default_address
            },
            "special_instructions": self.special_instructions
        }