"""
植物数据库模块 - 完整49种植物定义

本模块包含《植物大战僵尸》中所有49种植物的完整数据定义，
采用数据驱动设计，支持热重载和平衡性调整。

Categories:
    - ATTACK: 攻击类植物 (豌豆射手系列、蘑菇类等)
    - DEFENSE: 防御类植物 (坚果、南瓜头等)
    - PRODUCTION: 生产类植物 (向日葵、阳光菇等)
    - SPECIAL: 特殊类植物 (磁力菇、模仿者等)
    - UPGRADE: 升级类植物 (机枪射手、双子向日葵等)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Callable
import json
from pathlib import Path


class PlantCategory(Enum):
    """植物分类枚举"""
    ATTACK = "attack"
    DEFENSE = "defense"
    PRODUCTION = "production"
    SPECIAL = "special"
    UPGRADE = "upgrade"


class TargetType(Enum):
    """目标类型"""
    GROUND = "ground"      # 地面目标
    AIR = "air"           # 空中目标
    BOTH = "both"         # 地面和空中


class AttackMode(Enum):
    """攻击模式"""
    SINGLE = "single"        # 单体攻击
    PIERCING = "piercing"    # 穿透攻击
    SPLASH = "splash"        # 溅射伤害
    LINE = "line"           # 直线攻击
    AREA = "area"          # 范围攻击


@dataclass
class PlantConfig:
    """植物配置数据类"""
    name: str
    name_cn: str
    category: PlantCategory
    sun_cost: int
    cooldown: float  # 秒
    health: int
    damage: int
    attack_interval: float  # 秒
    range: int  # 格子数
    target_type: TargetType
    attack_mode: AttackMode
    special_ability: Optional[str] = None
    unlock_level: int = 1
    description: str = ""
    
    # 视觉属性
    color: str = "#00FF00"
    size: tuple = (50, 50)
    
    # 进阶属性
    upgrade_from: Optional[str] = None
    can_upgrade: bool = False
    upgrade_to: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "name": self.name,
            "name_cn": self.name_cn,
            "category": self.category.value,
            "sun_cost": self.sun_cost,
            "cooldown": self.cooldown,
            "health": self.health,
            "damage": self.damage,
            "attack_interval": self.attack_interval,
            "range": self.range,
            "target_type": self.target_type.value,
            "attack_mode": self.attack_mode.value,
            "special_ability": self.special_ability,
            "unlock_level": self.unlock_level,
            "description": self.description,
            "color": self.color,
            "size": self.size,
            "upgrade_from": self.upgrade_from,
            "can_upgrade": self.can_upgrade,
            "upgrade_to": self.upgrade_to,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PlantConfig":
        """从字典创建"""
        return cls(
            name=data["name"],
            name_cn=data["name_cn"],
            category=PlantCategory(data["category"]),
            sun_cost=data["sun_cost"],
            cooldown=data["cooldown"],
            health=data["health"],
            damage=data["damage"],
            attack_interval=data["attack_interval"],
            range=data["range"],
            target_type=TargetType(data["target_type"]),
            attack_mode=AttackMode(data["attack_mode"]),
            special_ability=data.get("special_ability"),
            unlock_level=data.get("unlock_level", 1),
            description=data.get("description", ""),
            color=data.get("color", "#00FF00"),
            size=tuple(data.get("size", [50, 50])),
            upgrade_from=data.get("upgrade_from"),
            can_upgrade=data.get("can_upgrade", False),
            upgrade_to=data.get("upgrade_to"),
        )


class PlantDatabase:
    """
    植物数据库单例类
    
    管理所有49种植物的配置数据，支持：
    - 按名称/分类查询
    - 解锁状态检查
    - 数据序列化/反序列化
    - 热重载配置
    """
    
    _instance: Optional["PlantDatabase"] = None
    
    def __new__(cls) -> "PlantDatabase":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._plants: Dict[str, PlantConfig] = {}
        self._by_category: Dict[PlantCategory, List[str]] = {
            cat: [] for cat in PlantCategory
        }
        self._load_all_plants()
        self._initialized = True
    
    def _load_all_plants(self):
        """加载所有49种植物配置"""
        
        # ==================== 攻击类植物 (ATTACK) ====================
        
        # 1. 豌豆射手
        self._add_plant(PlantConfig(
            name="peashooter",
            name_cn="豌豆射手",
            category=PlantCategory.ATTACK,
            sun_cost=100,
            cooldown=7.5,
            health=300,
            damage=20,
            attack_interval=1.5,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            unlock_level=1,
            description="发射豌豆攻击僵尸",
            color="#00AA00",
            can_upgrade=True,
            upgrade_to="repeater",
        ))
        
        # 2. 双发射手
        self._add_plant(PlantConfig(
            name="repeater",
            name_cn="双发射手",
            category=PlantCategory.ATTACK,
            sun_cost=200,
            cooldown=7.5,
            health=300,
            damage=20,
            attack_interval=1.5,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="每次发射两颗豌豆",
            unlock_level=3,
            description="一次发射两颗豌豆",
            color="#008800",
            upgrade_from="peashooter",
            can_upgrade=True,
            upgrade_to="gatling_pea",
        ))
        
        # 3. 三线射手
        self._add_plant(PlantConfig(
            name="threepeater",
            name_cn="三线射手",
            category=PlantCategory.ATTACK,
            sun_cost=325,
            cooldown=7.5,
            health=300,
            damage=20,
            attack_interval=1.5,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.LINE,
            special_ability="同时攻击三条线",
            unlock_level=5,
            description="向三条线路发射豌豆",
            color="#00AA44",
        ))
        
        # 4. 机枪射手
        self._add_plant(PlantConfig(
            name="gatling_pea",
            name_cn="机枪射手",
            category=PlantCategory.ATTACK,
            sun_cost=500,
            cooldown=7.5,
            health=450,
            damage=20,
            attack_interval=0.3,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="快速连续发射四颗豌豆",
            unlock_level=20,
            description="疯狂豌豆机器",
            color="#006600",
            upgrade_from="repeater",
        ))
        
        # 5. 寒冰射手
        self._add_plant(PlantConfig(
            name="snow_pea",
            name_cn="寒冰射手",
            category=PlantCategory.ATTACK,
            sun_cost=175,
            cooldown=7.5,
            health=300,
            damage=20,
            attack_interval=1.5,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="减速僵尸20%",
            unlock_level=4,
            description="发射冰豌豆减缓僵尸速度",
            color="#AADDFF",
        ))
        
        # 6. 大喷菇
        self._add_plant(PlantConfig(
            name="fume_shroom",
            name_cn="大喷菇",
            category=PlantCategory.ATTACK,
            sun_cost=75,
            cooldown=7.5,
            health=300,
            damage=20,
            attack_interval=1.5,
            range=3,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SPLASH,
            special_ability="穿透攻击",
            unlock_level=8,
            description="喷射孢子穿透多个僵尸",
            color="#8B4513",
        ))
        
        # 7. 磁力菇
        self._add_plant(PlantConfig(
            name="magnet_shroom",
            name_cn="磁力菇",
            category=PlantCategory.SPECIAL,
            sun_cost=100,
            cooldown=7.5,
            health=300,
            damage=0,
            attack_interval=0,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.AREA,
            special_ability="吸取铁制物品",
            unlock_level=12,
            description="吸走僵尸的铁桶、梯子等",
            color="#FF1493",
        ))
        
        # 8. 仙人掌
        self._add_plant(PlantConfig(
            name="cactus",
            name_cn="仙人掌",
            category=PlantCategory.ATTACK,
            sun_cost=125,
            cooldown=7.5,
            health=300,
            damage=20,
            attack_interval=1.5,
            range=5,
            target_type=TargetType.BOTH,
            attack_mode=AttackMode.SINGLE,
            special_ability="可攻击气球僵尸",
            unlock_level=15,
            description="发射尖刺，可对付飞行单位",
            color="#2E8B57",
        ))
        
        # 9. 双向射手
        self._add_plant(PlantConfig(
            name="split_pea",
            name_cn="双向射手",
            category=PlantCategory.ATTACK,
            sun_cost=125,
            cooldown=7.5,
            health=300,
            damage=20,
            attack_interval=1.5,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="前后同时攻击",
            unlock_level=18,
            description="向前后两个方向发射豌豆",
            color="#32CD32",
        ))
        
        # 10. 杨桃
        self._add_plant(PlantConfig(
            name="starfruit",
            name_cn="杨桃",
            category=PlantCategory.ATTACK,
            sun_cost=125,
            cooldown=7.5,
            health=300,
            damage=20,
            attack_interval=1.5,
            range=3,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.AREA,
            special_ability="向五个方向攻击",
            unlock_level=22,
            description="向周围五个方向发射星星",
            color="#FFD700",
        ))
        
        # 11. 西瓜投手
        self._add_plant(PlantConfig(
            name="melon_pult",
            name_cn="西瓜投手",
            category=PlantCategory.ATTACK,
            sun_cost=500,
            cooldown=7.5,
            health=300,
            damage=80,
            attack_interval=3.0,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SPLASH,
            special_ability="溅射伤害",
            unlock_level=25,
            description="投掷西瓜造成范围伤害",
            color="#006400",
            can_upgrade=True,
            upgrade_to="winter_melon",
        ))
        
        # 12. 冰西瓜
        self._add_plant(PlantConfig(
            name="winter_melon",
            name_cn="冰西瓜",
            category=PlantCategory.ATTACK,
            sun_cost=700,
            cooldown=7.5,
            health=300,
            damage=80,
            attack_interval=3.0,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SPLASH,
            special_ability="溅射伤害并减速",
            unlock_level=35,
            description="投掷冰西瓜减速僵尸",
            color="#87CEEB",
            upgrade_from="melon_pult",
        ))
        
        # 13. 玉米投手
        self._add_plant(PlantConfig(
            name="kernel_pult",
            name_cn="玉米投手",
            category=PlantCategory.ATTACK,
            sun_cost=100,
            cooldown=7.5,
            health=300,
            damage=20,
            attack_interval=1.5,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="25%概率投掷黄油定身",
            unlock_level=10,
            description="投掷玉米粒和黄油",
            color="#FFD700",
            can_upgrade=True,
            upgrade_to="cob_cannon",
        ))
        
        # 14. 玉米加农炮
        self._add_plant(PlantConfig(
            name="cob_cannon",
            name_cn="玉米加农炮",
            category=PlantCategory.ATTACK,
            sun_cost=500,
            cooldown=7.5,
            health=600,
            damage=300,
            attack_interval=35.0,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.AREA,
            special_ability="手动瞄准发射玉米导弹",
            unlock_level=45,
            description="毁灭性的玉米导弹",
            color="#FFA500",
            upgrade_from="kernel_pult",
        ))
        
        # 15. 卷心菜投手
        self._add_plant(PlantConfig(
            name="cabbage_pult",
            name_cn="卷心菜投手",
            category=PlantCategory.ATTACK,
            sun_cost=100,
            cooldown=7.5,
            health=300,
            damage=40,
            attack_interval=2.0,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            unlock_level=6,
            description="投掷卷心菜攻击僵尸",
            color="#90EE90",
        ))
        
        # 16. 花盆投手
        self._add_plant(PlantConfig(
            name="flower_pot",
            name_cn="花盆",
            category=PlantCategory.SPECIAL,
            sun_cost=25,
            cooldown=7.5,
            health=300,
            damage=0,
            attack_interval=0,
            range=0,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="可在屋顶种植植物",
            unlock_level=14,
            description="在屋顶上种植其他植物",
            color="#8B4513",
        ))
        
        # 17. 地刺
        self._add_plant(PlantConfig(
            name="spikeweed",
            name_cn="地刺",
            category=PlantCategory.ATTACK,
            sun_cost=100,
            cooldown=7.5,
            health=50,
            damage=20,
            attack_interval=0.5,
            range=1,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="对踩过的僵尸持续伤害",
            unlock_level=16,
            description="刺伤踩过的僵尸",
            color="#556B2F",
        ))
        
        # 18. 地刺王
        self._add_plant(PlantConfig(
            name="spikerock",
            name_cn="地刺王",
            category=PlantCategory.ATTACK,
            sun_cost=250,
            cooldown=7.5,
            health=300,
            damage=40,
            attack_interval=0.5,
            range=1,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="可承受多次碾压",
            unlock_level=38,
            description="强化版地刺",
            color="#708090",
        ))
        
        # 19. 火炬树桩
        self._add_plant(PlantConfig(
            name="torchwood",
            name_cn="火炬树桩",
            category=PlantCategory.SPECIAL,
            sun_cost=175,
            cooldown=7.5,
            health=300,
            damage=0,
            attack_interval=0,
            range=0,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="豌豆穿过变成火球",
            unlock_level=19,
            description="将豌豆变成火球增加伤害",
            color="#FF4500",
        ))
        
        # 20. 海蘑菇
        self._add_plant(PlantConfig(
            name="sea_shroom",
            name_cn="海蘑菇",
            category=PlantCategory.ATTACK,
            sun_cost=0,
            cooldown=7.5,
            health=300,
            damage=20,
            attack_interval=1.5,
            range=3,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="只能在水中生存",
            unlock_level=21,
            description="免费的水生攻击植物",
            color="#4682B4",
        ))
        
        # 21. 灯笼草
        self._add_plant(PlantConfig(
            name="plantern",
            name_cn="灯笼草",
            category=PlantCategory.SPECIAL,
            sun_cost=25,
            cooldown=7.5,
            health=300,
            damage=0,
            attack_interval=0,
            range=3,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="照亮周围迷雾",
            unlock_level=24,
            description="驱散周围的迷雾",
            color="#FF6347",
        ))
        
        # 22. 三叶草
        self._add_plant(PlantConfig(
            name="blover",
            name_cn="三叶草",
            category=PlantCategory.SPECIAL,
            sun_cost=100,
            cooldown=7.5,
            health=300,
            damage=0,
            attack_interval=0,
            range=0,
            target_type=TargetType.AIR,
            attack_mode=AttackMode.AREA,
            special_ability="吹走飞行僵尸",
            unlock_level=26,
            description="瞬间清除所有飞行单位",
            color="#98FB98",
        ))
        
        # 23. 裂荚射手
        self._add_plant(PlantConfig(
            name="snapdragon",
            name_cn="火龙草",
            category=PlantCategory.ATTACK,
            sun_cost=150,
            cooldown=7.5,
            health=300,
            damage=30,
            attack_interval=1.5,
            range=2,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SPLASH,
            special_ability="火焰范围攻击",
            unlock_level=28,
            description="向前方喷射火焰",
            color="#DC143C",
        ))
        
        # 24. 闪电芦苇
        self._add_plant(PlantConfig(
            name="lightning_reed",
            name_cn="闪电芦苇",
            category=PlantCategory.ATTACK,
            sun_cost=125,
            cooldown=7.5,
            health=300,
            damage=15,
            attack_interval=0.5,
            range=5,
            target_type=TargetType.BOTH,
            attack_mode=AttackMode.PIERCING,
            special_ability="连锁闪电伤害",
            unlock_level=30,
            description="闪电链攻击多个目标",
            color="#9370DB",
        ))
        
        # 25. 香蕉火箭炮
        self._add_plant(PlantConfig(
            name="banana_launcher",
            name_cn="香蕉火箭炮",
            category=PlantCategory.ATTACK,
            sun_cost=500,
            cooldown=7.5,
            health=300,
            damage=150,
            attack_interval=10.0,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.AREA,
            special_ability="手动瞄准发射香蕉导弹",
            unlock_level=40,
            description="发射追踪香蕉导弹",
            color="#FFE135",
        ))
        
        # ==================== 防御类植物 (DEFENSE) ====================
        
        # 26. 坚果墙
        self._add_plant(PlantConfig(
            name="wall_nut",
            name_cn="坚果墙",
            category=PlantCategory.DEFENSE,
            sun_cost=50,
            cooldown=30.0,
            health=4000,
            damage=0,
            attack_interval=0,
            range=0,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            unlock_level=2,
            description="坚硬的外壳保护后方植物",
            color="#8B4513",
        ))
        
        # 27. 高坚果
        self._add_plant(PlantConfig(
            name="tall_nut",
            name_cn="高坚果",
            category=PlantCategory.DEFENSE,
            sun_cost=125,
            cooldown=30.0,
            health=8000,
            damage=0,
            attack_interval=0,
            range=0,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="阻挡跳跃僵尸",
            unlock_level=23,
            description="更高更硬的坚果墙",
            color="#A0522D",
        ))
        
        # 28. 南瓜头
        self._add_plant(PlantConfig(
            name="pumpkin",
            name_cn="南瓜头",
            category=PlantCategory.DEFENSE,
            sun_cost=125,
            cooldown=30.0,
            health=4000,
            damage=0,
            attack_interval=0,
            range=0,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="可包裹其他植物",
            unlock_level=27,
            description="保护内部的植物",
            color="#FF8C00",
        ))
        
        # 29. 睡莲
        self._add_plant(PlantConfig(
            name="lily_pad",
            name_cn="睡莲",
            category=PlantCategory.SPECIAL,
            sun_cost=25,
            cooldown=7.5,
            health=300,
            damage=0,
            attack_interval=0,
            range=0,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="可在水面种植非水生植物",
            unlock_level=11,
            description="在水面上种植植物",
            color="#90EE90",
        ))
        
        # 30. 墓碑吞噬者
        self._add_plant(PlantConfig(
            name="grave_buster",
            name_cn="墓碑吞噬者",
            category=PlantCategory.SPECIAL,
            sun_cost=75,
            cooldown=7.5,
            health=300,
            damage=0,
            attack_interval=0,
            range=1,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="摧毁墓碑",
            unlock_level=17,
            description="移除墓碑障碍",
            color="#6B8E23",
        ))
        
        # ==================== 生产类植物 (PRODUCTION) ====================
        
        # 31. 向日葵
        self._add_plant(PlantConfig(
            name="sunflower",
            name_cn="向日葵",
            category=PlantCategory.PRODUCTION,
            sun_cost=50,
            cooldown=7.5,
            health=300,
            damage=0,
            attack_interval=0,
            range=0,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="每24秒产生25阳光",
            unlock_level=1,
            description="生产阳光的必备植物",
            color="#FFD700",
            can_upgrade=True,
            upgrade_to="twin_sunflower",
        ))
        
        # 32. 双子向日葵
        self._add_plant(PlantConfig(
            name="twin_sunflower",
            name_cn="双子向日葵",
            category=PlantCategory.PRODUCTION,
            sun_cost=150,
            cooldown=7.5,
            health=300,
            damage=0,
            attack_interval=0,
            range=0,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="每24秒产生50阳光",
            unlock_level=32,
            description="一次产生两倍阳光",
            color="#FFA500",
            upgrade_from="sunflower",
        ))
        
        # 33. 阳光菇
        self._add_plant(PlantConfig(
            name="sun_shroom",
            name_cn="阳光菇",
            category=PlantCategory.PRODUCTION,
            sun_cost=25,
            cooldown=7.5,
            health=300,
            damage=0,
            attack_interval=0,
            range=0,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="从小长大，产量递增",
            unlock_level=9,
            description="随时间增长阳光产量",
            color="#DDA0DD",
        ))
        
        # 34. 小喷菇
        self._add_plant(PlantConfig(
            name="puff_shroom",
            name_cn="小喷菇",
            category=PlantCategory.ATTACK,
            sun_cost=0,
            cooldown=7.5,
            health=300,
            damage=20,
            attack_interval=1.5,
            range=3,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="免费但会消失",
            unlock_level=7,
            description="免费的短程攻击蘑菇",
            color="#9370DB",
        ))
        
        # 35. 胆小菇
        self._add_plant(PlantConfig(
            name="scaredy_shroom",
            name_cn="胆小菇",
            category=PlantCategory.ATTACK,
            sun_cost=25,
            cooldown=7.5,
            health=300,
            damage=20,
            attack_interval=1.5,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="僵尸靠近时躲藏",
            unlock_level=13,
            description="远程攻击但害怕僵尸",
            color="#BA55D3",
        ))
        
        # 36. 寒冰菇
        self._add_plant(PlantConfig(
            name="ice_shroom",
            name_cn="寒冰菇",
            category=PlantCategory.SPECIAL,
            sun_cost=125,
            cooldown=50.0,
            health=300,
            damage=0,
            attack_interval=0,
            range=0,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.AREA,
            special_ability="冻结全屏僵尸",
            unlock_level=33,
            description="瞬间冻结所有僵尸",
            color="#ADD8E6",
        ))
        
        # 37. 末日菇
        self._add_plant(PlantConfig(
            name="doom_shroom",
            name_cn="末日菇",
            category=PlantCategory.SPECIAL,
            sun_cost=125,
            cooldown=50.0,
            health=300,
            damage=1800,
            attack_interval=0,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.AREA,
            special_ability="大范围爆炸，留下弹坑",
            unlock_level=42,
            description="毁灭性爆炸攻击",
            color="#4B0082",
        ))
        
        # 38. 咖啡豆
        self._add_plant(PlantConfig(
            name="coffee_bean",
            name_cn="咖啡豆",
            category=PlantCategory.SPECIAL,
            sun_cost=75,
            cooldown=7.5,
            health=0,
            damage=0,
            attack_interval=0,
            range=1,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="唤醒白天种植的蘑菇",
            unlock_level=14,
            description="激活休眠的蘑菇",
            color="#6F4E37",
        ))
        
        # 39. 大蒜
        self._add_plant(PlantConfig(
            name="garlic",
            name_cn="大蒜",
            category=PlantCategory.SPECIAL,
            sun_cost=50,
            cooldown=7.5,
            health=600,
            damage=0,
            attack_interval=0,
            range=1,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="僵尸咬后改道",
            unlock_level=20,
            description="让僵尸改变路线",
            color="#FFFFE0",
        ))
        
        # 40. 叶子保护伞
        self._add_plant(PlantConfig(
            name="umbrella_leaf",
            name_cn="叶子保护伞",
            category=PlantCategory.SPECIAL,
            sun_cost=100,
            cooldown=7.5,
            health=300,
            damage=0,
            attack_interval=0,
            range=3,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="保护周围植物免受空袭",
            unlock_level=29,
            description="阻挡投石车僵尸的石块",
            color="#228B22",
        ))
        
        # 41. 金盏花
        self._add_plant(PlantConfig(
            name="marigold",
            name_cn="金盏花",
            category=PlantCategory.PRODUCTION,
            sun_cost=50,
            cooldown=7.5,
            health=300,
            damage=0,
            attack_interval=0,
            range=0,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="生产银币或金币",
            unlock_level=36,
            description="生产钱币的花",
            color="#FFA500",
        ))
        
        # 42. 吸金磁
        self._add_plant(PlantConfig(
            name="gold_magnet",
            name_cn="吸金磁",
            category=PlantCategory.SPECIAL,
            sun_cost=100,
            cooldown=7.5,
            health=300,
            damage=0,
            attack_interval=0,
            range=7,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="自动吸取钱币",
            unlock_level=37,
            description="磁力升级版，吸钱专用",
            color="#FFD700",
        ))
        
        # 43. 模仿者
        self._add_plant(PlantConfig(
            name="imitater",
            name_cn="模仿者",
            category=PlantCategory.SPECIAL,
            sun_cost=0,
            cooldown=0,
            health=300,
            damage=0,
            attack_interval=0,
            range=0,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="复制任意植物",
            unlock_level=43,
            description="可以携带两株相同植物",
            color="#C0C0C0",
        ))
        
        # 44. 爆炸坚果
        self._add_plant(PlantConfig(
            name="explode_o_nut",
            name_cn="爆炸坚果",
            category=PlantCategory.DEFENSE,
            sun_cost=125,
            cooldown=30.0,
            health=4000,
            damage=1800,
            attack_interval=0,
            range=1,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.AREA,
            special_ability="被吃掉时爆炸",
            unlock_level=39,
            description="死亡时爆炸的坚果",
            color="#B22222",
        ))
        
        # 45. 反向双重射手
        self._add_plant(PlantConfig(
            name="reverse_repeater",
            name_cn="反向双重射手",
            category=PlantCategory.ATTACK,
            sun_cost=200,
            cooldown=7.5,
            health=300,
            damage=20,
            attack_interval=1.5,
            range=5,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="向后发射两颗豌豆",
            unlock_level=41,
            description="专门对付后方偷袭",
            color="#006400",
        ))
        
        # 46. 香蒲
        self._add_plant(PlantConfig(
            name="cattail",
            name_cn="香蒲",
            category=PlantCategory.ATTACK,
            sun_cost=225,
            cooldown=7.5,
            health=300,
            damage=20,
            attack_interval=1.0,
            range=5,
            target_type=TargetType.BOTH,
            attack_mode=AttackMode.SINGLE,
            special_ability="全图攻击，优先气球",
            unlock_level=34,
            description="可攻击任意位置的敌人",
            color="#FF69B4",
        ))
        
        # 47. 海带
        self._add_plant(PlantConfig(
            name="kelp",
            name_cn="海带",
            category=PlantCategory.ATTACK,
            sun_cost=25,
            cooldown=7.5,
            health=300,
            damage=1800,
            attack_interval=0,
            range=1,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.SINGLE,
            special_ability="拖拽第一个接近的僵尸",
            unlock_level=22,
            description="水下一次性武器",
            color="#2F4F4F",
        ))
        
        # 48. 火爆辣椒
        self._add_plant(PlantConfig(
            name="jalapeno",
            name_cn="火爆辣椒",
            category=PlantCategory.SPECIAL,
            sun_cost=125,
            cooldown=50.0,
            health=0,
            damage=1800,
            attack_interval=0,
            range=1,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.LINE,
            special_ability="整行火焰攻击",
            unlock_level=31,
            description="烧毁一整行的僵尸",
            color="#FF0000",
        ))
        
        # 49. 樱桃炸弹
        self._add_plant(PlantConfig(
            name="cherry_bomb",
            name_cn="樱桃炸弹",
            category=PlantCategory.SPECIAL,
            sun_cost=150,
            cooldown=50.0,
            health=0,
            damage=1800,
            attack_interval=0,
            range=1,
            target_type=TargetType.GROUND,
            attack_mode=AttackMode.AREA,
            special_ability="3x3范围爆炸",
            unlock_level=44,
            description="炸毁周围所有僵尸",
            color="#DC143C",
        ))
    
    def _add_plant(self, plant: PlantConfig):
        """添加植物到数据库"""
        self._plants[plant.name] = plant
        self._by_category[plant.category].append(plant.name)
    
    def get(self, name: str) -> Optional[PlantConfig]:
        """根据名称获取植物配置"""
        return self._plants.get(name)
    
    def get_by_category(self, category: PlantCategory) -> List[PlantConfig]:
        """获取指定分类的所有植物"""
        names = self._by_category.get(category, [])
        return [self._plants[name] for name in names if name in self._plants]
    
    def get_all(self) -> List[PlantConfig]:
        """获取所有植物配置"""
        return list(self._plants.values())
    
    def is_unlocked(self, name: str, current_level: int) -> bool:
        """检查植物是否已解锁"""
        plant = self._plants.get(name)
        if not plant:
            return False
        return current_level >= plant.unlock_level
    
    def get_unlockable(self, current_level: int) -> List[PlantConfig]:
        """获取当前等级可解锁的植物"""
        return [p for p in self._plants.values() if p.unlock_level == current_level]
    
    def to_json(self, filepath: Optional[str] = None) -> str:
        """导出为JSON"""
        data = {name: config.to_dict() for name, config in self._plants.items()}
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        if filepath:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json_str, encoding="utf-8")
        
        return json_str
    
    @classmethod
    def from_json(cls, filepath: str) -> "PlantDatabase":
        """从JSON文件加载"""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Plant database file not found: {filepath}")
        
        data = json.loads(path.read_text(encoding="utf-8"))
        
        db = cls()
        db._plants = {}
        db._by_category = {cat: [] for cat in PlantCategory}
        
        for name, config_data in data.items():
            plant = PlantConfig.from_dict(config_data)
            db._plants[name] = plant
            db._by_category[plant.category].append(name)
        
        return db
    
    def reload(self):
        """重新加载默认配置"""
        self._plants = {}
        self._by_category = {cat: [] for cat in PlantCategory}
        self._load_all_plants()
    
    @property
    def count(self) -> int:
        """植物总数"""
        return len(self._plants)
    
    @property
    def categories_count(self) -> Dict[str, int]:
        """各分类植物数量"""
        return {cat.value: len(names) for cat, names in self._by_category.items()}


# 全局单例实例
def get_plant_database() -> PlantDatabase:
    """获取植物数据库单例"""
    return PlantDatabase()


if __name__ == "__main__":
    # 测试代码
    db = get_plant_database()
    print(f"植物总数：{db.count}")
    print(f"分类统计：{db.categories_count}")
    
    peashooter = db.get("peashooter")
    if peashooter:
        print(f"\n豌豆射手配置:")
        print(f"  阳光消耗：{peashooter.sun_cost}")
        print(f"  伤害：{peashooter.damage}")
        print(f"  攻击间隔：{peashooter.attack_interval}s")
        print(f"  解锁等级：{peashooter.unlock_level}")
    
    # 导出JSON
    db.to_json("data/config/plants.json")
    print("\n已导出 plants.json")
