'''
经济系统 - 阳光管理、金币计算、植物成本的经济学系统
工业级标准：类型注解、文档字符串、错误处理、事件驱动架构
'''

from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from data.src.const import *
from data.src.settings import settings
from enum import Enum
import pygame
import random

if TYPE_CHECKING:
    from data.src.Game import Game


class CurrencyType(Enum):
    """货币类型枚举"""
    SUN = 'sun'  # 阳光
    GOLD = 'gold'  # 金币
    SILVER = 'silver'  # 银币
    DIAMOND = 'diamond'  # 钻石


class EconomyEvent:
    """经济事件数据类"""
    
    def __init__(
        self,
        event_type: str,
        currency_type: CurrencyType,
        amount: int,
        timestamp: float,
        source: str,
        position: Optional[Tuple[int, int]] = None
    ):
        self.event_type = event_type  # 'gain', 'spend', 'loss'
        self.currency_type = currency_type
        self.amount = amount
        self.timestamp = timestamp
        self.source = source
        self.position = position or (0, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'event_type': self.event_type,
            'currency_type': self.currency_type.value,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'source': self.source,
            'position': self.position
        }


class SunlightManager:
    """
    阳光管理器 - 单例模式
    负责阳光的生成、收集、消耗和自然掉落
    """
    
    _instance: Optional['SunlightManager'] = None
    
    def __new__(cls) -> 'SunlightManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.game: Optional['Game'] = None
        self.current_sun: int = 200  # 当前阳光数量
        self.sun_cap: int = 9999  # 阳光上限
        
        # 阳光生成配置
        self.natural_sun_interval: int = SUNLIGHT_TIME  # 自然掉落间隔（帧）
        self.natural_sun_value: int = 25  # 自然阳光价值
        self.sunflower_base_value: int = 25  # 向日葵基础产量
        self.twin_sunflower_value: int = 50  # 双子向日葵产量
        
        # 经济统计
        self.total_sun_gained: int = 0
        self.total_sun_spent: int = 0
        self.sun_collection_events: List[EconomyEvent] = []
        
        # 掉落位置缓存
        self.drop_positions: List[Tuple[int, int]] = []
        
        self._initialized = True
    
    def initialize(self, game: 'Game', initial_sun: int = 200) -> None:
        """
        初始化阳光管理器
        
        :param game: 游戏主对象
        :param initial_sun: 初始阳光数量
        """
        self.game = game
        self.current_sun = initial_sun
        self.sun_collection_events = []
        self.total_sun_gained = 0
        self.total_sun_spent = 0
    
    def add_sun(self, amount: int, source: str = 'natural', position: Optional[Tuple[int, int]] = None) -> bool:
        """
        增加阳光
        
        :param amount: 增加的数值
        :param source: 来源 ('natural', 'sunflower', 'twin_sunflower', 'falling')
        :param position: 阳光掉落位置
        :return: 是否成功添加
        """
        if amount <= 0:
            return False
        
        # 检查是否超过上限
        if self.current_sun + amount > self.sun_cap:
            amount = self.sun_cap - self.current_sun
        
        if amount <= 0:
            return False
        
        self.current_sun += amount
        self.total_sun_gained += amount
        
        # 记录事件
        event = EconomyEvent(
            event_type='gain',
            currency_type=CurrencyType.SUN,
            amount=amount,
            timestamp=pygame.time.get_ticks() / 1000.0,
            source=source,
            position=position
        )
        self.sun_collection_events.append(event)
        
        # 保持事件列表大小
        if len(self.sun_collection_events) > 100:
            self.sun_collection_events = self.sun_collection_events[-100:]
        
        return True
    
    def spend_sun(self, amount: int, plant_type: str) -> bool:
        """
        消耗阳光种植植物
        
        :param amount: 消耗的数值
        :param plant_type: 植物类型
        :return: 是否有足够的阳光
        """
        if amount <= 0:
            return False
        
        if self.current_sun < amount:
            return False
        
        self.current_sun -= amount
        self.total_sun_spent += amount
        
        # 记录事件
        event = EconomyEvent(
            event_type='spend',
            currency_type=CurrencyType.SUN,
            amount=amount,
            timestamp=pygame.time.get_ticks() / 1000.0,
            source=plant_type,
            position=None
        )
        self.sun_collection_events.append(event)
        
        return True
    
    def can_afford(self, plant_type: str) -> bool:
        """
        检查是否能负担某种植物
        
        :param plant_type: 植物类型
        :return: 是否能负担
        """
        cost = settings[plant_type]['gold']
        return self.current_sun >= cost
    
    def get_sunflower_production(self, sunflower_type: str = 'sunflower') -> int:
        """
        获取向日葵产量
        
        :param sunflower_type: 向日葵类型
        :return: 产量值
        """
        if sunflower_type == 'twin_sunflower':
            return self.twin_sunflower_value
        return self.sunflower_base_value
    
    def generate_natural_sun_drop(self) -> Optional[Tuple[int, int]]:
        """
        生成自然阳光掉落位置
        
        :return: 掉落位置坐标，如果无法生成则返回 None
        """
        if not self.game:
            return None
        
        # 在屏幕上方随机位置生成
        x = random.randint(GRID_LEFT_X, GRID_RIGHT_X - 100)
        y = 0  # 从顶部开始
        
        position = (x, y)
        self.drop_positions.append(position)
        
        return position
    
    def collect_sunlight(self, sunlight_object: Any) -> int:
        """
        收集阳光对象
        
        :param sunlight_object: 阳光对象
        :return: 收集的数值
        """
        amount = getattr(sunlight_object, 'value', self.natural_sun_value)
        position = getattr(sunlight_object, 'pos', (0, 0))
        
        if self.add_sun(amount, source='falling', position=tuple(position)):
            return amount
        return 0
    
    def update(self) -> None:
        """更新阳光状态（每帧调用）"""
        # 清理过期的掉落位置
        if len(self.drop_positions) > 50:
            self.drop_positions = self.drop_positions[-50:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取经济统计信息"""
        return {
            'current_sun': self.current_sun,
            'total_gained': self.total_sun_gained,
            'total_spent': self.total_sun_spent,
            'net_income': self.total_sun_gained - self.total_sun_spent,
            'recent_events': len(self.sun_collection_events)
        }


class PlantCostCalculator:
    """
    植物成本计算器
    负责计算植物的实际成本（考虑折扣、加成等）
    """
    
    def __init__(self):
        self.base_costs: Dict[str, int] = {}
        self.cost_modifiers: Dict[str, float] = {}
        
        # 从配置加载基础成本
        self._load_base_costs()
    
    def _load_base_costs(self) -> None:
        """从配置加载植物基础成本"""
        plant_types = [
            'peashooter', 'sunflower', 'cherry_bomb', 'wall_nut',
            'potato_mine', 'snow_pea', 'chomper', 'repeater',
            'puff_shroom', 'sun_shroom', 'fume_shroom', 'grave_buster',
            'hypno_shroom', 'dwarf_shroom', 'gloom_shroom', 'cactus',
            'blover', 'spikeweed', 'torchwood', 'tall_nut', 'sea_shroom',
            'plantern', 'lily_pad', 'squash', 'threepeater', 'tangle_kelp',
            'jalapeno', 'spike_rock', 'volcano', 'magnet_shroom',
            'cabbage_pult', 'flower_pot', 'kernel_pult', 'coffee_bean',
            'garlic', 'umbrella_leaf', 'marigold', 'melon_pult',
            'ice_shroom', 'doom_shroom'
        ]
        
        for plant_type in plant_types:
            if plant_type in settings:
                self.base_costs[plant_type] = settings[plant_type].get('gold', 0)
    
    def calculate_cost(
        self, 
        plant_type: str, 
        modifiers: Optional[Dict[str, float]] = None
    ) -> int:
        """
        计算植物实际成本
        
        :param plant_type: 植物类型
        :param modifiers: 成本修正系数
        :return: 实际成本
        """
        base_cost = self.base_costs.get(plant_type, 0)
        
        if modifiers:
            for modifier_name, value in modifiers.items():
                if modifier_name == 'discount':
                    base_cost = int(base_cost * (1 - value))
                elif modifier_name == 'surcharge':
                    base_cost = int(base_cost * (1 + value))
        
        # 确保成本不为负
        return max(0, base_cost)
    
    def get_refund_value(self, plant_type: str, refund_rate: float = 0.5) -> int:
        """
        计算铲子移除植物的返还值
        
        :param plant_type: 植物类型
        :param refund_rate: 返还比例（默认 50%）
        :return: 返还的阳光值
        """
        base_cost = self.base_costs.get(plant_type, 0)
        return int(base_cost * refund_rate)


class EconomySystem:
    """
    经济系统 - 统一管理阳光、金币等经济要素
    """
    
    def __init__(self, game: 'Game'):
        self.game = game
        self.sunlight_manager = SunlightManager()
        self.cost_calculator = PlantCostCalculator()
        
        # 初始化
        self.sunlight_manager.initialize(game)
    
    def can_plant(self, plant_type: str) -> bool:
        """
        检查是否可以种植某种植物
        
        :param plant_type: 植物类型
        :return: 是否可以种植
        """
        cost = self.cost_calculator.calculate_cost(plant_type)
        return self.sunlight_manager.can_afford(plant_type)
    
    def try_plant(self, plant_type: str) -> bool:
        """
        尝试种植植物（消耗阳光）
        
        :param plant_type: 植物类型
        :return: 是否成功
        """
        cost = self.cost_calculator.calculate_cost(plant_type)
        return self.sunlight_manager.spend_sun(cost, plant_type)
    
    def get_sun_refund(self, plant_type: str) -> int:
        """
        获取铲子移除植物的阳光返还
        
        :param plant_type: 植物类型
        :return: 返还的阳光值
        """
        return self.cost_calculator.get_refund_value(plant_type)
    
    def add_sun(self, amount: int, source: str = 'natural') -> bool:
        """增加阳光"""
        return self.sunlight_manager.add_sun(amount, source)
    
    def get_current_sun(self) -> int:
        """获取当前阳光数量"""
        return self.sunlight_manager.current_sun
    
    def update(self) -> None:
        """更新经济系统状态"""
        self.sunlight_manager.update()
    
    def get_economy_report(self) -> Dict[str, Any]:
        """获取经济报告"""
        sun_stats = self.sunlight_manager.get_statistics()
        return {
            'sun': sun_stats,
            'can_afford_peashooter': self.can_plant('peashooter'),
            'can_afford_sunflower': self.can_plant('sunflower'),
            'can_afford_cherry_bomb': self.can_plant('cherry_bomb')
        }


# 全局经济系统实例（延迟初始化）
economy_system: Optional[EconomySystem] = None


def initialize_economy(game: 'Game') -> EconomySystem:
    """初始化全局经济系统"""
    global economy_system
    economy_system = EconomySystem(game)
    return economy_system


def get_economy_system() -> Optional[EconomySystem]:
    """获取全局经济系统实例"""
    return economy_system
