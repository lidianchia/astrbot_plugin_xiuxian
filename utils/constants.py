# 修仙插件常量定义

# 境界定义
REALMS = [
    {"name": "练气期", "level": 1, "max_exp": 100, "power_base": 10},
    {"name": "筑基期", "level": 2, "max_exp": 300, "power_base": 30},
    {"name": "金丹期", "level": 3, "max_exp": 800, "power_base": 80},
    {"name": "元婴期", "level": 4, "max_exp": 2000, "power_base": 200},
    {"name": "化神期", "level": 5, "max_exp": 5000, "power_base": 500},
    {"name": "炼虚期", "level": 6, "max_exp": 12000, "power_base": 1200},
    {"name": "合体期", "level": 7, "max_exp": 30000, "power_base": 3000},
    {"name": "大乘期", "level": 8, "max_exp": 80000, "power_base": 8000},
    {"name": "渡劫期", "level": 9, "max_exp": 200000, "power_base": 20000},
    {"name": "仙人境", "level": 10, "max_exp": 999999999, "power_base": 50000},
]

# 装备类型
EQUIPMENT_TYPES = {
    "weapon": "武器",
    "armor": "防具", 
    "accessory": "饰品",
    "pill": "丹药"
}

# 装备品质
EQUIPMENT_QUALITY = [
    {"name": "凡品", "color": "gray", "bonus": 1.0},
    {"name": "良品", "color": "green", "bonus": 1.2},
    {"name": "精品", "color": "blue", "bonus": 1.5},
    {"name": "极品", "color": "purple", "bonus": 2.0},
    {"name": "神品", "color": "orange", "bonus": 3.0},
    {"name": "仙品", "color": "gold", "bonus": 5.0},
]

# 技能类型
SKILL_TYPES = {
    "attack": "攻击技能",
    "defense": "防御技能", 
    "heal": "治疗技能",
    "buff": "增益技能",
    "debuff": "减益技能"
}

# 事件类型
EVENT_TYPES = {
    "fortune": "机缘",
    "disaster": "劫难", 
    "encounter": "奇遇",
    "challenge": "挑战",
    "treasure": "寻宝"
}

# 默认冷却时间（秒） - 可通过配置覆盖
DEFAULT_COOLDOWN_TIMES = {
    "cultivation": 1800,  # 30分钟
    "adventure": 3600,    # 1小时
    "battle": 300,        # 5分钟
    "breakthrough": 7200  # 2小时
}

# 默认LLM配置 - 可通过配置覆盖
DEFAULT_LLM_CONFIG = {
    "max_tokens": 500,
    "temperature": 0.8,
    "top_p": 0.9
}

# 默认游戏平衡参数 - 可通过配置覆盖
DEFAULT_GAME_BALANCE = {
    "base_cultivation_exp": 10,
    "breakthrough_success_rate": 0.7,
    "adventure_reward_multiplier": 1.5,
    "battle_exp_multiplier": 2.0
}

# 配置相关的辅助函数
def get_cooldown_time(config_manager, action_type: str) -> int:
    """从配置管理器获取冷却时间"""
    if config_manager:
        return config_manager.get_cooldown_time(action_type)
    return DEFAULT_COOLDOWN_TIMES.get(action_type, 1800)

def get_game_balance_value(config_manager, key: str, default=None):
    """从配置管理器获取游戏平衡参数"""
    if config_manager:
        balance_config = config_manager.get_game_balance_config()
        return balance_config.get(key, default)
    return DEFAULT_GAME_BALANCE.get(key, default)
