'''
成就系统 - 玩家成就追踪、解锁条件、奖励发放
工业级标准：类型注解、文档字符串、错误处理、数据持久化
'''

from typing import Dict, List, Optional, Tuple, Any, Callable
from data.src.const import *
from data.src.settings import settings
from enum import Enum
import pygame
import json
import os
from datetime import datetime


class AchievementCategory(Enum):
    """成就分类枚举"""
    COMBAT = 'combat'  # 战斗类
    ECONOMY = 'economy'  # 经济类
    SURVIVAL = 'survival'  # 生存类
    COLLECTION = 'collection'  # 收集类
    SPECIAL = 'special'  # 特殊类


class AchievementTier(Enum):
    """成就等级枚举"""
    BRONZE = 'bronze'  # 铜牌
    SILVER = 'silver'  # 银牌
    GOLD = 'gold'  # 金牌
    PLATINUM = 'platinum'  # 白金
    DIAMOND = 'diamond'  # 钻石


class Achievement:
    """成就数据类"""
    
    def __init__(
        self,
        achievement_id: str,
        name: str,
        description: str,
        category: AchievementCategory,
        tier: AchievementTier,
        condition_type: str,  # 'count', 'reach', 'complete', 'collect'
        condition_target: Any,
        reward_sun: int = 0,
        reward_unlock: Optional[str] = None,
        hidden: bool = False
    ):
        self.achievement_id = achievement_id
        self.name = name
        self.description = description
        self.category = category
        self.tier = tier
        self.condition_type = condition_type
        self.condition_target = condition_target
        self.reward_sun = reward_sun
        self.reward_unlock = reward_unlock
        self.hidden = hidden
        self.unlocked = False
        self.progress = 0
        self.unlocked_date: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'achievement_id': self.achievement_id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'tier': self.tier.value,
            'condition_type': self.condition_type,
            'condition_target': self.condition_target,
            'reward_sun': self.reward_sun,
            'reward_unlock': self.reward_unlock,
            'hidden': self.hidden,
            'unlocked': self.unlocked,
            'progress': self.progress,
            'unlocked_date': self.unlocked_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Achievement':
        """从字典创建成就对象"""
        achievement = cls(
            achievement_id=data['achievement_id'],
            name=data['name'],
            description=data['description'],
            category=AchievementCategory(data['category']),
            tier=AchievementTier(data['tier']),
            condition_type=data['condition_type'],
            condition_target=data['condition_target'],
            reward_sun=data.get('reward_sun', 0),
            reward_unlock=data.get('reward_unlock'),
            hidden=data.get('hidden', False)
        )
        achievement.unlocked = data.get('unlocked', False)
        achievement.progress = data.get('progress', 0)
        achievement.unlocked_date = data.get('unlocked_date')
        return achievement
    
    def check_and_update(self, current_value: Any) -> bool:
        """
        检查并更新成就进度
        
        :param current_value: 当前值
        :return: 是否解锁
        """
        if self.unlocked:
            return False
        
        self.progress = current_value
        
        if self.progress >= self.condition_target:
            self.unlock()
            return True
        
        return False
    
    def unlock(self) -> None:
        """解锁成就"""
        self.unlocked = True
        self.unlocked_date = datetime.now().isoformat()
        self.progress = self.condition_target


