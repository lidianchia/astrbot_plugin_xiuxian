import asyncio
import json
import random
from typing import Dict, Any, List, Optional
from astrbot.api.star import Context
from astrbot.api import logger

from models.user import UserProfile
from utils.constants import REALMS, DEFAULT_LLM_CONFIG

class LLMManager:
    """LLM 管理器 - 负责与AI模型的交互"""
    
    def __init__(self, context: Context, config_manager):
        self.context = context
        self.config_manager = config_manager
        self.llm_client = None
        self.prompt_templates = {}
        
    async def initialize(self):
        """初始化LLM管理器"""
        try:
            # 尝试初始化LLM客户端
            await self._initialize_llm_client()
            
            # 加载提示词模板
            await self._load_prompt_templates()
            
            logger.info("LLM管理器初始化完成")
        except Exception as e:
            logger.warning(f"LLM初始化失败，将使用备用文本生成：{e}")
    
    async def _initialize_llm_client(self):
        """初始化LLM客户端"""
        # 这里可以根据配置选择不同的LLM服务
        # 暂时使用模拟实现
        self.llm_client = MockLLMClient()
    
    async def _load_prompt_templates(self):
        """加载提示词模板"""
        self.prompt_templates = {
            "user_info": """
你是一位修仙世界的智者，请根据以下信息生成一段生动的个人资料描述：

修仙者姓名：{username}
当前境界：{realm_name}
修为经验：{experience}
战斗力：{combat_power}
个性特质：{personality}
最近经历：{recent_context}

请用修仙小说的语言风格，生成一段200字左右的个人介绍，要体现出修仙者的风采和当前状态。
            """,
            
            "cultivation_start": """
欢迎{username}踏入修仙之路！

请生成一段修仙开始的故事，描述一个凡人如何因缘际会踏入修仙世界，字数控制在300字左右。
要包含：
- 奇遇或机缘
- 初次感受到灵气
- 获得修炼功法
- 对未来的憧憬

语言要生动有趣，富有修仙世界的韵味。
            """,
            
            "cultivation_story": """
{username}正在{realm_name}境界修炼，获得了{experience}点经验。

请根据以下情况生成修炼过程的描述：
- 当前境界：{realm_name}
- 修炼结果：{result_type}
- 个性特质：{personality}
- 修炼环境：随机选择一个有趣的地点

生成200字左右的修炼过程描述，要体现修炼的感受和收获。
            """,
            
            "breakthrough_story": """
{username}正在尝试从{current_realm}突破到下一境界。

突破结果：{success}
请生成突破过程的描述：
- 如果成功：描述突破时的感悟、力量提升、境界变化
- 如果失败：描述失败的原因、经验教训、继续努力的决心

字数300字左右，要有修仙小说的紧张感和仪式感。
            """,
            
            "adventure_story": """
{username}外出历练，经历了一次{event_type}。

请生成历练故事：
- 修仙者境界：{realm_name}
- 事件类型：{event_type}
- 收获结果：{rewards}
- 个性特质：{personality}

创造一个有趣的历练故事，包含遭遇、挑战、解决过程和收获，300字左右。
            """,
            
            "personal_story": """
为{username}生成一个个性化的修仙故事片段。

角色信息：
- 境界：{realm_name}
- 特质：{personality}
- 历史经历：{story_context}

请创造一个独特的修仙故事片段，可以是：
- 感悟道法的心得
- 遇到神秘高人
- 发现隐秘之地
- 悟出新的修炼心法

故事要新颖有趣，400字左右。
            """,
            
            "master_advice": """
你是一位修仙界的高深前辈，{username}向你请教问题："{question}"

根据提问者的信息回答：
- 境界：{realm_name}
- 特质：{personality}

请用智者的语调回答，要包含：
- 对问题的深入理解
- 修仙哲理和道理
- 具体的建议或指导
- 鼓励和启发

回答要有修仙世界的韵味，200字左右。
            """,
            
            "daily_fortune": """
为修仙者{username}生成今日修炼运势。

角色信息：
- 境界：{realm_name}
- 特质：{personality}

请生成包含以下内容的运势预测：
- 今日修炼运势（好/中/差）
- 适合的修炼方式
- 需要注意的事项
- 可能遇到的机缘或挑战
- 给出一句修仙格言

要有神秘感和指导性，150字左右。
            """
        }
    
    async def generate_user_info_description(self, user_data: UserProfile) -> str:
        """生成用户信息描述"""
        try:
            realm_name = user_data.get_realm_name()
            combat_power = user_data.get_combat_power()
            personality = "、".join(user_data.personality_traits)
            
            # 获取最近的故事上下文
            recent_context = ""
            if user_data.story_context:
                recent_context = user_data.story_context[-1].get("summary", "初入修仙世界")
            
            prompt = self.prompt_templates["user_info"].format(
                username=user_data.username,
                realm_name=realm_name,
                experience=user_data.cultivation.experience,
                combat_power=combat_power,
                personality=personality,
                recent_context=recent_context
            )
            
            if self.llm_client:
                response = await self.llm_client.generate(prompt)
                return response
            else:
                return self._generate_fallback_user_info(user_data)
                
        except Exception as e:
            logger.error(f"生成用户信息描述失败：{e}")
            return self._generate_fallback_user_info(user_data)
    
    async def generate_cultivation_start_story(self, username: str) -> str:
        """生成修仙开始故事"""
        try:
            prompt = self.prompt_templates["cultivation_start"].format(username=username)
            
            if self.llm_client:
                response = await self.llm_client.generate(prompt)
                return response
            else:
                return self._generate_fallback_start_story(username)
                
        except Exception as e:
            logger.error(f"生成开始故事失败：{e}")
            return self._generate_fallback_start_story(username)
    
    async def generate_cultivation_story(self, user_data: UserProfile, result: Dict[str, Any]) -> str:
        """生成修炼故事"""
        try:
            realm_name = user_data.get_realm_name()
            personality = "、".join(user_data.personality_traits)
            
            prompt = self.prompt_templates["cultivation_story"].format(
                username=user_data.username,
                realm_name=realm_name,
                experience=result.get("exp_gained", 0),
                result_type=result.get("type", "normal"),
                personality=personality
            )
            
            if self.llm_client:
                response = await self.llm_client.generate(prompt)
                # 添加到用户故事上下文
                user_data.add_story_context({
                    "type": "cultivation",
                    "summary": f"修炼获得{result.get('exp_gained', 0)}经验"
                })
                return response
            else:
                return self._generate_fallback_cultivation_story(user_data, result)
                
        except Exception as e:
            logger.error(f"生成修炼故事失败：{e}")
            return self._generate_fallback_cultivation_story(user_data, result)
    
    async def generate_breakthrough_story(self, user_data: UserProfile, result: Dict[str, Any]) -> str:
        """生成突破故事"""
        try:
            current_realm = user_data.get_realm_name()
            success = result.get("success", False)
            
            prompt = self.prompt_templates["breakthrough_story"].format(
                username=user_data.username,
                current_realm=current_realm,
                success="成功" if success else "失败"
            )
            
            if self.llm_client:
                response = await self.llm_client.generate(prompt)
                user_data.add_story_context({
                    "type": "breakthrough",
                    "summary": f"突破{'成功' if success else '失败'}"
                })
                return response
            else:
                return self._generate_fallback_breakthrough_story(user_data, result)
                
        except Exception as e:
            logger.error(f"生成突破故事失败：{e}")
            return self._generate_fallback_breakthrough_story(user_data, result)
    
    async def generate_adventure_story(self, user_data: UserProfile, result: Dict[str, Any]) -> str:
        """生成历练故事"""
        try:
            realm_name = user_data.get_realm_name()
            personality = "、".join(user_data.personality_traits)
            event_type = result.get("event_type", "普通历练")
            rewards = result.get("rewards", "修炼经验")
            
            prompt = self.prompt_templates["adventure_story"].format(
                username=user_data.username,
                realm_name=realm_name,
                event_type=event_type,
                rewards=rewards,
                personality=personality
            )
            
            if self.llm_client:
                response = await self.llm_client.generate(prompt)
                user_data.add_story_context({
                    "type": "adventure",
                    "summary": f"历练遇到{event_type}"
                })
                return response
            else:
                return self._generate_fallback_adventure_story(user_data, result)
                
        except Exception as e:
            logger.error(f"生成历练故事失败：{e}")
            return self._generate_fallback_adventure_story(user_data, result)
    
    async def generate_personal_story(self, user_data: UserProfile) -> str:
        """生成个性化故事"""
        try:
            realm_name = user_data.get_realm_name()
            personality = "、".join(user_data.personality_traits)
            story_context = ""
            
            if user_data.story_context:
                recent_stories = user_data.story_context[-3:]
                story_context = "；".join([ctx.get("summary", "") for ctx in recent_stories])
            
            prompt = self.prompt_templates["personal_story"].format(
                username=user_data.username,
                realm_name=realm_name,
                personality=personality,
                story_context=story_context
            )
            
            if self.llm_client:
                response = await self.llm_client.generate(prompt)
                return response
            else:
                return self._generate_fallback_personal_story(user_data)
                
        except Exception as e:
            logger.error(f"生成个人故事失败：{e}")
            return self._generate_fallback_personal_story(user_data)
    
    async def generate_master_advice(self, user_data: UserProfile, question: str) -> str:
        """生成师傅建议"""
        try:
            realm_name = user_data.get_realm_name()
            personality = "、".join(user_data.personality_traits)
            
            prompt = self.prompt_templates["master_advice"].format(
                username=user_data.username,
                question=question,
                realm_name=realm_name,
                personality=personality
            )
            
            if self.llm_client:
                response = await self.llm_client.generate(prompt)
                return f"🧙‍♂️ 师傅说道：\n\n{response}"
            else:
                return self._generate_fallback_master_advice(user_data, question)
                
        except Exception as e:
            logger.error(f"生成师傅建议失败：{e}")
            return self._generate_fallback_master_advice(user_data, question)
    
    async def generate_daily_fortune(self, user_data: UserProfile) -> str:
        """生成每日运势"""
        try:
            realm_name = user_data.get_realm_name()
            personality = "、".join(user_data.personality_traits)
            
            prompt = self.prompt_templates["daily_fortune"].format(
                username=user_data.username,
                realm_name=realm_name,
                personality=personality
            )
            
            if self.llm_client:
                response = await self.llm_client.generate(prompt)
                return f"🔮 今日运势：\n\n{response}"
            else:
                return self._generate_fallback_daily_fortune(user_data)
                
        except Exception as e:
            logger.error(f"生成每日运势失败：{e}")
            return self._generate_fallback_daily_fortune(user_data)
    
    # 备用文本生成方法
    def _generate_fallback_user_info(self, user_data: UserProfile) -> str:
        realm_name = user_data.get_realm_name()
        combat_power = user_data.get_combat_power()
        personality = "、".join(user_data.personality_traits)
        
        return f"""
🌟 修仙者档案 🌟

姓名：{user_data.username}
境界：{realm_name}
修为：{user_data.cultivation.experience} 点经验
战力：{combat_power}
灵力：{user_data.cultivation.spiritual_power}

个性特质：{personality}

{user_data.username}乃是一位{personality}的修仙者，目前已达{realm_name}境界，在修仙路上稳步前行。其战力{combat_power}，在同境界中{self._get_power_level_desc(combat_power)}。
        """
    
    def _generate_fallback_start_story(self, username: str) -> str:
        stories = [
            f"夜深人静，{username}在山间行走时突然感受到一股神秘的灵气波动。跟随着灵气的指引，发现了一本古老的修炼秘籍。翻开第一页，金光闪闪的文字映入眼帘：'修仙之路，始于今日。'从此，{username}踏上了修仙之路！",
            f"{username}在偶然间救助了一位受伤的老者，老者为了感谢救命之恩，传授了{username}一套基础的修炼心法。'小友，你有修仙的资质，愿你在这条路上走得更远。'说完，老者便消失在晨光中，留下了满怀憧憬的{username}。",
            f"一颗流星划过夜空，正好落在{username}面前。流星化作一块玉佩，散发着温润的光芒。当{username}触摸玉佩的瞬间，脑海中涌现出无数修炼口诀。原来这是上古修仙者留下的传承，{username}因此获得了修仙的机缘！"
        ]
        return random.choice(stories)
    
    def _generate_fallback_cultivation_story(self, user_data: UserProfile, result: Dict[str, Any]) -> str:
        exp_gained = result.get("exp_gained", 0)
        environments = ["幽静山洞", "灵气充沛的竹林", "古老的道观", "云雾缭绕的山峰", "星空下的湖畔"]
        environment = random.choice(environments)
        
        return f"""
🧘‍♂️ 修炼感悟

{user_data.username}在{environment}中静心修炼，感受着天地间的灵气缓缓汇聚。随着功法的运转，丹田内的灵力如春水般温润流淌。

经过一番苦修，{user_data.username}的修为有所增进，获得了{exp_gained}点修炼经验。在{user_data.get_realm_name()}的境界中，每一分进步都来之不易。

'修仙路漫漫，唯有持之以恒方能登临绝顶。'
        """
    
    def _generate_fallback_breakthrough_story(self, user_data: UserProfile, result: Dict[str, Any]) -> str:
        success = result.get("success", False)
        current_realm = user_data.get_realm_name()
        
        if success:
            return f"""
✨ 突破成功！

{user_data.username}盘坐修炼，感受到境界瓶颈开始松动。天地灵气如洪流般涌入体内，丹田内的灵力急速旋转，发出阵阵轰鸣。

突然，一道金光从天灵盖冲出，{user_data.username}成功突破到了更高境界！实力大增，对道法的理解更加深刻。

'山重水复疑无路，柳暗花明又一村。'突破的喜悦让{user_data.username}对未来充满了信心！
            """
        else:
            return f"""
💫 突破失败

{user_data.username}尝试冲击更高境界，但在关键时刻感受到了强大的阻力。境界瓶颈如铁壁铜墙般坚固，任凭如何努力都无法突破。

虽然这次突破失败了，但{user_data.username}从中获得了宝贵的经验。明白了自己的不足，也更加清楚了前进的方向。

'失败乃成功之母，每一次的挫折都是成长的阶梯。'{user_data.username}没有气馁，而是更加坚定了修炼的决心！
            """
    
    def _generate_fallback_adventure_story(self, user_data: UserProfile, result: Dict[str, Any]) -> str:
        adventures = [
            f"{user_data.username}在深山中遇到了一群妖兽，经过激烈的战斗后成功击败了它们，获得了珍贵的修炼资源。",
            f"{user_data.username}发现了一处隐秘的灵泉，在其中修炼获得了意想不到的收获。",
            f"{user_data.username}遇到了一位神秘的前辈高人，获得了宝贵的修炼指导。",
            f"{user_data.username}在古老的遗迹中找到了一些珍贵的丹药和法器。"
        ]
        return random.choice(adventures)
    
    def _generate_fallback_personal_story(self, user_data: UserProfile) -> str:
        stories = [
            f"在修炼的过程中，{user_data.username}突然悟出了一个新的心法诀窍，对修仙之道有了更深的理解。",
            f"{user_data.username}在梦中见到了一位仙人，仙人传授了一些修炼的秘诀。",
            f"观察自然万物的变化，{user_data.username}对天地大道有了新的感悟。"
        ]
        return random.choice(stories)
    
    def _generate_fallback_master_advice(self, user_data: UserProfile, question: str) -> str:
        advices = [
            "修仙之路贵在坚持，切勿急躁冒进。",
            "心境平和是修炼的根本，保持内心的宁静很重要。",
            "多观察自然，从中领悟天地大道的奥秘。",
            "与人为善，修仙也要修心，德行与实力同样重要。"
        ]
        return f"🧙‍♂️ 师傅说道：\n\n{random.choice(advices)}"
    
    def _generate_fallback_daily_fortune(self, user_data: UserProfile) -> str:
        fortunes = [
            "今日灵气充沛，适合静心修炼，可能会有意外的收获。",
            "今日运势平稳，适合巩固基础，不宜冒险。",
            "今日吉星高照，外出历练可能会遇到机缘。",
            "今日需要谨慎，修炼时要格外小心，避免走火入魔。"
        ]
        return f"🔮 今日运势：\n\n{random.choice(fortunes)}"
    
    def _get_power_level_desc(self, combat_power: int) -> str:
        if combat_power < 50:
            return "实力尚浅"
        elif combat_power < 100:
            return "小有所成"
        elif combat_power < 200:
            return "颇有实力"
        elif combat_power < 500:
            return "实力不俗"
        else:
            return "实力强悍"


class MockLLMClient:
    """模拟LLM客户端，用于测试"""
    
    async def generate(self, prompt: str) -> str:
        # 模拟网络延迟
        await asyncio.sleep(0.1)
        
        # 返回模拟响应
        return "这是一个模拟的AI响应，实际使用时会连接真实的LLM服务。"
