# Collective-Buff

> LLM Agent 经验引擎 —— 让 Agent 拥有可积累、可演化的集体经验。
> A lightweight experience engine for LLM agents — learn, evolve, and share.

---

## 项目故事 / Project Story

**中文**

本文分享的方案，我已在自己项目中稳定运行近一个月，经过多轮打磨验证。目前我正在着手下一步优化——让经验在多场景下的化学反应更加剧烈，敬请期待。

我在开发自己的多 Agent 平台时，发现一个反复出现的痛点：Agent 总是犯同样的错误，成功的经验也无法在任务之间传递。每个任务都像第一次面对这个世界。

于是我自己写了一套经验引擎来解决这个问题——让 Agent 踩过的坑自动记住，成功的经验自动泛化，经验随时间自然衰减而非永久固化。

后来刷抖音、逛技术网站时发现，原来大家都在被同样的问题困扰。我就把这部分从自己的平台里提取出来，独立成项目，又经过几轮 bug 修复和压力测试打磨，现在放到了 GitHub 上。

**English**

The solution shared here has been running stably in my own project for nearly a month, refined through multiple rounds of testing. Meanwhile, I'm working on the next iteration — to make the chemical reaction of experience even more powerful across scenarios. Stay tuned.

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

| Version / 版本 | What happened / 内容 |
|------|------|
| v0.1 | Core formed: register/retrieve/search/rate + semantic matching + JSON persistence / 内核成型：注册/检索/追溯/评分 + 语义匹配 + JSON 持久化 |
| v0.2 | Knowledge evolution: failure learning / success generalization / log capture / time decay / source credibility / 经验演化：失败学习/成功泛化/日志捕获/时间衰减/来源可信度 |
| v0.3 | Engineering hardening: 15 scenes × 3 rounds all passed, 6 kernel bugs fixed, integration docs / 工程加固：15 场景×3 轮全通过，修复 6 项内核 bug，接入文档完善 |
| v0.4 | High-bar stress test: 20 scenes × 3 rounds all passed (null safety, fast recovery, ranking stability, response <50ms, Git sync) / 高标测试：20 场景×3 轮全通过 |
| v0.5 | Open-source prep: Apache 2.0 license, 3 rounds of originality audit, zero external traces / 开源准备：Apache 2.0 许可，三轮原创性审计，零外部影子 |

---

## 未来规划 / Roadmap

| Phase / 阶段 | Goal / 目标 |
|------|------|
| v0.6 | Multi-framework field test (LangChain + AutoGen end-to-end demo, performance benchmarks) / 多框架实战验证 |
| v0.7 | Storage backend expansion (SQLite / Redis) / 存储后端扩展 |
| v1.0 | PyPI release + full API docs + CI/CD / PyPI 发布 + 完整 API 文档 |
| Future / 远期 | LLM quality scoring / conflict resolution / federated sharing / vector search / LLM 评估 / 冲突消解 / 联邦共享 / 向量检索 |

---

## 项目结构 / Project Structure

```
core/
  __init__.py          — Module entry / 模块入口
  flywheel.py          — Engine kernel (~950 lines) / 经验引擎内核
state/
  knowledge_store.json — Knowledge storage / 经验知识存储
demo.py                — Quick demo / 入门演示
test_15scenes.py       — 15-scene stability test / 15 场景稳定性验证
stress_20scenes.py     — 20-scene stress test / 20 场景压力测试
INTEGRATION.md         — Integration guide / 接入文档
VISION.md              — This file / 本文件
```

---

## 许可证 / License

Apache License 2.0