class AchievementTracker:
    """
    成就追踪器 - 单例模式
    负责追踪玩家的各类成就进度
    """
    
    _instance: Optional['AchievementTracker'] = None
    
    def __new__(cls) -> 'AchievementTracker':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.achievements: Dict[str, Achievement] = {}
        self.statistics: Dict[str, Any] = {}
        self.save_path: str = 'data/user/achievements.json'
        
        # 统计项
        self._init_statistics()
        
        # 加载预定义成就
        self._load_default_achievements()
        
        self._initialized = True
    
    def _init_statistics(self) -> None:
        """初始化统计数据"""
        self.statistics = {
            # 战斗统计
            'zombies_killed': 0,
            'zombies_killed_by_type': {},
            'peas_fired': 0,
            'plants_lost': 0,
            'lawnmowers_used': 0,
            
            # 经济统计
            'sun_collected': 0,
            'sun_spent': 0,
            'max_sun_reached': 0,
            
            # 生存统计
            'levels_completed': 0,
            'waves_survived': 0,
            'longest_survival_time': 0,
            
            # 收集统计
            'plants_unlocked': 0,
            'total_play_time': 0
        }
    
    def _load_default_achievements(self) -> None:
        """加载预定义成就"""
        default_achievements = [
            # 战斗类成就
            Achievement(
                achievement_id='combat_001',
                name='初出茅庐',
                description='击败 10 个僵尸',
                category=AchievementCategory.COMBAT,
                tier=AchievementTier.BRONZE,
                condition_type='count',
                condition_target=10,
                reward_sun=100
            ),
            Achievement(
                achievement_id='combat_002',
                name='僵尸杀手',
                description='击败 100 个僵尸',
                category=AchievementCategory.COMBAT,
                tier=AchievementTier.SILVER,
                condition_type='count',
                condition_target=100,
                reward_sun=500
            ),
            Achievement(
                achievement_id='combat_003',
                name='豌豆大师',
                description='发射 1000 发豌豆',
                category=AchievementCategory.COMBAT,
                tier=AchievementTier.GOLD,
                condition_type='count',
                condition_target=1000,
                reward_sun=1000
            ),
            Achievement(
                achievement_id='combat_004',
                name='无敌防线',
                description='在不损失任何植物的情况下完成一波进攻',
                category=AchievementCategory.COMBAT,
                tier=AchievementTier.PLATINUM,
                condition_type='special',
                condition_target='no_plant_loss_wave',
                reward_sun=2000,
                reward_unlock='golden_peashooter'
            ),
            
            # 经济类成就
            Achievement(
                achievement_id='economy_001',
                name='阳光收集者',
                description='收集 1000 阳光',
                category=AchievementCategory.ECONOMY,
                tier=AchievementTier.BRONZE,
                condition_type='count',
                condition_target=1000,
                reward_sun=200
            ),
            Achievement(
                achievement_id='economy_002',
                name='富翁',
                description='同时拥有 8000 阳光',
                category=AchievementCategory.ECONOMY,
                tier=AchievementTier.GOLD,
                condition_type='reach',
                condition_target=8000,
                reward_sun=1500
            ),
            
            # 生存类成就
            Achievement(
                achievement_id='survival_001',
                name='首战告捷',
                description='完成 1 个关卡',
                category=AchievementCategory.SURVIVAL,
                tier=AchievementTier.BRONZE,
                condition_type='count',
                condition_target=1,
                reward_sun=300
            ),
            Achievement(
                achievement_id='survival_002',
                name='久经沙场',
                description='完成 10 个关卡',
                category=AchievementCategory.SURVIVAL,
                tier=AchievementTier.SILVER,
                condition_type='count',
                condition_target=10,
                reward_sun=1000
            ),
            Achievement(
                achievement_id='survival_003',
                name='传奇幸存者',
                description='完成所有 50 个关卡',
                category=AchievementCategory.SURVIVAL,
                tier=AchievementTier.DIAMOND,
                condition_type='count',
                condition_target=50,
                reward_sun=5000,
                reward_unlock='all_plants'
            ),
            
            # 收集类成就
            Achievement(
                achievement_id='collection_001',
                name='植物学家',
                description='解锁 10 种植物',
                category=AchievementCategory.COLLECTION,
                tier=AchievementTier.SILVER,
                condition_type='count',
                condition_target=10,
                reward_sun=800
            ),
            Achievement(
                achievement_id='collection_002',
                name='全图鉴大师',
                description='解锁所有植物',
                category=AchievementCategory.COLLECTION,
                tier=AchievementTier.DIAMOND,
                condition_type='count',
                condition_target=49,
                reward_sun=10000,
                reward_unlock='golden_watering_can'
            ),
            
            # 特殊成就
            Achievement(
                achievement_id='special_001',
                name='樱桃炸弹专家',
                description='用樱桃炸弹一次性炸掉 5 个僵尸',
                category=AchievementCategory.SPECIAL,
                tier=AchievementTier.GOLD,
                condition_type='special',
                condition_target='cherry_bomb_multikill_5',
                reward_sun=1500
            ),
            Achievement(
                achievement_id='special_002',
                name='速战速决',
                description='在 60 秒内完成一个关卡',
                category=AchievementCategory.SPECIAL,
                tier=AchievementTier.PLATINUM,
                condition_type='special',
                condition_target='level_under_60s',
                reward_sun=3000
            )
        ]
        
        for achievement in default_achievements:
            self.achievements[achievement.achievement_id] = achievement
    
    def update_statistic(self, stat_name: str, value: Any, operation: str = 'add') -> None:
        """
        更新统计数据
        
        :param stat_name: 统计项名称
        :param value: 更新的值
        :param operation: 操作类型 ('add', 'set', 'max', 'min')
        """
        if stat_name not in self.statistics:
            self.statistics[stat_name] = 0
        
        if operation == 'add':
            self.statistics[stat_name] += value
        elif operation == 'set':
            self.statistics[stat_name] = value
        elif operation == 'max':
            self.statistics[stat_name] = max(self.statistics[stat_name], value)
        elif operation == 'min':
            self.statistics[stat_name] = min(self.statistics[stat_name], value)
        
        # 检查相关成就
        self._check_achievements_for_stat(stat_name, self.statistics[stat_name])
    
    def _check_achievements_for_stat(self, stat_name: str, value: Any) -> None:
        """检查与统计项相关的成就"""
        achievement_mapping = {
            'zombies_killed': ['combat_001', 'combat_002'],
            'peas_fired': ['combat_003'],
            'sun_collected': ['economy_001'],
            'max_sun_reached': ['economy_002'],
            'levels_completed': ['survival_001', 'survival_002', 'survival_003'],
            'plants_unlocked': ['collection_001', 'collection_002']
        }
        
        if stat_name in achievement_mapping:
            for achievement_id in achievement_mapping[stat_name]:
                if achievement_id in self.achievements:
                    achievement = self.achievements[achievement_id]
                    if achievement.check_and_update(value):
                        self._on_achievement_unlocked(achievement)
    
    def _on_achievement_unlocked(self, achievement: Achievement) -> None:
        """成就解锁回调"""
        print(f"🏆 成就解锁：{achievement.name}")
        print(f"   描述：{achievement.description}")
        print(f"   奖励：{achievement.reward_sun} 阳光")
        if achievement.reward_unlock:
            print(f"   解锁：{achievement.reward_unlock}")
        
        # 发放奖励
        if achievement.reward_sun > 0:
            # 这里可以通过回调通知经济系统
            pass
    
    def record_zombie_kill(self, zombie_type: str) -> None:
        """记录僵尸击杀"""
        self.update_statistic('zombies_killed', 1, 'add')
        
        if zombie_type not in self.statistics['zombies_killed_by_type']:
            self.statistics['zombies_killed_by_type'][zombie_type] = 0
        self.statistics['zombies_killed_by_type'][zombie_type] += 1
    
    def record_pea_fired(self, count: int = 1) -> None:
        """记录豌豆发射"""
        self.update_statistic('peas_fired', count, 'add')
    
    def record_plant_lost(self) -> None:
        """记录植物损失"""
        self.update_statistic('plants_lost', 1, 'add')
    
    def record_sun_collected(self, amount: int) -> None:
        """记录阳光收集"""
        self.update_statistic('sun_collected', amount, 'add')
        self.update_statistic('max_sun_reached', amount, 'max')
    
    def record_level_completed(self) -> None:
        """记录关卡完成"""
        self.update_statistic('levels_completed', 1, 'add')
    
    def get_achievement_progress(self, achievement_id: str) -> Tuple[int, Any]:
        """
        获取成就进度
        
        :param achievement_id: 成就 ID
        :return: (当前进度，目标进度)
        """
        if achievement_id not in self.achievements:
            return (0, 0)
        
        achievement = self.achievements[achievement_id]
        return (achievement.progress, achievement.condition_target)
    
    def get_unlocked_achievements(self) -> List[Achievement]:
        """获取已解锁的成就列表"""
        return [a for a in self.achievements.values() if a.unlocked]
    
    def get_locked_achievements(self) -> List[Achievement]:
        """获取未解锁的成就列表"""
        return [a for a in self.achievements.values() if not a.unlocked]
    
    def get_achievements_by_category(self, category: AchievementCategory) -> List[Achievement]:
        """按分类获取成就"""
        return [a for a in self.achievements.values() if a.category == category]
    
    def get_completion_percentage(self) -> float:
        """获取成就完成百分比"""
        if not self.achievements:
            return 0.0
        
        unlocked_count = len(self.get_unlocked_achievements())
        return (unlocked_count / len(self.achievements)) * 100
    
    def save(self) -> bool:
        """保存成就数据到文件"""
        try:
            data = {
                'achievements': [a.to_dict() for a in self.achievements.values()],
                'statistics': self.statistics,
                'last_updated': datetime.now().isoformat()
            }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存成就数据失败：{e}")
            return False
    
    def load(self) -> bool:
        """从文件加载成就数据"""
        try:
            if not os.path.exists(self.save_path):
                return False
            
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载成就
            for achievement_data in data.get('achievements', []):
                achievement = Achievement.from_dict(achievement_data)
                self.achievements[achievement.achievement_id] = achievement
            
            # 加载统计
            self.statistics.update(data.get('statistics', {}))
            
            return True
        except Exception as e:
            print(f"加载成就数据失败：{e}")
            return False


# 全局成就追踪器实例
achievement_tracker = AchievementTracker()


def get_achievement_tracker() -> AchievementTracker:
    """获取全局成就追踪器实例"""
    return achievement_tracker


def initialize_achievements() -> AchievementTracker:
    """初始化成就系统"""
    tracker = achievement_tracker
    tracker.load()  # 尝试加载已保存的数据
    return tracker
