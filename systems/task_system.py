from datetime import datetime, timedelta
from typing import Dict, Any, List

from models.user import UserProfile

class TaskSystem:
    """任务系统"""
    
    def __init__(self, data_manager, llm_manager, config_manager):
        self.data_manager = data_manager
        self.llm_manager = llm_manager
        self.config_manager = config_manager
    
    async def get_daily_tasks(self, user: UserProfile) -> List[Dict[str, Any]]:
        """获取每日任务"""
        tasks = [
            {
                "id": "daily_cultivation",
                "name": "日常修炼",
                "description": "完成一次修炼",
                "type": "daily",
                "progress": 0,
                "target": 1,
                "rewards": {
                    "exp": 100,
                    "spiritual_power": 50
                },
                "completed": False
            },
            {
                "id": "daily_battle",
                "name": "历练战斗",
                "description": "进行一次历练",
                "type": "daily", 
                "progress": 0,
                "target": 1,
                "rewards": {
                    "exp": 150,
                    "cultivation_points": 5
                },
                "completed": False
            },
            {
                "id": "daily_login",
                "name": "签到修炼",
                "description": "每日登录签到",
                "type": "daily",
                "progress": 1,
                "target": 1,
                "rewards": {
                    "exp": 50,
                    "spiritual_power": 30
                },
                "completed": True  # 登录即完成
            }
        ]
        
        # 检查任务完成状态
        user_tasks = await self.get_user_task_progress(user)
        for task in tasks:
            task_id = task["id"]
            if task_id in user_tasks:
                progress_data = user_tasks[task_id]
                task["progress"] = progress_data.get("progress", 0)
                task["completed"] = progress_data.get("completed", False)
        
        return tasks
    
    async def get_weekly_tasks(self, user: UserProfile) -> List[Dict[str, Any]]:
        """获取每周任务"""
        tasks = [
            {
                "id": "weekly_cultivation",
                "name": "修炼大师",
                "description": "本周完成10次修炼",
                "type": "weekly",
                "progress": 0,
                "target": 10,
                "rewards": {
                    "exp": 500,
                    "special_item": "筑基丹"
                },
                "completed": False
            },
            {
                "id": "weekly_battle",
                "name": "降妖除魔",
                "description": "本周击败5只妖兽",
                "type": "weekly",
                "progress": 0,
                "target": 5,
                "rewards": {
                    "exp": 800,
                    "equipment": "随机装备"
                },
                "completed": False
            },
            {
                "id": "weekly_breakthrough",
                "name": "境界突破",
                "description": "本周尝试突破3次",
                "type": "weekly",
                "progress": 0,
                "target": 3,
                "rewards": {
                    "cultivation_points": 50,
                    "spiritual_power": 200
                },
                "completed": False
            }
        ]
        
        # 检查任务完成状态
        user_tasks = await self.get_user_task_progress(user)
        for task in tasks:
            task_id = task["id"]
            if task_id in user_tasks:
                progress_data = user_tasks[task_id]
                task["progress"] = progress_data.get("progress", 0)
                task["completed"] = progress_data.get("completed", False)
        
        return tasks
    
    async def get_user_task_progress(self, user: UserProfile) -> Dict[str, Any]:
        """获取用户任务进度"""
        # 从用户数据中获取任务进度，这里简化处理
        # 实际项目中可能需要单独的任务进度存储
        return getattr(user, 'task_progress', {})
    
    async def update_task_progress(self, user: UserProfile, task_type: str, increment: int = 1):
        """更新任务进度"""
        if not hasattr(user, 'task_progress'):
            user.task_progress = {}
        
        today = datetime.now().strftime("%Y-%m-%d")
        this_week = datetime.now().strftime("%Y-W%U")
        
        # 更新每日任务
        if task_type == "cultivation":
            daily_key = f"daily_cultivation_{today}"
            self._update_single_task_progress(user, daily_key, increment, 1)
            
            # 同时更新周任务
            weekly_key = f"weekly_cultivation_{this_week}"
            self._update_single_task_progress(user, weekly_key, increment, 10)
        
        elif task_type == "battle":
            daily_key = f"daily_battle_{today}"
            self._update_single_task_progress(user, daily_key, increment, 1)
            
            # 同时更新周任务
            weekly_key = f"weekly_battle_{this_week}"
            self._update_single_task_progress(user, weekly_key, increment, 5)
        
        elif task_type == "breakthrough":
            weekly_key = f"weekly_breakthrough_{this_week}"
            self._update_single_task_progress(user, weekly_key, increment, 3)
    
    def _update_single_task_progress(self, user: UserProfile, task_key: str, increment: int, target: int):
        """更新单个任务进度"""
        if task_key not in user.task_progress:
            user.task_progress[task_key] = {"progress": 0, "completed": False}
        
        task_data = user.task_progress[task_key]
        if not task_data["completed"]:
            task_data["progress"] = min(task_data["progress"] + increment, target)
            
            if task_data["progress"] >= target:
                task_data["completed"] = True
    
    async def claim_task_reward(self, user: UserProfile, task_id: str) -> Dict[str, Any]:
        """领取任务奖励"""
        # 获取任务信息
        daily_tasks = await self.get_daily_tasks(user)
        weekly_tasks = await self.get_weekly_tasks(user)
        all_tasks = daily_tasks + weekly_tasks
        
        task = None
        for t in all_tasks:
            if t["id"] == task_id:
                task = t
                break
        
        if not task:
            return {"success": False, "message": "任务不存在"}
        
        if not task["completed"]:
            return {"success": False, "message": "任务尚未完成"}
        
        # 检查是否已经领取过奖励
        claimed_key = f"{task_id}_claimed"
        if hasattr(user, 'claimed_rewards') and claimed_key in user.claimed_rewards:
            return {"success": False, "message": "奖励已经领取过了"}
        
        # 发放奖励
        rewards = task["rewards"]
        reward_text = []
        
        if "exp" in rewards:
            user.cultivation.experience += rewards["exp"]
            reward_text.append(f"经验+{rewards['exp']}")
        
        if "spiritual_power" in rewards:
            max_sp = user.stats.intelligence * 10
            user.cultivation.spiritual_power = min(
                user.cultivation.spiritual_power + rewards["spiritual_power"],
                max_sp
            )
            reward_text.append(f"灵力+{rewards['spiritual_power']}")
        
        if "cultivation_points" in rewards:
            user.cultivation.cultivation_points += rewards["cultivation_points"]
            reward_text.append(f"修炼点+{rewards['cultivation_points']}")
        
        if "special_item" in rewards:
            # 添加特殊物品到背包
            item = {
                "name": rewards["special_item"],
                "type": "pill",
                "quality": {"name": "良品", "color": "green"},
                "attributes": {"healing": 100, "exp_bonus": 50}
            }
            user.inventory.append(item)
            reward_text.append(f"获得{rewards['special_item']}")
        
        if "equipment" in rewards:
            # 生成随机装备
            from systems.equipment_system import EquipmentSystem
            equipment_system = EquipmentSystem(self.data_manager, self.llm_manager)
            equipment = equipment_system.generate_equipment(user.cultivation.realm_level)
            user.inventory.append(equipment)
            reward_text.append(f"获得{equipment['name']}")
        
        # 标记奖励已领取
        if not hasattr(user, 'claimed_rewards'):
            user.claimed_rewards = set()
        user.claimed_rewards.add(claimed_key)
        
        return {
            "success": True,
            "message": f"成功领取任务奖励：{', '.join(reward_text)}",
            "rewards": reward_text
        }
    
    async def reset_daily_tasks(self):
        """重置每日任务（定时任务）"""
        # 这个方法可以被定时器调用来重置每日任务
        # 实际实现中需要遍历所有用户并重置他们的每日任务进度
        pass
    
    async def reset_weekly_tasks(self):
        """重置每周任务（定时任务）"""
        # 这个方法可以被定时器调用来重置每周任务
        pass
