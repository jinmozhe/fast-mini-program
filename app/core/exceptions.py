"""
异常处理模块

定义系统的异常类型和全局异常处理器，
将各种异常转换为统一格式的API响应。
支持多语言错误消息。
"""
import logging
import traceback
from typing import Any, Dict, List, Optional, Type, Union, cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError

from app.utils.i18n import get_text, i18n

logger = logging.getLogger(__name__)


class ErrorCode:
    """错误代码常量定义"""
    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = "COMMON_UNKNOWN_ERROR"  # 未知错误
    VALIDATION_ERROR = "COMMON_VALIDATION_ERROR"  # 数据验证错误
    RESOURCE_NOT_FOUND = "COMMON_RESOURCE_NOT_FOUND"  # 资源未找到
    
    # 认证相关错误 (2000-2999)
    AUTHENTICATION_FAILED = "AUTH_INVALID_CREDENTIALS"  # 认证失败
    TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"  # 令牌过期
    PERMISSION_DENIED = "AUTH_PERMISSION_DENIED"  # 权限被拒绝
    
    # 数据库相关错误 (3000-3999)
    DATABASE_ERROR = "DB_UNKNOWN_ERROR"  # 数据库通用错误
    UNIQUE_VIOLATION = "DB_UNIQUE_VIOLATION"  # 唯一性约束冲突
    FOREIGN_KEY_VIOLATION = "DB_FOREIGN_KEY_VIOLATION"  # 外键约束冲突
    
    # 业务逻辑错误 (4000-4999)
    BUSINESS_ERROR = "BIZ_GENERAL_ERROR"  # 通用业务错误
    
    # 外部服务错误 (5000-5999)
    EXTERNAL_SERVICE_ERROR = "EXT_SERVICE_ERROR"  # 外部服务错误
    PAYMENT_SERVICE_ERROR = "EXT_PAYMENT_ERROR"  # 支付服务错误
    MAP_SERVICE_ERROR = "EXT_MAP_ERROR"  # 地图服务错误
    SMS_SERVICE_ERROR = "EXT_SMS_ERROR"  # 短信服务错误


class APIException(Exception):
    """
    API异常基类
    
    所有自定义API异常都应该继承自此类，
    以确保统一处理和响应格式。
    """
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = ErrorCode.UNKNOWN_ERROR
    error_message: str = "发生了未知错误"
    error_details: Optional[Dict[str, Any]] = None
    
    def __init__(
        self, 
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ):
        if error_message:
            self.error_message = error_message
        if error_code:
            self.error_code = error_code
        if error_details:
            self.error_details = error_details
        if status_code:
            self.status_code = status_code
        
        super().__init__(self.error_message)


class NotFoundError(APIException):
    """资源未找到异常"""
    status_code = status.HTTP_404_NOT_FOUND
    error_code = ErrorCode.RESOURCE_NOT_FOUND
    error_message = "请求的资源未找到"


class ValidationError(APIException):
    """数据验证错误"""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = ErrorCode.VALIDATION_ERROR
    error_message = "提供的数据无效"


class AuthenticationError(APIException):
    """认证错误"""
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = ErrorCode.AUTHENTICATION_FAILED
    error_message = "认证失败"


class PermissionDeniedError(APIException):
    """权限错误"""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = ErrorCode.PERMISSION_DENIED
    error_message = "权限不足"


class TokenError(APIException):
    """令牌错误"""
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = ErrorCode.TOKEN_EXPIRED
    error_message = "认证令牌已过期或无效"


