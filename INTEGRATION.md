***


# 接入指南

任何 Agent 框架只要在三个时机回调，就能挂上经验引擎。

## 三步接入

```python
from core import EnginePlugin

plugin = EnginePlugin("你的框架名")
```

### 1. 任务结束时

```python
# 你的框架执行完一个任务后：
plugin.on_task_complete(task_description, result, success=True)
```

成功时自动提取经验，失败时记录错误。返回 rule_id 或不返回。

### 2. 工具调用后

```python
# 你的框架调完一个工具后：
plugin.on_tool_result(tool_name, success)
```

自动对匹配的经验条目投票，驱动评分升降。

### 3. 遇到问题时查经验

```python
hints = plugin.suggest_actions("当前遇到的困难描述")
for hint in hints:
    print(hint["action"])  # 前人踩坑后留下的方案
```

## 实际例子

AutoGen 挂载：

```python
# 在 AutoGen 的 AssistantAgent 里加三行
class MyAgent(AssistantAgent):
    def __init__(self):
        self.engine_plugin = EnginePlugin("AutoGen")
    
    def on_message(self, msg):
        # ... 原有逻辑 ...
        result = self.execute(msg)
        self.engine_plugin.on_task_complete(msg, result)
        self.engine_plugin.on_tool_result("search", success=True)
```

LangChain 挂载：

```python
from core import EnginePlugin

plugin = EnginePlugin("LangChain")

# 在 BaseCallbackHandler 子类里：
def on_chain_end(self, outputs, **kwargs):
    plugin.on_task_complete(kwargs.get("inputs", ""), outputs)

def on_tool_end(self, output, **kwargs):
    plugin.on_tool_result(kwargs["name"], not isinstance(output, Exception))
```

CrewAI / MetaGPT / Dify 同理，找到任务完成点和工具调用点，挂三行。

## 零依赖

不需要 pip install 任何东西。拷 `core/` 目录过去，`import` 就能用。
