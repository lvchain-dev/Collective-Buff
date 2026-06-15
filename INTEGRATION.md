# 接入指南 / Integration Guide

---

## 30 秒上手 / 30-Second Quickstart

**Step 1: Copy the `core/` folder into your project.**
**第一步：把 `core/` 文件夹拷到你项目里。**

```
your_project/
  core/          ← copy this folder / 拷这个文件夹
  your_code.py
```

**Step 2: Add 4 lines to your code.**
**第二步：在你代码里加 4 行。**

```python
from core import EnginePlugin

plugin = EnginePlugin("YourFramework")

# When your agent finishes a task / Agent 完成任务时
plugin.on_task_complete("task description", result)

# When your agent calls a tool / Agent 调用工具时
plugin.on_tool_result("tool_name", success=True)

# When your agent hits a problem / Agent 遇到困难时
hints = plugin.suggest_actions("describe the problem")
```

**That's it. No pip install, no config file, no database.**
**完。不需要 pip install，不需要配置文件，不需要数据库。**

---

## 三个挂载点 / Three Hooks

| When / 时机 | Method / 方法 | What it does / 作用 |
|------|------|------|
| Task complete / 任务完成 | `on_task_complete(desc, result)` | Auto-remembers successes, logs failures / 自动记住成功经验、记录失败教训 |
| Tool called / 工具调用 | `on_tool_result(tool, success)` | Votes on relevant experience, good rises, bad sinks / 给相关经验投票，好上浮、差下沉 |
| Problem encountered / 遇到问题 | `suggest_actions(problem)` | Searches past experience, returns suggestions / 查前人经验，返回解决建议 |

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

Same pattern — find where your framework signals "task done" and "tool called", add one line at each.
同理——找到你框架里"任务完成"和"工具调用"两个时机，各加一行即可。

---

## 零依赖 / Zero Dependencies

| No need for / 不需要 | Why / 原因 |
|------|------|
| `pip install` | Pure Python stdlib / 纯标准库 |
| Database / 数据库 | JSON file auto-managed / JSON 文件自动管理 |
| Config file / 配置文件 | Sensible defaults, zero config / 开箱即用 |
| Code restructuring / 改代码结构 | Drop-in, no changes to existing code / 直接挂载 |
