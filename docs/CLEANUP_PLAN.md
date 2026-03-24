# 项目清理计划

## 📊 清理概览

**总文件数**: 约 1000+ 文件
**需要清理**: 18 个文件
**保留但标记为遗留**: 4 个文件
**预期收益**: 减少 ~5% 代码量，提升项目可维护性

---

## 🔴 需要删除的文件（18个）

### 1. 旧的模型文件（2个）

```bash
# 这些文件已被新版本替代，可以安全删除
backend/app/models/task_old.py          # 旧版 AsyncTask 模型
backend/app/models/task_new.py          # 过渡版本（功能已迁移到 __init__.py）
```

**影响范围**: 无影响，未被任何代码引用

---

### 2. 测试文件（8个）

```bash
# 临时测试文件，建议移动到 tests/ 目录或删除
backend/test_db.py                      # 数据库连接测试
backend/test_db_connection.py           # 重复的数据库测试
backend/test_milvus.py                  # Milvus 连接测试
backend/test_optional_project_id.py     # 可选项目ID测试
backend/test_llamaindex.py              # LlamaIndex 集成测试（已删除）
backend/test_agent.py                   # Agent 测试（如存在）
backend/test_*.py                       # 其他临时测试文件
```

**建议**:
- 如果测试有价值，移动到 `backend/tests/` 目录
- 如果是临时测试，可以删除
- 正式测试应该使用 pytest 框架

---

### 3. 未使用的前端文件（3个）

```bash
# Vue 项目模板默认文件，未被使用
frontend/src/components/HelloWorld.vue  # Vue 默认示例组件
frontend/src/style.css                  # 未使用的全局样式（项目使用 Tailwind）
frontend/public/vue.svg                 # 未使用的 Vue logo
```

**影响范围**: 无影响，未被任何页面引用

---

### 4. 空的 Service 文件（4个）

```bash
# 这些文件几乎为空，未被使用
backend/app/services/requirement_service.py  # 只有 5 行代码
backend/app/services/testcase_service.py     # 只有 5 行代码
backend/app/services/testplan_service.py     # 只有 5 行代码
backend/app/services/testreport_service.py   # 只有 5 行代码
```

**内容示例**:
```python
"""
需求服务
"""
# TODO: 实现需求服务
```

**建议**: 删除空文件，需要时再创建

---

### 5. 工具脚本（1个）

```bash
backend/alter_db_schema.py              # 数据库修改脚本（一次性使用）
```

**建议**: 如果数据库迁移已完成，可以删除

---

## 🟡 保留但标记为遗留（4个）

### RAG 旧实现

```bash
backend/app/rag/index_manager.py        # 旧版 IndexManager（659 行）
backend/app/rag/embeddings.py           # 旧版 QwenEmbedding（101 行）
backend/app/rag/vector_store.py         # 旧版 MilvusVectorStore（225 行）
backend/app/rag/document_loader.py      # 旧版 DocumentLoader（使用中）
```

**保留原因**:
- ✅ 支持配置切换新旧实现（`rag_backend: "legacy"`）
- ✅ 向后兼容性保证
- ✅ 现有 Milvus 数据无需迁移

**标记方式**:
```python
"""
旧版 IndexManager - 已迁移到 LlamaIndex 0.14.18

该文件保留用于向后兼容，新项目建议使用 LlamaIndexIndexManager。
配置方式: settings.rag_backend = "legacy"

迁移指南: docs/CHANGELOG.md
"""
```

---

## 🔵 可能重复的文件（需检查）

### Milvus 工具

```bash
backend/milvus_server.py                # 根目录脚本
backend/app/utils/milvus_server.py      # utils 模块
```

**建议**: 检查功能是否重复，保留一个即可

---

## 📝 清理步骤

### 第一步：备份（重要！）

```bash
# 创建备份分支
git checkout -b backup-before-cleanup
git add .
git commit -m "备份：清理前状态"
git checkout main
```

---

### 第二步：删除明确无用的文件

```bash
# 1. 删除旧模型文件
rm backend/app/models/task_old.py
rm backend/app/models/task_new.py

# 2. 删除临时测试文件（建议先移动到 tests/ 目录）
mkdir -p backend/tests/archived
mv backend/test_*.py backend/tests/archived/

# 3. 删除未使用的前端文件
rm frontend/src/components/HelloWorld.vue
rm frontend/src/style.css
rm frontend/public/vue.svg

# 4. 删除空的 service 文件
rm backend/app/services/requirement_service.py
rm backend/app/services/testcase_service.py
rm backend/app/services/testplan_service.py
rm backend/app/services/testreport_service.py

# 5. 删除一次性工具脚本
rm backend/alter_db_schema.py
```

