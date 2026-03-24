# 后端测试目录

## 目录结构

```
tests/
├── conftest.py          # pytest 全局 fixtures
├── test_sample.py      # 示例测试
└── archived/           # 历史测试（待迁移）
```

## 运行测试

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行所有测试
pytest

# 运行指定文件
pytest tests/test_sample.py

# 运行并生成报告
pytest --alluredir=allure-results
```
