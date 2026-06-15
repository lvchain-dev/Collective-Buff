# 经验引擎 Collective-Buff / ExperienceEngine — Collective Buff

> 自进化式任务执行知识库。为多 Agent 框架提供知识的自动积累、检索与复用能力。
> A self-evolving knowledge base for task execution. Auto-accumulates, retrieves, and reuses knowledge across multi-agent frameworks.
>
> **稳定运行近一个月的成熟方案。下一代优化研发中，敬请期待。**
> **A battle-tested solution running stably for nearly a month. Next-gen optimization in the works. Stay tuned.**

---

## 概述 / Overview

ExperienceEngine 是一个零外部依赖的 Python 库。它在 Agent 执行任务时自动记录经验（成功/失败/日志），在下次遇到相似场景时检索匹配经验并辅助决策，减少重复错误、加速任务执行。

ExperienceEngine is a zero-dependency Python library. It automatically records experience (successes, failures, logs) as agents execute tasks, then retrieves relevant knowledge when similar scenarios arise — reducing repeated mistakes and accelerating execution.

---

## 核心机制 / Core Mechanisms

| Mechanism / 机制 | Description / 说明 |
|------|------|
| Knowledge entry management / 知识条目管理 | Register, retrieve, rate, update, deactivate / 注册、检索、评价、更新、停用 |
| Semantic search / 语义检索 | N-gram hash projection + cosine similarity / n-gram 哈希投影 + 余弦相似度 |
| Version control / 版本控制 | Auto Git commit on knowledge changes / 知识变更自动 Git 提交 |
| Adaptive threshold / 自适应阈值 | Dynamic retrieval threshold based on hit rate / 按命中率动态调整检索门槛 |
| Time decay / 时间衰减 | Unused entries gradually lose weight / 长期未使用的条目自动降权 |

---

## 三种学习模式 / Three Learning Modes

| Mode / 模式 | Description / 说明 |
|------|------|
| Failure-driven / 失败驱动 | Record error features and fixes after task failure / 任务失败后记录错误特征与修复方案 |
| Success generalization / 成功泛化 | Extract reusable patterns from successful executions / 成功执行后提炼可复用的通用模式 |
| Log capture / 日志捕获 | Auto-extract knowledge from execution logs / 从执行日志中自动提取知识 |

---

## 快速开始 / Quickstart

```python
from core import ExperienceEngine

# Initialize engine / 初始化引擎
engine = ExperienceEngine()

# Register knowledge / 注册知识条目
engine.register(
    trigger_pattern="API returns 429 status code / API 返回 429 状态码",
    recommendation="Wait for Retry-After header seconds before retrying / 等待 Retry-After 头指定的秒数后重试",
    origin="FIX"
)

# Search knowledge / 检索知识
hints = engine.search("how to handle rate limiting / 请求频率限制怎么处理", top_k=3)
for entry in hints:
    print(entry.recommendation, f"(score: {entry.quality_score:.2f})")
```

---

## 项目结构 / Project Structure

```
experience_engine/
├── core/
│   ├── __init__.py      # Package entry / 包入口
│   └── flywheel.py      # Main engine / 主引擎 (~950 lines)
├── state/
│   └── knowledge_store.json  # Knowledge storage / 知识存储
├── demo.py              # Quick demo / 入门演示
├── test_15scenes.py     # 15-scene stability test / 15 场景稳定性验证
├── stress_20scenes.py   # 20-scene stress test / 20 场景压力测试
├── INTEGRATION.md       # Integration guide / 接入指南
├── VISION.md            # Vision & roadmap / 愿景与路线
└── README.md
```

---

## 技术特点 / Technical Highlights

- Zero external dependencies (stdlib only) / 零外部依赖（标准库即可运行）
- Chinese-enhanced: built-in 200-term tech dictionary tokenizer; English via n-gram directly, no external NLP / 中文增强：内置 200 词技术词典分词器，英文由 n-gram 直接处理
- JSON file persistence with auto Git backup / JSON 文件持久化，支持 Git 自动备份
- Runtime hot-reload — new entries effective immediately / 运行时热加载，新增条目即时生效
- Pluggable into any multi-agent framework / 可作为插件接入任意多 Agent 框架

---

## 许可证 / License

Apache-2.0 License — commercial use, modification, and distribution allowed. Copyright notice must be retained.
Apache-2.0 许可 — 允许商用、修改、分发，需保留版权声明。

Copyright © 2026 吕氏链 Lvchain
