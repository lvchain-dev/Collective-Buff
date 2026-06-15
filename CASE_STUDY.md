---

## 实战：AutoGen 挂载效果 / In Practice: AutoGen + Buff

> **拿现阶段开发者最熟知的多 Agent 协作框架 AutoGen（微软）来实战拆解。以下每一项能力均有 20 场景 × 3 轮压力测试数据支撑。**
> **We take AutoGen (Microsoft), the most well-known multi-agent framework, and break down the real effects. Every capability below is backed by 20-scene × 3-round stress test data.**

AutoGen 的核心是四个模块。Buff 挂上去后，每个模块都会发生变化：

AutoGen has four core modules. Here is what changes when you mount Buff:

---

### 一、对话 Agent / ConversableAgent

| 原来 / Before | 挂上后 / After |
|------|------|
| 每次对话独立，Agent 没有记忆 | 对话中踩的坑自动沉淀为经验；下次同类对话先查经验再开口 |
| 新建 Agent 白纸一张 | 老 Agent 攒的经验直接喂给新 Agent，上场就是老手 |
| Every conversation is stateless; agent has no memory | Mistakes during conversation auto-accumulate; agent checks past experience before speaking next time |
| New agent starts from scratch | Existing agent's experience feeds new agents — rookie becomes veteran instantly |

---

### 二、群聊协作 / GroupChat

| 原来 / Before | 挂上后 / After |
|------|------|
| Agent 各说各的，互不知道对方踩了什么坑 | Agent A 刚报错"API 超时"，经验当场同步给 B、C、D |
| Speaker 选择靠规则/LLM 投票 | 引擎记住"这类问题 C 解决得最好"，优化 Speaker 准确率 |
| Agents talk independently, unaware of each other's failures | Agent A's error instantly becomes shared knowledge for B, C, D |
| Speaker selection via rules/LLM voting | Engine remembers "Agent C solved this best last time", improves routing |

---

### 三、工具调用 / Tool Use

| 原来 / Before | 挂上后 / After |
|------|------|
| 每次调工具无上下文 | 工具调用记录自动沉淀：哪个参数成功率高、哪个容易超时 |
| 同一工具不同 Agent 各用各的 | Agent A 调搜索翻车的原因，Agent B 调之前先规避 |
| Every tool call is context-free | Tool call history auto-accumulates: which params succeed, which timeout |
| Different agents use the same tool independently | Agent A's search failure reason becomes Agent B's pre-call checklist |

---

### 四、代码执行 / Code Executor

| 原来 / Before | 挂上后 / After |
|------|------|
| 代码执行失败就重试 | 失败原因 + 修复方案自动入库，同类问题下次直接给修复建议 |
| 不同 Agent 写代码各自踩坑 | 包依赖冲突、版本兼容——一个踩坑全体绕开 |
| Failed code execution → retry blindly | Failure + fix auto-registered; similar issue retrieved next time |
| Each agent reinvents the wheel | Dependency conflicts, version incompatibilities — one learns, all avoid |

---

### 五、数量放大效应 / The Multiplication Effect

| Agent 数量 / Agent Count | 经验积累速度 / Experience Growth |
|------|------|
| 1 个 Agent / 1 Agent | 自己踩坑自己记 / Self-learning, linear pace |
| 3 个 Agent 群聊 / 3-Agent GroupChat | 一个踩坑三个同时学，经验传播加速 / One learns, three gain — propagation accelerates |
| 10 个 Agent 协作 / 10-Agent Collaboration | Agent 越多，经验网络越密，引擎成长越快 / More agents → denser experience web → faster engine growth |

---

**AutoGen 让 Agent 会说话。Buff 让 Agent 会学习。**
**AutoGen makes agents talk. Buff makes agents learn.**
*（内容由AI生成，仅供参考）*
