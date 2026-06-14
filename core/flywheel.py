# ================================================================
# 经验引擎 群体BUFF (ExperienceEngine - Collective Buff)
# 自进化式任务执行知识库
# ================================================================

"""
经验引擎 — 从任务执行中自动积累可复用知识的自进化系统

一个轻量级 Python 库，接入多 Agent 框架后可在任务执行过程中自动提取、
沉淀并复用经验知识，减少重复错误、缩短决策路径。

核心能力：
  1. 知识条目管理：注册、检索、评价、更新、停用
  2. 语义检索：基于 n-gram 哈希投影构建文本向量 + 余弦相似度（零外部依赖）
  3. Git 版本控制：知识变更自动提交，支持团队共享
  4. 三种学习模式：
     - 失败驱动：记录错误现象与修复方案
     - 成功泛化：从已验证的解决方案中衍生变体
     - 日志捕获：从完整的执行日志中提取新知识
  5. 自适应阈值：根据历史命中率自动调整检索匹配门槛
  6. 来源可信度：基于历史反馈为不同知识来源分配动态权重
  7. 时间衰减：长期未使用的知识条目自动降权

技术特性：
  - 零外部依赖（不依赖 numpy / sklearn / torch / jieba）
  - 纯 Python 实现文本嵌入与向量相似度计算
  - 中英文输入均支持：中文内置分词器（200 词词典 + 双向最大匹配），英文由 n-gram 处理
  - JSON 文件持久化 + Git 自动备份
  - 运行时热加载
  - 可作为插件接入任意多 Agent 框架

Copyright © 2026 吕氏链 Lvchain
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# ================================================================
# 全局配置常量
# ================================================================

DEFAULT_STORE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "state", "knowledge_store.json"
)
EMBEDDING_DIMENSION = 256

# ---- 自适应阈值参数 ----
TUNE_INTERVAL = 100          # 每 100 次查询触发一次阈值校准
TUNE_HIT_RATE_LOW = 0.10     # 命中率低于此值 → 放宽匹配
TUNE_HIT_RATE_HIGH = 0.60    # 命中率高于此值 → 收紧匹配
TUNE_STEP = 0.05             # 每次调整步长
THRESHOLD_FLOOR = 0.10       # 检索门槛下限
THRESHOLD_CEILING = 0.50     # 检索门槛上限

# ---- 时间衰减参数 ----
DECAY_HALF_LIFE_DAYS = 30    # 30 天未使用，权重减半
RECENCY_BOOST_WINDOW = 1.0   # 24 小时内的条目轻微加分
RECENCY_BOOST_FACTOR = 0.1

# ---- 复合评分权重 ----
WEIGHT_SEMANTIC = 0.5
WEIGHT_DECAY = 0.3
WEIGHT_SOURCE = 0.2

# ---- 来源初始可信度 ----
DEFAULT_SOURCE_WEIGHTS: Dict[str, float] = {
    "CAPTURED": 1.0,   # 真实执行日志 → 最可信
    "DERIVED":  0.9,   # 从已验证方案衍生
    "FIX":      0.7,   # 失败后总结
    "SKILL":    0.5,   # 自动提取
}


# ================================================================
# 自定义异常
# ================================================================

class EngineError(Exception):
    """经验引擎基础异常。"""
    pass


class RuleNotFoundError(EngineError):
    """目标知识条目不存在。"""
    pass


# ================================================================
# 内置中文分词（零外部依赖）
# ================================================================

_TECHNICAL_LEXICON: Set[str] = {
    # AI 与机器学习
    "人工智能", "机器学习", "深度学习", "神经网络", "自然语言处理",
    "大语言模型", "语言模型", "嵌入向量", "向量检索", "语义理解",
    "文本生成", "图像识别", "语音识别", "强化学习", "迁移学习",
    "微调", "预训练", "推理", "提示词", "上下文窗口",
    "token", "embedding", "transformer", "attention", "RAG",
    # 编程与工程
    "数据分析", "数据清洗", "数据可视化", "数据处理", "数据挖掘",
    "后端", "前端", "全栈", "微服务", "单体架构",
    "API", "REST", "GraphQL", "WebSocket", "数据库",
    "MySQL", "PostgreSQL", "MongoDB", "Redis", "SQLite",
    "Docker", "Kubernetes", "CI/CD", "DevOps", "容器化",
    "Python", "JavaScript", "TypeScript", "Go", "Rust",
    "pandas", "polars", "numpy", "matplotlib", "pip",
    "npm", "Node.js", "React", "Vue", "Next.js",
    "单元测试", "集成测试", "端到端测试", "压力测试", "回归测试",
    "重构", "代码审查", "合并请求", "分支管理", "版本控制",
    "Git", "GitHub", "GitLab", "SSH", "HTTPS",
    "JSON", "CSV", "XML", "YAML", "Markdown",
    "正则表达式", "日志", "监控", "告警", "调试",
    # SaaS 与产品
    "用户画像", "推荐系统", "搜索", "个性化", "协同过滤",
    "登录", "注册", "认证", "授权", "OAuth",
    "支付", "订单", "退款", "发票", "订阅",
    "消息推送", "短信", "邮件", "通知", "提醒",
    "权限管理", "角色管理", "租户隔离", "多租户", "SaaS",
    "仪表盘", "报表", "导出", "导入", "批量",
    "工作流", "审批", "规则引擎", "事件驱动", "消息队列",
    # 文件与 I/O
    "读取", "写入", "追加", "覆盖", "删除",
    "重命名", "移动", "复制", "压缩", "解压",
    "文件处理", "目录", "路径", "编码", "格式转换",
    # 通用动作
    "创建", "更新", "查询", "搜索", "检索",
    "分析", "生成", "验证", "部署", "发布",
    "备份", "恢复", "迁移", "同步", "导出",
    "错误", "失败", "成功", "完成", "中断",
    "超时", "重试", "降级", "熔断", "限流",
    # 英文技术关键词
    "error", "exception", "timeout", "retry", "success",
    "failed", "pipeline", "model", "agent", "memory",
    "score", "threshold", "batch", "async", "sync",
}


def _tokenize_chinese(text: str) -> List[str]:
    """中文分词：双向最大匹配，取切词更少的版本。

    正向最大匹配（FMM）与逆向最大匹配（BMM）各切一次，
    词数少者通常切出了更长的有效词，语义更准确。
    词典未覆盖的字按单字切分。
    """
    if not text:
        return []

    chinese_only = re.sub(r'[^\u4e00-\u9fff]', '', text)
    if not chinese_only:
        return []

    forward = _match_forward(chinese_only)
    backward = _match_backward(chinese_only)

    return backward if len(backward) < len(forward) else forward


def _match_forward(text: str) -> List[str]:
    """正向最大匹配。"""
    output: List[str] = []
    pos = 0
    length = len(text)
    max_word_len = 6

    while pos < length:
        found = False
        for span in range(min(max_word_len, length - pos), 0, -1):
            candidate = text[pos:pos + span]
            if candidate in _TECHNICAL_LEXICON:
                output.append(candidate)
                pos += span
                found = True
                break
        if not found:
            output.append(text[pos])
            pos += 1

    return output


def _match_backward(text: str) -> List[str]:
    """逆向最大匹配。"""
    output: List[str] = []
    length = len(text)
    max_word_len = 6

    pos = length
    while pos > 0:
        found = False
        for span in range(min(max_word_len, pos), 0, -1):
            candidate = text[pos - span:pos]
            if candidate in _TECHNICAL_LEXICON:
                output.append(candidate)
                pos -= span
                found = True
                break
        if not found:
            output.append(text[pos - 1])
            pos -= 1

    output.reverse()
    return output


# ================================================================
# 文本嵌入与相似度（零外部依赖）
# ================================================================

def _build_embedding(text: str, dimensions: int = EMBEDDING_DIMENSION) -> List[float]:
    """将文本转换为固定维度嵌入向量。

    流程：中文分词 → 字符级/词级 n-gram → MD5 哈希投影 → L2 归一化。
    不依赖任何第三方库。
    """
    vector = [0.0] * dimensions
    text = text.lower().strip()
    if not text:
        return vector

    tokens: List[str] = []

    # 中文分词结果作为独立 token
    cn_words = _tokenize_chinese(text)
    tokens.extend(cn_words)

    # 英文/数字部分生成 n-gram
    non_cn = re.sub(r'[\u4e00-\u9fff]+', ' ', text)
    for word in non_cn.split():
        word = word.strip()
        if not word:
            continue
        for ch in word:
            tokens.append(ch)
        for i in range(len(word) - 1):
            tokens.append(word[i:i + 2])
        for i in range(len(word) - 2):
            tokens.append(word[i:i + 3])

    # 中文 n-gram 作为补充特征（捕获未登录词）
    cn_text = re.sub(r'[^\u4e00-\u9fff]', '', text)
    if len(cn_text) >= 2:
        for i in range(len(cn_text) - 1):
            tokens.append(cn_text[i:i + 2])
    if len(cn_text) >= 3:
        for i in range(len(cn_text) - 2):
            tokens.append(cn_text[i:i + 3])

    # 哈希投影
    for token in tokens:
        hash_digest = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
        bucket = hash_digest % dimensions
        direction = 1.0 if (hash_digest // dimensions) % 2 == 0 else -1.0
        vector[bucket] += direction

    # L2 归一化
    magnitude = math.sqrt(sum(v * v for v in vector))
    if magnitude > 1e-10:
        vector = [v / magnitude for v in vector]

    return vector


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """两向量间的余弦相似度。"""
    if len(vec_a) != len(vec_b) or not vec_a:
        return 0.0
    dot_product = sum(x * y for x, y in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(x * x for x in vec_b))
    if norm_a < 1e-10 or norm_b < 1e-10:
        return 0.0
    return dot_product / (norm_a * norm_b)


# ================================================================
# 知识条目数据模型
# ================================================================

@dataclass
class Rule:
    """一条从任务执行中提取的可复用知识。

    包含触发条件、建议操作、历史表现、来源追溯等完整元信息。
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    trigger_pattern: str = ""             # 触发匹配的文本模式
    recommendation: str = ""              # 建议执行的操作
    category: str = "general"             # 分类标签
    quality_score: float = 0.5            # 质量评分 (0.0 ~ 1.0)
    use_count: int = 0                    # 被引用的次数
    approvals: int = 0                    # 正向评价数
    rejections: int = 0                   # 负向评价数
    source: str = ""                      # 来源任务描述
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    enabled: bool = True                  # 是否处于启用状态
    embedding: Optional[List[float]] = None
    tags: List[str] = field(default_factory=list)
    revision: int = 1                     # 修改版本号
    origin: str = "SKILL"                 # 来源类型：FIX / DERIVED / CAPTURED / SKILL

    # ---- 增强元信息 ----
    keywords: List[str] = field(default_factory=list)
    validation_criteria: str = ""
    history: str = ""
    complexity: int = 0                   # 复杂度 0=通用 1-4=层级
    executor_hint: str = ""
    procedure: str = ""
    examples: List[Dict] = field(default_factory=list)
    parent_id: str = ""

    @property
    def current_score(self) -> float:
        """当前有效评分 = 原始评分 × 时间衰减 × 近期加成。

        距上次使用超过半衰期的条目按幂函数衰减；
        24 小时内使用过的条目获得轻微加分。
        """
        now = time.time()
        days_elapsed = max((now - self.updated_at) / 86400.0, 0.0)
        half_life = DECAY_HALF_LIFE_DAYS

        decay = 0.5 ** (days_elapsed / half_life)

        recency_bonus = 1.0
        if days_elapsed < RECENCY_BOOST_WINDOW:
            recency_bonus = 1.0 + RECENCY_BOOST_FACTOR * (1.0 - days_elapsed)

        effective = self.quality_score * decay * recency_bonus
        return max(effective, 0.01)

    def apply_rating(self, direction: str) -> None:
        """应用一次评价（正向或负向），更新评分和时间戳。"""
        self.updated_at = time.time()
        if direction == "UPVOTE":
            self.approvals += 1
            self.quality_score = min(1.0, self.quality_score + 0.1)
        elif direction == "DOWNVOTE":
            self.rejections += 1
            self.quality_score = max(0.0, self.quality_score - 0.1)

    def mark_used(self) -> None:
        """标记一次使用，刷新时间戳。"""
        self.use_count += 1
        self.updated_at = time.time()

    def serialize(self) -> Dict[str, Any]:
        """序列化为字典。"""
        record: Dict[str, Any] = {
            "rule_id": self.id,
            "pattern": self.trigger_pattern,
            "action": self.recommendation,
            "category": self.category,
            "score": self.quality_score,
            "use_count": self.use_count,
            "upvotes": self.approvals,
            "downvotes": self.rejections,
            "source_task": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "active": self.enabled,
            "tags": self.tags,
            "version": self.revision,
            "source_type": self.origin,
        }
        if self.keywords:
            record["triggers"] = self.keywords
        if self.validation_criteria:
            record["verify"] = self.validation_criteria
        if self.history:
            record["outcome"] = self.history
        if self.complexity:
            record["difficulty"] = self.complexity
        if self.executor_hint:
            record["agent_hint"] = self.executor_hint
        if self.procedure:
            record["instruction_prompt"] = self.procedure
        if self.examples:
            record["examples"] = self.examples
        if self.embedding:
            record["embedding"] = self.embedding
        if self.parent_id:
            record["parent_rule_id"] = self.parent_id
        return record

    @classmethod
    def deserialize(cls, raw: Dict[str, Any]) -> Rule:
        """从字典反序列化，仅提取已知字段。"""
        valid_fields = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in raw.items() if k in valid_fields}
        return cls(**filtered)


