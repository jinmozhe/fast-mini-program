"""
异常处理注册模块

提供将所有异常处理器注册到FastAPI应用的功能。
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import (
    APIException, ErrorCode, 
    handle_api_exception, validation_exception_handler,
    sqlalchemy_exception_handler, global_exception_handler
)


def register_exception_handlers(app: FastAPI) -> None:
    """
    向FastAPI应用注册所有异常处理器
    
    Args:
        app: FastAPI应用实例
    """
    # 注册APIException处理器
    app.add_exception_handler(
        APIException, 
        handle_api_exception
    )
    
    # 注册请求验证错误处理器
    app.add_exception_handler(
        RequestValidationError, 
        validation_exception_handler
    )
    
    # 注册数据库错误处理器
    app.add_exception_handler(
        SQLAlchemyError,
        sqlalchemy_exception_handler
    )
    
    # 注册全局异常处理器
    app.add_exception_handler(
        Exception,
        global_exception_handler
    )