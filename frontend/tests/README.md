# 前端测试目录

## 目录结构

```
frontend/
├── tests/
│   ├── setup.ts         # 测试全局配置
│   ├── utils/
│   │   └── format.test.ts   # 工具函数测试示例
│   └── components/
│       └── Button.test.tsx  # 组件测试示例（可选）
└── vitest.config.ts     # Vitest 配置
```

## 安装依赖

```bash
cd frontend
npm install -D vitest @vue/test-utils jsdom @vitest/coverage-v8
```

## 运行测试

```bash
# 运行所有测试
npm test

# 监听模式
npm test -- --watch

# 生成覆盖率报告
npm test -- --coverage
```

## 编写测试

```ts
// tests/utils/format.test.ts
import { describe, it, expect } from 'vitest'

describe('format utilities', () => {
  it('should format date correctly', () => {
    // ...
  })
})
```