# ================================================================
# 来源可信度追踪
# ================================================================

def _init_source_tracker() -> Dict[str, Dict[str, float]]:
    """构建来源可信度追踪表的初始状态。"""
    return {
        source_type: {"weight": w, "hits": 0.0, "total": 0.0}
        for source_type, w in DEFAULT_SOURCE_WEIGHTS.items()
    }


# ================================================================
# 经验引擎主类
# ================================================================

class ExperienceEngine:
    """自进化经验引擎（线程安全单例）。

    接入任意多 Agent 框架后，引擎自动从任务执行流中提取、沉淀、
    检索并迭代经验知识。支持三种学习模式、自适应阈值、来源可信度
    追踪和时间衰减机制。

    典型用法::

        engine = ExperienceEngine()
        # 注册知识
        engine.register("安装依赖失败", "用 pip install --user 重试")
        # 检索知识
        hints = engine.search("pip 安装报错")
        # 评价反馈
        engine.rate(hints[0].id, "UPVOTE")
    """

    _instance: Optional['ExperienceEngine'] = None
    _init_lock = threading.Lock()

    def __new__(cls, store_path: Optional[str] = None):
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._setup(store_path or DEFAULT_STORE_PATH)
                    cls._instance = instance
        return cls._instance

    @classmethod
    def get_instance(cls, store_path: Optional[str] = None) -> 'ExperienceEngine':
        """获取全局唯一实例。"""
        return cls(store_path)

    # ---- 初始化 ----

    def _setup(self, store_path: str) -> None:
        """引擎初始化：加载知识库、设置状态、初始化 Git。"""
        self._store_path = store_path
        self._entries: Dict[str, Rule] = {}
        self._write_lock = threading.Lock()
        self._git_ready: bool = False
        self._counters: Dict[str, int] = {
            "registered": 0, "upvoted": 0, "downvoted": 0,
            "updated": 0, "deactivated": 0,
        }

        # 检索门槛状态
        self._retrieval_threshold: float = 0.2
        self._threshold_state: Dict[str, Any] = {
            "query_count": 0,
            "hit_count": 0,
            "last_adjusted": time.time(),
            "threshold_history": [0.2],
        }

        # 来源可信度
        self._source_tracker = _init_source_tracker()

        self._load_store()
        self._git_setup()

    # ================================================================
    # 持久化层
    # ================================================================

    def _load_store(self) -> int:
        """从 JSON 文件加载知识条目。"""
        if not os.path.exists(self._store_path):
            return 0
        try:
            with open(self._store_path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            for item in data:
                rule = Rule.deserialize(item)
                self._entries[rule.id] = rule
            logger.debug("已加载 %d 条知识", len(self._entries))
            return len(self._entries)
        except (json.JSONDecodeError, IOError) as exc:
            logger.warning("知识库加载失败: %s", exc)
            return 0

    def _save_store(self) -> None:
        """保存知识条目到 JSON 文件。写入失败时备份旧文件并重试一次。"""
        store_dir = os.path.dirname(self._store_path)
        try:
            os.makedirs(store_dir, exist_ok=True)
            with open(self._store_path, 'w', encoding='utf-8') as fh:
                json.dump(
                    [r.serialize() for r in self._entries.values()],
                    fh, ensure_ascii=False, indent=2,
                )
        except IOError as exc:
            logger.warning("知识库保存失败: %s，尝试备份旧文件后重试", exc)
            backup_path = self._store_path + ".bak"
            try:
                if os.path.exists(self._store_path):
                    os.replace(self._store_path, backup_path)
                with open(self._store_path, 'w', encoding='utf-8') as fh:
                    json.dump(
                        [r.serialize() for r in self._entries.values()],
                        fh, ensure_ascii=False, indent=2,
                    )
            except IOError as exc2:
                logger.error("知识库保存重试仍失败: %s", exc2)

    # ================================================================
    # Git 版本控制
    # ================================================================

    def _git_setup(self) -> None:
        """初始化 Git 仓库，用于知识库版本追踪。"""
        if self._git_ready:
            return
        store_dir = os.path.dirname(self._store_path)
        os.makedirs(store_dir, exist_ok=True)
        try:
            if not os.path.exists(os.path.join(store_dir, ".git")):
                subprocess.run(
                    ["git", "init"], cwd=store_dir,
                    capture_output=True, timeout=10, check=True,
                )
                subprocess.run(
                    ["git", "config", "user.email", "engine@auto.commit"],
                    cwd=store_dir, capture_output=True, timeout=10, check=True,
                )
                subprocess.run(
                    ["git", "config", "user.name", "ExperienceEngine"],
                    cwd=store_dir, capture_output=True, timeout=10, check=True,
                )
            self._git_ready = True
        except (subprocess.SubprocessError, FileNotFoundError) as exc:
            logger.debug("Git 初始化未能完成: %s", exc)

    def _git_commit(self, message: str) -> None:
        """提交当前知识库变更到 Git。"""
        if not self._git_ready:
            return
        store_dir = os.path.dirname(self._store_path)
        try:
            subprocess.run(
                ["git", "add", os.path.basename(self._store_path)],
                cwd=store_dir, capture_output=True, timeout=10, check=True,
            )
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=store_dir, capture_output=True, timeout=10, check=True,
            )
        except subprocess.SubprocessError as exc:
            logger.debug("Git 提交未能完成: %s", exc)

    # ================================================================
    # CRUD 操作
    # ================================================================

    def register(self, trigger_pattern: str, recommendation: str,
                 category: str = "general",
                 source: str = "",
                 tags: Optional[List[str]] = None,
                 origin: str = "SKILL") -> str:
        """注册一条新的知识条目。

        Args:
            trigger_pattern: 触发匹配的文本描述。
            recommendation: 建议执行的操作。
            category: 分类标签。
            source: 来源任务。
            tags: 附加标签。
            origin: 来源类型（SKILL / FIX / DERIVED / CAPTURED）。

        Returns:
            新条目的唯一标识符。
        """
        entry = Rule(
            trigger_pattern=trigger_pattern,
            recommendation=recommendation,
            category=category,
            source=source,
            tags=tags or [],
            origin=origin,
        )
        entry.embedding = _build_embedding(trigger_pattern + " " + recommendation)

        with self._write_lock:
            self._entries[entry.id] = entry
            self._save_store()

        self._counters["registered"] += 1
        self._git_commit(f"register: {trigger_pattern[:30]}")
        return entry.id

    def search(self, query: str, top_k: int = 5,
               threshold: Optional[float] = None,
               category: Optional[str] = None) -> List[Rule]:
        """检索与查询最匹配的知识条目。

        采用复合评分：语义相似度（50%）+ 时间衰减（30%）+ 来源可信度（20%）。
        每次检索后触发自适应阈值校准。

        Args:
            query: 查询文本。
            top_k: 返回条目数上限。
            threshold: 最低评分门槛，未指定时使用当前自适应阈值。
            category: 可选分类过滤。

        Returns:
            按复合评分降序排列的匹配条目列表。
        """
        if threshold is None:
            threshold = self._retrieval_threshold

        query_vector = _build_embedding(query)
        candidates: List[Tuple[float, Rule]] = []

        query_keywords = self._extract_keywords(query)

        for entry in self._entries.values():
            if not entry.enabled:
                continue
            if entry.current_score < threshold:
                continue
            if category and entry.category != category:
                continue

            # 语义相似度
            if entry.embedding:
                semantic = _cosine_similarity(query_vector, entry.embedding)
            else:
                semantic = 0.3 if query.lower() in entry.trigger_pattern.lower() else 0.0

            # 语义太弱时，关键词兜底
            if semantic <= 0.1:
                if query_keywords and (entry.keywords or entry.tags):
                    target = set(entry.keywords) | set(entry.tags)
                    overlap = len(set(query_keywords) & target)
                    if overlap >= 1:
                        semantic = 0.15 + overlap * 0.05
                    else:
                        # 子串兜底：查询词是某个标签的子串，或反之
                        matched = False
                        for qk in query_keywords:
                            for tk in target:
                                if qk in tk or tk in qk:
                                    semantic = 0.15
                                    matched = True
                                    break
                            if matched:
                                break
                        if not matched:
                            continue
                else:
                    continue

            # 时间衰减因子
            decay = self._calculate_decay(entry)

            # 来源可信度
            origin = entry.origin
            if origin not in self._source_tracker:
                origin = "SKILL"
            tracker = self._source_tracker[origin]
            if tracker["total"] >= 5:
                source_weight = (tracker["hits"] + 1.0) / (tracker["total"] + 2.0)
            else:
                source_weight = tracker["weight"]

            composite = (semantic * WEIGHT_SEMANTIC +
                         decay * WEIGHT_DECAY +
                         source_weight * WEIGHT_SOURCE)
            candidates.append((composite, entry))

        candidates.sort(key=lambda pair: pair[0], reverse=True)
        results = [entry for _, entry in candidates[:top_k]]

        for entry in results:
            entry.mark_used()

        if results:
            self._save_store()

        self._threshold_state["query_count"] += 1
        if results:
            self._threshold_state["hit_count"] += 1
        self._adjust_threshold()

        return results

    def rate(self, rule_id: str, direction: str) -> bool:
        """对知识条目进行评价。

        Args:
            rule_id: 目标条目 ID。
            direction: "UPVOTE" 或 "DOWNVOTE"。

        Returns:
            操作是否成功。

        Raises:
            ValueError: 评价方向不合法。
        """
        if direction not in ("UPVOTE", "DOWNVOTE"):
            raise ValueError(f"非法的评价方向: {direction!r}，需为 UPVOTE 或 DOWNVOTE")

        entry = self._entries.get(rule_id)
        if not entry:
            return False

        entry.apply_rating(direction)
        self._save_store()
        key = "upvoted" if direction == "UPVOTE" else "downvoted"
        self._counters[key] += 1
        self._git_commit(f"{direction.lower()} rule: {entry.trigger_pattern[:30]}")

        # 更新来源可信度统计
        origin = entry.origin
        if origin in self._source_tracker:
            self._source_tracker[origin]["total"] += 1
            if direction == "UPVOTE":
                self._source_tracker[origin]["hits"] += 1
                self._threshold_state["hit_count"] += 1

        # 低质量条目自动停用
        if entry.quality_score < 0.1 and entry.use_count > 5:
            entry.enabled = False
            entry.updated_at = time.time()
            self._counters["deactivated"] += 1

        return True

    def update(self, rule_id: str, **kwargs) -> bool:
        """更新知识条目的任意字段。

        Args:
            rule_id: 目标条目 ID。
            **kwargs: 要更新的字段名与值。

        Returns:
            是否成功更新。
        """
        entry = self._entries.get(rule_id)
        if not entry:
            return False

        for field, value in kwargs.items():
            if hasattr(entry, field) and field != "id":
                setattr(entry, field, value)

        entry.updated_at = time.time()
        entry.revision += 1
        if "trigger_pattern" in kwargs or "recommendation" in kwargs:
            combined = entry.trigger_pattern + " " + entry.recommendation
            entry.embedding = _build_embedding(combined)

        self._save_store()
        self._counters["updated"] += 1
        self._git_commit(f"update v{entry.revision}: {entry.trigger_pattern[:30]}")
        return True

    def deactivate(self, rule_id: str) -> bool:
        """停用一条知识条目（软删除）。"""
        entry = self._entries.get(rule_id)
        if not entry:
            return False
        entry.enabled = False
        entry.updated_at = time.time()
        self._save_store()
        self._counters["deactivated"] += 1
        self._git_commit(f"deactivate: {entry.trigger_pattern[:30]}")
        return True

    def retrieve(self, rule_id: str) -> Optional[Rule]:
        """按 ID 获取单条知识条目。"""
        return self._entries.get(rule_id)

    def list_all(self, active_only: bool = True,
                 category: Optional[str] = None) -> List[Rule]:
        """列出所有知识条目，按当前有效评分降序排列。"""
        entries = list(self._entries.values())
        if active_only:
            entries = [e for e in entries if e.enabled]
        if category:
            entries = [e for e in entries if e.category == category]
        entries.sort(key=lambda e: e.current_score, reverse=True)
        return entries

    # ================================================================
    # 三种学习模式
    # ================================================================

    def learn_from_failure(self, task: str, error: str) -> Optional[str]:
        """失败驱动学习：从错误中提取知识，避免重复犯错。

        Args:
            task: 失败任务的描述。
            error: 错误信息。

        Returns:
            新创建或更新的条目 ID，无匹配则返回 None。
        """
        context = {"complexity": 1, "executor_hint": "FIX_MODE"}
        rid = self._extract_rule(task, context)
        if rid:
            entry = self._entries.get(rid)
            if entry:
                entry.tags = list(set(entry.tags + ["failure", "fix"]))
                entry.history += f"\n[FIX] ERROR: {error[:100]}"
                entry.quality_score = max(0.0, entry.quality_score - 0.1)
                entry.origin = "FIX"
                entry.updated_at = time.time()
                self._save_store()
        return rid

    def derive_from_success(self, parent_id: str,
                            variations: Optional[List[Dict]] = None) -> Optional[str]:
        """成功泛化学习：从已验证的解决方案衍生新变体。

        源条目质量评分需 >= 0.4 才允许衍生。

        Args:
            parent_id: 父条目 ID。
            variations: 变体配置列表，每个含 trigger / context 等字段。

        Returns:
            新条目的 ID，或不满足条件时返回 None。
        """
        parent = self._entries.get(parent_id)
        if not parent or parent.quality_score < 0.4:
            return None

        new_entry = Rule(
            trigger_pattern=parent.trigger_pattern,
            recommendation=f"[衍生] {parent.recommendation}",
            category=parent.category,
            source=f"DERIVED from {parent_id}",
            keywords=list(parent.keywords),
            procedure=parent.procedure,
            complexity=parent.complexity,
            executor_hint=parent.executor_hint,
            examples=list(parent.examples[-5:]),
            validation_criteria=parent.validation_criteria,
            history=f"[DERIVED from {parent_id}] 成功率: {parent.quality_score:.1%}",
            parent_id=parent_id,
            origin="DERIVED",
        )

        if variations:
            all_keywords = list(parent.keywords)
            all_examples = list(parent.examples)
            for variation in variations:
                if "trigger" in variation:
                    all_keywords.append(variation["trigger"])
                ctx = variation.get("context", {})
                if "parent_id" in ctx:
                    sibling = self._entries.get(ctx["parent_id"])
                    if sibling:
                        all_keywords.extend(sibling.keywords)
                        all_examples.extend(sibling.examples)
                        new_entry.recommendation += f" + {sibling.recommendation}"
            new_entry.keywords = list(dict.fromkeys(all_keywords))[:15]
            new_entry.examples = all_examples[-15:]

        combined = new_entry.trigger_pattern + " " + " ".join(new_entry.keywords)
        new_entry.embedding = _build_embedding(combined)
        new_entry.revision = parent.revision + 1

        with self._write_lock:
            self._entries[new_entry.id] = new_entry
            self._save_store()
        self._counters["registered"] += 1
        self._git_commit(f"DERIVED: {new_entry.id} from {parent_id}")

        return new_entry.id

    def capture_from_log(self, execution_log: Dict[str, Any]) -> Optional[str]:
        """日志捕获学习：从完整执行日志创建全新知识条目。

        仅处理标记为成功的执行日志。

        Args:
            execution_log: 包含 task / steps / tools_used / pattern_keywords 等字段。

        Returns:
            新条目 ID，或日志不满足条件时返回 None。
        """
        if not execution_log.get("success", True):
            return None

        task = execution_log.get("task", "")
        steps = execution_log.get("steps", [])
        tools = execution_log.get("tools_used", [])
        pattern_keywords = execution_log.get("pattern_keywords", [])

        if not task or not steps:
            return None

        captured_keywords = list(pattern_keywords)
        if not captured_keywords:
            captured_keywords = self._extract_keywords(task)

        procedure_lines = [f"技能: {task[:80]}"]
        procedure_lines.append(f"触发条件: {', '.join(captured_keywords[:5])}")
        procedure_lines.append("执行流程:")
        for idx, step in enumerate(steps[:8], 1):
            procedure_lines.append(f"  {idx}. {step[:120]}")
        if tools:
            procedure_lines.append(f"涉及工具: {', '.join(tools[:6])}")

        primary_keyword = captured_keywords[0] if captured_keywords else task[:30]

        entry = Rule(
            trigger_pattern=task[:200],
            recommendation=f"技能: {primary_keyword}",
            category="captured",
            source=task,
            keywords=captured_keywords[:10],
            procedure="\n".join(procedure_lines),
            complexity=0,
            examples=[{"input": task[:200], "steps": steps[:5], "tools": tools[:5]}],
            history="[CAPTURED] 来自执行日志",
            origin="CAPTURED",
        )
        entry.embedding = _build_embedding(
            task + " " + " ".join(captured_keywords) + " " + " ".join(tools)
        )

        with self._write_lock:
            self._entries[entry.id] = entry
            self._save_store()
        self._counters["registered"] += 1
        self._git_commit(f"CAPTURED: {entry.id}")

        return entry.id

    # ================================================================
    # 自适应阈值引擎
    # ================================================================

    def _adjust_threshold(self) -> None:
        """根据历史命中率自动校准检索阈值。

        命中率过低 → 放宽门槛（阈值 -0.05）
        命中率过高 → 收紧门槛（阈值 +0.05）
        阈值始终保持在 [0.10, 0.50] 区间内。
        """
        qc = self._threshold_state["query_count"]
        if qc <= 0 or qc % TUNE_INTERVAL != 0:
            return

        hc = self._threshold_state["hit_count"]
        hit_rate = hc / qc if qc > 0 else 0.0
        old_threshold = self._retrieval_threshold

        if hit_rate < TUNE_HIT_RATE_LOW:
            self._retrieval_threshold = max(
                THRESHOLD_FLOOR, self._retrieval_threshold - TUNE_STEP
            )
        elif hit_rate > TUNE_HIT_RATE_HIGH:
            self._retrieval_threshold = min(
                THRESHOLD_CEILING, self._retrieval_threshold + TUNE_STEP
            )

        if abs(self._retrieval_threshold - old_threshold) > 0.001:
            self._threshold_state["threshold_history"].append(self._retrieval_threshold)
            self._threshold_state["last_adjusted"] = time.time()
            self._log_adjustment(
                f"threshold {old_threshold:.2f}→{self._retrieval_threshold:.2f} "
                f"(hit_rate={hit_rate:.1%}, queries={qc})"
            )

        self._threshold_state["query_count"] = 0
        self._threshold_state["hit_count"] = 0

    def _log_adjustment(self, message: str) -> None:
        """将阈值调整事件写入引用最频繁的条目中，作为审计日志。"""
        active = [e for e in self._entries.values() if e.enabled]
        if not active:
            return
        anchor = max(active, key=lambda e: e.use_count)
        timestamp = time.strftime("%Y-%m-%d %H:%M")
        anchor.history += f"\n[ADJUST {timestamp}] {message}"

    def threshold_info(self) -> Dict[str, Any]:
        """获取当前阈值引擎状态，供调试与监控使用。"""
        qc = self._threshold_state["query_count"]
        hc = self._threshold_state["hit_count"]
        return {
            "current_threshold": self._retrieval_threshold,
            "hit_rate": hc / qc if qc > 0 else 0.0,
            "queries_since_last": qc,
            "hits_since_last": hc,
            "queries_until_next": TUNE_INTERVAL - (qc % TUNE_INTERVAL),
            "threshold_history": self._threshold_state.get("threshold_history", []),
            "source_reliability": {
                origin: {
                    "weight": s["weight"],
                    "hit_rate": s["hits"] / s["total"] if s["total"] > 0 else s["weight"],
                    "samples": int(s["total"]),
                }
                for origin, s in self._source_tracker.items()
            },
        }

    # ================================================================
    # 辅助方法
    # ================================================================

    def _calculate_decay(self, entry: Rule) -> float:
        """计算单条知识的时间衰减因子 (0.0 ~ 1.0)。"""
        now = time.time()
        days_elapsed = max((now - entry.updated_at) / 86400.0, 0.0)
        decay = 0.5 ** (days_elapsed / DECAY_HALF_LIFE_DAYS)
        if days_elapsed < RECENCY_BOOST_WINDOW:
            decay *= (1.0 + RECENCY_BOOST_FACTOR * (1.0 - days_elapsed))
        return decay

    def _extract_keywords(self, text: str) -> List[str]:
        """从给定文本中提取关键词。

        中文文本走分词流程，英文/数字部分用正则提取。
        关键词去重后最多返回 10 个。
        """
        text = text.strip()
        tokens: List[str] = []

        cn_words = _tokenize_chinese(text)
        tokens.extend(cn_words[:8])

        en_words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{2,}', text)
        tokens.extend(w.lower() for w in en_words[:6])

        seen: Set[str] = set()
        unique: List[str] = []
        for t in tokens:
            if t not in seen:
                seen.add(t)
                unique.append(t)
        return unique[:10]

    def _extract_rule(self, user_query: str,
                      context: Optional[Dict] = None) -> Optional[str]:
        """从用户查询中提取或更新结构化知识。

        若找到高度相似（>0.8）的已有条目则合并关键词和示例；
        否则创建新条目。
        """
        if not user_query or len(user_query.strip()) < 4:
            return None

        keywords = self._extract_keywords(user_query)
        if not keywords:
            return None

        existing = self.search(user_query, top_k=1, threshold=0.3)
        if existing:
            entry = existing[0]
            similarity = _cosine_similarity(
                _build_embedding(user_query), entry.embedding or []
            )
            if similarity > 0.8:
                new_kw = [k for k in keywords if k not in entry.keywords]
                if new_kw:
                    entry.keywords.extend(new_kw)
                entry.examples.append({
                    "input": user_query[:200],
                    "context": str(context or {})[:100],
                })
                if len(entry.examples) > 10:
                    entry.examples = entry.examples[-10:]
                entry.updated_at = time.time()
                entry.revision += 1
                self._save_store()
                return entry.id
            self.rate(entry.id, "UPVOTE")
            return entry.id

        complexity = (context or {}).get("complexity", 0)
        executor_hint = (context or {}).get("executor_hint", "")

        primary_kw = keywords[0] if keywords else user_query[:30]
        entry = Rule(
            trigger_pattern=user_query[:200],
            recommendation=f"技能: {primary_kw}",
            category="skill",
            source=user_query,
            keywords=keywords,
            procedure=self._build_procedure(user_query, keywords),
            complexity=complexity,
            executor_hint=executor_hint,
            examples=[{"input": user_query[:200], "context": str(context or {})[:100]}],
            origin="SKILL",
        )
        entry.embedding = _build_embedding(user_query + " " + " ".join(keywords))

        with self._write_lock:
            self._entries[entry.id] = entry
            self._save_store()
        return entry.id

    def _build_procedure(self, query: str, keywords: List[str]) -> str:
        """根据查询和关键词构建结构化执行步骤模板。"""
        main_action = keywords[0] if keywords else query[:20]
        return (
            f"技能: {main_action}\n"
            f"触发条件: {', '.join(keywords[:5])}\n"
            f"原始需求: {query[:150]}\n"
            f"执行步骤: 1.分析需求 2.制定方案 3.执行 4.验证"
        )

    # ================================================================
    # 反馈闭环
    # ================================================================

    def record_outcome(self, observer: str, rule_id: str,
                       observation: str, success: bool) -> bool:
        """记录一次执行后的观察结果，闭环反馈到对应条目。

        Args:
            observer: 反馈来源标识。
            rule_id: 目标条目 ID。
            observation: 观察到的结果描述。
            success: 执行是否成功。

        Returns:
            是否成功写入。
        """
        entry = self._entries.get(rule_id)
        if not entry:
            return False
        timestamp = time.strftime("%m-%d %H:%M")
        status = "OK" if success else "FAIL"
        entry.history += f"\n[{observer}|{timestamp}] {status}: {observation}"
        entry.quality_score = min(1.0, max(
            0.0, entry.quality_score + (0.05 if success else -0.05)
        ))
        entry.updated_at = time.time()
        self._save_store()
        return True

    # ================================================================
    # 状态查询
    # ================================================================

    def status(self) -> Dict[str, Any]:
        """获取引擎总体状态，包括条目统计与阈值信息。"""
        active_count = sum(1 for e in self._entries.values() if e.enabled)
        total = len(self._entries)
        return {
            "total_entries": total,
            "active_entries": active_count,
            "deactivated_entries": total - active_count,
            "counters": dict(self._counters),
            "git_ready": self._git_ready,
            "threshold": self.threshold_info(),
        }

    def reset_counters(self) -> None:
        """重置操作计数器。"""
        self._counters = {
            "registered": 0, "upvoted": 0, "downvoted": 0,
            "updated": 0, "deactivated": 0,
        }

    def reset(self) -> None:
        """清空全部知识条目和统计数据，恢复到初始状态。"""
        with self._write_lock:
            self._entries.clear()
            self._save_store()
        self.reset_counters()
        self._threshold_state = {
            "query_count": 0, "hit_count": 0,
            "last_adjusted": time.time(),
            "threshold_history": [0.2],
        }
        self._retrieval_threshold = 0.2
        self._source_tracker = _init_source_tracker()


