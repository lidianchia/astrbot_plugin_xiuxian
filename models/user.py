from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

@dataclass
class CultivationData:
    """修炼数据"""
    realm_level: int = 1  # 境界等级
    experience: int = 0   # 当前经验
    spiritual_power: int = 100  # 灵力值
    cultivation_points: int = 0  # 修炼点数
    breakthrough_attempts: int = 0  # 突破尝试次数
    last_cultivation_time: Optional[datetime] = None
    last_breakthrough_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "realm_level": self.realm_level,
            "experience": self.experience,
            "spiritual_power": self.spiritual_power,
            "cultivation_points": self.cultivation_points,
            "breakthrough_attempts": self.breakthrough_attempts,
            "last_cultivation_time": self.last_cultivation_time.isoformat() if self.last_cultivation_time else None,
            "last_breakthrough_time": self.last_breakthrough_time.isoformat() if self.last_breakthrough_time else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CultivationData':
        cultivation_data = cls()
        cultivation_data.realm_level = data.get("realm_level", 1)
        cultivation_data.experience = data.get("experience", 0)
        cultivation_data.spiritual_power = data.get("spiritual_power", 100)
        cultivation_data.cultivation_points = data.get("cultivation_points", 0)
        cultivation_data.breakthrough_attempts = data.get("breakthrough_attempts", 0)
        
        if data.get("last_cultivation_time"):
            cultivation_data.last_cultivation_time = datetime.fromisoformat(data["last_cultivation_time"])
        if data.get("last_breakthrough_time"):
            cultivation_data.last_breakthrough_time = datetime.fromisoformat(data["last_breakthrough_time"])
            
        return cultivation_data

@dataclass
class UserStats:
    """用户属性统计"""
    strength: int = 10      # 力量
    agility: int = 10       # 敏捷
    intelligence: int = 10  # 智力
    constitution: int = 10  # 体质
    luck: int = 10         # 运气
    
    # 战斗相关
    attack_power: int = 0   # 攻击力
    defense_power: int = 0  # 防御力
    max_hp: int = 100      # 最大生命值
    current_hp: int = 100  # 当前生命值
    
    def calculate_combat_power(self) -> int:
        """计算战斗力"""
        return (self.strength * 2 + self.agility + self.intelligence + 
                self.constitution + self.attack_power + self.defense_power)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strength": self.strength,
            "agility": self.agility,
            "intelligence": self.intelligence,
            "constitution": self.constitution,
            "luck": self.luck,
            "attack_power": self.attack_power,
            "defense_power": self.defense_power,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserStats':
        stats = cls()
        stats.strength = data.get("strength", 10)
        stats.agility = data.get("agility", 10)
        stats.intelligence = data.get("intelligence", 10)
        stats.constitution = data.get("constitution", 10)
        stats.luck = data.get("luck", 10)
        stats.attack_power = data.get("attack_power", 0)
        stats.defense_power = data.get("defense_power", 0)
        stats.max_hp = data.get("max_hp", 100)
        stats.current_hp = data.get("current_hp", 100)
        return stats

@dataclass
class UserProfile:
    """用户档案"""
    user_id: str
    username: str
    created_at: datetime
    last_active: datetime
    
    # 修炼数据
    cultivation: CultivationData = field(default_factory=CultivationData)
    
    # 属性数据
    stats: UserStats = field(default_factory=UserStats)
    
    # 装备和物品
    equipment: Dict[str, Any] = field(default_factory=dict)
    inventory: List[Dict[str, Any]] = field(default_factory=list)
    
    # 宗门信息
    sect_id: Optional[str] = None
    sect_position: str = "弟子"
    
    # 成就和记录
    achievements: List[str] = field(default_factory=list)
    battle_records: Dict[str, int] = field(default_factory=lambda: {"wins": 0, "losses": 0})
    
    # 个性化数据（用于LLM）
    personality_traits: List[str] = field(default_factory=list)
    story_context: List[Dict[str, Any]] = field(default_factory=list)
    
    def get_realm_name(self) -> str:
        """获取当前境界名称"""
        from utils.constants import REALMS
        for realm in REALMS:
            if realm["level"] == self.cultivation.realm_level:
                return realm["name"]
        return "未知境界"
    
    def get_combat_power(self) -> int:
        """获取战斗力"""
        return self.stats.calculate_combat_power()
    
    def add_experience(self, exp: int):
        """增加经验"""
        self.cultivation.experience += exp
    
    def add_story_context(self, context: Dict[str, Any]):
        """添加故事上下文（用于LLM记忆）"""
        self.story_context.append({
            **context,
            "timestamp": datetime.now().isoformat()
        })
        # 保持最近50条记录
        if len(self.story_context) > 50:
            self.story_context = self.story_context[-50:]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "cultivation": self.cultivation.to_dict(),
            "stats": self.stats.to_dict(),
            "equipment": self.equipment,
            "inventory": self.inventory,
            "sect_id": self.sect_id,
            "sect_position": self.sect_position,
            "achievements": self.achievements,
            "battle_records": self.battle_records,
            "personality_traits": self.personality_traits,
            "story_context": self.story_context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        profile = cls(
            user_id=data["user_id"],
            username=data["username"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_active=datetime.fromisoformat(data["last_active"])
        )
        
        profile.cultivation = CultivationData.from_dict(data.get("cultivation", {}))
        profile.stats = UserStats.from_dict(data.get("stats", {}))
        profile.equipment = data.get("equipment", {})
        profile.inventory = data.get("inventory", [])
        profile.sect_id = data.get("sect_id")
        profile.sect_position = data.get("sect_position", "弟子")
        profile.achievements = data.get("achievements", [])
        profile.battle_records = data.get("battle_records", {"wins": 0, "losses": 0})
        profile.personality_traits = data.get("personality_traits", [])
        profile.story_context = data.get("story_context", [])
        
        return profile
