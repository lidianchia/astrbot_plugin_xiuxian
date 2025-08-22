from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from astrbot.api import logger

from models.user import UserProfile
from utils.constants import get_cooldown_time

class CultivationSystem:
    """修炼系统"""
    
    def __init__(self, data_manager, llm_manager, config_manager):
        self.data_manager = data_manager
        self.llm_manager = llm_manager
        self.config_manager = config_manager
    
    async def can_cultivate(self, user_data: UserProfile) -> bool:
        """检查是否可以修炼（冷却时间）"""
        if not user_data.cultivation.last_cultivation_time:
            return True
        
        cooldown_seconds = get_cooldown_time(self.config_manager, "cultivation")
        cooldown = timedelta(seconds=cooldown_seconds)
        next_cultivation_time = user_data.cultivation.last_cultivation_time + cooldown
        
        return datetime.now() >= next_cultivation_time
    
    async def get_cultivation_cooldown(self, user_data: UserProfile) -> str:
        """获取修炼冷却剩余时间"""
        if not user_data.cultivation.last_cultivation_time:
            return "0分钟"
        
        cooldown_seconds = get_cooldown_time(self.config_manager, "cultivation")
        cooldown = timedelta(seconds=cooldown_seconds)
        next_cultivation_time = user_data.cultivation.last_cultivation_time + cooldown
        remaining = next_cultivation_time - datetime.now()
        
        if remaining.total_seconds() <= 0:
            return "0分钟"
        
        minutes = int(remaining.total_seconds() // 60)
        seconds = int(remaining.total_seconds() % 60)
        
        if minutes > 0:
            return f"{minutes}分钟{seconds}秒"
        else:
            return f"{seconds}秒"
    
    async def perform_cultivation(self, user_data: UserProfile) -> Dict[str, Any]:
        """执行修炼"""
        # 获取游戏引擎来计算经验
        from core.game_engine import GameEngine
        game_engine = GameEngine(self.data_manager, self.llm_manager, self.config_manager)
        
        # 计算获得的经验
        exp_gained = game_engine.calculate_cultivation_exp(user_data)
        
        # 生成随机事件
        event = game_engine.generate_random_event(user_data)
        
        # 更新用户数据
        user_data.cultivation.experience += exp_gained
        user_data.cultivation.last_cultivation_time = datetime.now()
        
        # 应用事件效果
        game_engine.apply_event_rewards(user_data, event)
        
        # 更新服务器统计
        await self.data_manager.update_server_stats("total_cultivations")
        
        result = {
            "exp_gained": exp_gained,
            "event": event,
            "type": event.get("type", "normal")
        }
        
        self.config_manager.debug_log(f"用户 {user_data.username} 修炼获得 {exp_gained} 经验，遇到 {event.get('type', 'normal')} 事件")
        
        return result
    
    async def can_breakthrough(self, user_data: UserProfile) -> bool:
        """检查是否可以突破"""
        from core.game_engine import GameEngine
        game_engine = GameEngine(self.data_manager, self.llm_manager, self.config_manager)
        
        return game_engine.can_breakthrough(user_data)
    
    async def attempt_breakthrough(self, user_data: UserProfile) -> Dict[str, Any]:
        """尝试突破"""
        from core.game_engine import GameEngine
        game_engine = GameEngine(self.data_manager, self.llm_manager, self.config_manager)
        
        old_realm = user_data.get_realm_name()
        result = game_engine.perform_breakthrough(user_data)
        
        if result["success"]:
            new_realm = user_data.get_realm_name()
            self.config_manager.debug_log(f"用户 {user_data.username} 成功从 {old_realm} 突破到 {new_realm}")
            
            # 添加成就
            achievement = f"突破到{new_realm}"
            if achievement not in user_data.achievements:
                user_data.achievements.append(achievement)
        else:
            self.config_manager.debug_log(f"用户 {user_data.username} 突破失败，损失 {result.get('exp_lost', 0)} 经验")
        
        return result
