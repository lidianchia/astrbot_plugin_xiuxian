import random
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from models.user import UserProfile
from utils.constants import REALMS, get_game_balance_value

class GameEngine:
    """游戏引擎 - 核心游戏逻辑处理"""
    
    def __init__(self, data_manager, llm_manager, config_manager):
        self.data_manager = data_manager
        self.llm_manager = llm_manager
        self.config_manager = config_manager
    
    def calculate_cultivation_exp(self, user_data: UserProfile) -> int:
        """计算修炼获得的经验"""
        base_exp = get_game_balance_value(self.config_manager, "base_cultivation_exp", 10)
        
        # 根据境界调整经验获得
        realm_bonus = user_data.cultivation.realm_level * 0.1
        
        # 根据个性特质调整
        trait_bonus = 1.0
        if "勤奋刻苦" in user_data.personality_traits:
            trait_bonus += 0.2
        if "天赋异禀" in user_data.personality_traits:
            trait_bonus += 0.3
        
        # 随机因子
        random_factor = random.uniform(0.8, 1.5)
        
        final_exp = int(base_exp * (1 + realm_bonus) * trait_bonus * random_factor)
        return max(1, final_exp)
    
    def calculate_breakthrough_success_rate(self, user_data: UserProfile) -> float:
        """计算突破成功率"""
        base_rate = get_game_balance_value(self.config_manager, "breakthrough_success_rate", 0.7)
        
        # 根据尝试次数调整（失败次数越多，下次成功率稍微提高）
        attempt_bonus = min(0.1, user_data.cultivation.breakthrough_attempts * 0.02)
        
        # 根据个性特质调整
        trait_bonus = 0.0
        if "意志坚定" in user_data.personality_traits:
            trait_bonus += 0.1
        if "运气极佳" in user_data.personality_traits:
            trait_bonus += 0.15
        
        final_rate = min(0.95, base_rate + attempt_bonus + trait_bonus)
        return final_rate
    
    def get_realm_info(self, realm_level: int) -> Optional[Dict[str, Any]]:
        """获取境界信息"""
        for realm in REALMS:
            if realm["level"] == realm_level:
                return realm
        return None
    
    def can_breakthrough(self, user_data: UserProfile) -> bool:
        """检查是否可以突破"""
        current_realm = self.get_realm_info(user_data.cultivation.realm_level)
        if not current_realm:
            return False
        
        # 需要达到当前境界的最大经验才能尝试突破
        return user_data.cultivation.experience >= current_realm["max_exp"]
    
    def perform_breakthrough(self, user_data: UserProfile) -> Dict[str, Any]:
        """执行突破"""
        success_rate = self.calculate_breakthrough_success_rate(user_data)
        success = random.random() < success_rate
        
        user_data.cultivation.breakthrough_attempts += 1
        user_data.cultivation.last_breakthrough_time = datetime.now()
        
        if success:
            # 突破成功
            user_data.cultivation.realm_level += 1
            user_data.cultivation.experience = 0
            user_data.cultivation.breakthrough_attempts = 0
            
            # 提升属性
            self._upgrade_stats_on_breakthrough(user_data)
            
            return {
                "success": True,
                "new_realm": self.get_realm_info(user_data.cultivation.realm_level)
            }
        else:
            # 突破失败，消耗一些经验
            exp_loss = user_data.cultivation.experience // 10
            user_data.cultivation.experience = max(0, user_data.cultivation.experience - exp_loss)
            
            return {
                "success": False,
                "exp_lost": exp_loss
            }
    
    def _upgrade_stats_on_breakthrough(self, user_data: UserProfile):
        """突破时提升属性"""
        # 随机提升属性
        stat_increases = {
            "strength": random.randint(2, 5),
            "agility": random.randint(2, 5),
            "intelligence": random.randint(2, 5),
            "constitution": random.randint(2, 5),
            "luck": random.randint(1, 3)
        }
        
        user_data.stats.strength += stat_increases["strength"]
        user_data.stats.agility += stat_increases["agility"]
        user_data.stats.intelligence += stat_increases["intelligence"]
        user_data.stats.constitution += stat_increases["constitution"]
        user_data.stats.luck += stat_increases["luck"]
        
        # 重新计算生命值和攻防
        user_data.stats.max_hp = user_data.stats.constitution * 10 + user_data.cultivation.realm_level * 50
        user_data.stats.current_hp = user_data.stats.max_hp
        user_data.stats.attack_power = user_data.stats.strength * 2 + user_data.cultivation.realm_level * 10
        user_data.stats.defense_power = user_data.stats.constitution + user_data.cultivation.realm_level * 5
    
    def generate_random_event(self, user_data: UserProfile) -> Dict[str, Any]:
        """生成随机事件"""
        event_types = ["normal", "fortune", "disaster", "encounter"]
        event_weights = [0.6, 0.15, 0.1, 0.15]  # 普通、机缘、劫难、奇遇
        
        # 运气影响事件概率
        if "运气极佳" in user_data.personality_traits:
            event_weights[1] += 0.1  # 增加机缘概率
            event_weights[2] -= 0.05  # 减少劫难概率
        
        event_type = random.choices(event_types, weights=event_weights)[0]
        
        if event_type == "normal":
            return {"type": "normal", "description": "平静的修炼"}
        elif event_type == "fortune":
            return self._generate_fortune_event(user_data)
        elif event_type == "disaster":
            return self._generate_disaster_event(user_data)
        elif event_type == "encounter":
            return self._generate_encounter_event(user_data)
    
    def _generate_fortune_event(self, user_data: UserProfile) -> Dict[str, Any]:
        """生成机缘事件"""
        fortunes = [
            {
                "description": "发现天材地宝",
                "reward_type": "exp",
                "reward_value": user_data.cultivation.realm_level * 50
            },
            {
                "description": "遇到隐世高人指点",
                "reward_type": "cultivation_points",
                "reward_value": 10
            },
            {
                "description": "找到古老的修炼秘籍",
                "reward_type": "exp",
                "reward_value": user_data.cultivation.realm_level * 30
            }
        ]
        
        fortune = random.choice(fortunes)
        return {
            "type": "fortune",
            "description": fortune["description"],
            "reward": fortune
        }
    
    def _generate_disaster_event(self, user_data: UserProfile) -> Dict[str, Any]:
        """生成劫难事件"""
        disasters = [
            {
                "description": "遭遇心魔入侵",
                "penalty_type": "exp",
                "penalty_value": user_data.cultivation.experience // 20
            },
            {
                "description": "修炼时走火入魔",
                "penalty_type": "hp",
                "penalty_value": user_data.stats.max_hp // 4
            }
        ]
        
        disaster = random.choice(disasters)
        return {
            "type": "disaster",
            "description": disaster["description"],
            "penalty": disaster
        }
    
    def _generate_encounter_event(self, user_data: UserProfile) -> Dict[str, Any]:
        """生成奇遇事件"""
        encounters = [
            {
                "description": "遇到同境界的修仙者切磋",
                "outcome": "平局",
                "reward_type": "exp",
                "reward_value": 20
            },
            {
                "description": "帮助村民解决妖兽困扰",
                "outcome": "获得感谢",
                "reward_type": "cultivation_points",
                "reward_value": 5
            }
        ]
        
        encounter = random.choice(encounters)
        return {
            "type": "encounter",
            "description": encounter["description"],
            "outcome": encounter["outcome"],
            "reward": {
                "reward_type": encounter["reward_type"],
                "reward_value": encounter["reward_value"]
            }
        }
    
    def apply_event_rewards(self, user_data: UserProfile, event: Dict[str, Any]):
        """应用事件奖励"""
        if "reward" in event:
            reward = event["reward"]
            reward_type = reward.get("reward_type")
            reward_value = reward.get("reward_value", 0)
            
            if reward_type == "exp":
                user_data.cultivation.experience += reward_value
            elif reward_type == "cultivation_points":
                user_data.cultivation.cultivation_points += reward_value
            elif reward_type == "hp":
                user_data.stats.current_hp = min(
                    user_data.stats.max_hp,
                    user_data.stats.current_hp + reward_value
                )
        
        if "penalty" in event:
            penalty = event["penalty"]
            penalty_type = penalty.get("penalty_type")
            penalty_value = penalty.get("penalty_value", 0)
            
            if penalty_type == "exp":
                user_data.cultivation.experience = max(0, user_data.cultivation.experience - penalty_value)
            elif penalty_type == "hp":
                user_data.stats.current_hp = max(1, user_data.stats.current_hp - penalty_value)
