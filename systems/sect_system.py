from typing import Dict, Any, List, Optional
from datetime import datetime

from models.user import UserProfile

class SectSystem:
    """宗门系统"""
    
    def __init__(self, data_manager, llm_manager, config_manager):
        self.data_manager = data_manager
        self.llm_manager = llm_manager
        self.config_manager = config_manager
    
    async def get_available_sects(self) -> List[Dict[str, Any]]:
        """获取可用的宗门列表"""
        sects_data = await self.data_manager.get_game_data("sects", {})
        
        # 如果没有宗门，创建默认宗门
        if not sects_data:
            default_sects = self._create_default_sects()
            await self.data_manager.set_game_data("sects", default_sects)
            sects_data = default_sects
        
        return list(sects_data.values())
    
    def _create_default_sects(self) -> Dict[str, Dict[str, Any]]:
        """创建默认宗门"""
        return {
            "qingyun": {
                "id": "qingyun",
                "name": "青云门",
                "description": "正道宗门，以剑道闻名于世",
                "type": "正道",
                "requirements": {"min_realm": 1},
                "benefits": {
                    "cultivation_bonus": 0.1,
                    "exp_bonus": 0.05
                },
                "members": {},
                "created_at": datetime.now().isoformat()
            },
            "tianmo": {
                "id": "tianmo",
                "name": "天魔宗",
                "description": "魔道宗门，修炼天魔功法",
                "type": "魔道",
                "requirements": {"min_realm": 2},
                "benefits": {
                    "attack_bonus": 0.15,
                    "battle_exp_bonus": 0.1
                },
                "members": {},
                "created_at": datetime.now().isoformat()
            },
            "wudang": {
                "id": "wudang",
                "name": "武当派",
                "description": "道家宗门，修炼太极玄功",
                "type": "道门",
                "requirements": {"min_realm": 1},
                "benefits": {
                    "defense_bonus": 0.1,
                    "breakthrough_bonus": 0.05
                },
                "members": {},
                "created_at": datetime.now().isoformat()
            },
            "emei": {
                "id": "emei",
                "name": "峨眉派",
                "description": "佛门宗门，慈悲为怀",
                "type": "佛门",
                "requirements": {"min_realm": 1},
                "benefits": {
                    "healing_bonus": 0.2,
                    "luck_bonus": 0.1
                },
                "members": {},
                "created_at": datetime.now().isoformat()
            }
        }
    
    async def join_sect(self, user: UserProfile, sect_id: str) -> Dict[str, Any]:
        """加入宗门"""
        if user.sect_id:
            return {
                "success": False,
                "message": f"您已经是{await self.get_sect_name(user.sect_id)}的弟子了！"
            }
        
        sects_data = await self.data_manager.get_game_data("sects", {})
        sect = sects_data.get(sect_id)
        
        if not sect:
            return {
                "success": False,
                "message": "该宗门不存在！"
            }
        
        # 检查加入条件
        requirements = sect.get("requirements", {})
        min_realm = requirements.get("min_realm", 1)
        
        if user.cultivation.realm_level < min_realm:
            return {
                "success": False,
                "message": f"您的境界不足，需要达到第{min_realm}层境界才能加入{sect['name']}！"
            }
        
        # 加入宗门
        user.sect_id = sect_id
        user.sect_position = "外门弟子"
        
        # 更新宗门成员列表
        if "members" not in sect:
            sect["members"] = {}
        
        sect["members"][user.user_id] = {
            "username": user.username,
            "position": "外门弟子",
            "joined_at": datetime.now().isoformat(),
            "contribution": 0
        }
        
        # 保存数据
        await self.data_manager.set_game_data("sects", sects_data)
        
        return {
            "success": True,
            "message": f"恭喜您成功加入{sect['name']}，成为外门弟子！",
            "sect": sect
        }
    
    async def leave_sect(self, user: UserProfile) -> Dict[str, Any]:
        """离开宗门"""
        if not user.sect_id:
            return {
                "success": False,
                "message": "您还没有加入任何宗门！"
            }
        
        sect_name = await self.get_sect_name(user.sect_id)
        
        # 从宗门成员列表中移除
        sects_data = await self.data_manager.get_game_data("sects", {})
        if user.sect_id in sects_data:
            sect = sects_data[user.sect_id]
            if "members" in sect and user.user_id in sect["members"]:
                del sect["members"][user.user_id]
                await self.data_manager.set_game_data("sects", sects_data)
        
        # 清除用户的宗门信息
        user.sect_id = None
        user.sect_position = "散修"
        
        return {
            "success": True,
            "message": f"您已离开{sect_name}，重新成为散修。"
        }
    
    async def get_sect_info(self, sect_id: str) -> Optional[Dict[str, Any]]:
        """获取宗门信息"""
        sects_data = await self.data_manager.get_game_data("sects", {})
        return sects_data.get(sect_id)
    
    async def get_sect_name(self, sect_id: str) -> str:
        """获取宗门名称"""
        sect = await self.get_sect_info(sect_id)
        return sect["name"] if sect else "未知宗门"
    
    async def get_user_sect_info(self, user: UserProfile) -> Optional[Dict[str, Any]]:
        """获取用户所在宗门的信息"""
        if not user.sect_id:
            return None
        return await self.get_sect_info(user.sect_id)
    
    async def get_sect_benefits(self, user: UserProfile) -> Dict[str, float]:
        """获取宗门福利"""
        if not user.sect_id:
            return {}
        
        sect = await self.get_sect_info(user.sect_id)
        if not sect:
            return {}
        
        return sect.get("benefits", {})
    
    async def apply_sect_benefits(self, user: UserProfile, action_type: str, base_value: float) -> float:
        """应用宗门福利"""
        benefits = await self.get_sect_benefits(user)
        
        if action_type == "cultivation" and "cultivation_bonus" in benefits:
            return base_value * (1 + benefits["cultivation_bonus"])
        elif action_type == "battle" and "battle_exp_bonus" in benefits:
            return base_value * (1 + benefits["battle_exp_bonus"])
        elif action_type == "breakthrough" and "breakthrough_bonus" in benefits:
            return base_value * (1 + benefits["breakthrough_bonus"])
        
        return base_value
    
    async def get_sect_tasks(self, user: UserProfile) -> List[Dict[str, Any]]:
        """获取宗门任务"""
        if not user.sect_id:
            return []
        
        # 生成基础宗门任务
        tasks = [
            {
                "id": "daily_cultivation",
                "name": "日常修炼",
                "description": "完成一次修炼",
                "type": "daily",
                "requirements": {"cultivate": 1},
                "rewards": {"sect_contribution": 10, "exp": 50},
                "completed": False
            },
            {
                "id": "weekly_battle",
                "name": "降妖除魔",
                "description": "与妖兽战斗3次",
                "type": "weekly",
                "requirements": {"monster_battles": 3},
                "rewards": {"sect_contribution": 50, "exp": 200},
                "completed": False
            },
            {
                "id": "monthly_breakthrough",
                "name": "突破挑战",
                "description": "尝试突破一次",
                "type": "monthly",
                "requirements": {"breakthrough": 1},
                "rewards": {"sect_contribution": 100, "special_item": "筑基丹"},
                "completed": False
            }
        ]
        
        return tasks
