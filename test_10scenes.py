"""
Demo: 经验引擎 10 场景 × 5 轮稳定性验证
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

    results = {
        "round": round_num,
        "S1_基础闭环": None,
        "S2_跨Agent共享": None,
        "S3_失败驱动学习": None,
        "S4_成功泛化": None,
        "S5_日志捕获": None,
        "S6_多框架并发": None,
        "S7_评分进化": None,
        "S8_时间衰减": None,
        "S9_分类过滤": None,
        "S10_来源可信度": None,
    }

    # ──── S1: 基础闭环 ────
    rid1 = engine.register("pip install tensorflow 报错 No matching distribution", "用 conda install tensorflow 代替 pip", tags=["python", "pip", "tensorflow"])
    hints = engine.search("pip install 失败", top_k=5)
    results["S1_基础闭环"] = PASS if any("conda" in h.recommendation for h in hints) else FAIL

    # ──── S2: 跨 Agent 共享 ────
    engine.register("nginx 反向代理 502 Bad Gateway", "检查 upstream 地址是否正确，确认后端服务端口开放", tags=["nginx", "502", "proxy"])
    hints = engine.search("反向代理一直返回 502", top_k=5)
    results["S2_跨Agent共享"] = PASS if any("upstream" in h.recommendation for h in hints) else FAIL

    # ──── S3: 失败驱动学习 ────
    rid3 = engine.learn_from_failure("部署 FastAPI 到 Ubuntu", "gunicorn worker timeout")
    entry = engine.retrieve(rid3) if rid3 else None
    results["S3_失败驱动学习"] = PASS if entry and "FIX" in entry.origin else FAIL

    # ──── S4: 成功泛化 ────
    rid4 = engine.register("MySQL 慢查询优化", "用 EXPLAIN 分析查询计划，给 WHERE 条件列加索引", tags=["mysql", "slow", "index"])
    engine.rate(rid4, "UPVOTE")
    engine.rate(rid4, "UPVOTE")
    engine.rate(rid4, "UPVOTE")
    derived = engine.derive_from_success(rid4, [{"trigger": "PostgreSQL 慢查询"}, {"trigger": "慢查询"}])
    d = engine.retrieve(derived) if derived else None
    results["S4_成功泛化"] = PASS if d and "衍生" in d.recommendation and d.parent_id == rid4 else FAIL

    # ──── S5: 日志捕获 ────
    rid5 = engine.capture_from_log({
        "success": True,
        "task": "用 redis-cli 批量删除过期 key",
        "steps": ["redis-cli --scan --pattern 'session:*' | xargs redis-cli DEL", "确认内存下降"],
        "tools_used": ["redis-cli"],
        "pattern_keywords": ["redis", "key", "过期", "批量删除"],
    })
    entry5 = engine.retrieve(rid5) if rid5 else None
    results["S5_日志捕获"] = PASS if entry5 and entry5.origin == "CAPTURED" else FAIL

    # ──── S6: 多框架并发 ────
    frameworks = ["AutoGen", "LangChain", "CrewAI"]
    engine.register("API 返回 401 Unauthorized", "检查 token 是否过期，重新获取 access_token", tags=["api", "401", "auth"])
    for fw in frameworks:
        engine.register(f"{fw} 任务超时终止", f"增加超时时间到 {30 + len(fw) % 30} 秒", tags=["timeout", fw])
    hits = 0
    for fw in frameworks:
        h = engine.search(f"在 {fw} 中 API 调用返回 401", top_k=1)
        if h and "access_token" in h[0].recommendation:
            hits += 1
    results["S6_多框架并发"] = PASS if hits >= 1 else FAIL

    # ──── S7: 评分进化（低质条目自动降分，高质上升） ────
    rid_low = engine.register("随便写的测试", "直接重启", tags=["low-quality"])
    rid_high = engine.register("Elasticsearch 集群健康检查", "GET /_cluster/health, 关注 status 字段和 unassigned_shards", tags=["es", "ops"])
    for _ in range(6):
        engine.rate(rid_low, "DOWNVOTE")
        engine.rate(rid_high, "UPVOTE")
    low_entry = engine.retrieve(rid_low)
    high_entry = engine.retrieve(rid_high)
    ok_low = low_entry.quality_score < 0.2 or not low_entry.enabled
    ok_high = high_entry.quality_score > 0.5
    results["S7_评分进化"] = PASS if ok_low and ok_high else FAIL

    # ──── S8: 时间衰减（模拟旧条目权重降低） ────
    rid8 = engine.register("CUDA OOM 内存不足", "减小 batch_size 到 16，启用 gradient_checkpointing", tags=["cuda", "oom", "gpu"])
    entry8 = engine.retrieve(rid8)
    entry8.updated_at = time.time() - 86400 * 30  # 30 天前
    entry8.use_count = 0
    # 直接触发 _save_store 写入，不调 update（update 会重置 updated_at）
    engine._save_store()
    entry8_after = engine.retrieve(rid8)
    cs = entry8_after.current_score if entry8_after else 0
    results["S8_时间衰减"] = PASS if cs < 0.45 else FAIL

    # ──── S9: 分类过滤 ────
    engine.register("Vue3 组件间通信", "父子用 props/emit，跨层级用 provide/inject，全局用 Pinia", category="frontend", tags=["vue", "组件", "通信", "component", "frontend"])
    engine.register("Django 数据库迁移", "python manage.py makemigrations && python manage.py migrate", category="backend", tags=["django", "数据库", "迁移", "migrate", "backend"])
    all_frontend = engine.search("组件通信", top_k=5, category="frontend")
    all_backend = engine.search("数据库迁移", top_k=5, category="backend")
    has_vue = any("Pinia" in h.recommendation for h in all_frontend)
    has_django = any("makemigrations" in h.recommendation for h in all_backend)
    results["S9_分类过滤"] = PASS if has_vue and has_django else FAIL

    # ──── S10: 来源可信度 ────
    rid_fix = engine.register("Docker build 推送镜像失败", "docker login 先登录，确认镜像名格式为 registry/namespace/repo:tag", tags=["docker", "push"], origin="FIX")
    rid_skill = engine.register("Git 合并冲突解决", "git merge --abort 先回退，再解决冲突后 git add && git commit", tags=["git", "merge"], origin="SKILL")
    for _ in range(5):
        engine.rate(rid_fix, "UPVOTE")
        engine.rate(rid_skill, "UPVOTE")
        engine.rate(rid_skill, "DOWNVOTE")

    fix_entry = engine.retrieve(rid_fix)
    skill_entry = engine.retrieve(rid_skill)
    # FIX 来源全赞 → 可信；SKILL 来源混赞 → 不可信
    results["S10_来源可信度"] = PASS if fix_entry.quality_score > skill_entry.quality_score else FAIL

    return results


if __name__ == "__main__":
    all_rounds = []
    for r in range(1, 6):
        engine = ExperienceEngine()
        round_results = run_one_round(engine, r)
        all_rounds.append(round_results)

    # 打印汇总
    scenes = list(all_rounds[0].keys())
    scenes.remove("round")

    print(f"\n{'场景':<20} {'R1':>5} {'R2':>5} {'R3':>5} {'R4':>5} {'R5':>5} {'结果':>6}")
    print("-" * 60)

    total_fail = 0
    for scene in scenes:
        row = f"{scene:<20}"
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

    print("-" * 60)
    print(f"\n总失败次数: {total_fail}")
    if total_fail == 0:
        print("10 场景 × 5 轮全稳定通过。")
    else:
        print(f"有 {total_fail} 次未通过，需检查。")
