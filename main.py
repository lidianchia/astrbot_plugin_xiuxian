from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import json
import os
import random
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from models.user import UserProfile, CultivationData
from systems.cultivation_system import CultivationSystem
from systems.battle_system import BattleSystem
from systems.equipment_system import EquipmentSystem
from systems.sect_system import SectSystem
from systems.event_system import EventSystem
from core.llm_integration import LLMManager
from core.game_engine import GameEngine
from utils.data_manager import DataManager
from utils.config_manager import ConfigManager

@register("xiuxian", "lithium", "修仙养成游戏插件，体验修仙之路的乐趣", "2.0.0", "https://github.com/lithium/astrbot_plugin_xiuxian")
class XiuxianPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        
        # 初始化配置管理器
        self.config_manager = ConfigManager(context)
        
        # 初始化核心组件
        self.data_manager = DataManager(context, self.config_manager)
        self.llm_manager = LLMManager(context, self.config_manager)
        self.game_engine = GameEngine(self.data_manager, self.llm_manager, self.config_manager)
        
        # 初始化各个系统
        self.cultivation_system = CultivationSystem(self.data_manager, self.llm_manager, self.config_manager)
        self.battle_system = BattleSystem(self.data_manager, self.llm_manager, self.config_manager)
        self.equipment_system = EquipmentSystem(self.data_manager, self.llm_manager, self.config_manager)
        self.sect_system = SectSystem(self.data_manager, self.llm_manager, self.config_manager)
        self.event_system = EventSystem(self.data_manager, self.llm_manager, self.config_manager)
        
        logger.info("修仙插件初始化完成")

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法"""
        await self.data_manager.initialize()
        await self.llm_manager.initialize()
        logger.info("修仙插件异步初始化完成")

    @filter.command("修仙帮助", "xiuxian", "xianxiu")
    async def help_command(self, event: AstrMessageEvent):
        """查看修仙插件的完整帮助信息，包括所有可用指令和功能介绍"""
        help_text = """
🌟 修仙世界欢迎您 🌟

📖 基础指令：
• /我的信息 - 查看个人修仙资料
• /开始修仙 - 踏入修仙之路
• /修炼 - 进行修炼提升境界
• /突破 - 尝试突破到下一境界

⚔️ 战斗系统：
• /挑战 [@用户] - 挑战其他修仙者
• /历练 - 外出历练获得经验
• /降妖除魔 - 斩杀妖魔获得奖励

🎒 装备系统：
• /我的装备 - 查看当前装备
• /炼器 - 炼制装备
• /寻宝 - 寻找天材地宝

🏛️ 宗门系统：
• /宗门信息 - 查看宗门详情
• /加入宗门 [宗门名] - 加入指定宗门
• /宗门任务 - 查看可接取的宗门任务

🎲 特色功能：
• /修仙故事 - AI生成个性化修仙剧情
• /问道 [问题] - 向AI师傅请教修仙问题
• /占卜 - 预测今日修炼运势

