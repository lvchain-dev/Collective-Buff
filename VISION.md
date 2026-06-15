# Collective-Buff

> LLM Agent 经验引擎 —— 让 Agent 拥有可积累、可演化的集体经验。
> A lightweight experience engine for LLM agents — learn, evolve, and share.

---

## 项目故事 / Project Story

**中文**

我在开发自己的多 Agent 平台时，发现一个反复出现的痛点：Agent 总是犯同样的错误，成功的经验也无法在任务之间传递。每个任务都像第一次面对这个世界。

于是我自己写了一套经验引擎来解决这个问题——让 Agent 踩过的坑自动记住，成功的经验自动泛化，经验随时间自然衰减而非永久固化。

后来刷抖音、逛技术网站时发现，原来大家都在被同样的问题困扰。我就把这部分从自己的平台里提取出来，独立成项目，又经过几轮 bug 修复和压力测试打磨，现在放到了 GitHub 上。

**English**

While building my own multi-agent platform, I kept hitting the same pain point: agents repeat the same mistakes, and successful experience never transfers across tasks. Every task felt like starting from scratch.

So I built an experience engine to solve it — agents remember failures, generalize successes, and let knowledge decay naturally over time instead of staying frozen.

Later, browsing through Douyin and tech forums, I realized many others were struggling with the exact same problem. I extracted this component from my platform, polished it through several rounds of bug fixes and stress testing, and here it is on GitHub.

---

## 项目愿景 / Vision

**让 Agent 像有经验的工程师一样思考。**

一个 Agent 踩过的坑，所有 Agent 都能绕开；一条经验反复验证后自动强化，长期不用则自然衰减。框架无关，三个回调即可挂载到 LangChain、AutoGen、CrewAI 等任意 Agent 框架。

**Let agents think like experienced engineers.**

A pitfall learned by one agent is avoided by all. Verified experience strengthens automatically; unused knowledge fades naturally. Framework-agnostic — mount to any agent framework (LangChain, AutoGen, CrewAI, etc.) with just three callbacks.

---

## 核心设计 / Core Design

| 原则 / Principle | 说明 / Description |
|------|------|
| 框架无关 / Framework-Agnostic | 三个回调函数挂载，不侵入核心逻辑 |
| 经验演化 / Living Knowledge | 评分进化、时间衰减、成功泛化——经验是活的 |
| 集合智慧 / Collective Wisdom | 跨 Agent、跨任务共享经验 |
| 零依赖 / Zero Dependencies | 纯 Python 标准库 + JSON 文件，即插即用 |

---

## 迭代历程 / Development Journey

| 版本 | 内容 |
|------|------|
| v0.1 | 内核成型：注册/检索/追溯/评分 + 语义匹配 + JSON 持久化 |
| v0.2 | 经验演化：失败学习/成功泛化/日志捕获/时间衰减/来源可信度 |
| v0.3 | 工程加固：15 场景×3 轮全通过，修复 6 项内核 bug，接入文档完善 |
| v0.4 | 高标测试：20 场景×3 轮全通过（空值安全/快速恢复/排名稳定/响应耗时/Git 同步） |
| v0.5 | 开源准备：Apache 2.0 许可，三轮原创性审计，零外部影子 |

---

## 未来规划 / Roadmap

| 阶段 | 目标 |
|------|------|
| v0.6 | 多框架实战验证（LangChain + AutoGen 端到端 demo，性能基准数据） |
| v0.7 | 存储后端扩展（SQLite / Redis） |
| v1.0 | PyPI 发布 + 完整 API 文档 + CI/CD |
| 远期 | LLM 经验质量评估 / 冲突消解 / 联邦经验共享 / 向量化检索 |

---

## 项目结构 / Project Structure

```
core/
  __init__.py          — 模块入口
  flywheel.py          — 经验引擎内核 (~950 行)
state/
  knowledge_store.json — 经验知识存储
demo.py                — 入门演示
test_15scenes.py       — 15 场景稳定性验证
stress_20scenes.py     — 20 场景高标压力测试
INTEGRATION.md         — 接入文档
VISION.md              — 本文件
```

---

## 许可证 / License

Apache License 2.0
