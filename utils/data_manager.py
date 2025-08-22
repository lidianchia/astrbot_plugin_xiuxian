import json
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from astrbot.api.star import Context
from astrbot.api import logger

from models.user import UserProfile, CultivationData, UserStats

class DataManager:
    """数据管理器 - 负责用户数据的存储和读取"""
    
    def __init__(self, context: Context, config_manager):
        self.context = context
        self.config_manager = config_manager
        # 根据 AstrBot 文档，使用 context.base_config.data_dir 作为数据目录
        # 插件数据应该存放在独立的子目录中
        self.data_dir = os.path.join(context.base_config.data_dir, "plugins", "xiuxian")
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.game_data_file = os.path.join(self.data_dir, "game_data.json")
        
        # 内存缓存
        self._user_cache: Dict[str, UserProfile] = {}
        self._game_data_cache: Dict[str, Any] = {}
        
    async def initialize(self):
        """初始化数据管理器"""
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 加载用户数据
        await self._load_users()
        
        # 加载游戏数据
        await self._load_game_data()
        
        logger.info(f"数据管理器初始化完成，数据目录：{self.data_dir}")
    
    async def _load_users(self):
        """加载用户数据"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                    
                for user_id, user_data in users_data.items():
                    self._user_cache[user_id] = UserProfile.from_dict(user_data)
                    
                logger.info(f"加载了 {len(self._user_cache)} 个用户数据")
            except Exception as e:
                logger.error(f"加载用户数据失败：{e}")
                self._user_cache = {}
        else:
            self._user_cache = {}
    
    async def _load_game_data(self):
        """加载游戏数据"""
        if os.path.exists(self.game_data_file):
            try:
                with open(self.game_data_file, 'r', encoding='utf-8') as f:
                    self._game_data_cache = json.load(f)
                logger.info("游戏数据加载完成")
            except Exception as e:
                logger.error(f"加载游戏数据失败：{e}")
                self._game_data_cache = {}
        else:
            self._game_data_cache = {
                "sects": {},
                "global_events": [],
                "server_stats": {
                    "total_users": 0,
                    "total_cultivations": 0,
                    "total_battles": 0
                }
            }
    
    async def get_user_data(self, user_id: str) -> Optional[UserProfile]:
        """获取用户数据"""
        return self._user_cache.get(user_id)
    
    async def save_user_data(self, user_id: str, user_data: UserProfile):
        """保存用户数据"""
        user_data.last_active = datetime.now()
        self._user_cache[user_id] = user_data
        
        # 异步保存到文件
        asyncio.create_task(self._save_users_to_file())
    
    async def create_new_user(self, user_id: str, username: str) -> UserProfile:
        """创建新用户"""
        now = datetime.now()
        new_user = UserProfile(
            user_id=user_id,
            username=username,
            created_at=now,
            last_active=now
        )
        
        # 随机生成一些个性化特质
        import random
        personality_pool = [
            "勤奋刻苦", "天赋异禀", "运气极佳", "意志坚定", "心境平和",
            "好奇心强", "谨慎小心", "勇敢无畏", "智慧过人", "仁慈善良"
        ]
        new_user.personality_traits = random.sample(personality_pool, 3)
        
        self._user_cache[user_id] = new_user
        await self._save_users_to_file()
        
        # 更新服务器统计
        self._game_data_cache["server_stats"]["total_users"] += 1
        await self._save_game_data_to_file()
        
        logger.info(f"创建新用户：{username} ({user_id})")
        return new_user
    
    async def _save_users_to_file(self):
        """保存用户数据到文件"""
        try:
            users_data = {}
            for user_id, user_profile in self._user_cache.items():
                users_data[user_id] = user_profile.to_dict()
            
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存用户数据失败：{e}")
    
    async def _save_game_data_to_file(self):
        """保存游戏数据到文件"""
        try:
            with open(self.game_data_file, 'w', encoding='utf-8') as f:
                json.dump(self._game_data_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存游戏数据失败：{e}")
    
    async def get_game_data(self, key: str, default=None):
        """获取游戏数据"""
        return self._game_data_cache.get(key, default)
    
    async def set_game_data(self, key: str, value: Any):
        """设置游戏数据"""
        self._game_data_cache[key] = value
        await self._save_game_data_to_file()
    
    async def get_server_stats(self) -> Dict[str, Any]:
        """获取服务器统计数据"""
        return self._game_data_cache.get("server_stats", {})
    
    async def update_server_stats(self, stat_key: str, increment: int = 1):
        """更新服务器统计"""
        if "server_stats" not in self._game_data_cache:
            self._game_data_cache["server_stats"] = {}
        
        current_value = self._game_data_cache["server_stats"].get(stat_key, 0)
        self._game_data_cache["server_stats"][stat_key] = current_value + increment
        
        await self._save_game_data_to_file()
    
    async def get_top_users_by_realm(self, limit: int = 10) -> list:
        """获取境界排行榜"""
        users = list(self._user_cache.values())
        users.sort(key=lambda u: (u.cultivation.realm_level, u.cultivation.experience), reverse=True)
        return users[:limit]
    
    async def get_top_users_by_combat_power(self, limit: int = 10) -> list:
        """获取战力排行榜"""
        users = list(self._user_cache.values())
        users.sort(key=lambda u: u.get_combat_power(), reverse=True)
        return users[:limit]
    
    async def close(self):
        """关闭数据管理器"""
        await self._save_users_to_file()
        await self._save_game_data_to_file()
        logger.info("数据管理器已关闭")