✨ 所有体验都由AI智能生成，每次都有不同的惊喜！
        """
        yield event.plain_result(help_text)

    @filter.command("我的信息", "个人信息", "资料")
    async def user_info(self, event: AstrMessageEvent):
        """查看个人修仙资料，包括境界、经验、战力、装备等详细信息"""
        user_id = event.get_sender_id()
        user_data = await self.data_manager.get_user_data(user_id)
        
        if not user_data:
            yield event.plain_result("您还未踏入修仙之路，请先使用 /开始修仙 指令开启修仙之旅！")
            return
        
        # 使用LLM生成个性化的信息描述
        info_text = await self.llm_manager.generate_user_info_description(user_data)
        yield event.plain_result(info_text)

    @filter.command("开始修仙", "踏入修仙", "开始修炼")
    async def start_cultivation(self, event: AstrMessageEvent):
        """踏入修仙之路，创建修仙档案，开始您的修仙旅程"""
        user_id = event.get_sender_id()
        user_name = event.get_sender_name()
        
        # 检查用户是否已经开始修仙
        existing_data = await self.data_manager.get_user_data(user_id)
        if existing_data:
            yield event.plain_result("您已经踏上修仙之路了！使用 /我的信息 查看当前状态。")
            return
        
        # 创建新用户数据
        new_user = await self.data_manager.create_new_user(user_id, user_name)
        
        # 使用LLM生成个性化的开始修仙故事
        start_story = await self.llm_manager.generate_cultivation_start_story(user_name)
        
        yield event.plain_result(start_story)

    @filter.command("修炼", "打坐", "练功")
    async def cultivate(self, event: AstrMessageEvent):
        """进行修炼提升境界，获得经验值，有几率遇到随机事件"""
        user_id = event.get_sender_id()
        user_data = await self.data_manager.get_user_data(user_id)
        
        if not user_data:
            yield event.plain_result("您还未踏入修仙之路，请先使用 /开始修仙 指令！")
            return
        
        # 检查修炼冷却时间
        if not await self.cultivation_system.can_cultivate(user_data):
            remaining_time = await self.cultivation_system.get_cultivation_cooldown(user_data)
            yield event.plain_result(f"您刚刚修炼过，需要休息 {remaining_time} 后才能再次修炼。")
            return
        
        # 执行修炼
        result = await self.cultivation_system.perform_cultivation(user_data)
        
        # 使用LLM生成修炼过程的生动描述
        cultivation_story = await self.llm_manager.generate_cultivation_story(user_data, result)
        
        # 保存用户数据
        await self.data_manager.save_user_data(user_id, user_data)
        
        yield event.plain_result(cultivation_story)

    @filter.command("突破")
    async def breakthrough(self, event: AstrMessageEvent):
        """尝试突破到更高境界，需要足够的修为经验，成功率基于多种因素"""
        user_id = event.get_sender_id()
        user_data = await self.data_manager.get_user_data(user_id)
        
        if not user_data:
            yield event.plain_result("您还未踏入修仙之路，请先使用 /开始修仙 指令！")
            return
        
        # 检查是否可以突破
        if not await self.cultivation_system.can_breakthrough(user_data):
            yield event.plain_result("您当前的修为还不足以突破，请继续修炼积累经验。")
            return
        
        # 执行突破
        result = await self.cultivation_system.attempt_breakthrough(user_data)
        
        # 使用LLM生成突破过程的故事
        breakthrough_story = await self.llm_manager.generate_breakthrough_story(user_data, result)
        
        # 保存用户数据
        await self.data_manager.save_user_data(user_id, user_data)
        
        yield event.plain_result(breakthrough_story)

    @filter.command("历练", "外出历练", "冒险")
    async def adventure(self, event: AstrMessageEvent):
        """外出历练获得经验和奖励，可能遇到机缘、劫难或奇遇等随机事件"""
        user_id = event.get_sender_id()
        user_data = await self.data_manager.get_user_data(user_id)
        
        if not user_data:
            yield event.plain_result("您还未踏入修仙之路，请先使用 /开始修仙 指令！")
            return
        
        # 检查历练冷却时间
        if not await self.event_system.can_adventure(user_data):
            remaining_time = await self.event_system.get_adventure_cooldown(user_data)
            yield event.plain_result(f"您刚刚历练归来，需要休息 {remaining_time} 后才能再次外出。")
            return
        
        # 执行历练
        result = await self.event_system.perform_adventure(user_data)
        
        # 使用LLM生成历练故事
        adventure_story = await self.llm_manager.generate_adventure_story(user_data, result)
        
        # 保存用户数据
        await self.data_manager.save_user_data(user_id, user_data)
        
        yield event.plain_result(adventure_story)

    @filter.command("挑战")
    async def challenge_user(self, event: AstrMessageEvent):
        """挑战其他修仙者进行 PVP 战斗，胜利者获得经验奖励"""
        # 检查 PVP 功能是否启用
        if not self.config_manager.is_feature_enabled("enable_pvp"):
            yield event.plain_result("玩家对战功能未启用。")
            return
        
        user_id = event.get_sender_id()
        message_str = event.message_str.strip()
        
        # 简单解析目标用户（这里可以根据实际需求改进）
        target_mention = None
        if "@" in message_str:
            # 提取@的用户
            parts = message_str.split("@")
            if len(parts) > 1:
                target_mention = parts[1].strip()
        
        if not target_mention:
            yield event.plain_result("请指定要挑战的对象，格式：/挑战 @用户名")
            return
        
        user_data = await self.data_manager.get_user_data(user_id)
        if not user_data:
            yield event.plain_result("您还未踏入修仙之路，请先使用 /开始修仙 指令！")
            return
        
        # 这里可以添加更复杂的用户查找逻辑
        yield event.plain_result("挑战系统正在开发中，敬请期待！")

    @filter.command("修仙故事", "生成故事")
    async def generate_story(self, event: AstrMessageEvent):
        """使用 AI 生成基于您修仙经历的个性化故事，每次都有不同的内容"""
        # 检查功能是否启用
        if not self.config_manager.is_feature_enabled("enable_ai_stories"):
            yield event.plain_result("AI 故事生成功能未启用。")
            return
        
        user_id = event.get_sender_id()
        user_data = await self.data_manager.get_user_data(user_id)
        
        if not user_data:
            yield event.plain_result("您还未踏入修仙之路，请先使用 /开始修仙 指令！")
            return
        
        # 生成个性化故事
        story = await self.llm_manager.generate_personal_story(user_data)
        yield event.plain_result(story)

    @filter.command("问道")
    async def ask_master(self, event: AstrMessageEvent):
        """向 AI 师傅请教修仙相关问题，获得个性化的修炼建议和指导"""
        user_id = event.get_sender_id()
        message_str = event.message_str.strip()
        
        # 提取问题
        question = message_str.replace("/问道", "").strip()
        if not question:
            yield event.plain_result("请提出您的问题，格式：/问道 您的问题")
            return
        
        user_data = await self.data_manager.get_user_data(user_id)
        if not user_data:
            yield event.plain_result("您还未踏入修仙之路，请先使用 /开始修仙 指令！")
            return
        
        # AI师傅回答问题
        answer = await self.llm_manager.generate_master_advice(user_data, question)
        yield event.plain_result(answer)

    @filter.command("占卜", "运势", "预测")
    async def divination(self, event: AstrMessageEvent):
        """占卜今日修炼运势，预测适合的修炼方式和可能遇到的机缘挑战"""
        # 检查功能是否启用
        if not self.config_manager.is_feature_enabled("enable_daily_fortune"):
            yield event.plain_result("每日运势功能未启用。")
            return
        
        user_id = event.get_sender_id()
        user_data = await self.data_manager.get_user_data(user_id)
        
        if not user_data:
            yield event.plain_result("您还未踏入修仙之路，请先使用 /开始修仙 指令！")
            return
        
        # 生成今日运势
        fortune = await self.llm_manager.generate_daily_fortune(user_data)
        yield event.plain_result(fortune)

    @filter.llm_tool(name="get_cultivation_info")
    async def get_cultivation_info(self, event: AstrMessageEvent, user_name: str) -> MessageEventResult:
        """获取指定用户的修仙信息。

        Args:
            user_name(string): 用户名称
        """
        try:
            # 这里可以根据用户名查找用户信息
            # 简化实现，直接获取当前用户信息
            user_id = event.get_sender_id()
            user_data = await self.data_manager.get_user_data(user_id)
            
            if not user_data:
                yield event.plain_result(f"用户 {user_name} 还未踏入修仙之路")
                return
            
            realm_name = user_data.get_realm_name()
            combat_power = user_data.get_combat_power()
            
            info = f"用户 {user_name} 的修仙信息：\n"
            info += f"境界：{realm_name}\n"
            info += f"经验：{user_data.cultivation.experience}\n" 
            info += f"战力：{combat_power}"
            
            yield event.plain_result(info)
        except Exception as e:
            yield event.plain_result(f"获取修仙信息时发生错误：{str(e)}")

    async def terminate(self):
        """插件销毁方法，当插件被卸载/停用时会调用"""
        try:
            await self.data_manager.close()
            logger.info("修仙插件已安全关闭")
        except Exception as e:
            logger.error(f"插件关闭时发生错误：{e}")