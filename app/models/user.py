"""
文件路径: app/models/user.py

用户模型模块

定义与用户相关的所有数据模型，包括用户基本信息、认证、权限和状态管理。
用户模型是系统核心模型，包含用户身份验证、个人资料、账户状态和关联关系。
适用于仅在中国境内使用的应用，使用北京时区(UTC+8)处理所有时间。
"""
from typing import TYPE_CHECKING  # 导入类型检查工具，用于处理循环引用

# 使用中央导入点获取所需组件
from app.models.base import (
    Base, StatusMixin, SoftDeleteMixin,
    datetime, timedelta, beijing_now,
    Boolean, ForeignKey, Integer, String, Text,
    Mapped, mapped_column, relationship,
    Dict, List, Optional
)
from app.core.security import get_password_hash, verify_password  # 导入密码处理工具

# 处理循环引用
if TYPE_CHECKING:
    from app.models.user_address import UserAddress
    from app.models.user_preference import UserPreference


class User(Base, StatusMixin, SoftDeleteMixin):
    """
    用户模型
    
    存储应用系统中的用户信息，包括认证凭据、个人资料、账户状态和权限。
    提供密码管理、账户锁定、登录记录等功能。
    
    字段组:
    - 认证信息: 用于用户登录和身份验证(username, email, phone, password_hash)
    - 个人资料: 用户的基本个人信息(full_name, avatar_url, gender等)
    - 账户状态: 控制账户的可用性和验证状态(is_active, is_verified等)
    - 权限控制: 定义用户权限级别(user_type, is_admin)
    - 安全管理: 处理登录尝试和账户锁定(failed_login_attempts, locked_until)
    - 用户设置: 个性化偏好(language_preference, theme)
    - 会员信息: 用户的会员状态(membership_level, membership_points)
    
    关联关系:
    - addresses: 用户关联的地址列表(一对多)
    - payment_methods: 用户的支付方式(一对多)
    - preferences: 用户偏好设置(一对一)
    - orders: 用户的订单历史(一对多)
    """
    
    # 表名设置
    __tablename__ = "users"
    
    # 基本认证信息
    username: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True, 
        index=True, 
        nullable=True,
        comment="用户名，可选，用于登录"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), 
        unique=True, 
        index=True, 
        nullable=True,
        comment="电子邮件，可选，用于登录和通知"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20), 
        unique=True, 
        index=True, 
        nullable=True,
        comment="手机号码，可选，用于登录和通知"
    )
    password_hash: Mapped[str] = mapped_column(
        String(128), 
        nullable=False,
        comment="密码哈希，不存储原始密码"
    )
    
    # 个人资料
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True,
        comment="用户全名"
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        comment="头像图片URL"
    )
    gender: Mapped[Optional[str]] = mapped_column(
        String(20), 
        nullable=True,
        comment="性别：MALE(男)、FEMALE(女)、OTHER(其他)、PREFER_NOT_TO_SAY(不愿透露)"
    )
    birthdate: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="出生日期"
    )
    bio: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="个人简介"
    )
    
    # 账户状态
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="账户是否激活，False表示账户被禁用"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="账户是否已验证身份"
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="电子邮件是否已验证"
    )
    phone_verified: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="手机号是否已验证"
    )
    
    # 用户类型和权限
    user_type: Mapped[str] = mapped_column(
        String(20), 
        default="REGULAR", 
        nullable=False,
        comment="用户类型：REGULAR(普通)、PREMIUM(高级)、BUSINESS(企业)"
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="是否为管理员账户"
    )
    
    # 登录安全
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="最后一次成功登录时间，使用北京时区(UTC+8)"
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, 
        default=0, 
        nullable=False,
        comment="连续登录失败次数"
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="账户锁定截止时间，NULL表示未锁定，使用北京时区(UTC+8)"
    )
    
    # 关联关系 - 使用字符串类型标注避免循环引用
    addresses: Mapped[List["UserAddress"]] = relationship(
        "UserAddress",
        back_populates="user", 
        cascade="all, delete-orphan",
        comment="用户关联的地址列表"
    )

    preferences: Mapped["UserPreference"] = relationship(
        "UserPreference",
        back_populates="user", 
        uselist=False, 
        cascade="all, delete-orphan",
        comment="用户偏好设置"
    )
    
    # 用户设置
    language_preference: Mapped[str] = mapped_column(
        String(10), 
        default="zh", 
        nullable=False,
        comment="语言偏好，默认中文(zh)"
    )
    theme: Mapped[str] = mapped_column(
        String(10), 
        default="SYSTEM", 
        nullable=False,
        comment="界面主题：LIGHT(亮色)、DARK(暗色)、SYSTEM(跟随系统)"
    )
    
    # 会员信息
    membership_level: Mapped[str] = mapped_column(
        String(20), 
        default="BRONZE", 
        nullable=False,
        comment="会员等级：BRONZE(铜)、SILVER(银)、GOLD(金)、PLATINUM(白金)、DIAMOND(钻石)"
    )
    membership_points: Mapped[int] = mapped_column(
        Integer, 
        default=0, 
        nullable=False,
        comment="会员积分"
    )
    membership_expires_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="会员到期时间，NULL表示永不过期，使用北京时区(UTC+8)"
    )
    
    def __repr__(self) -> str:
        """
        返回用户对象的字符串表示
        
        优先使用用户名、电子邮件或手机号作为标识符，如果都为空则使用ID。
        
        返回:
            str: 格式为"<User {identifier}>"的字符串
        """
        identifier = self.username or self.email or self.phone or self.id
        return f"<User {identifier}>"
    
    def set_password(self, password: str) -> None:
        """
        设置用户密码
        
        对明文密码进行哈希处理后存储，不保存原始密码。
        使用安全的哈希算法，如Argon2。
        
        参数:
            password: 明文密码
        """
        self.password_hash = get_password_hash(password)
    
    def verify_password(self, password: str) -> bool:
        """
        验证用户密码
        
        检查提供的明文密码是否与存储的密码哈希匹配。
        
        参数:
            password: 待验证的明文密码
            
        返回:
            bool: 密码正确返回True，否则返回False
        """
        return verify_password(password, self.password_hash)
    
    def lock_account(self, duration_minutes: int = 30) -> None:
        """
        锁定用户账户
        
        暂时禁止用户登录指定时间，通常用于多次登录失败后的安全措施。
        
        参数:
            duration_minutes: 锁定时长（分钟），默认30分钟
        """
        self.locked_until = beijing_now() + timedelta(minutes=duration_minutes)
    
    def is_locked(self) -> bool:
        """
        检查账号是否被锁定
        
        根据locked_until字段判断当前时间是否超过锁定时间。
        
        返回:
            bool: 账号被锁定返回True，否则返回False
        """
        if self.locked_until is None:
            return False
        return beijing_now() < self.locked_until
    
    def increment_failed_login(self) -> int:
        """
        增加失败登录次数
        
        每次登录失败时调用，用于实现连续多次失败后锁定账户的功能。
        
        返回:
            int: 更新后的失败登录次数
        """
        self.failed_login_attempts += 1
        return self.failed_login_attempts
    
    def reset_failed_login(self) -> None:
        """
        重置失败登录次数
        
        成功登录后调用，将失败计数器归零。
        """
        self.failed_login_attempts = 0
    
    def record_login(self) -> None:
        """
        记录成功登录
        
        更新最后登录时间并重置失败登录计数器。
        通常在用户成功认证后调用。
        """
        self.last_login_at = beijing_now()
        self.reset_failed_login()
    
    def to_dict(self) -> Dict:
        """
        将用户对象转换为字典表示
        
        基于父类方法，但排除敏感字段（如密码哈希）。
        适用于API响应中返回用户信息。
        
        返回:
            Dict: 不含敏感信息的用户数据字典
        """
        data = super().to_dict()
        # 移除敏感字段
        sensitive_fields = ["password_hash", "failed_login_attempts", "locked_until"]
        for field in sensitive_fields:
            data.pop(field, None)
        return data