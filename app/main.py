"""
应用程序入口点

负责初始化FastAPI应用，配置中间件，注册路由，
并设置应用程序的启动和关闭事件处理器。
"""
import logging
import os
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# 创建限速器实例
limiter = Limiter(key_func=get_remote_address)

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    description="外卖配送系统API，支持用户、商家、骑手和管理员等多角色操作。",
    version="1.0.0",
    debug=settings.DEBUG,
)

# 添加速率限制异常处理器
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 配置CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# 请求ID中间件
class RequestIDMiddleware(BaseHTTPMiddleware):
    """为每个请求添加唯一ID"""

    async def dispatch(self, request: Request, call_next):
        # 导入在这里避免循环导入
        from app.utils.ulid import generate_ulid
        
        request_id = generate_ulid()
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# 添加请求ID中间件
app.add_middleware(RequestIDMiddleware)


# 日志记录中间件
class LoggingMiddleware(BaseHTTPMiddleware):
    """记录请求和响应信息"""

    async def dispatch(self, request: Request, call_next):
        start_time = datetime.utcnow()
        
        # 记录请求信息
        logging.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            },
        )
        
        response = await call_next(request)
        
        # 计算处理时间
        process_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # 记录响应信息
        logging.info(
            f"Response: {response.status_code} {process_time:.2f}ms",
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "status_code": response.status_code,
                "process_time": f"{process_time:.2f}ms",
            },
        )
        
        return response


# 添加日志中间件
app.add_middleware(LoggingMiddleware)


# 设置静态文件目录
@app.on_event("startup")
async def create_static_dirs():
    """确保静态文件和上传目录存在"""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    

# 如果静态文件目录存在，则挂载
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


# 根路由 - 健康检查
@app.get("/", tags=["健康检查"])
async def root():
    """API根端点，可用于健康检查"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
    }


# 这里会在后续导入API路由
# from app.api.api_v1.api import api_router
# app.include_router(api_router, prefix=settings.API_V1_STR)


# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用程序启动时执行"""
    logging.info(
        f"应用程序启动: {settings.PROJECT_NAME} v1.0.0",
        extra={"event": "startup", "time": datetime.utcnow().isoformat()},
    )


# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用程序关闭时执行"""
    logging.info(
        f"应用程序关闭: {settings.PROJECT_NAME}",
        extra={"event": "shutdown", "time": datetime.utcnow().isoformat()},
    )


if __name__ == "__main__":
    # 仅用于开发环境
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)