"""
文件路径: app/models/user_address.py

用户地址模型模块

定义与用户地址相关的数据模型，支持多种地址类型和地理位置信息。
适用于中国内地用户的地址管理，包含省、市、区等中国特有的行政区划结构。
使用北京时区(UTC+8)处理时间字段。
"""
from __future__ import annotations  # 启用延迟类型评估，解决循环引用
from typing import TYPE_CHECKING

# 从中央导入点获取所需组件
from app.models.base import (
    Base, AuditMixin,
    Boolean, Float, ForeignKey, String, Text,
    Mapped, mapped_column, relationship,
    Optional
)

# 处理循环引用
if TYPE_CHECKING:
    from app.models.user import User


class UserAddress(Base, AuditMixin):
    """
    用户地址模型
    
    存储用户的收货地址、账单地址等信息，支持中国地址格式和坐标定位。
    提供地址标记、默认地址设置和格式化功能。
    
    字段组:
    - 关联信息: 与用户的关联(user_id)
    - 基本地址: 收件人信息和详细地址(recipient_name, province等)
    - 地理位置: 经纬度和位置描述(latitude, longitude)
    - 分类标记: 地址类型和标签(address_type, tag, is_default)
    
    关联关系:
    - user: 地址所属的用户(多对一)
    """
    
    # 表名设置
    __tablename__ = "user_addresses"
    
    # 关联信息
    user_id: Mapped[str] = mapped_column(
        String(26), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        comment="所属用户ID，外键关联users表"
    )
    
    # 地址类型和基本信息
    address_type: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment="地址类型：HOME(家庭)、WORK(工作)、SCHOOL(学校)、OTHER(其他)"
    )
    recipient_name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="收件人姓名"
    )
    recipient_phone: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment="收件人电话"
    )
    
    # 行政区划
    province: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="省份/直辖市"
    )
    city: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="城市"
    )
    district: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="区/县"
    )
    street_address: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="街道地址，详细门牌号"
    )
    
    # 详细地址信息（可选）
    building: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True,
        comment="建筑名称/小区名称"
    )
    room: Mapped[Optional[str]] = mapped_column(
        String(50), 
        nullable=True,
        comment="房间号/门牌号"
    )
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(20), 
        nullable=True,
        comment="邮政编码"
    )
    
    # 地理位置信息
    latitude: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True,
        comment="纬度坐标"
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True,
        comment="经度坐标"
    )
    location_description: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="位置描述，如地标、交通指引等"
    )
    
    # 地址标签和默认标记
    tag: Mapped[Optional[str]] = mapped_column(
        String(20), 
        nullable=True,
        comment="地址标签，如'家'、'公司'等，用于用户快速识别"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="是否为默认地址，用户只能有一个默认地址"
    )
    
    # 关系 - 使用字符串类型标注避免循环引用
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="addresses",
        comment="地址所属的用户"
    )
    
    def __repr__(self) -> str:
        """
        返回地址对象的字符串表示
        
        返回:
            str: 格式化的地址字符串表示
        """
        return f"<UserAddress {self.id}: {self.province}{self.city}{self.district}{self.street_address}>"
    
    def format_full_address(self) -> str:
        """
        格式化完整地址
        
        将地址各组成部分连接成符合中国地址习惯的完整地址字符串。
        
        返回:
            str: 格式化后的完整地址字符串
        
        示例:
            '浙江省杭州市西湖区文三路100号某大厦3单元303室'
        """
        components = [
            self.province,
            self.city,
            self.district,
            self.street_address
        ]
        
        if self.building:
            components.append(self.building)
        
        if self.room:
            components.append(self.room)
            
        return "".join(components)