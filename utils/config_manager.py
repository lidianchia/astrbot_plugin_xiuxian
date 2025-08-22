from typing import Dict, Any, Optional
from astrbot.api.star import Context
from astrbot.api import logger

class ConfigManager:
    """配置管理器 - 统一管理插件配置"""
    
    def __init__(self, context: Context):
        self.context = context
        self._cached_config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        try:
            # 从 AstrBot 的插件配置中获取配置
            # 根据 AstrBot 文档，插件配置通过 context.get_plugin_config() 获取
            plugin_config = getattr(self.context, 'get_plugin_config', lambda: None)()
            if plugin_config:
                self._cached_config = plugin_config
                logger.info("已加载插件配置")
            else:
                logger.warning("未找到插件配置，使用默认配置")
                self._load_default_config()
        except Exception as e:
            logger.error(f"加载配置失败：{e}，使用默认配置")
            self._load_default_config()
    
    def _load_default_config(self):
        """加载默认配置"""
        self._cached_config = {
            # LLM 配置
            "llm_provider": "mock",
            "llm_api_key": "",
            "llm_model": "gpt-3.5-turbo",
            "llm_base_url": "",
            "llm_max_tokens": 500,
            "llm_temperature": 0.8,
            
            # 游戏平衡配置
            "base_cultivation_exp": 10,
            "breakthrough_success_rate": 0.7,
            "cultivation_cooldown": 30,
            "adventure_cooldown": 60,
            "battle_cooldown": 5,
            
            # 功能开关
            "enable_ai_stories": True,
            "enable_daily_fortune": True,
            "enable_sect_system": True,
            "enable_task_system": True,
            "enable_pvp": True,
            
            # 高级配置
            "max_inventory_size": 100,
            "debug_mode": False
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._cached_config.get(key, default)
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取 LLM 配置"""
        return {
            "provider": self.get("llm_provider", "mock"),
            "api_key": self.get("llm_api_key", ""),
            "model": self.get("llm_model", "gpt-3.5-turbo"),
            "base_url": self.get("llm_base_url", ""),
            "max_tokens": self.get("llm_max_tokens", 500),
            "temperature": self.get("llm_temperature", 0.8)
        }
    
    def get_game_balance_config(self) -> Dict[str, Any]:
        """获取游戏平衡配置"""
        return {
            "base_cultivation_exp": self.get("base_cultivation_exp", 10),
            "breakthrough_success_rate": self.get("breakthrough_success_rate", 0.7),
            "cultivation_cooldown": self.get("cultivation_cooldown", 30) * 60,  # 转换为秒
            "adventure_cooldown": self.get("adventure_cooldown", 60) * 60,
            "battle_cooldown": self.get("battle_cooldown", 5) * 60,
            "max_inventory_size": self.get("max_inventory_size", 100)
        }
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """获取功能开关配置"""
        return {
            "enable_ai_stories": self.get("enable_ai_stories", True),
            "enable_daily_fortune": self.get("enable_daily_fortune", True),
            "enable_sect_system": self.get("enable_sect_system", True),
            "enable_task_system": self.get("enable_task_system", True),
            "enable_pvp": self.get("enable_pvp", True),
            "debug_mode": self.get("debug_mode", False)
        }
    
    def is_feature_enabled(self, feature: str) -> bool:
        """检查功能是否启用"""
        feature_flags = self.get_feature_flags()
        return feature_flags.get(feature, False)
    
    def get_cooldown_time(self, action_type: str) -> int:
        """获取冷却时间（秒）"""
        balance_config = self.get_game_balance_config()
        cooldown_map = {
            "cultivation": balance_config["cultivation_cooldown"],
            "adventure": balance_config["adventure_cooldown"],
            "battle": balance_config["battle_cooldown"]
        }
        return cooldown_map.get(action_type, 1800)  # 默认30分钟
    
    def reload_config(self):
        """重新加载配置"""
        logger.info("重新加载插件配置")
        self._load_config()
    
    def debug_log(self, message: str):
        """调试日志"""
        if self.get("debug_mode", False):
            logger.info(f"[DEBUG] {message}")
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        try:
            # 验证数值范围
            if not (0.1 <= self.get("breakthrough_success_rate", 0.7) <= 0.9):
                logger.warning("突破成功率配置超出有效范围 (0.1-0.9)")
                return False
            
            if not (1 <= self.get("base_cultivation_exp", 10) <= 100):
                logger.warning("基础修炼经验配置超出有效范围 (1-100)")
                return False
            
            if not (0.0 <= self.get("llm_temperature", 0.8) <= 2.0):
                logger.warning("LLM 温度参数配置超出有效范围 (0.0-2.0)")
                return False
            
            # 验证 LLM 配置
            llm_provider = self.get("llm_provider", "mock")
            if llm_provider not in ["mock", "openai", "claude", "local"]:
                logger.warning(f"不支持的 LLM 服务商: {llm_provider}")
                return False
            
            # 如果使用真实 LLM 服务，检查 API 密钥
            if llm_provider in ["openai", "claude"] and not self.get("llm_api_key", ""):
                logger.warning(f"使用 {llm_provider} 服务需要配置 API 密钥")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败：{e}")
            return False
