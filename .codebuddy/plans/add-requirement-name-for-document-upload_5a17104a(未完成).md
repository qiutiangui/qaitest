---
name: add-requirement-name-for-document-upload
overview: 在AI用例生成的文档上传模式添加需求名称输入框，便于管理多文档场景下的向量数据和功能点分组。
todos:
  - id: add-requirement-name-input
    content: 在文档上传模式添加需求名称输入框UI
    status: pending
  - id: add-validation-logic
    content: 扩展startGeneration验证逻辑，文档模式校验需求名称
    status: pending
---

## 产品概述

为AI用例生成模块的文档上传界面添加需求名称输入框，支持用户在上传需求文档时自定义需求名称，便于后续功能点分组展示和向量数据管理。

## 核心功能

- 文档上传模式新增需求名称输入框（必填）
- 表单验证：提交时校验需求名称是否填写
- 与现有手动输入模式的需求名称字段共用同一变量

## 技术栈

- 前端框架：Vue 3 + TypeScript
- UI组件：Element Plus
- 后端框架：FastAPI

## 实现方案

在文档上传模式的UI中复用已有的 `requirementName` 变量，添加输入框组件。前端验证逻辑扩展至文档模式，确保提交时需求名称不为空。

## 目录结构

```
frontend/src/views/AICaseGeneration/
└── Generate.vue  # [MODIFY] 文档上传模式添加需求名称输入框，扩展验证逻辑
```

## 实现细节

1. **UI层改动**（第376行附近）：在文件上传区域之前添加需求名称输入框，样式与手动输入模式一致
2. **验证逻辑改动**（第91-96行）：在 `else` 分支中添加 `requirementName` 的非空校验
3. **表单重置**：`resetForm` 函数已包含 `requirementName.value = ''`，无需额外改动