---
name: 修复 .env 配置路径问题
overview: 修复 pydantic-settings 加载 .env 文件的路径问题，确保从任意目录启动后端都能正确读取配置
todos:
  - id: fix-env-path
    content: 修改 config.py 中 env_file 为绝对路径
    status: completed
---

## 问题描述

后端启动时 MySQL 连接显示 `localhost:3306`，但 `.env` 配置的是 `8.148.248.39`。

## 根本原因

`config.py` 中的 `env_file = ".env"` 使用相对路径，`pydantic-settings` 从**当前工作目录**查找 `.env` 文件。当从项目根目录启动后端时，找不到 `backend/.env` 文件，导致使用默认值。

## 修复目标

修改 `config.py`，使用绝对路径定位 `.env` 文件，确保无论从哪个目录启动都能正确加载配置。

## 修复方案

修改 `/Users/qiutian/cursor_code/qaitest_platform/backend/app/core/config.py` 第 66-68 行：

**修改前**：

```python
class Config:
    env_file = ".env"
    extra = "allow"
```

**修改后**：

```python
class Config:
    # 使用绝对路径定位 .env 文件（在 backend 目录下）
    env_file = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    extra = "allow"
```

## 路径说明

- `config.py` 位于 `backend/app/core/`
- `.env` 位于 `backend/`
- 相对路径 `../../.env` 从 `core/` 上溯到 `app/` 再到 `backend/`