class DatabaseError(APIException):
    """数据库错误"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = ErrorCode.DATABASE_ERROR
    error_message = "数据库操作失败"


class UniqueViolationError(DatabaseError):
    """唯一性约束错误"""
    status_code = status.HTTP_409_CONFLICT
    error_code = ErrorCode.UNIQUE_VIOLATION
    error_message = "记录已存在"


class ForeignKeyViolationError(DatabaseError):
    """外键约束错误"""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.FOREIGN_KEY_VIOLATION
    error_message = "关联记录不存在"


class BusinessError(APIException):
    """业务逻辑错误"""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.BUSINESS_ERROR
    error_message = "业务处理失败"


class ExternalServiceError(APIException):
    """外部服务错误"""
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = ErrorCode.EXTERNAL_SERVICE_ERROR
    error_message = "外部服务调用失败"


# 数据库异常与错误代码的映射
DB_CONSTRAINT_ERROR_MAP = {
    # PostgreSQL错误代码
    "23505": ErrorCode.UNIQUE_VIOLATION,  # 唯一性约束违反
    "23503": ErrorCode.FOREIGN_KEY_VIOLATION,  # 外键约束违反
    # MySQL错误代码
    "1062": ErrorCode.UNIQUE_VIOLATION,   # 重复键
    "1451": ErrorCode.FOREIGN_KEY_VIOLATION,  # 外键约束违反
    "1452": ErrorCode.FOREIGN_KEY_VIOLATION,  # 外键约束违反
}

# 约束名称到错误消息的映射
CONSTRAINT_TO_ERROR_MAP = {
    # 用户模块约束
    "users_email_key": ("user.errors.EMAIL_EXISTS", {}),
    "users_phone_key": ("user.errors.PHONE_EXISTS", {}),
    "users_username_key": ("user.errors.USERNAME_EXISTS", {}),
    
    # 商家模块约束
    "merchants_business_license_key": ("merchant.errors.LICENSE_EXISTS", {}),
    
    # 店铺模块约束
    "shops_name_merchant_id_key": ("shop.errors.NAME_EXISTS_FOR_MERCHANT", {}),
    
    # 骑手模块约束
    "riders_id_number_key": ("rider.errors.ID_NUMBER_EXISTS", {}),
    
    # 外键约束
    "orders_user_id_fkey": ("order.errors.USER_NOT_EXISTS", {}),
    "orders_shop_id_fkey": ("order.errors.SHOP_NOT_EXISTS", {}),
    "products_shop_id_fkey": ("product.errors.SHOP_NOT_EXISTS", {}),
    "order_items_product_id_fkey": ("order.errors.PRODUCT_NOT_EXISTS", {}),
    "order_items_order_id_fkey": ("order.errors.ORDER_NOT_EXISTS", {}),
    "deliveries_rider_id_fkey": ("delivery.errors.RIDER_NOT_EXISTS", {}),
    "deliveries_order_id_fkey": ("delivery.errors.ORDER_NOT_EXISTS", {})
}


def format_validation_errors(errors: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    格式化验证错误，方便客户端处理
    
    Args:
        errors: 原始错误列表
        
    Returns:
        按字段分组的错误消息字典
    """
    error_dict: Dict[str, List[str]] = {}
    
    for error in errors:
        location = error.get("loc", [])
        if len(location) > 1:  # 忽略非字段错误
            field_name = str(location[1])  # 获取字段名
            message = error.get("msg", "字段验证失败")
            
            if field_name not in error_dict:
                error_dict[field_name] = []
                
            error_dict[field_name].append(message)
    
    return error_dict


