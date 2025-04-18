"""
文件路径: app/core/security.py

安全性工具模块

提供应用程序所需的各种安全相关功能，包括密码哈希、令牌生成和验证、加密等。
专注于保护用户凭据和确保API安全访问。
使用Argon2哈希算法，该算法是密码哈希竞赛的获胜者，安全性高于bcrypt。
"""
import base64
import hmac
import secrets
import string
from datetime import timedelta
from typing import Any, Dict, Optional, Union

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt
from itsdangerous import URLSafeTimedSerializer

# 从环境变量获取密钥和配置
from app.core.config import settings
# 使用集中的时间处理模块
from app.utils.time import beijing_now

# 配置Argon2密码哈希工具
# Argon2是目前推荐的最安全的密码哈希算法
ph = PasswordHasher()

# 从配置中加载加密相关常量
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_MINUTES = settings.REFRESH_TOKEN_EXPIRE_MINUTES


def get_password_hash(password: str) -> str:
    """
    生成密码哈希
    
    使用Argon2算法对明文密码进行哈希处理，
    自动处理加盐、内存消耗和并行因子，提供最高级别的安全性。
    
    参数:
        password: 待哈希的明文密码
        
    返回:
        str: 哈希处理后的密码字符串
    
    示例:
        hashed = get_password_hash("my_secure_password")
    """
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    比较明文密码是否与存储的哈希值匹配，
    使用恒定时间比较防止计时攻击。
    
    参数:
        plain_password: 待验证的明文密码
        hashed_password: 存储的密码哈希值
        
    返回:
        bool: 密码匹配返回True，否则返回False
        
    示例:
        is_valid = verify_password("entered_password", user.password_hash)
    """
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False


def check_password_strength(password: str) -> Dict[str, Union[bool, str]]:
    """
    检查密码强度
    
    根据多个指标评估密码强度，包括长度、复杂性、常见模式等。
    
    参数:
        password: 待评估的明文密码
        
    返回:
        Dict: 包含评估结果的字典，包括是否合格和具体问题描述
        
    示例:
        result = check_password_strength("password123")
        if not result["valid"]:
            print(f"密码问题: {result['message']}")
    """
    # 检查密码长度
    if len(password) < 8:
        return {"valid": False, "message": "密码长度不足8个字符"}
    
    # 检查密码复杂性
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in string.punctuation for c in password)
    
    complexity_count = sum([has_lower, has_upper, has_digit, has_special])
    
    if complexity_count < 3:
        return {
            "valid": False, 
            "message": "密码需要包含至少3种字符类型（大写字母、小写字母、数字和特殊字符）"
        }
    
    # 检查常见密码模式
    common_patterns = ["password", "123456", "qwerty", "abc123", "admin"]
    for pattern in common_patterns:
        if pattern in password.lower():
            return {"valid": False, "message": "密码包含常见易猜测的模式"}
    
    # 密码符合要求
    return {
        "valid": True,
        "message": "密码强度符合要求",
        "strength": "strong" if complexity_count == 4 else "medium"
    }


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    生成用于API认证的JWT令牌，包含用户标识和权限信息。
    使用北京时区(UTC+8)计算过期时间。
    
    参数:
        data: 要编码到令牌中的数据，通常包含用户ID和权限
        expires_delta: 令牌有效期，如不提供则使用默认值
        
    返回:
        str: 编码后的JWT令牌字符串
        
    示例:
        token = create_access_token({"sub": user.id, "scopes": ["read", "write"]})
    """
    to_encode = data.copy()
    expire = beijing_now() + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    创建JWT刷新令牌
    
    生成用于刷新访问令牌的长期令牌。
    使用北京时区(UTC+8)计算过期时间。
    
    参数:
        data: 要编码到令牌中的数据，通常只包含用户ID
        
    返回:
        str: 编码后的JWT刷新令牌字符串
    """
    to_encode = data.copy()
    expire = beijing_now() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "token_type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    解码JWT令牌
    
    验证并解码JWT令牌，获取其中包含的数据。
    注意: 解码时使用与编码时相同的时区设置。
    
    参数:
        token: JWT令牌字符串
        
    返回:
        Dict: 令牌中包含的数据
        
    抛出:
        JWTError: 令牌无效或已过期
        
    示例:
        try:
            data = decode_token(token)
            user_id = data.get("sub")
        except JWTError:
            # 处理无效令牌
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def generate_secure_random_string(length: int = 32) -> str:
    """
    生成安全的随机字符串
    
    用于创建安全令牌、密钥和其他需要随机性的场景。
    
    参数:
        length: 所需字符串长度，默认32位
        
    返回:
        str: 包含字母和数字的随机字符串
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_password_reset_token(email: str) -> str:
    """
    生成密码重置令牌
    
    创建一个加密的令牌，用于安全地重置用户密码。
    
    参数:
        email: 用户电子邮件，作为令牌的主题
        
    返回:
        str: 加密的密码重置令牌
    """
    # 使用itsdangerous库创建安全令牌
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps({"email": email, "type": "reset"})


def verify_password_reset_token(token: str, max_age_seconds: int = 3600) -> Optional[str]:
    """
    验证密码重置令牌
    
    解码并验证密码重置令牌的有效性，并返回关联的电子邮件。
    
    参数:
        token: 密码重置令牌
        max_age_seconds: 令牌最大有效期（秒），默认1小时
        
    返回:
        Optional[str]: 如果令牌有效则返回电子邮件，否则返回None
    """
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        data = serializer.loads(token, max_age=max_age_seconds)
        if data.get("type") != "reset":
            return None
        return data.get("email")
    except Exception:
        return None


def generate_verification_code(length: int = 6) -> str:
    """
    生成数字验证码
    
    用于电子邮件验证、手机验证等场景的数字验证码。
    
    参数:
        length: 验证码长度，默认6位
        
    返回:
        str: 数字验证码
    """
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def get_hmac_digest(data: str, key: str = SECRET_KEY) -> str:
    """
    使用HMAC计算数据摘要
    
    为数据创建加密签名，用于验证数据完整性。
    
    参数:
        data: 需要签名的数据
        key: 用于签名的密钥，默认使用应用密钥
        
    返回:
        str: Base64编码的HMAC摘要
    """
    digest = hmac.new(
        key.encode('utf-8'),
        msg=data.encode('utf-8'),
        digestmod='sha256'
    ).digest()
    return base64.b64encode(digest).decode()


def validate_hmac_digest(data: str, digest: str, key: str = SECRET_KEY) -> bool:
    """
    验证HMAC摘要
    
    验证数据的HMAC摘要是否有效，确保数据未被篡改。
    
    参数:
        data: 原始数据
        digest: 收到的摘要
        key: 用于签名的密钥，默认使用应用密钥
        
    返回:
        bool: 摘要有效返回True，否则返回False
    """
    expected = get_hmac_digest(data, key)
    return hmac.compare_digest(digest, expected)