import random
from datetime import datetime, timedelta
from typing import Dict, Any, List

from models.user import UserProfile
from utils.constants import COOLDOWN_TIMES, EVENT_TYPES

class EventSystem:
    """事件系统 - 负责历练、随机事件等"""
    
    def __init__(self, data_manager, llm_manager, config_manager):
        self.data_manager = data_manager
        self.llm_manager = llm_manager
        self.config_manager = config_manager
    
    async def can_adventure(self, user_data: UserProfile) -> bool:
        """检查是否可以历练"""
        # 检查历练冷却时间
        last_adventure = getattr(user_data, 'last_adventure_time', None)
        if not last_adventure:
            return True
        
        if isinstance(last_adventure, str):
            last_adventure = datetime.fromisoformat(last_adventure)
        
        cooldown = timedelta(seconds=COOLDOWN_TIMES["adventure"])
        next_adventure_time = last_adventure + cooldown
        
        return datetime.now() >= next_adventure_time
    
    async def get_adventure_cooldown(self, user_data: UserProfile) -> str:
        """获取历练冷却剩余时间"""
        last_adventure = getattr(user_data, 'last_adventure_time', None)
        if not last_adventure:
            return "0分钟"
        
        if isinstance(last_adventure, str):
            last_adventure = datetime.fromisoformat(last_adventure)
        
        cooldown = timedelta(seconds=COOLDOWN_TIMES["adventure"])
        next_adventure_time = last_adventure + cooldown
        remaining = next_adventure_time - datetime.now()
        
        if remaining.total_seconds() <= 0:
            return "0分钟"
        
        minutes = int(remaining.total_seconds() // 60)
        seconds = int(remaining.total_seconds() % 60)
        
        if minutes > 0:
            return f"{minutes}分钟{seconds}秒"
        else:
            return f"{seconds}秒"
    
    async def perform_adventure(self, user_data: UserProfile) -> Dict[str, Any]:
        """执行历练"""
        # 生成历练事件
        event = self._generate_adventure_event(user_data)
        
        # 应用事件效果
        self._apply_event_effects(user_data, event)
        
        # 更新历练时间
        user_data.last_adventure_time = datetime.now()
        
        return event
    
    def _generate_adventure_event(self, user_data: UserProfile) -> Dict[str, Any]:
        """生成历练事件"""
        # 基于用户境界和特质决定事件类型
        event_weights = {
            "battle": 0.4,      # 战斗
            "treasure": 0.25,   # 寻宝
            "encounter": 0.2,   # 奇遇
            "cultivation": 0.1, # 修炼感悟
            "disaster": 0.05    # 灾难
        }
        
        # 运气影响事件概率
        if "运气极佳" in user_data.personality_traits:
            event_weights["treasure"] += 0.1
            event_weights["encounter"] += 0.05
            event_weights["disaster"] -= 0.03
        
        # 勇敢特质增加战斗概率
        if "勇敢无畏" in user_data.personality_traits:
            event_weights["battle"] += 0.1
        
        event_type = random.choices(
            list(event_weights.keys()),
            weights=list(event_weights.values())
        )[0]
        
        if event_type == "battle":
            return self._generate_battle_event(user_data)
        elif event_type == "treasure":
            return self._generate_treasure_event(user_data)
        elif event_type == "encounter":
            return self._generate_encounter_event(user_data)
        elif event_type == "cultivation":
            return self._generate_cultivation_event(user_data)
        elif event_type == "disaster":
            return self._generate_disaster_event(user_data)
    
    def _generate_battle_event(self, user_data: UserProfile) -> Dict[str, Any]:
        """生成战斗事件"""
        from systems.battle_system import BattleSystem
        battle_system = BattleSystem(self.data_manager, self.llm_manager)
        
        # 与怪物战斗
        battle_result = battle_system.fight_monster(user_data)
        
        return {
            "event_type": "战斗",
            "type": "battle",
            "description": "遭遇妖兽",
            "result": battle_result,
            "rewards": f"战斗{'胜利' if battle_result['victory'] else '失败'}"
        }
    
    def _generate_treasure_event(self, user_data: UserProfile) -> Dict[str, Any]:
        """生成寻宝事件"""
        success_rate = 0.6 + user_data.stats.luck * 0.02
        success = random.random() < success_rate
        
        if success:
            # 获得宝物
            from systems.equipment_system import EquipmentSystem
            equipment_system = EquipmentSystem(self.data_manager, self.llm_manager)
            treasure = equipment_system.generate_equipment(user_data.cultivation.realm_level)
            user_data.inventory.append(treasure)
            
            return {
                "event_type": "寻宝",
                "type": "treasure",
                "description": "发现宝物",
                "success": True,
                "treasure": treasure,
                "rewards": f"获得{treasure['name']}"
            }
        else:
            return {
                "event_type": "寻宝",
                "type": "treasure",
                "description": "搜寻宝物",
                "success": False,
                "rewards": "一无所获"
            }
    
    def _generate_encounter_event(self, user_data: UserProfile) -> Dict[str, Any]:
        """生成奇遇事件"""
        encounters = [
            {
                "description": "遇到隐世高人",
                "reward_type": "exp",
                "reward_value": user_data.cultivation.realm_level * 30,
                "story": "指点迷津"
            },
            {
                "description": "发现古老洞府",
                "reward_type": "cultivation_points",
                "reward_value": 20,
                "story": "获得修炼心得"
            },
            {
                "description": "救助被困修士",
                "reward_type": "exp",
                "reward_value": user_data.cultivation.realm_level * 20,
                "story": "获得感谢"
            },
            {
                "description": "参悟天地奥秘",
                "reward_type": "spiritual_power",
                "reward_value": 50,
                "story": "心境提升"
            }
        ]
        
        encounter = random.choice(encounters)
        
        return {
            "event_type": "奇遇",
            "type": "encounter",
            "description": encounter["description"],
            "story": encounter["story"],
            "reward_type": encounter["reward_type"],
            "reward_value": encounter["reward_value"],
            "rewards": f"{encounter['story']}，{encounter['reward_type']}+{encounter['reward_value']}"
        }
    
    def _generate_cultivation_event(self, user_data: UserProfile) -> Dict[str, Any]:
        """生成修炼感悟事件"""
        insights = [
            "感悟天地大道",
            "领悟功法精髓",
            "参透境界奥义",
            "体悟自然法则"
        ]
        
        insight = random.choice(insights)
        exp_gain = user_data.cultivation.realm_level * 25
        
        return {
            "event_type": "感悟",
            "type": "cultivation",
            "description": insight,
            "exp_gain": exp_gain,
            "rewards": f"修炼经验+{exp_gain}"
        }
    
    def _generate_disaster_event(self, user_data: UserProfile) -> Dict[str, Any]:
        """生成灾难事件"""
        disasters = [
            {
                "description": "迷失在幻境中",
                "penalty_type": "exp",
                "penalty_value": user_data.cultivation.experience // 30
            },
            {
                "description": "遭遇天劫之力",
                "penalty_type": "hp", 
                "penalty_value": user_data.stats.max_hp // 5
            },
            {
                "description": "被邪气侵扰",
                "penalty_type": "spiritual_power",
                "penalty_value": 30
            }
        ]
        
        disaster = random.choice(disasters)
        
        return {
            "event_type": "劫难",
            "type": "disaster",
            "description": disaster["description"],
            "penalty_type": disaster["penalty_type"],
            "penalty_value": disaster["penalty_value"],
            "rewards": f"损失{disaster['penalty_type']} {disaster['penalty_value']}"
        }
    
    def _apply_event_effects(self, user_data: UserProfile, event: Dict[str, Any]):
        """应用事件效果"""
        event_type = event.get("type")
        
        if event_type == "encounter":
            # 应用奇遇奖励
            reward_type = event.get("reward_type")
            reward_value = event.get("reward_value", 0)
            
            if reward_type == "exp":
                user_data.cultivation.experience += reward_value
            elif reward_type == "cultivation_points":
                user_data.cultivation.cultivation_points += reward_value
            elif reward_type == "spiritual_power":
                user_data.cultivation.spiritual_power = min(
                    user_data.cultivation.spiritual_power + reward_value,
                    user_data.stats.intelligence * 10
                )
        
        elif event_type == "cultivation":
            # 应用修炼感悟奖励
            exp_gain = event.get("exp_gain", 0)
            user_data.cultivation.experience += exp_gain
        
        elif event_type == "disaster":
            # 应用灾难惩罚
            penalty_type = event.get("penalty_type")
            penalty_value = event.get("penalty_value", 0)
            
            if penalty_type == "exp":
                user_data.cultivation.experience = max(0, user_data.cultivation.experience - penalty_value)
            elif penalty_type == "hp":
                user_data.stats.current_hp = max(1, user_data.stats.current_hp - penalty_value)
            elif penalty_type == "spiritual_power":
                user_data.cultivation.spiritual_power = max(0, user_data.cultivation.spiritual_power - penalty_value)