def handle_database_error(exc: SQLAlchemyError, request: Request) -> APIException:
    """
    处理数据库异常，转换为API异常
    
    Args:
        exc: SQLAlchemy异常对象
        request: FastAPI请求对象
        
    Returns:
        转换后的API异常
    """
    locale = i18n.get_preferred_locale(request)
    
    # 处理完整性错误（约束违反等）
    if isinstance(exc, IntegrityError):
        # 获取原始数据库错误
        if hasattr(exc.orig, 'pgcode'):  # PostgreSQL
            error_code = exc.orig.pgcode
        elif hasattr(exc.orig, 'args') and len(exc.orig.args) > 0:  # MySQL
            error_code = str(exc.orig.args[0])
        else:
            error_code = None
            
        # 尝试获取约束名称
        constraint_name = None
        orig_msg = str(exc.orig)
        
        # 从错误消息中提取约束名称
        # PostgreSQL格式示例: Key (email)=(test@example.com) already exists.
        if "already exists" in orig_msg and "Key" in orig_msg:
            constraint_parts = orig_msg.split('violates unique constraint "')
            if len(constraint_parts) > 1:
                constraint_name = constraint_parts[1].split('"')[0]
        
        # MySQL格式示例: Duplicate entry 'test@example.com' for key 'users.users_email_key'
        elif "Duplicate entry" in orig_msg and "for key" in orig_msg:
            constraint_parts = orig_msg.split("for key '")
            if len(constraint_parts) > 1:
                constraint_name = constraint_parts[1].split("'")[0].split('.')[-1]
                
        # 根据约束名称查找合适的错误消息
        if constraint_name and constraint_name in CONSTRAINT_TO_ERROR_MAP:
            error_key, params = CONSTRAINT_TO_ERROR_MAP[constraint_name]
            error_message = get_text(error_key, params, locale=locale)
            
            if "unique constraint" in orig_msg or "Duplicate entry" in orig_msg:
                return UniqueViolationError(error_message=error_message)
            elif "foreign key constraint" in orig_msg or "Cannot add or update a child row" in orig_msg:
                return ForeignKeyViolationError(error_message=error_message)
        
        # 回退到通用错误代码
        if error_code and error_code in DB_CONSTRAINT_ERROR_MAP:
            mapped_error = DB_CONSTRAINT_ERROR_MAP[error_code]
            if mapped_error == ErrorCode.UNIQUE_VIOLATION:
                return UniqueViolationError()
            elif mapped_error == ErrorCode.FOREIGN_KEY_VIOLATION:
                return ForeignKeyViolationError()
    
    # 记录详细的数据库错误以便调试
    logger.error(f"数据库错误: {str(exc)}")
    
    # 返回通用数据库错误
    return DatabaseError(
        error_message=get_text("database.errors.QUERY_FAILED", locale=locale)
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    设置FastAPI应用的全局异常处理器
    
    Args:
        app: FastAPI应用实例
    """
    
    @app.exception_handler(APIException)
    async def handle_api_exception(request: Request, exc: APIException) -> JSONResponse:
        """处理自定义API异常"""
        locale = i18n.get_preferred_locale(request)
        
        # 获取本地化错误消息
        if hasattr(exc, 'error_code') and exc.error_code:
            # 尝试从i18n获取消息
            module_name = exc.error_code.split('_')[0].lower()
            error_type = "errors"
            error_key = exc.error_code.split('_', 1)[1] if '_' in exc.error_code else exc.error_code
            
            i18n_key = f"{module_name}.{error_type}.{error_key}"
            error_message = get_text(i18n_key, locale=locale)
            
            # 如果无法获取i18n消息，使用异常中的原始消息
            if error_message == error_key:
                error_message = exc.error_message
        else:
            error_message = exc.error_message
        
        # 开发环境记录完整错误堆栈
        logger.error(
            f"API异常: {exc.error_code} - {error_message}\n"
            f"状态码: {exc.status_code}"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": error_message,
                    "details": exc.error_details
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """处理FastAPI请求验证错误"""
        locale = i18n.get_preferred_locale(request)
        
        # 获取本地化错误消息
        error_message = get_text("common.messages.FORM_INVALID", locale=locale)
        
        # 格式化错误详情
        error_details = format_validation_errors(exc.errors())
        
        # 日志记录
        logger.warning(f"请求验证错误: {error_details}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": ErrorCode.VALIDATION_ERROR,
                    "message": error_message,
                    "details": error_details
                }
            }
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """处理数据库异常"""
        api_exc = handle_database_error(exc, request)
        
        # 调用API异常处理器处理转换后的异常
        return await handle_api_exception(request, api_exc)
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """全局异常处理器，捕获所有未处理的异常"""
        locale = i18n.get_preferred_locale(request)
        
        # 获取本地化错误消息
        error_message = get_text("common.messages.UNKNOWN_ERROR", locale=locale)
        
        # 记录详细错误信息，但不返回给客户端
        logger.error(
            f"未处理的异常: {str(exc)}\n"
            f"请求路径: {request.url.path}\n"
            f"堆栈跟踪: {traceback.format_exc()}"
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": ErrorCode.UNKNOWN_ERROR,
                    "message": error_message
                }
            }
        )