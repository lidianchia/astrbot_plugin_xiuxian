import random
from typing import Dict, Any, Optional
from datetime import datetime

from models.user import UserProfile

class BattleSystem:
    """战斗系统"""
    
    def __init__(self, data_manager, llm_manager, config_manager):
        self.data_manager = data_manager
        self.llm_manager = llm_manager
        self.config_manager = config_manager
    
    def calculate_battle_result(self, attacker: UserProfile, defender: UserProfile) -> Dict[str, Any]:
        """计算战斗结果"""
        attacker_power = attacker.get_combat_power()
        defender_power = defender.get_combat_power()
        
        # 计算基础胜率
        power_ratio = attacker_power / (defender_power + 1)  # 避免除零
        base_win_rate = min(0.95, max(0.05, power_ratio / (power_ratio + 1)))
        
        # 运气因素
        luck_factor = (attacker.stats.luck - defender.stats.luck) * 0.01
        final_win_rate = max(0.05, min(0.95, base_win_rate + luck_factor))
        
        # 随机因素
        battle_random = random.random()
        attacker_wins = battle_random < final_win_rate
        
        # 计算奖励和损失
        if attacker_wins:
            exp_reward = max(10, defender_power // 10)
            exp_loss = max(5, attacker_power // 20)
        else:
            exp_reward = max(5, attacker_power // 20)
            exp_loss = max(10, defender_power // 10)
        
        return {
            "attacker_wins": attacker_wins,
            "attacker_power": attacker_power,
            "defender_power": defender_power,
            "win_rate": final_win_rate,
            "exp_reward": exp_reward,
            "exp_loss": exp_loss
        }
    
    async def execute_pvp_battle(self, attacker: UserProfile, defender: UserProfile) -> Dict[str, Any]:
        """执行PVP战斗"""
        result = self.calculate_battle_result(attacker, defender)
        
        if result["attacker_wins"]:
            # 攻击者胜利
            attacker.cultivation.experience += result["exp_reward"]
            defender.cultivation.experience = max(0, defender.cultivation.experience - result["exp_loss"])
            
            # 更新战斗记录
            attacker.battle_records["wins"] += 1
            defender.battle_records["losses"] += 1
            
            winner = attacker
            loser = defender
        else:
            # 防御者胜利
            defender.cultivation.experience += result["exp_reward"]
            attacker.cultivation.experience = max(0, attacker.cultivation.experience - result["exp_loss"])
            
            # 更新战斗记录
            defender.battle_records["wins"] += 1
            attacker.battle_records["losses"] += 1
            
            winner = defender
            loser = attacker
        
        # 保存用户数据
        await self.data_manager.save_user_data(attacker.user_id, attacker)
        await self.data_manager.save_user_data(defender.user_id, defender)
        
        # 更新服务器统计
        await self.data_manager.update_server_stats("total_battles")
        
        return {
            **result,
            "winner": winner,
            "loser": loser
        }
    
    def generate_monster(self, user_level: int) -> Dict[str, Any]:
        """生成怪物"""
        monster_types = [
            {"name": "野兽", "power_range": (0.7, 1.0)},
            {"name": "妖兽", "power_range": (0.9, 1.3)},
            {"name": "邪修", "power_range": (1.1, 1.5)},
            {"name": "魔物", "power_range": (1.3, 2.0)}
        ]
        
        monster_type = random.choice(monster_types)
        user_power_estimate = user_level * 50  # 粗略估计用户战力
        
        power_min, power_max = monster_type["power_range"]
        monster_power = int(user_power_estimate * random.uniform(power_min, power_max))
        
        names = {
            "野兽": ["狂暴野猪", "巨型黑熊", "闪电豹", "巨蟒"],
            "妖兽": ["赤炎狼王", "冰晶雪豹", "雷鸟", "地龙"],
            "邪修": ["血魔散人", "阴尸道人", "毒蛇老怪", "黑煞魔头"],
            "魔物": ["深渊恶魔", "幽冥骷髅", "炼狱火魔", "虚空魅影"]
        }
        
        monster_name = random.choice(names[monster_type["name"]])
        
        return {
            "name": monster_name,
            "type": monster_type["name"],
            "power": monster_power,
            "level": user_level + random.randint(-1, 2)
        }
    
    async def fight_monster(self, user: UserProfile) -> Dict[str, Any]:
        """与怪物战斗"""
        monster = self.generate_monster(user.cultivation.realm_level)
        user_power = user.get_combat_power()
        
        # 计算胜率
        power_ratio = user_power / (monster["power"] + 1)
        win_rate = min(0.9, max(0.1, power_ratio / (power_ratio + 1)))
        
        # 运气影响
        if "运气极佳" in user.personality_traits:
            win_rate += 0.1
        
        user_wins = random.random() < win_rate
        
        if user_wins:
            # 胜利奖励
            exp_reward = max(15, monster["power"] // 8)
            user.cultivation.experience += exp_reward
            
            result = {
                "victory": True,
                "monster": monster,
                "exp_gained": exp_reward,
                "user_power": user_power,
                "monster_power": monster["power"]
            }
        else:
            # 失败惩罚
            exp_loss = max(5, user.cultivation.experience // 20)
            hp_loss = max(10, user.stats.max_hp // 10)
            
            user.cultivation.experience = max(0, user.cultivation.experience - exp_loss)
            user.stats.current_hp = max(1, user.stats.current_hp - hp_loss)
            
            result = {
                "victory": False,
                "monster": monster,
                "exp_lost": exp_loss,
                "hp_lost": hp_loss,
                "user_power": user_power,
                "monster_power": monster["power"]
            }
        
        await self.data_manager.save_user_data(user.user_id, user)
        return result
