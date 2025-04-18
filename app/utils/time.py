"""
文件路径: app/utils/time.py

时间处理工具模块

提供统一的时间处理功能，确保系统中所有时间都使用北京时区(UTC+8)。
提供时间格式化、解析和转换功能。
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

# 定义北京时区常量 (UTC+8)
BEIJING_TIMEZONE = timezone(timedelta(hours=8))

def beijing_now() -> datetime:
    """
    获取北京时区的当前时间
    
    返回带有北京时区信息的当前时间
    
    返回:
        datetime: 当前的北京时间
    """
    return datetime.now(BEIJING_TIMEZONE)


def localize_datetime(dt: datetime) -> datetime:
    """
    为不带时区的日期时间设置北京时区
    
    如果输入的datetime没有时区信息，将其设置为北京时区
    如果已有时区信息，则转换成北京时区
    
    参数:
        dt: 需要本地化的日期时间对象
        
    返回:
        datetime: 具有北京时区信息的日期时间对象
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=BEIJING_TIMEZONE)
    return dt.astimezone(BEIJING_TIMEZONE)


def format_datetime(dt: Optional[datetime] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化日期时间为字符串
    
    将日期时间对象格式化为指定格式的字符串
    如果未提供日期时间对象，则使用当前北京时间
    
    参数:
        dt: 要格式化的日期时间对象，默认为None（使用当前时间）
        fmt: 格式化模板，默认为"年-月-日 时:分:秒"
        
    返回:
        str: 格式化的日期时间字符串
    """
    if dt is None:
        dt = beijing_now()
    else:
        dt = localize_datetime(dt)
    
    return dt.strftime(fmt)


def parse_datetime(datetime_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    解析日期时间字符串
    
    将字符串解析为带有北京时区的日期时间对象
    
    参数:
        datetime_str: 日期时间字符串
        fmt: 日期时间格式，默认为"年-月-日 时:分:秒"
        
    返回:
        datetime: 解析后的带有北京时区信息的日期时间对象
    """
    dt = datetime.strptime(datetime_str, fmt)
    return dt.replace(tzinfo=BEIJING_TIMEZONE)


def timestamp_to_datetime(timestamp: float) -> datetime:
    """
    将时间戳转换为北京时间
    
    参数:
        timestamp: UNIX时间戳（秒）
        
    返回:
        datetime: 对应的北京时间
    """
    return datetime.fromtimestamp(timestamp, BEIJING_TIMEZONE)


def datetime_to_timestamp(dt: datetime) -> float:
    """
    将日期时间对象转换为UNIX时间戳
    
    参数:
        dt: 日期时间对象
        
    返回:
        float: UNIX时间戳（秒）
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=BEIJING_TIMEZONE)
    return dt.timestamp()

# 导出标准库的时间类和函数以及自定义的函数
__all__ = [
    # 从datetime模块导出的类和函数
    'datetime', 'timedelta', 'timezone',
    
    # 自定义的时区常量
    'BEIJING_TIMEZONE',
    
    # 自定义的函数
    'beijing_now', 'localize_datetime', 'format_datetime',
    'parse_datetime', 'timestamp_to_datetime', 'datetime_to_timestamp'
]