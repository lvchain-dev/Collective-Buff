# Collective-Buff：给多 Agent 框架装上"经验引擎" / Give Your Multi-Agent Framework a Memory

> **30 秒接入。零依赖。挂上自动变强。**
> **30-second integration. Zero dependencies. Mount it and watch your agents get smarter.**
>
> **稳定运行近一个月的成熟方案。下一代优化研发中，敬请期待。**
> **Battle-tested for nearly a month. Next-gen optimization in the works. Stay tuned.**

---

## 它能做什么 / What It Does

你的 Agent 框架本来不会"长记性"——每次任务从零开始，昨天踩的坑今天再踩一遍，Agent A 翻过的车 Agent B 接着翻。

Collective-Buff 是一个插件，挂上去之后：

| 原来 / Before | 挂上后 / After |
|------|------|
| Agent 踩坑 → 重试 → 再踩 | 踩坑自动记，下次先查经验再动手 |
| Agent 之间互不知道对方踩的坑 | 一个 Agent 翻车，全场秒学 |
| 新 Agent 白纸一张 | 老 Agent 攒的经验直接喂，上场就是老手 |
| 代码失败就盲重试 | 失败原因 + 修复方案自动入库 |

用大白话说：**让你的 Agent 像老工程师带新人一样，越用越强。**

---

## 30 秒上手 / 30-Second Quickstart

```
拷文件夹 → 加 4 行代码 → 完。
Copy the folder → Add 4 lines → Done.
```

```python
from core import EnginePlugin

plugin = EnginePlugin("YourFramework")

# Agent 完成任务时 / When your agent finishes a task
plugin.on_task_complete("task description", result)

# Agent 调用工具时 / When your agent calls a tool
plugin.on_tool_result("tool_name", success=True)

# Agent 遇到困难时 / When your agent hits a problem
hints = plugin.suggest_actions("describe the problem")
```

不需要 pip install，不需要配置文件，不需要数据库。纯 Python 标准库。

---

## 三个挂载点，强化全局 / Three Hooks, Global Boost

很多人以为三个挂载点是三个独立功能。不是——它们是三个"接入点"，接的是 Agent 框架的**主水管**。挂上之后，平台所有功能全部受益：

1. **`on_task_complete`** — 任务完成时自动记录：成功泛化模式、失败自动学教训
2. **`on_tool_result`** — 工具调用时自动投票：好的经验上浮，差的下沉
3. **`suggest_actions`** — 遇到问题时查前人经验，返回解决建议

引擎内部自动做 8 件事：失败学习、成功泛化、日志捕获、语义检索、自适应阈值、时间衰减、来源可信度、Git 自动备份。

---

## 实战验证 / Proven in Practice

**20 场景 × 3 轮压力测试全绿通过**：精确闭环、语义跨越、失败即时学习、泛化链、多框架并发、评分分化、时间衰减、百条批量、停用闭环、上限安全、版本递增、阈值自调整、空值安全、快速恢复、排名稳定、响应耗时、Git 同步——无一失败。

**AutoGen 实战拆解** → [CASE_STUDY.md](CASE_STUDY.md)

---

## 核心机制 / Core Mechanisms

| 机制 / Mechanism | 说明 / Description |
|------|------|
| 失败驱动 / Failure-driven | 任务失败后自动记录错误特征与修复方案 |
| 成功泛化 / Success generalization | 从已验证方案中自动衍生变体 |
| 日志捕获 / Log capture | 从执行日志中自动提取可复用知识 |
| 语义检索 / Semantic search | N-gram 哈希投影 + 余弦相似度（零外部 NLP 依赖） |
| 自适应阈值 / Adaptive threshold | 按历史命中率动态调整检索门槛 |
| 时间衰减 / Time decay | 长期未用条目自动降权 |
| Git 版本控制 / Git version control | 知识变更自动提交，支持团队共享 |

---

## 快速开始 / Quickstart

```python
from core import ExperienceEngine

engine = ExperienceEngine()

# 注册经验 / Register knowledge
engine.register(
    "API returns 429 status code / API 返回 429 状态码",
    "Wait for Retry-After header seconds before retrying / 等待 Retry-After 头指定的秒数后重试",
    origin="FIX"
)

# 检索经验 / Search knowledge
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
│   └── flywheel.py      # Main engine / 主引擎
├── state/
│   └── knowledge_store.json  # Knowledge storage / 知识存储
├── demo.py              # Quick demo / 入门演示
├── test_15scenes.py     # 15-scene stability test / 15 场景稳定性验证
├── stress_20scenes.py   # 20-scene stress test / 20 场景压力测试
├── INTEGRATION.md       # Integration guide / 接入指南
├── VISION.md            # Vision & roadmap / 愿景与路线
├── CASE_STUDY.md        # AutoGen 实战拆解 / AutoGen case study
└── README.md
```

---

## 技术特点 / Technical Highlights

- **零外部依赖** — 纯 Python 标准库，不需要 pip install 任何东西
- **中文增强** — 内置 200 词技术词典分词器；英文由 n-gram 直接处理，不依赖外部 NLP 库
- **JSON 持久化 + Git 自动备份** — 知识变更自动提交，团队可共享经验库
- **运行时热加载** — 新增条目即时生效，无需重启
- **任意多 Agent 框架可接入** — 三个回调，通用接口，不绑死任何框架

---

## 许可证 / License

Apache-2.0 License — commercial use, modification, and distribution allowed. Copyright notice must be retained.
Apache-2.0 许可 — 允许商用、修改、分发，需保留版权声明。

Copyright © 2026 吕氏链 Lvchain