---

### 第三步：更新文档

在文件头部添加遗留代码标记：

```python
# backend/app/rag/index_manager.py
"""
[LEGACY] 旧版 IndexManager - 已迁移到 LlamaIndex 0.14.18

该文件保留用于向后兼容，新项目建议使用 LlamaIndexIndexManager。

配置切换:
  settings.rag_backend = "legacy"  # 使用旧版
  settings.rag_backend = "llamaindex"  # 使用新版（推荐）

迁移指南: docs/CHANGELOG.md
"""
```

---

### 第四步：更新 .gitignore

```bash
# 添加到 .gitignore
echo "# 临时测试文件" >> .gitignore
echo "backend/test_*.py" >> .gitignore
echo "backend/tests/archived/" >> .gitignore
```

---

## 📊 清理效果评估

### 代码量减少

| 类别 | 删除文件数 | 代码行数 | 占比 |
|------|-----------|---------|------|
| 旧模型文件 | 2 | ~133 行 | 0.5% |
| 测试文件 | 8 | ~500 行 | 2.0% |
| 前端文件 | 3 | ~120 行 | 0.5% |
| 空 service | 4 | ~20 行 | 0.1% |
| 工具脚本 | 1 | ~62 行 | 0.2% |
| **总计** | **18** | **~835 行** | **~3.3%** |

### 项目结构优化

**清理前**:
```
backend/
├── test_*.py (散落的测试文件)
├── app/
│   ├── models/
│   │   ├── task_old.py (旧版)
│   │   └── task_new.py (过渡版)
│   └── services/
│       ├── *_service.py (空文件)
│       └── ...
```

**清理后**:
```
backend/
├── tests/ (统一测试目录)
│   ├── unit/
│   ├── integration/
│   └── archived/ (历史测试)
├── app/
│   ├── models/
│   │   └── __init__.py (当前版本)
│   └── services/
│       ├── project_service.py (有效服务)
│       └── version_service.py (有效服务)
```

---

## ⚠️ 注意事项

### 1. 数据安全

- ✅ 确认数据库迁移已完成再删除 `alter_db_schema.py`
- ✅ 确认无依赖后再删除旧模型文件
- ✅ 测试文件移到 archived/ 而非直接删除

### 2. 兼容性

- ✅ RAG 旧实现保留，支持配置切换
- ✅ 旧版 API 接口保持不变
- ✅ 前端无需改动

### 3. 回滚计划

```bash
# 如果清理后出现问题，可以快速回滚
git checkout backup-before-cleanup
```

---

## 🚀 后续优化建议

### 1. 代码质量

- [ ] 使用 `pylint` 或 `flake8` 检查代码规范
- [ ] 使用 `vulture` 检测未使用的代码
- [ ] 使用 `pytest` 建立正式测试框架

### 2. 依赖管理

- [ ] 检查 `requirements.txt` 中未使用的依赖
- [ ] 使用 `pipdeptree` 分析依赖树
- [ ] 清理间接依赖中的冗余包

### 3. 文档更新

- [ ] 更新 README.md 中的目录结构
- [ ] 添加代码迁移指南
- [ ] 更新 API 文档

---

## 📅 清理时间表

| 时间 | 任务 | 负责人 |
|------|------|--------|
| 第1天 | 备份和删除旧模型文件 | - |
| 第2天 | 整理测试文件 | - |
| 第3天 | 清理前端文件 | - |
| 第4天 | 删除空 service 文件 | - |
| 第5天 | 更新文档和 .gitignore | - |

---

## ✅ 验收标准

清理完成后，项目应该满足：

- [ ] 无未使用的文件
- [ ] 无空的 service 文件
- [ ] 测试文件统一在 tests/ 目录
- [ ] RAG 旧实现标记为 [LEGACY]
- [ ] .gitignore 更新完整
- [ ] 项目可以正常启动和运行
- [ ] 所有测试通过

---

## 📞 联系方式

如有疑问，请参考：
- 项目文档: `docs/CHANGELOG.md`
- 技术支持: 提交 Issue
