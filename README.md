# FastAPI多角色外卖配送系统

![版本](https://img.shields.io/badge/版本-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.108.0+-lightblue.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.x-red.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.0+-blue.svg)

一个基于FastAPI构建的高性能、类型安全、可扩展的多角色外卖配送系统，支持商家、客户、骑手和管理员四种角色，采用现代Python技术栈和最佳实践。

## 功能特点

### 多角色支持
- **客户端**：浏览商品、下单、支付、查看订单状态、评价
- **商家端**：店铺管理、商品管理、订单处理、销售统计
- **骑手端**：接单、配送、订单状态更新、路线规划
- **管理员**：系统配置、用户管理、数据分析、权限控制

### 技术亮点
- 完整的**RBAC权限控制**系统
- 基于JWT的安全**认证与授权**机制
- **国际化(i18n)错误处理**与消息提示
- **标准化API响应**格式与错误处理
- **自动文档生成**与交互测试界面
- **PostgreSQL高级特性**充分利用(JSONB、GIN索引)
- **高性能异步处理**，适应高并发场景

## 技术栈

### 后端框架
- **FastAPI** - 高性能异步API框架
- **Pydantic V2** - 数据验证与序列化
- **SQLAlchemy 2.0** - ORM与数据库交互
- **Alembic** - 数据库迁移管理
- **Starlette** - ASGI应用底层库

### 数据存储
- **PostgreSQL 15+** - 主数据库
- **Redis** - 缓存与令牌黑名单

### 认证与安全
- **JWT令牌** - 用户认证
- **密码哈希** - Argon2/Bcrypt
- **CORS** - 跨域资源共享
- **速率限制** - API访问控制

### 工具与库
- **ULID** - 有序唯一标识符
- **orjson** - 高性能JSON序列化
- **python-dotenv** - 环境变量管理
- **structlog** - 结构化日志记录

## 项目结构

```
app/
├── alembic/                # 数据库迁移配置与版本
├── api/                    # API路由层
│   ├── deps/               # API依赖项
│   ├── admin/              # 管理员API端点
│   ├── merchant/           # 商家API端点
│   ├── customer/           # 客户API端点
│   └── rider/              # 骑手API端点
├── core/                   # 核心功能组件
│   ├── config.py           # 应用配置
│   ├── security.py         # 安全与认证
│   ├── permissions.py      # 权限控制
│   ├── response.py         # 响应格式化
│   └── exceptions.py       # 异常定义
├── db/                     # 数据库相关
│   ├── base.py             # 数据库基础配置
│   └── session.py          # 会话管理
├── locale/                 # 国际化资源
│   ├── en/                 # 英文资源
│   └── zh/                 # 中文资源
├── middleware/             # 中间件
│   ├── error_middleware.py # 错误处理
│   └── logging.py          # 日志中间件
├── models/                 # 数据库模型
│   ├── base.py             # 模型基类
│   ├── user.py             # 用户模型
│   ├── merchant.py         # 商家模型
│   └── ...                 # 其他模型
├── schemas/                # 数据验证模式
│   ├── user.py             # 用户验证模式
│   ├── auth.py             # 认证验证模式
│   └── ...                 # 其他验证模式
├── services/               # 业务逻辑服务
│   ├── auth_service.py     # 认证服务
│   ├── user_service.py     # 用户服务
│   └── ...                 # 其他服务
├── utils/                  # 工具函数
│   ├── i18n.py             # 国际化工具
│   └── exceptions.py       # 异常工具
├── .env                    # 环境变量
├── main.py                 # 应用入口
└── requirements.txt        # 项目依赖
```

## 安装与设置

### 前置条件
- Python 3.10+
- PostgreSQL 15+
- 虚拟环境工具(推荐使用Poetry或venv)

### 安装步骤

1. **克隆代码库**
   ```bash
   git clone https://github.com/yourusername/fastapi-delivery-system.git
   cd fastapi-delivery-system
   ```

2. **创建并激活虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # 或
   .\venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   创建`.env`文件并设置必要的环境变量
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
   SECRET_KEY=your-secret-key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

5. **运行数据库迁移**
   ```bash
   alembic upgrade head
   ```

6. **启动应用**
   ```bash
   uvicorn app.main:app --reload
   ```

## API文档

启动应用后，可以通过以下URL访问自动生成的API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

API分为以下几个主要部分：

- **/api/auth** - 认证相关API（登录、注册、刷新令牌）
- **/api/customer** - 客户相关API（浏览商品、下单、评价）
- **/api/merchant** - 商家相关API（店铺管理、订单处理）
- **/api/rider** - 骑手相关API（接单、配送）
- **/api/admin** - 管理员相关API（系统管理、用户管理）

## 开发指南

### 代码风格
- 使用[Black](https://github.com/psf/black)和[isort](https://github.com/pycqa/isort)进行代码格式化
- 遵循[PEP 8](https://pep8.org/)编码规范
- 使用类型注解增强代码可读性和IDE支持

### 添加新功能
1. 在`models/`目录下创建数据库模型
2. 在`schemas/`目录下定义数据验证模式
3. 在`services/`目录下实现业务逻辑
4. 在`api/`相应目录下创建API端点
5. 在`alembic/`中添加数据库迁移脚本
6. 更新测试和文档

### 测试
运行单元测试：
```bash
pytest
```

运行覆盖率测试：
```bash
pytest --cov=app
```

### 代码检查
```bash
# 代码格式化
black app
isort app

# 静态类型检查
mypy app
```

## 贡献
欢迎贡献代码、报告问题或提出新功能建议！请遵循以下步骤：
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证
本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。

## 联系方式
项目维护者: [jinmozhe](https://github.com/jinmozhe)

---