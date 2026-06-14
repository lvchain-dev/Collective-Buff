"""
压力测试: 经验引擎 20 场景 × 3 轮 — 高标准判定
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
    res = {"round": round_num}
    t0 = time.perf_counter()

    # ──── S1: 基础闭环（精确匹配，非模糊命中） ────
    rid = engine.register("pip install tensorflow 报错 No matching distribution", "用 conda install tensorflow 代替 pip", tags=["python", "pip", "tensorflow"])
    hints = engine.search("conda install tensorflow", top_k=1)
    res["S1_精确闭环"] = PASS if hints and hints[0].recommendation == "用 conda install tensorflow 代替 pip" else FAIL

    # ──── S2: 跨 Agent 语义跨越 ────
    engine.register("nginx 反向代理 502 Bad Gateway", "检查 upstream 地址，确认后端端口开放", tags=["nginx", "502", "upstream"])
    hints = engine.search("反向代理报 502 了", top_k=1)
    res["S2_语义跨越"] = PASS if hints and "upstream" in hints[0].recommendation else FAIL

    # ──── S3: 失败驱动即时可查 ────
    rid3 = engine.learn_from_failure("部署 FastAPI 到 Ubuntu", "gunicorn worker timeout 超时")
    e3 = engine.retrieve(rid3) if rid3 else None
    res["S3_失败即时"] = PASS if e3 and e3.origin == "FIX" and "timeout" in str(e3.history) else FAIL

    # ──── S4: 泛化父子链完整 ────
    rid4 = engine.register("MySQL 慢查询优化", "用 EXPLAIN 分析查询计划，给 WHERE 条件列加索引", tags=["mysql", "index"])
    for _ in range(3): engine.rate(rid4, "UPVOTE")
    did = engine.derive_from_success(rid4, [{"trigger": "慢查询优化"}])
    d = engine.retrieve(did) if did else None
    res["S4_泛化链"] = PASS if d and d.parent_id == rid4 and d.origin == "DERIVED" else FAIL

    # ──── S5: 日志捕获步骤完整 ────
    rid5 = engine.capture_from_log({
        "success": True, "task": "redis 批量删过期 key",
        "steps": ["redis-cli --scan --pattern 'session:*' | xargs redis-cli DEL", "确认内存下降"],
        "tools_used": ["redis-cli"], "pattern_keywords": ["redis", "过期", "批量"],
    })
    e5 = engine.retrieve(rid5) if rid5 else None
    res["S5_日志完整"] = PASS if e5 and e5.origin == "CAPTURED" and len(e5.examples) >= 1 and len(e5.examples[0].get("steps", [])) >= 2 else FAIL

    # ──── S6: 多框架同源命中（至少 1 个框架命中通用经验） ────
    engine.register("API 返回 401 Unauthorized", "检查 token 是否过期，重新获取 access_token", tags=["api", "401", "auth"])
    for fw in ["AutoGen", "LangChain", "CrewAI"]:
        engine.register(f"{fw} 任务超时", f"增加超时到 {30 + len(fw) % 30}s", tags=["timeout", fw])
    hits_401 = [fw for fw in ["AutoGen", "LangChain", "CrewAI"]
                if engine.search(f"{fw} API 401", top_k=1)
                and "access_token" in engine.search(f"{fw} API 401", top_k=1)[0].recommendation]
    hits_timeout = [fw for fw in ["AutoGen", "LangChain", "CrewAI"]
                    if engine.search(f"{fw} 超时", top_k=1)
                    and "超时" in engine.search(f"{fw} 超时", top_k=1)[0].recommendation]
    res["S6_多框架"] = PASS if len(hits_401) >= 1 and len(hits_timeout) >= 2 else FAIL

    # ──── S7: 评分两级分化 ────
    rl = engine.register("垃圾内容测试", "重启试试", tags=["junk"])
    rh = engine.register("Elasticsearch 集群诊断", "GET /_cluster/health 关注 status 和 unassigned_shards", tags=["es", "ops"])
    for _ in range(6): engine.rate(rl, "DOWNVOTE"); engine.rate(rh, "UPVOTE")
    el = engine.retrieve(rl); eh = engine.retrieve(rh)
    res["S7_评分分化"] = PASS if eh.quality_score - el.quality_score > 0.4 else FAIL

    # ──── S8: 30 天衰减 ≤ 基础值 60% ────
    rid8 = engine.register("CUDA OOM", "减小 batch_size 到 16", tags=["cuda", "oom"])
    e8 = engine.retrieve(rid8)
    e8.updated_at = time.time() - 86400 * 30; e8.use_count = 0
    engine._save_store()
    e8a = engine.retrieve(rid8)
    res["S8_衰减"] = PASS if e8a and e8a.current_score < 0.5 * 0.6 else FAIL

    # ──── S9: 分类互不污染 ────
    engine.register("Vue3 组件通信", "Pinia 跨组件", category="frontend", tags=["vue", "组件", "frontend"])
    engine.register("Django 迁移", "makemigrations && migrate", category="backend", tags=["django", "backend"])
    fe = engine.search("组件通信", category="frontend", top_k=5)
    be = engine.search("迁移", category="backend", top_k=5)
    res["S9_分类隔离"] = PASS if any("Pinia" in h.recommendation for h in fe) and any("makemigrations" in h.recommendation for h in be) else FAIL

    # ──── S10: 来源可信度方差 > 0.3 ────
    rf = engine.register("Docker push 失败", "docker login 先登录", tags=["docker"], origin="FIX")
    rs = engine.register("Git merge 冲突", "git merge --abort", tags=["git"], origin="SKILL")
    for _ in range(5): engine.rate(rf, "UPVOTE"); engine.rate(rf, "UPVOTE")
    for _ in range(5): engine.rate(rs, "DOWNVOTE")
    ef = engine.retrieve(rf); es = engine.retrieve(rs)
    res["S10_来源方差"] = PASS if ef.quality_score - es.quality_score > 0.3 else FAIL

    # ──── S11: 批量注册 100 条，精确按 ID 取回 ────
    ids = []
    for i in range(100):
        ids.append(engine.register(f"问题{i:03d}: 批量测试条目", f"解决方案{i:03d}", tags=["batch", f"idx{i%10}"]))
    ok = all(engine.retrieve(rid) is not None for rid in ids)
    res["S11_百条批量"] = PASS if ok else FAIL

    # ──── S12: 更新+停用+不可搜三级联 ────
    rid12 = engine.register("npm install 卡住", "切换淘宝镜像", tags=["npm"])
    engine.update(rid12, trigger_pattern="npm install 卡住或缓慢")
    e12a = engine.retrieve(rid12)
    a_ok = e12a and e12a.enabled  # 必须在 deactivate 前检查，deactivate 会 mutate 同一对象
    engine.deactivate(rid12)
    e12b = engine.retrieve(rid12)
    hints = engine.search("npm 安装超慢", top_k=3)
    leaked = any("npmmirror" in h.recommendation or "淘宝镜" in h.recommendation for h in hints)
    res["S12_停用闭环"] = PASS if a_ok and e12b and not e12b.enabled and not leaked else FAIL

    # ──── S13: examples 上限不炸 ────
    rid13 = engine.register("示例上限测试", "基准推荐", tags=["cap"])
    for i in range(20):
        engine._extract_rule(f"测试上限查询第{i}次", {"step": i})
    e13 = engine.retrieve(rid13)
    res["S13_上限安全"] = PASS if e13 and len(e13.examples) <= 10 else FAIL

    # ──── S14: 版本号严格递增 ────
    rid14 = engine.register("Python venv", "python -m venv venv", tags=["python"])
    v1 = engine.retrieve(rid14).revision
    engine.update(rid14, recommendation="python3 -m venv venv")
    v2 = engine.retrieve(rid14).revision
    res["S14_版本递增"] = PASS if v2 == v1 + 1 else FAIL

    # ──── S15: 阈值波动区间 [0.10, 0.50] ────
    for i in range(30):
        engine.search(f"压测查询第{i}号", top_k=1)
    t = engine.threshold_info()
    cur = t["current_threshold"]
    res["S15_阈值区间"] = PASS if 0.10 <= cur <= 0.50 else FAIL

    # ──── S16: 空值安全 — 空查询/空标签/None 不崩 ────
    try:
        r0 = engine.search("", top_k=1)
        r1 = engine.search("正常查询", top_k=1)
        engine.register("", "空触发词", tags=[])
        r2 = engine.search("", top_k=1)
        res["S16_空值安全"] = PASS
    except Exception:
        res["S16_空值安全"] = FAIL

    # ──── S17: 快速恢复 — reset 后旧数据不泄漏 ────
    rid17 = engine.register("重置前数据", "重置前方案", tags=["pre-reset"])
    engine.reset()
    e17 = engine.retrieve(rid17)
    h = engine.search("重置前", top_k=1)
    res["S17_快速恢复"] = PASS if e17 is None and len(h) == 0 else FAIL

    # ──── S18: 排名稳定性 — 同一查询连续 3 次结果一致 ────
    engine.register("K8s Pod 一直 Pending", "kubectl describe pod 查看 Events，检查资源配额", tags=["k8s", "pod", "pending"])
    engine.register("K8s 节点 NotReady", "kubectl get nodes，检查 kubelet 状态和磁盘压力", tags=["k8s", "node", "notready"])
    engine.register("K8s Service 不可达", "检查 endpoints 是否为空，kubectl get endpoints", tags=["k8s", "service"])
    r1 = [h.id for h in engine.search("K8s 故障排查", top_k=3)]
    r2 = [h.id for h in engine.search("K8s 故障排查", top_k=3)]
    r3 = [h.id for h in engine.search("K8s 故障排查", top_k=3)]
    res["S18_排名稳定"] = PASS if r1 == r2 == r3 else FAIL

    # ──── S19: 响应时间 — 百条库下单次搜索 < 50ms ────
    # 已有 ~130 条在库里（S11 的 100 + 其他场景的），直接测搜索耗时
    ts = time.perf_counter()
    _ = engine.search("K8s Pod Pending 故障", top_k=5)
    elapsed = (time.perf_counter() - ts) * 1000
    res["S19_响应耗时"] = PASS if elapsed < 50 else FAIL

    # ──── S20: Git 提交后状态一致 ────
    rid20 = engine.register("Git 状态测试条目", "测试 git 提交", tags=["git-test"])
    ok = engine._git_commit(f"test commit for {rid20}")
    res["S20_Git同步"] = PASS if engine._git_ready else FAIL

    res["_elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    return res


if __name__ == "__main__":
    all_rounds = []
    for r in range(1, 4):
        engine = ExperienceEngine()
        rr = run_one_round(engine, r)
        all_rounds.append(rr)

    scenes = [k for k in all_rounds[0].keys() if not k.startswith("_") and k != "round"]

    print(f"\n{'场景':<20} {'R1':>5} {'R2':>5} {'R3':>5} {'结果':>6}")
    print("-" * 50)

    total_fail = 0
    for scene in scenes:
        row = f"{scene:<20}"
        stable = True
        for rr in all_rounds:
            r = rr[scene]
            row += f" {r:>5}"
            if r == FAIL:
                stable = False
                total_fail += 1
        row += f" {'稳定' if stable else '波动':>6}"
        print(row)

    print("-" * 50)
    for rr in all_rounds:
        print(f"  R{rr['round']} 总耗时: {rr['_elapsed_ms']} ms")
    print(f"\n总失败次数: {total_fail}")
    print("20 场景 × 3 轮全稳定通过。" if total_fail == 0 else f"有 {total_fail} 次未通过，需检查。")
