# 阿里供应商签名报备接口（三方对接）

基于 FastAPI 的后端服务，用于接收阿里云下发的短信签名报备推送数据，完成解密验证、入库存储，并提供内部管理接口对接阿里云回调/提交/查询接口。

## 功能特性

- 接收阿里云 AES-CBC 加密的三方推送数据，解密后验证字段合法性
- 将报备任务持久化到 MySQL，记录完整的事件日志
- 内部管理接口：任务列表查询、详情查看、触发回调/提交/查询
- 静态运营页面（`/static/opss.html`）用于日常操作

## 系统架构

```
阿里云 ──推送──▶ POST /openapi/ali/register/push
                        │
                  AES-CBC 解密
                        │
                  字段校验（必填项、枚举值）
                        │
                  入库（SignatureRegisterTask）
                        │
           内部接口 ──▶ 回调 / 提交 / 查询 ──▶ 阿里云
```

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| ORM | SQLAlchemy |
| 数据库 | MySQL |
| 加密解密 | AES-CBC（PyCryptodome） |
| 数据校验 | Pydantic v2 |

## 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入实际的数据库连接和阿里云密钥
```

主要配置项说明：

| 环境变量 | 说明 |
|----------|------|
| `DATABASE_URL` | MySQL 连接串 |
| `SUPPLIER_ID` | 阿里云分配的供应商 ID |
| `THIRD_DECRYPT_KEY` / `THIRD_DECRYPT_IV` | 接收推送时的 AES 解密密钥 |
| `THIRD_UPLOAD_KEY` / `THIRD_UPLOAD_IV` | 向阿里云发送数据时的 AES 加密密钥 |

> AES 密钥和供应商 ID 由阿里云在供应商入网时下发。

### 3. 初始化数据库

```bash
mysql -u root -p ali_supplier < sql/init.sql
```

### 4. 启动服务

```bash
python run.py
```

服务默认启动在 `http://0.0.0.0:5772`，接口文档访问 `http://localhost:5772/docs`

## 接口说明

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/openapi/ali/register/push` | 接收三方供应商推送 |
| POST | `/openapi/ali/register/direct/push` | 接收直连供应商推送 |
| GET | `/internal/register/tasks` | 查询任务列表（支持多条件筛选） |
| GET | `/internal/register/{flow_id}` | 获取任务详情及事件日志 |
| POST | `/internal/register/{flow_id}/callback` | 触发向阿里云的回调请求 |
| POST | `/internal/register/{flow_id}/submit` | 触发向阿里云的提交请求 |
| POST | `/internal/register/query` | 触发向阿里云的状态查询 |
| GET | `/health` | 健康检查 |

## 项目结构

```
.
├── run.py                    # 启动入口
├── app/
│   ├── main.py               # FastAPI 应用、中间件、路由注册
│   ├── config.py             # 配置项（读取环境变量）
│   ├── crypto/
│   │   └── aes_util.py       # AES-CBC 加解密工具
│   ├── db/
│   │   ├── models.py         # SQLAlchemy ORM 数据模型
│   │   └── session.py        # 数据库引擎和会话管理
│   ├── routers/
│   │   ├── push.py           # 推送接收接口
│   │   └── internal.py       # 内部管理接口
│   └── services/
│       ├── push_service.py   # 推送处理业务逻辑
│       └── ali_client.py     # 对接阿里云的出站请求
├── sql/
│   └── init.sql              # 数据库建表 SQL
├── static/
│   └── opss.html             # 运营操作页面
├── .env.example              # 环境变量配置示例
└── requirements.txt
```
