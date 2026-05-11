"""
插件管理器
实现插件懒加载和生命周期管理
"""
from typing import Dict, List, Type, Optional, Any
from enum import Enum
from ..plugins.base import BasePlugin
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PluginLoadStrategy(Enum):
    """插件加载策略"""
    EAGER = "eager"      # 立即加载所有插件
    LAZY = "lazy"        # 按需加载
    BACKGROUND = "background"  # 后台预加载


class PluginManager:
    """插件管理器 - 实现懒加载"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_registry: Dict[str, Type[BasePlugin]] = {}
        self._load_strategy = PluginLoadStrategy.LAZY
        self._initialized = False

    def register_plugin(self, name: str, plugin_class: Type[BasePlugin]):
        """注册插件类"""
        self._plugin_registry[name] = plugin_class
        logger.info(f"Plugin registered: {name}")

    def register_all_plugins(self):
        """注册所有内置插件"""
        from ..plugins import (
            EmailPlugin,
            CalendarPlugin,
            TaskPlugin,
            DocumentPlugin,
            PPTPlugin,
            KnowledgePlugin,
            ChartPlugin,
            CalcPlugin,
        )

        plugins = {
            "email": EmailPlugin,
            "calendar": CalendarPlugin,
            "task": TaskPlugin,
            "document": DocumentPlugin,
            "ppt": PPTPlugin,
            "knowledge": KnowledgePlugin,
            "chart": ChartPlugin,
            "calc": CalcPlugin,
        }

        for name, plugin_class in plugins.items():
            self.register_plugin(name, plugin_class)

    def load_plugin(self, name: str) -> Optional[BasePlugin]:
        """加载单个插件（懒加载）"""
        if name in self._plugins:
            return self._plugins[name]

        if name not in self._plugin_registry:
            logger.warning(f"Plugin not registered: {name}")
            return None

        try:
            plugin_class = self._plugin_registry[name]
            plugin = plugin_class()
            plugin.initialize(self.config)
            self._plugins[name] = plugin
            logger.info(f"Plugin loaded: {name}")
            return plugin
        except Exception as e:
            logger.error(f"Failed to load plugin {name}: {e}")
            return None

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """获取插件（如果未加载则懒加载）"""
        return self.load_plugin(name)

    def unload_plugin(self, name: str):
        """卸载插件（释放内存）"""
        if name in self._plugins:
            del self._plugins[name]
            logger.info(f"Plugin unloaded: {name}")

    def preload_plugins(self, names: List[str] = None):
        """预加载插件"""
        if names is None:
            names = list(self._plugin_registry.keys())

        for name in names:
            self.load_plugin(name)

        self._initialized = True
        logger.info(f"Preloaded {len(names)} plugins")

    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """获取所有已加载的插件"""
        return self._plugins.copy()

    def get_available_plugins(self) -> List[str]:
        """获取所有已注册的插件名称"""
        return list(self._plugin_registry.keys())

    def get_loaded_plugins(self) -> List[str]:
        """获取所有已加载的插件名称"""
        return list(self._plugins.keys())

    def is_plugin_loaded(self, name: str) -> bool:
        """检查插件是否已加载"""
        return name in self._plugins

    def set_load_strategy(self, strategy: PluginLoadStrategy):
        """设置加载策略"""
        self._load_strategy = strategy

        if strategy == PluginLoadStrategy.EAGER:
            self.preload_plugins()
        elif strategy == PluginLoadStrategy.LAZY:
            pass

    def cleanup(self):
        """清理所有插件"""
        self._plugins.clear()
        logger.info("All plugins cleaned up")

    def get_plugin_info(self) -> List[Dict[str, Any]]:
        """获取所有插件信息"""
        info = []
        for name in self._plugin_registry.keys():
            is_loaded = self.is_plugin_loaded(name)
            info.append({
                "name": name,
                "loaded": is_loaded,
                "class": self._plugin_registry[name].__name__
            })
        return info
