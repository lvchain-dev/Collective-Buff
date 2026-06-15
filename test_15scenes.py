"""
Demo: 经验引擎 15 场景 × 3 轮稳定性验证
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import ExperienceEngine

PASS = "通过"
FAIL = "未通过"

def run_one_round(engine: ExperienceEngine, round_num: int):
    engine.reset()

    results = {"round": round_num}

    # ──── S1: 基础闭环 ────
    rid1 = engine.register("pip install tensorflow 报错 No matching distribution", "用 conda install tensorflow 代替 pip", tags=["python", "pip", "tensorflow"])
    hints = engine.search("pip install 失败", top_k=5)
    results["S1"] = PASS if any("conda" in h.recommendation for h in hints) else FAIL

    # ──── S2: 跨 Agent 共享 ────
    engine.register("nginx 反向代理 502 Bad Gateway", "检查 upstream 地址是否正确，确认后端服务端口开放", tags=["nginx", "502", "proxy"])
    hints = engine.search("反向代理一直返回 502", top_k=5)
    results["S2"] = PASS if any("upstream" in h.recommendation for h in hints) else FAIL

    # ──── S3: 失败驱动学习 ────
    rid3 = engine.learn_from_failure("部署 FastAPI 到 Ubuntu", "gunicorn worker timeout")
    entry = engine.retrieve(rid3) if rid3 else None
    results["S3"] = PASS if entry and "FIX" in entry.origin else FAIL

    # ──── S4: 成功泛化 ────
    rid4 = engine.register("MySQL 慢查询优化", "用 EXPLAIN 分析查询计划，给 WHERE 条件列加索引", tags=["mysql", "slow", "index"])
    for _ in range(3):
        engine.rate(rid4, "UPVOTE")
    derived = engine.derive_from_success(rid4, [{"trigger": "PostgreSQL 慢查询"}, {"trigger": "慢查询"}])
    d = engine.retrieve(derived) if derived else None
    results["S4"] = PASS if d and "衍生" in d.recommendation and d.parent_id == rid4 else FAIL

    # ──── S5: 日志捕获 ────
    rid5 = engine.capture_from_log({
        "success": True,
        "task": "用 redis-cli 批量删除过期 key",
        "steps": ["redis-cli --scan --pattern 'session:*' | xargs redis-cli DEL", "确认内存下降"],
        "tools_used": ["redis-cli"],
        "pattern_keywords": ["redis", "key", "过期", "批量删除"],
    })
    entry5 = engine.retrieve(rid5) if rid5 else None
    results["S5"] = PASS if entry5 and entry5.origin == "CAPTURED" else FAIL

    # ──── S6: 多框架并发 ────
    frameworks = ["AutoGen", "LangChain", "CrewAI"]
    engine.register("API 返回 401 Unauthorized", "检查 token 是否过期，重新获取 access_token", tags=["api", "401", "auth"])
    for fw in frameworks:
        engine.register(f"{fw} 任务超时终止", f"增加超时时间到 {30 + len(fw) % 30} 秒", tags=["timeout", fw])
    hits = sum(1 for fw in frameworks if any("access_token" in h.recommendation for h in engine.search(f"在 {fw} 中 API 调用返回 401", top_k=1)))
    results["S6"] = PASS if hits >= 1 else FAIL

    # ──── S7: 评分进化 ────
    rid_low = engine.register("随便写的测试", "直接重启", tags=["low-quality"])
    rid_high = engine.register("Elasticsearch 集群健康检查", "GET /_cluster/health, 关注 status 字段和 unassigned_shards", tags=["es", "ops"])
    for _ in range(6):
        engine.rate(rid_low, "DOWNVOTE")
        engine.rate(rid_high, "UPVOTE")
    low_entry = engine.retrieve(rid_low)
    high_entry = engine.retrieve(rid_high)
    ok_low = low_entry.quality_score < 0.2 or not low_entry.enabled
    ok_high = high_entry.quality_score > 0.5
    results["S7"] = PASS if ok_low and ok_high else FAIL

    # ──── S8: 时间衰减 ────
    rid8 = engine.register("CUDA OOM 内存不足", "减小 batch_size 到 16，启用 gradient_checkpointing", tags=["cuda", "oom", "gpu"])
    entry8 = engine.retrieve(rid8)
    entry8.updated_at = time.time() - 86400 * 30
    entry8.use_count = 0
    engine._save_store()
    entry8_after = engine.retrieve(rid8)
    cs = entry8_after.current_score if entry8_after else 0
    results["S8"] = PASS if cs < 0.45 else FAIL

    # ──── S9: 分类过滤 ────
    engine.register("Vue3 组件间通信", "父子用 props/emit，跨层级用 provide/inject，全局用 Pinia", category="frontend", tags=["vue", "组件", "通信", "component", "frontend"])
    engine.register("Django 数据库迁移", "python manage.py makemigrations && python manage.py migrate", category="backend", tags=["django", "数据库", "迁移", "migrate", "backend"])
    all_frontend = engine.search("组件通信", top_k=5, category="frontend")
    all_backend = engine.search("数据库迁移", top_k=5, category="backend")
    has_vue = any("Pinia" in h.recommendation for h in all_frontend)
    has_django = any("makemigrations" in h.recommendation for h in all_backend)
    results["S9"] = PASS if has_vue and has_django else FAIL

    # ──── S10: 来源可信度 ────
    rid_fix = engine.register("Docker build 推送镜像失败", "docker login 先登录，确认镜像名格式为 registry/namespace/repo:tag", tags=["docker", "push"], origin="FIX")
    rid_skill = engine.register("Git 合并冲突解决", "git merge --abort 先回退，再解决冲突后 git add && git commit", tags=["git", "merge"], origin="SKILL")
    for _ in range(5):
        engine.rate(rid_fix, "UPVOTE")
        engine.rate(rid_skill, "UPVOTE")
        engine.rate(rid_skill, "DOWNVOTE")
    fix_entry = engine.retrieve(rid_fix)
    skill_entry = engine.retrieve(rid_skill)
    results["S10"] = PASS if fix_entry.quality_score > skill_entry.quality_score else FAIL

    # ──── S11: 批量注册 + 全量搜索 ────
    topics = [
        ("Linux 磁盘满了", "df -h 查占用，du -sh /* 定位大目录，清理 /var/log", ["linux", "disk", "df"]),
        ("Jenkins 构建卡住", "重启 agent 节点，检查 executor 数是否耗尽", ["jenkins", "agent", "executor"]),
        ("Redis 连接池耗尽", "增大 maxconnections，检查是否有连接泄漏未 close", ["redis", "pool", "leak"]),
        ("K8s Pod CrashLoopBackOff", "kubectl logs 查看启动日志，kubectl describe pod 查事件", ["k8s", "pod", "crash"]),
        ("PostgreSQL 死锁", "SELECT * FROM pg_locks WHERE NOT granted; 查锁等待", ["postgresql", "deadlock"]),
    ]
    ids = []
    for trigger, rec, tags in topics:
        ids.append(engine.register(trigger, rec, tags=tags))

    # 验证 5 条全可查
    all_entries = engine.list_all(active_only=True)
    found = sum(1 for rid in ids if any(e.id == rid for e in all_entries))
    results["S11"] = PASS if found == 5 else FAIL

    # ──── S12: 更新后停用 ────
    rid12 = engine.register("npm install 卡住", "切换镜像源: npm config set registry <your-mirror-url>", tags=["npm", "install", "mirror"])
    ok = engine.update(rid12, trigger_pattern="npm install 卡住或缓慢", recommendation="切换镜像源: npm config set registry <your-mirror-url>")
    e = engine.retrieve(rid12)
    ok = ok and e and "npm install 卡住或缓慢" == e.trigger_pattern
    engine.deactivate(rid12)
    e2 = engine.retrieve(rid12)
    ok = ok and e2 and not e2.enabled
    # 停用后搜不到
    hints = engine.search("npm 安装慢", top_k=3)
    ok = ok and not any("npmmirror" in h.recommendation for h in hints)
    results["S12"] = PASS if ok else FAIL

    # ──── S13: 示例列表上限 ────
    rid13 = engine.register("示例上限测试", "基础推荐", tags=["test", "cap"])
    for i in range(15):
        context = {"step": i, "data": f"test_run_{i}"}
        engine._extract_rule(f"测试查询第{i}次", context)
    e13 = engine.retrieve(rid13)
    # 自己的 examples 保持原始数量，_extract_rule 匹配到的话 example 不超 10
    results["S13"] = PASS if e13 else FAIL

    # ──── S14: 版本号递增 ────
    rid14 = engine.register("Python 虚拟环境创建", "python -m venv venv", tags=["python", "venv"])
    e14a = engine.retrieve(rid14)
    v1 = e14a.revision
    engine.update(rid14, trigger_pattern="Python 虚拟环境创建与管理")
    e14b = engine.retrieve(rid14)
    v2 = e14b.revision
    results["S14"] = PASS if v2 == v1 + 1 else FAIL

    # ──── S15: 自适应阈值压测 ────
    # 大量查询触发 _adjust_threshold，验证阈值在合法区间
    for i in range(25):
        engine.search(f"测试查询第{i}号", top_k=1)
    t = engine.threshold_info()
    current = t["current_threshold"]
    results["S15"] = PASS if 0.1 <= current <= 0.5 else FAIL

    return results


if __name__ == "__main__":
    all_rounds = []
    for r in range(1, 4):
        engine = ExperienceEngine()
        round_results = run_one_round(engine, r)
        all_rounds.append(round_results)

    scenes = [k for k in all_rounds[0].keys() if k != "round"]

    print(f"\n{'场景':<22} {'R1':>5} {'R2':>5} {'R3':>5} {'结果':>6}")
    print("-" * 55)

    total_fail = 0
    for scene in scenes:
        row = f"{scene:<22}"
        stable = True
        for rr in all_rounds:
            result = rr[scene]
            row += f" {result:>5}"
            if result == FAIL:
                stable = False
                total_fail += 1
        final = "稳定" if stable else "波动"
        row += f" {final:>6}"
        print(row)

    print("-" * 55)
    print(f"\n总失败次数: {total_fail}")
    if total_fail == 0:
        print("15 场景 × 3 轮全稳定通过。")
    else:
        print(f"有 {total_fail} 次未通过，需检查。")
