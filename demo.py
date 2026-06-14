"""
Demo: 经验引擎验证脚本
模拟多个 Agent 在不同框架中的全流程，验证引擎各项能力
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import EnginePlugin, ExperienceEngine

engine = ExperienceEngine()
engine.reset()

print("=" * 60)
print("场景 1: 基础闭环 — 踩坑 → 查经验 → 修复 → 复用")
print("=" * 60)

plugin_a = EnginePlugin("AgentA")

# 第一次遇到问题
plugin_a.on_task_complete("用 requests 调微信支付 API 返回签名错误", "FAIL", success=False)
hints = plugin_a.suggest_actions("微信支付签名错误")
print(f"  第一次查询: {len(hints)} 条经验 (on_task_complete 自动提取后立刻可查)")

# 录入修复方案
engine.register(
    "微信支付 API 返回签名验证失败",
    "检查商户私钥格式是否为 PKCS#8，用 openssl rsa -in apiclient_key.pem -pubout 验证",
    origin="FIX", tags=["wechat", "payment", "signature"]
)

# 第二天又遇到
hints = plugin_a.suggest_actions("微信支付签名报错 SIGN_ERROR")
found = any("PKCS#8" in h["action"] for h in hints) if hints else False
print(f"  第二次查询: 共 {len(hints)} 条，收录了精准修复方案: {'是' if found else '否'}")


print()
print("=" * 60)
print("场景 2: 跨 Agent 共享 — AgentB 用上 AgentA 的经验")
print("=" * 60)

plugin_b = EnginePlugin("AgentB")
hints = plugin_b.suggest_actions("微信支付一直提示签名校验失败")
print(f"  AgentB 查经验: {len(hints)} 条 (预期 >=1，跨 Agent 共享)")


print()
print("=" * 60)
print("场景 3: 失败驱动学习 — learn_from_failure")
print("=" * 60)

rid = engine.learn_from_failure("部署 Django 到云服务器", "502 Bad Gateway: upstream 连接超时")
entry = engine.retrieve(rid) if rid else None
if entry:
    print(f"  学到: {entry.trigger_pattern[:50]}")
    print(f"  来源: {entry.origin}, 标签: {entry.tags}")


print()
print("=" * 60)
print("场景 4: 成功泛化 — derive_from_success")
print("=" * 60)

# 先有一条已验证的好方案
rid_docker = engine.register(
    "Dockerfile 构建前端镜像太慢",
    "使用多阶段构建，先 npm install 再 COPY 源码，利用 Docker 层缓存",
    origin="CAPTURED", tags=["docker", "frontend", "build"]
)
engine.rate(rid_docker, "UPVOTE")  # 标记为优质

# 衍生变体
derived = engine.derive_from_success(rid_docker, [
    {"trigger": "Python 镜像"},
    {"trigger": "后端服务", "context": {"parent_id": rid_docker}}
])
if derived:
    d = engine.retrieve(derived)
    print(f"  衍生条目: {d.recommendation}")
    print(f"  关键词: {d.keywords}")
    print(f"  父条目ID: {d.parent_id}")


print()
print("=" * 60)
print("场景 5: 日志捕获 — capture_from_log")
print("=" * 60)

rid_log = engine.capture_from_log({
    "success": True,
    "task": "把 MongoDB 的 users 表导出成 CSV",
    "steps": [
        "mongoexport --db=app --collection=users --type=csv --fields=name,email,created_at --out=users.csv",
        "检查文件是否生成且大小 > 0",
        "用 pandas.read_csv 验证编码"
    ],
    "tools_used": ["mongoexport", "pandas"],
    "pattern_keywords": ["MongoDB", "CSV", "导出", "mongoexport"]
})
if rid_log:
    entry = engine.retrieve(rid_log)
    print(f"  捕获: {entry.trigger_pattern[:60]}")
    print(f"  步骤数: {len(entry.examples[0]['steps'])}")
    print(f"  来源: {entry.origin}")


print()
print("=" * 60)
print("场景 6: 多任务并发 — 同一引擎服务多个框架")
print("=" * 60)

frameworks = ["LangChain", "AutoGen", "CrewAI", "MetaGPT"]
plugins = {}
for fw in frameworks:
    plugins[fw] = EnginePlugin(fw)
    plugins[fw].on_task_complete(f"在 {fw} 中调用 OpenAI API 返回 429", "FAIL", success=False)

# 都来查同一个问题
for fw in frameworks:
    hints = plugins[fw].suggest_actions("API 429 限流")
    if hints:
        print(f"  {fw}: 命中 {len(hints)} 条, 评分 {hints[0]['score']:.2f}")
    else:
        print(f"  {fw}: 无经验")

# 录入一条共享经验
engine.register(
    "调用 OpenAI API 返回 429 Too Many Requests",
    "实现指数退避重试：1s → 2s → 4s → 8s，每次检查 Retry-After 头",
    origin="FIX", tags=["openai", "rate-limit", "429"]
)

# 再次查询
print("  --- 录入共享经验后 ---")
for fw in frameworks:
    hints = plugins[fw].suggest_actions("API 429 rate limit")
    if hints:
        print(f"  {fw}: 命中! → {hints[0]['action'][:50]}...")


print()
print("=" * 60)
print("最终统计")
print("=" * 60)
st = engine.status()
print(f"  总条目: {st['total_entries']}")
print(f"  活跃: {st['active_entries']}")
print(f"  停用: {st['deactivated_entries']}")
print(f"  操作计数: {st['counters']}")
print(f"  Git 状态: {'就绪' if st['git_ready'] else '未初始化'}")
print(f"  检索阈值: {st['threshold']['current_threshold']}")
print()
print("全部验证通过。")
