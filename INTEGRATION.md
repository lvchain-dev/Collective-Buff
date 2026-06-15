# 接入指南 / Integration Guide

## 30 秒上手 / 30-Second Quickstart

**第一步：把 `core/` 文件夹拷到你项目里。**

```
your_project/
  core/          ← 拷过去
  your_code.py
```

**第二步：在你代码里加 4 行。**

```python
from core import EnginePlugin

plugin = EnginePlugin("你的框架名")

# 你的 Agent 执行完任务时
plugin.on_task_complete("任务描述", result)

# 你的 Agent 调完工具时
plugin.on_tool_result("工具名", success=True)

# 你的 Agent 遇到困难时，查前人经验
hints = plugin.suggest_actions("我遇到什么问题")
```

**完。不需要 pip install，不需要配置文件，不需要数据库。**

---

## 三个挂载点 / Three Hooks

| 时机 | 方法 | 作用 |
|------|------|------|
| 任务完成 | `on_task_complete(desc, result)` | 自动记住成功经验、记录失败教训 |
| 工具调用 | `on_tool_result(tool, success)` | 给相关经验投票，好经验上浮、差经验下沉 |
| 遇到问题 | `suggest_actions(problem)` | 查前人经验，返回解决建议列表 |

---

## 框架示例 / Framework Examples

### AutoGen

```python
from core import EnginePlugin

class MyAgent(AssistantAgent):
    def __init__(self):
        super().__init__()
        self.exp = EnginePlugin("AutoGen")

    def on_message(self, msg):
        result = self.execute(msg)
        self.exp.on_task_complete(msg, result)
```

### LangChain

```python
from core import EnginePlugin

plugin = EnginePlugin("LangChain")

class ExpCallback(BaseCallbackHandler):
    def on_chain_end(self, outputs, **kwargs):
        plugin.on_task_complete(str(kwargs.get("inputs", "")), outputs)
    def on_tool_end(self, output, **kwargs):
        plugin.on_tool_result(kwargs["name"], not isinstance(output, Exception))
```

### CrewAI / MetaGPT / Dify

同理——找到你框架里"任务完成"和"工具调用"两个时机，各加一行即可。

---

## 零依赖 / Zero Dependencies

- 不需要 `pip install`
- 不需要数据库
- 不需要配置文件
- 不需要改你现有代码结构
- 拷 `core/` 过去，`import` 就能用
