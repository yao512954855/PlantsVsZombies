"""
僵尸数据库模块 - 完整26种僵尸定义

本模块包含《植物大战僵尸》中所有26种僵尸的完整数据定义，
包括普通僵尸、特殊能力僵尸和BOSS级僵尸。

Categories:
    - NORMAL: 普通僵尸 (基础变种)
    - SPECIAL: 特殊僵尸 (拥有特殊能力)
    - BOSS: BOSS级僵尸 (伽刚特尔、僵王博士等)
    - AQUATIC: 水生僵尸
    - AIRBORNE: 飞行僵尸
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
import json
from pathlib import Path


class ZombieCategory(Enum):
    """僵尸分类枚举"""
    NORMAL = "normal"
    SPECIAL = "special"
    BOSS = "boss"
    AQUATIC = "aquatic"
    AIRBORNE = "airborne"


class ZombieBehavior(Enum):
    """僵尸行为模式"""
    WALK = "walk"              # 正常行走
    RUN = "run"                # 奔跑
    JUMP = "jump"              # 跳跃
    DIG = "dig"                # 挖地
    SWIM = "swim"              # 游泳
    FLY = "fly"                # 飞行
    DRIVE = "drive"            # 驾驶
    DANCE = "dance"            # 跳舞召唤
    THROW = "throw"            # 投掷
    EXPLODE = "explode"        # 自爆


@dataclass
class ZombieConfig:
    """僵尸配置数据类"""
    name: str
    name_cn: str
    category: ZombieCategory
    health: int
    damage: int          # 对植物的伤害
    speed: float         # 格子/秒
    attack_speed: float  # 攻击间隔 (秒)
    behavior: ZombieBehavior
    special_ability: Optional[str] = None
    first_appearance_level: int = 1
    description: str = ""
    
    # 视觉属性
    color: str = "#8B0000"
    size: tuple = (50, 70)
    
    # 抗性属性
    ice_resistance: float = 1.0    # 冰系抗性
    fire_resistance: float = 1.0   # 火系抗性
    explosion_resistance: float = 1.0  # 爆炸抗性
    
    # 掉落物
    drops: List[str] = None
    
    def __post_init__(self):
        if self.drops is None:
            self.drops = []
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "name": self.name,
            "name_cn": self.name_cn,
            "category": self.category.value,
            "health": self.health,
            "damage": self.damage,
            "speed": self.speed,
            "attack_speed": self.attack_speed,
            "behavior": self.behavior.value,
            "special_ability": self.special_ability,
            "first_appearance_level": self.first_appearance_level,
            "description": self.description,
            "color": self.color,
            "size": self.size,
            "ice_resistance": self.ice_resistance,
            "fire_resistance": self.fire_resistance,
            "explosion_resistance": self.explosion_resistance,
            "drops": self.drops,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ZombieConfig":
        """从字典创建"""
        return cls(
            name=data["name"],
            name_cn=data["name_cn"],
            category=ZombieCategory(data["category"]),
            health=data["health"],
            damage=data["damage"],
            speed=data["speed"],
            attack_speed=data["attack_speed"],
            behavior=ZombieBehavior(data["behavior"]),
            special_ability=data.get("special_ability"),
            first_appearance_level=data.get("first_appearance_level", 1),
            description=data.get("description", ""),
            color=data.get("color", "#8B0000"),
            size=tuple(data.get("size", [50, 70])),
            ice_resistance=data.get("ice_resistance", 1.0),
            fire_resistance=data.get("fire_resistance", 1.0),
            explosion_resistance=data.get("explosion_resistance", 1.0),
            drops=data.get("drops", []),
        )


class ZombieDatabase:
    """
    僵尸数据库单例类
    
    管理所有26种僵尸的配置数据，支持：
    - 按名称/分类查询
    - 关卡出现检查
    - 数据序列化/反序列化
    - 波次生成配置
    """
    
    _instance: Optional["ZombieDatabase"] = None
    
    def __new__(cls) -> "ZombieDatabase":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._zombies: Dict[str, ZombieConfig] = {}
        self._by_category: Dict[ZombieCategory, List[str]] = {
            cat: [] for cat in ZombieCategory
        }
        self._load_all_zombies()
        self._initialized = True
    
    def _load_all_zombies(self):
        """加载所有26种僵尸配置"""
        
        # ==================== 普通僵尸 (NORMAL) ====================
        
        # 1. 普通僵尸
        self._add_zombie(ZombieConfig(
            name="basic_zombie",
            name_cn="普通僵尸",
            category=ZombieCategory.NORMAL,
            health=200,
            damage=25,
            speed=0.3,
            attack_speed=1.0,
            behavior=ZombieBehavior.WALK,
            first_appearance_level=1,
            description="最基础的僵尸，缓慢前行",
            color="#556B2F",
            drops=["coin_small"],
        ))
        
        # 2. 路障僵尸
        self._add_zombie(ZombieConfig(
            name="conehead_zombie",
            name_cn="路障僵尸",
            category=ZombieCategory.NORMAL,
            health=560,  # 200 + 360(路障)
            damage=25,
            speed=0.3,
            attack_speed=1.0,
            behavior=ZombieBehavior.WALK,
            special_ability="路障提供额外护甲",
            first_appearance_level=2,
            description="戴着路障的僵尸，防御力更高",
            color="#FF8C00",
            drops=["coin_small"],
        ))
        
        # 3. 铁桶僵尸
        self._add_zombie(ZombieConfig(
            name="buckethead_zombie",
            name_cn="铁桶僵尸",
            category=ZombieCategory.NORMAL,
            health=1300,  # 200 + 1100(铁桶)
            damage=25,
            speed=0.3,
            attack_speed=1.0,
            behavior=ZombieBehavior.WALK,
            special_ability="铁桶提供高护甲",
            first_appearance_level=4,
            description="戴着铁桶的僵尸，非常耐打",
            color="#708090",
            drops=["coin_medium"],
        ))
        
        # 4. 报纸僵尸
        self._add_zombie(ZombieConfig(
            name="newspaper_zombie",
            name_cn="报纸僵尸",
            category=ZombieCategory.SPECIAL,
            health=250,  # 报纸 150 + 本体 100
            damage=25,
            speed=0.2,
            attack_speed=1.0,
            behavior=ZombieBehavior.WALK,
            special_ability="报纸破碎后狂暴加速",
            first_appearance_level=9,
            description="拿着报纸的僵尸，报纸被打烂后会发怒狂奔",
            color="#D2B48C",
            drops=["coin_small"],
        ))
        
        # 5. 撑杆跳僵尸
        self._add_zombie(ZombieConfig(
            name="pole_vaulting_zombie",
            name_cn="撑杆跳僵尸",
            category=ZombieCategory.SPECIAL,
            health=300,
            damage=25,
            speed=0.5,
            attack_speed=1.0,
            behavior=ZombieBehavior.JUMP,
            special_ability="跳过第一个遇到的植物",
            first_appearance_level=7,
            description="用撑杆跳过植物防线",
            color="#4169E1",
            drops=["coin_small"],
        ))
        
        # 6. 舞王僵尸
        self._add_zombie(ZombieConfig(
            name="dancing_zombie",
            name_cn="舞王僵尸",
            category=ZombieCategory.SPECIAL,
            health=500,
            damage=25,
            speed=0.3,
            attack_speed=1.0,
            behavior=ZombieBehavior.DANCE,
            special_ability="每走一段距离召唤伴舞僵尸",
            first_appearance_level=15,
            description="召唤四个伴舞僵尸助战",
            color="#FFD700",
            drops=["coin_medium"],
        ))
        
        # 7. 伴舞僵尸
        self._add_zombie(ZombieConfig(
            name="backup_dancer",
            name_cn="伴舞僵尸",
            category=ZombieCategory.NORMAL,
            health=200,
            damage=25,
            speed=0.3,
            attack_speed=1.0,
            behavior=ZombieBehavior.WALK,
            special_ability="由舞王僵尸召唤",
            first_appearance_level=15,
            description="舞王的跟班",
            color="#FFA500",
            drops=["coin_small"],
        ))
        
        # 8. 橄榄球僵尸
        self._add_zombie(ZombieConfig(
            name="football_zombie",
            name_cn="橄榄球僵尸",
            category=ZombieCategory.SPECIAL,
            health=1400,
            damage=50,
            speed=0.6,
            attack_speed=1.0,
            behavior=ZombieBehavior.RUN,
            special_ability="高速冲锋，高血量",
            first_appearance_level=20,
            description="穿着橄榄球服的狂暴僵尸",
            color="#8B0000",
            drops=["coin_large"],
        ))
        
        # 9. 雪人僵尸
        self._add_zombie(ZombieConfig(
            name="yeti_zombie",
            name_cn="雪人僵尸",
            category=ZombieCategory.SPECIAL,
            health=600,
            damage=50,
            speed=0.4,
            attack_speed=1.0,
            behavior=ZombieBehavior.WALK,
            special_ability="出现一段时间后逃跑",
            first_appearance_level=40,
            description="稀有的雪人僵尸，击败获得大量奖励",
            color="#F0FFFF",
            drops=["diamond", "coin_large"],
        ))
        
        # ==================== 水生僵尸 (AQUATIC) ====================
        
        # 10. 潜水僵尸
        self._add_zombie(ZombieConfig(
            name="snorkel_zombie",
            name_cn="潜水僵尸",
            category=ZombieCategory.AQUATIC,
            health=200,
            damage=25,
            speed=0.4,
            attack_speed=1.0,
            behavior=ZombieBehavior.SWIM,
            special_ability="在水下躲避直线攻击",
            first_appearance_level=12,
            description="潜水躲避攻击，只在进食时露头",
            color="#4682B4",
            drops=["coin_small"],
        ))
        
        # 11. 海豚骑士僵尸
        self._add_zombie(ZombieConfig(
            name="dolphin_rider_zombie",
            name_cn="海豚骑士僵尸",
            category=ZombieCategory.AQUATIC,
            health=350,
            damage=25,
            speed=0.8,
            attack_speed=1.0,
            behavior=ZombieBehavior.JUMP,
            special_ability="骑海豚快速移动并跳过植物",
            first_appearance_level=16,
            description="骑着海豚冲刺的僵尸",
            color="#20B2AA",
            drops=["coin_medium"],
        ))
        
        # 12. 海龟僵尸
        self._add_zombie(ZombieConfig(
            name="turtle_zombie",
            name_cn="海龟僵尸",
            category=ZombieCategory.AQUATIC,
            health=800,
            damage=25,
            speed=0.2,
            attack_speed=1.0,
            behavior=ZombieBehavior.SWIM,
            special_ability="龟壳提供高防御",
            first_appearance_level=18,
            description="背着龟壳的水中坦克",
            color="#556B2F",
            drops=["coin_medium"],
        ))
        
        # 13. 章鱼僵尸
        self._add_zombie(ZombieConfig(
            name="octo_zombie",
            name_cn="章鱼僵尸",
            category=ZombieCategory.AQUATIC,
            health=400,
            damage=25,
            speed=0.3,
            attack_speed=1.0,
            behavior=ZombieBehavior.THROW,
            special_ability="投掷章鱼缠绕植物使其无法攻击",
            first_appearance_level=28,
            description="用章鱼困住植物",
            color="#FF69B4",
            drops=["coin_medium"],
        ))
        
        # ==================== 飞行僵尸 (AIRBORNE) ====================
        
        # 14. 气球僵尸
        self._add_zombie(ZombieConfig(
            name="balloon_zombie",
            name_cn="气球僵尸",
            category=ZombieCategory.AIRBORNE,
            health=150,
            damage=25,
            speed=0.5,
            attack_speed=1.0,
            behavior=ZombieBehavior.FLY,
            special_ability="飞行越过大部分植物",
            first_appearance_level=17,
            description="乘着气球飞越防线",
            color="#FFB6C1",
            drops=["coin_small"],
        ))
        
        # 15. 飞贼僵尸
        self._add_zombie(ZombieConfig(
            name="bungee_zombie",
            name_cn="飞贼僵尸",
            category=ZombieCategory.AIRBORNE,
            health=450,
            damage=0,
            speed=0,
            attack_speed=0,
            behavior=ZombieBehavior.FLY,
            special_ability="从天而降偷走植物",
            first_appearance_level=22,
            description="偷取植物的空中威胁",
            color="#000000",
            drops=[],
        ))
        
        # 16. 滑翔机僵尸
        self._add_zombie(ZombieConfig(
            name="glider_zombie",
            name_cn="滑翔机僵尸",
            category=ZombieCategory.AIRBORNE,
            health=300,
            damage=25,
            speed=0.6,
            attack_speed=1.0,
            behavior=ZombieBehavior.FLY,
            special_ability="滑翔降落避开前排防御",
            first_appearance_level=30,
            description="驾驶滑翔机突袭",
            color="#87CEEB",
            drops=["coin_medium"],
        ))
        
        # ==================== 特殊能力僵尸 (SPECIAL) ====================
        
        # 17. 梯子僵尸
        self._add_zombie(ZombieConfig(
            name="ladder_zombie",
            name_cn="梯子僵尸",
            category=ZombieCategory.SPECIAL,
            health=500,  # 梯子 300 + 本体 200
            damage=25,
            speed=0.3,
            attack_speed=1.0,
            behavior=ZombieBehavior.WALK,
            special_ability="放置梯子让僵尸翻过高坚果",
            first_appearance_level=25,
            description="携带梯子跨越高墙",
            color="#CD853F",
            drops=["coin_small"],
        ))
        
        # 18. 矿工僵尸
        self._add_zombie(ZombieConfig(
            name="digger_zombie",
            name_cn="矿工僵尸",
            category=ZombieCategory.SPECIAL,
            health=300,
            damage=25,
            speed=0.2,
            attack_speed=1.0,
            behavior=ZombieBehavior.DIG,
            special_ability="挖地道到后方出现",
            first_appearance_level=24,
            description="挖地偷袭后方植物",
            color="#8B4513",
            drops=["coin_medium", "diamond"],
        ))
        
        # 19. 投石车僵尸
        self._add_zombie(ZombieConfig(
            name="catapult_zombie",
            name_cn="投石车僵尸",
            category=ZombieCategory.SPECIAL,
            health=600,
            damage=50,
            speed=0.25,
            attack_speed=2.0,
            behavior=ZombieBehavior.THROW,
            special_ability="远程投掷篮球攻击植物",
            first_appearance_level=26,
            description="隔空打击植物防线",
            color="#A52A2A",
            drops=["coin_large"],
        ))
        
        # 20. 冰车僵尸
        self._add_zombie(ZombieConfig(
            name="zamboni_zombie",
            name_cn="冰车僵尸",
            category=ZombieCategory.SPECIAL,
            health=800,
            damage=100,
            speed=0.4,
            attack_speed=1.0,
            behavior=ZombieBehavior.DRIVE,
            special_ability="压扁植物并留下冰道",
            first_appearance_level=27,
            description="驾驶冰面清理车碾压一切",
            color="#ADD8E6",
            drops=["coin_large"],
        ))
        
        # 21. 小丑僵尸
        self._add_zombie(ZombieConfig(
            name="jack_in_the_box_zombie",
            name_cn="小丑僵尸",
            category=ZombieCategory.SPECIAL,
            health=300,
            damage=25,
            speed=0.5,
            attack_speed=1.0,
            behavior=ZombieBehavior.EXPLODE,
            special_ability="随机自爆造成范围伤害",
            first_appearance_level=21,
            description="拿着炸弹箱子的疯狂小丑",
            color="#FF1493",
            drops=["coin_small"],
        ))
        
        # 22. 巨型爆竹僵尸
        self._add_zombie(ZombieConfig(
            name="giga_gargantuar_imp",
            name_cn="小鬼炮僵尸",
            category=ZombieCategory.SPECIAL,
            health=400,
            damage=25,
            speed=0.2,
            attack_speed=1.0,
            behavior=ZombieBehavior.THROW,
            special_ability="发射小鬼僵尸到后方",
            first_appearance_level=35,
            description="远程投掷小鬼偷袭",
            color="#DC143C",
            drops=["coin_medium"],
        ))
        
        # 23. 小鬼僵尸
        self._add_zombie(ZombieConfig(
            name="imp_zombie",
            name_cn="小鬼僵尸",
            category=ZombieCategory.NORMAL,
            health=150,
            damage=25,
            speed=0.5,
            attack_speed=1.0,
            behavior=ZombieBehavior.WALK,
            special_ability="被伽刚特尔投掷到后方",
            first_appearance_level=10,
            description="小型快速僵尸",
            color="#32CD32",
            drops=["coin_small"],
        ))
        
        # ==================== BOSS 级僵尸 (BOSS) ====================
        
        # 24. 伽刚特尔
        self._add_zombie(ZombieConfig(
            name="gargantuar",
            name_cn="伽刚特尔",
            category=ZombieCategory.BOSS,
            health=3000,
            damage=150,
            speed=0.15,
            attack_speed=2.0,
            behavior=ZombieBehavior.WALK,
            special_ability="砸扁植物，半血时投掷小鬼",
            first_appearance_level=30,
            description="巨型僵尸 boss，极其危险",
            color="#2F4F4F",
            size=(80, 120),
            ice_resistance=0.8,
            fire_resistance=0.8,
            explosion_resistance=0.5,
            drops=["coin_huge"],
        ))
        
        # 25. 冰车伽刚特尔
        self._add_zombie(ZombieConfig(
            name="ice_gargantuar",
            name_cn="冰车伽刚特尔",
            category=ZombieCategory.BOSS,
            health=3500,
            damage=150,
            speed=0.18,
            attack_speed=2.0,
            behavior=ZombieBehavior.DRIVE,
            special_ability="驾驶冰车碾压，半血时投掷小鬼",
            first_appearance_level=40,
            description="强化版伽刚特尔",
            color="#B0E0E6",
            size=(80, 120),
            ice_resistance=0.5,
            fire_resistance=1.0,
            explosion_resistance=0.5,
            drops=["coin_huge", "diamond"],
        ))
        
        # 26. 僵王博士
        self._add_zombie(ZombieConfig(
            name="dr_zomboss",
            name_cn="僵王博士",
            category=ZombieCategory.BOSS,
            health=20000,
            damage=300,
            speed=0.1,
            attack_speed=5.0,
            behavior=ZombieBehavior.DRIVE,
            special_ability="驾驶机甲，释放多种技能",
            first_appearance_level=50,
            description="最终 BOSS，拥有毁灭性力量",
            color="#4B0082",
            size=(150, 200),
            ice_resistance=0.3,
            fire_resistance=0.3,
            explosion_resistance=0.2,
            drops=["trophy"],
        ))
    
    def _add_zombie(self, zombie: ZombieConfig):
        """添加僵尸到数据库"""
        self._zombies[zombie.name] = zombie
        self._by_category[zombie.category].append(zombie.name)
    
    def get(self, name: str) -> Optional[ZombieConfig]:
        """根据名称获取僵尸配置"""
        return self._zombies.get(name)
    
    def get_by_category(self, category: ZombieCategory) -> List[ZombieConfig]:
        """获取指定分类的所有僵尸"""
        names = self._by_category.get(category, [])
        return [self._zombies[name] for name in names if name in self._zombies]
    
    def get_all(self) -> List[ZombieConfig]:
        """获取所有僵尸配置"""
        return list(self._zombies.values())
    
    def appears_at_level(self, level: int) -> List[ZombieConfig]:
        """获取在指定关卡首次出现的僵尸"""
        return [z for z in self._zombies.values() if z.first_appearance_level == level]
    
    def available_at_level(self, level: int) -> List[ZombieConfig]:
        """获取在指定关卡可用的所有僵尸"""
        return [z for z in self._zombies.values() if z.first_appearance_level <= level]
    
    def to_json(self, filepath: Optional[str] = None) -> str:
        """导出为 JSON"""
        data = {name: config.to_dict() for name, config in self._zombies.items()}
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        if filepath:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json_str, encoding="utf-8")
        
        return json_str
    
    @classmethod
    def from_json(cls, filepath: str) -> "ZombieDatabase":
        """从 JSON 文件加载"""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Zombie database file not found: {filepath}")
        
        data = json.loads(path.read_text(encoding="utf-8"))
        
        db = cls()
        db._zombies = {}
        db._by_category = {cat: [] for cat in ZombieCategory}
        
        for name, config_data in data.items():
            zombie = ZombieConfig.from_dict(config_data)
            db._zombies[name] = zombie
            db._by_category[zombie.category].append(name)
        
        return db
    
    def reload(self):
        """重新加载默认配置"""
        self._zombies = {}
        self._by_category = {cat: [] for cat in ZombieCategory}
        self._load_all_zombies()
    
    @property
    def count(self) -> int:
        """僵尸总数"""
        return len(self._zombies)
    
    @property
    def categories_count(self) -> Dict[str, int]:
        """各分类僵尸数量"""
        return {cat.value: len(names) for cat, names in self._by_category.items()}


# 全局单例实例
def get_zombie_database() -> ZombieDatabase:
    """获取僵尸数据库单例"""
    return ZombieDatabase()


if __name__ == "__main__":
    # 测试代码
    db = get_zombie_database()
    print(f"僵尸总数：{db.count}")
    print(f"分类统计：{db.categories_count}")
    
    gargantuar = db.get("gargantuar")
    if gargantuar:
        print(f"\n伽刚特尔配置:")
        print(f"  血量：{gargantuar.health}")
        print(f"  伤害：{gargantuar.damage}")
        print(f"  速度：{gargantuar.speed} 格子/秒")
        print(f"  首次出现：{gargantuar.first_appearance_level}关")
    
    # 导出 JSON
    db.to_json("data/config/zombies.json")
    print("\n已导出 zombies.json")