# ================================================================
# 插件接口 — 便于接入其他 Agent 框架
# ================================================================

class EnginePlugin:
    """经验引擎的适配插件，用于快速接入任意多 Agent 框架。

    典型用法::

        plugin = EnginePlugin("my_framework")
        plugin.on_task_complete("查询用户订单", result, success=True)
        hints = plugin.suggest_actions("订单支付失败")
    """

    def __init__(self, framework_name: str = "unknown"):
        self._engine = ExperienceEngine.get_instance()
        self._framework = framework_name
        logger.info("[EnginePlugin] 已接入 %s", framework_name)

    def on_task_complete(self, task: str, result: Any,
                         success: bool = True) -> Optional[str]:
        """任务完成回调，自动提取经验知识。"""
        if success:
            return self._engine._extract_rule(task, {"success": True})
        else:
            return self._engine.learn_from_failure(task, str(result))

    def on_tool_result(self, tool_name: str, success: bool) -> None:
        """工具执行结果回调。"""
        hints = self._engine.search(tool_name, top_k=1, threshold=0.0)
        if hints:
            self._engine.rate(hints[0].id, "UPVOTE" if success else "DOWNVOTE")

    def suggest_actions(self, query: str) -> List[Dict]:
        """根据查询返回建议的操作列表。"""
        hints = self._engine.search(query, top_k=3)
        return [
            {"rule_id": e.id, "action": e.recommendation, "score": e.quality_score}
            for e in hints
        ]

    def get_status(self) -> Dict[str, Any]:
        """获取引擎统计信息。"""
        return self._engine.status()


# ================================================================
# 公共 API
# ================================================================

def get_engine(store_path: Optional[str] = None) -> ExperienceEngine:
    """获取经验引擎全局实例。"""
    return ExperienceEngine.get_instance(store_path)


def create_plugin(framework_name: str = "unknown") -> EnginePlugin:
    """创建经验引擎插件实例。"""
    return EnginePlugin(framework_name)
