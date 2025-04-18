"""
ULID (Universally Unique Lexicographically Sortable Identifier) 工具模块

提供生成ULID的功能，ULID是一种结合了时间戳和随机性的唯一标识符，
类似于UUID但提供了时间排序功能。
"""
import os
import time
from datetime import datetime
from typing import Optional

# Crockford的Base32字符集（不包含 I, L, O, U 以避免混淆）
# 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, A, B, C, D, E, F, G, H, J, K, M, N, P, Q, R, S, T, V, W, X, Y, Z
ENCODING_CHARS = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
ENCODING_LENGTH = len(ENCODING_CHARS)

# ULID组成部分的长度
TIME_PART_LENGTH = 10  # 10个字符表示48位时间戳
RANDOM_PART_LENGTH = 16  # 16个字符表示80位随机数
TOTAL_LENGTH = TIME_PART_LENGTH + RANDOM_PART_LENGTH  # 26字符


def generate_ulid(timestamp: Optional[int] = None) -> str:
    """
    生成一个ULID (Universally Unique Lexicographically Sortable Identifier)
    
    ULID由两部分组成：
    1. 时间戳部分：10个字符，基于毫秒级Unix时间戳
    2. 随机部分：16个字符，随机生成
    
    Args:
        timestamp: 可选的Unix时间戳（毫秒），若不提供则使用当前时间
    
    Returns:
        26个字符的ULID字符串
    """
    # 如果未提供时间戳，使用当前时间
    if timestamp is None:
        timestamp = int(time.time() * 1000)

    # 生成时间戳部分（10个字符）
    time_chars = encode_time(timestamp)
    
    # 生成随机部分（16个字符）
    random_chars = generate_random_chars(RANDOM_PART_LENGTH)
    
    # 组合成完整的ULID
    return time_chars + random_chars


def encode_time(timestamp_ms: int) -> str:
    """
    将毫秒级时间戳编码为10个字符的字符串
    
    Args:
        timestamp_ms: 毫秒时间戳
        
    Returns:
        10个字符的编码字符串
    """
    if timestamp_ms < 0 or timestamp_ms > 0xFFFFFFFFFFFF:  # 48位的最大值
        raise ValueError("时间戳超出有效范围")
    
    encoded = ""
    for i in range(TIME_PART_LENGTH):
        mod = timestamp_ms % ENCODING_LENGTH
        encoded = ENCODING_CHARS[mod] + encoded
        timestamp_ms //= ENCODING_LENGTH
    
    return encoded


def generate_random_chars(length: int) -> str:
    """
    生成指定长度的随机字符串
    
    Args:
        length: 要生成的字符数量
        
    Returns:
        随机字符串
    """
    # 计算需要多少随机字节
    byte_length = ((length * 5) + 7) // 8  # 每个Base32字符表示5位，向上取整到字节
    random_bytes = os.urandom(byte_length)
    
    result = ""
    for i in range(length):
        # 每个字节8位，每个字符5位，所以需要处理边界情况
        byte_idx = (i * 5) // 8
        bit_idx = (i * 5) % 8
        
        # 从当前字节提取需要的位
        if bit_idx <= 3:
            # 可以从单个字节获取所有5位
            char_value = (random_bytes[byte_idx] >> (3 - bit_idx)) & 0x1F
        else:
            # 需要跨两个字节获取5位
            bits_from_first = 8 - bit_idx
            char_value = ((random_bytes[byte_idx] & ((1 << bits_from_first) - 1)) << (5 - bits_from_first))
            
            # 如果还有下一个字节，获取剩余位
            if byte_idx + 1 < byte_length:
                char_value |= random_bytes[byte_idx + 1] >> (8 - (5 - bits_from_first))
        
        result += ENCODING_CHARS[char_value]
    
    return result


def decode_time(ulid: str) -> datetime:
    """
    从ULID中解码时间戳部分，并返回对应的datetime对象
    
    Args:
        ulid: ULID字符串
        
    Returns:
        对应的datetime对象
    """
    if len(ulid) != TOTAL_LENGTH:
        raise ValueError(f"ULID长度必须为{TOTAL_LENGTH}个字符")
    
    # 提取时间部分
    time_part = ulid[:TIME_PART_LENGTH].upper()
    
    # 解码时间戳
    timestamp_ms = 0
    for char in time_part:
        timestamp_ms = timestamp_ms * ENCODING_LENGTH + ENCODING_CHARS.index(char)
    
    # 转换为datetime对象
    return datetime.fromtimestamp(timestamp_ms / 1000.0)


def is_valid_ulid(ulid: str) -> bool:
    """
    验证字符串是否为有效的ULID格式
    
    Args:
        ulid: 要验证的字符串
        
    Returns:
        如果是有效ULID则返回True，否则返回False
    """
    if not isinstance(ulid, str) or len(ulid) != TOTAL_LENGTH:
        return False
    
    # 检查是否所有字符都在有效的字符集中
    for char in ulid.upper():
        if char not in ENCODING_CHARS:
            return False
            
    return True


def get_timestamp_from_ulid(ulid: str) -> int:
    """
    从ULID中提取毫秒级时间戳
    
    Args:
        ulid: ULID字符串
        
    Returns:
        毫秒时间戳
    """
    if not is_valid_ulid(ulid):
        raise ValueError("无效的ULID格式")
    
    # 提取时间部分
    time_part = ulid[:TIME_PART_LENGTH].upper()
    
    # 解码时间戳
    timestamp_ms = 0
    for char in time_part:
        timestamp_ms = timestamp_ms * ENCODING_LENGTH + ENCODING_CHARS.index(char)
    
    return timestamp_ms


if __name__ == "__main__":
    # 简单测试
    ulid = generate_ulid()
    print(f"生成的ULID: {ulid}")
    print(f"时间戳部分: {ulid[:TIME_PART_LENGTH]}")
    print(f"随机部分: {ulid[TIME_PART_LENGTH:]}")
    print(f"创建时间: {decode_time(ulid)}")