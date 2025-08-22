import random
from typing import Dict, Any, List, Optional

from models.user import UserProfile
from utils.constants import EQUIPMENT_TYPES, EQUIPMENT_QUALITY

class EquipmentSystem:
    """装备系统"""
    
    def __init__(self, data_manager, llm_manager, config_manager):
        self.data_manager = data_manager
        self.llm_manager = llm_manager
        self.config_manager = config_manager
    
    def generate_equipment(self, user_level: int, equipment_type: str = None) -> Dict[str, Any]:
        """生成装备"""
        if not equipment_type:
            equipment_type = random.choice(list(EQUIPMENT_TYPES.keys()))
        
        # 根据用户等级调整装备品质概率
        quality_weights = [0.4, 0.3, 0.2, 0.08, 0.015, 0.005]  # 对应EQUIPMENT_QUALITY
        
        # 高等级用户更容易获得高品质装备
        if user_level >= 5:
            quality_weights = [0.2, 0.25, 0.25, 0.2, 0.08, 0.02]
        elif user_level >= 8:
            quality_weights = [0.1, 0.15, 0.25, 0.3, 0.15, 0.05]
        
        quality = random.choices(EQUIPMENT_QUALITY, weights=quality_weights)[0]
        
        # 生成装备属性
        base_value = user_level * 10
        equipment_value = int(base_value * quality["bonus"] * random.uniform(0.8, 1.2))
        
        equipment_names = {
            "weapon": {
                "凡品": ["铁剑", "钢刀", "短匕"],
                "良品": ["精钢剑", "寒光刀", "追魂匕"],
                "精品": ["青锋剑", "霜雪刀", "影刺"],
                "极品": ["龙吟剑", "破天刀", "无影匕"],
                "神品": ["天罡剑", "斩魔刀", "鬼哭匕"],
                "仙品": ["太极剑", "诛仙刀", "弑神匕"]
            },
            "armor": {
                "凡品": ["布衣", "皮甲", "铁甲"],
                "良品": ["精钢甲", "云纹袍", "护心镜"],
                "精品": ["蓝纹甲", "法师袍", "龙鳞甲"],
                "极品": ["紫金甲", "星辰袍", "玄武甲"],
                "神品": ["天罡甲", "仙云袍", "神龙甲"],
                "仙品": ["太极袍", "混沌甲", "不朽衣"]
            },
            "accessory": {
                "凡品": ["铜戒", "银镯", "玉佩"],
                "良品": ["金戒", "宝镯", "灵玉"],
                "精品": ["法戒", "法镯", "护身符"],
                "极品": ["灵戒", "仙镯", "天珠"],
                "神品": ["神戒", "圣镯", "混元珠"],
                "仙品": ["仙戒", "道镯", "造化珠"]
            },
            "pill": {
                "凡品": ["回血丹", "补气丹", "疗伤药"],
                "良品": ["小还丹", "聚气丹", "筑基丹"],
                "精品": ["大还丹", "破境丹", "金丹"],
                "极品": ["九转丹", "化神丹", "渡劫丹"],
                "神品": ["仙灵丹", "造化丹", "天道丹"],
                "仙品": ["混沌丹", "太极丹", "无极丹"]
            }
        }
        
        name = random.choice(equipment_names[equipment_type][quality["name"]])
        
        # 根据装备类型设置属性
        attributes = {}
        if equipment_type == "weapon":
            attributes["attack"] = equipment_value
        elif equipment_type == "armor":
            attributes["defense"] = equipment_value
        elif equipment_type == "accessory":
            attributes["hp"] = equipment_value * 2
            attributes["spiritual_power"] = equipment_value
        elif equipment_type == "pill":
            attributes["healing"] = equipment_value
            attributes["exp_bonus"] = equipment_value // 2
        
        return {
            "name": name,
            "type": equipment_type,
            "quality": quality,
            "level": user_level,
            "attributes": attributes,
            "value": equipment_value
        }
    
    def calculate_equipment_effects(self, user: UserProfile) -> Dict[str, int]:
        """计算装备效果"""
        effects = {
            "attack_bonus": 0,
            "defense_bonus": 0,
            "hp_bonus": 0,
            "spiritual_power_bonus": 0
        }
        
        for slot, equipment in user.equipment.items():
            if equipment:
                attrs = equipment.get("attributes", {})
                effects["attack_bonus"] += attrs.get("attack", 0)
                effects["defense_bonus"] += attrs.get("defense", 0)
                effects["hp_bonus"] += attrs.get("hp", 0)
                effects["spiritual_power_bonus"] += attrs.get("spiritual_power", 0)
        
        return effects
    
    def equip_item(self, user: UserProfile, equipment: Dict[str, Any]) -> bool:
        """装备物品"""
        equipment_type = equipment["type"]
        
        # 检查是否有该装备槽位
        valid_slots = {
            "weapon": "weapon_slot",
            "armor": "armor_slot",
            "accessory": "accessory_slot",
            "pill": None  # 丹药直接使用，不装备
        }
        
        if equipment_type == "pill":
            # 丹药直接使用
            self.use_pill(user, equipment)
            return True
        
        slot = valid_slots.get(equipment_type)
        if not slot:
            return False
        
        # 如果已有装备，先卸下
        if slot in user.equipment and user.equipment[slot]:
            old_equipment = user.equipment[slot]
            user.inventory.append(old_equipment)
        
        # 装备新物品
        user.equipment[slot] = equipment
        
        # 更新属性
        self.update_user_stats_from_equipment(user)
        
        return True
    
    def use_pill(self, user: UserProfile, pill: Dict[str, Any]):
        """使用丹药"""
        attrs = pill.get("attributes", {})
        
        # 回复生命值
        healing = attrs.get("healing", 0)
        if healing > 0:
            user.stats.current_hp = min(
                user.stats.max_hp,
                user.stats.current_hp + healing
            )
        
        # 增加经验
        exp_bonus = attrs.get("exp_bonus", 0)
        if exp_bonus > 0:
            user.cultivation.experience += exp_bonus
        
        # 回复灵力
        spiritual_power = attrs.get("spiritual_power", 0)
        if spiritual_power > 0:
            user.cultivation.spiritual_power = min(
                user.cultivation.spiritual_power + spiritual_power,
                user.stats.intelligence * 10  # 最大灵力与智力相关
            )
    
    def update_user_stats_from_equipment(self, user: UserProfile):
        """根据装备更新用户属性"""
        effects = self.calculate_equipment_effects(user)
        
        # 重置到基础属性，然后加上装备加成
        base_attack = user.stats.strength * 2 + user.cultivation.realm_level * 10
        base_defense = user.stats.constitution + user.cultivation.realm_level * 5
        base_hp = user.stats.constitution * 10 + user.cultivation.realm_level * 50
        
        user.stats.attack_power = base_attack + effects["attack_bonus"]
        user.stats.defense_power = base_defense + effects["defense_bonus"]
        user.stats.max_hp = base_hp + effects["hp_bonus"]
        
        # 确保当前生命值不超过最大值
        user.stats.current_hp = min(user.stats.current_hp, user.stats.max_hp)
    
    async def treasure_hunt(self, user: UserProfile) -> Dict[str, Any]:
        """寻宝功能"""
        # 基于用户运气和境界的寻宝成功率
        base_success_rate = 0.6
        luck_bonus = user.stats.luck * 0.02
        realm_bonus = user.cultivation.realm_level * 0.05
        
        success_rate = min(0.9, base_success_rate + luck_bonus + realm_bonus)
        
        if random.random() < success_rate:
            # 寻宝成功
            num_items = random.randint(1, 3)
            treasures = []
            
            for _ in range(num_items):
                # 30% 概率获得高一级的装备
                bonus_level = 1 if random.random() < 0.3 else 0
                treasure = self.generate_equipment(
                    user.cultivation.realm_level + bonus_level
                )
                treasures.append(treasure)
                user.inventory.append(treasure)
            
            return {
                "success": True,
                "treasures": treasures
            }
        else:
            # 寻宝失败
            return {
                "success": False,
                "message": "这次没有找到什么有价值的东西..."
            }
