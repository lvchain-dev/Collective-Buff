"""经验引擎 (ExperienceEngine) - 自进化式任务执行知识库"""

from .flywheel import (
    ExperienceEngine,
    EnginePlugin,
    Rule,
    get_engine,
    create_plugin,
)

__all__ = [
    "ExperienceEngine",
    "EnginePlugin",
    "Rule",
    "get_engine",
    "create_plugin",
]

__version__ = "1.0.0"
__description__ = "经验引擎 - 自进化式任务执行知识库"
__author__ = "Lvchain"
