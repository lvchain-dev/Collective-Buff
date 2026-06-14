# 经验引擎 群体BUFF (ExperienceEngine - Collective Buff)

自进化式任务执行知识库。为多 Agent 框架提供知识的自动积累、检索与复用能力。

## 概述

ExperienceEngine 是一个零外部依赖的 Python 库。它在 Agent 执行任务时自动记录经验（成功/失败/日志），在下次遇到相似场景时检索匹配经验并辅助决策，减少重复错误、加速任务执行。

## 核心机制

| 机制 | 说明 |
|------|------|
| 知识条目管理 | 注册、检索、评价、更新、停用 |
| 语义检索 | n-gram 哈希投影嵌入 + 余弦相似度 |
| 版本控制 | 知识变更自动 Git 提交 |
| 自适应阈值 | 按命中率动态调整检索门槛 |
| 时间衰减 | 长期未使用的条目自动降权 |

## 三种学习模式

- **失败驱动**：任务失败后记录错误特征与修复方案
- **成功泛化**：成功执行后提炼可复用的通用模式
- **日志捕获**：从执行日志中自动提取知识

## 快速开始

```python
from core import ExperienceEngine

# 初始化引擎
engine = ExperienceEngine()

# 注册知识条目
engine.register(
    trigger_pattern="API 返回 429 状态码",
    recommendation="等待 Retry-After 头指定的秒数后重试",
    origin="FIX"
)

# 检索知识
hints = engine.search("请求频率限制怎么处理", top_k=3)
for entry in hints:
    print(entry.recommendation, f"(score: {entry.quality_score:.2f})")
```

## 目录结构

```
experience_engine/
├── core/
│   ├── __init__.py      # 包入口
│   └── flywheel.py      # 主引擎
└── README.md
```

## 技术特点

- 零外部依赖（标准库即可运行）
- 中文增强：内置 200 词技术词典的中文分词器，英文文本由 n-gram 直接处理，均无需外部依赖
- JSON 文件持久化，支持 Git 自动备份
- 运行时热加载，新增条目即时生效
- 可作为插件接入任意多 Agent 框架

## 许可

Apache-2.0 License — 允许商用、修改、分发，需保留版权声明。

Copyright © 2026 吕氏链 Lvchain
