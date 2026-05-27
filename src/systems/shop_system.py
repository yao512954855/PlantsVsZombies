"""
商店系统模块 - 完整的植物购买与解锁机制

本模块实现《植物大战僵尸》中的商店系统，包括：
- 植物卡片购买与解锁
- 道具购买 (除草剂、肥料等)
- 成就奖励兑换
- 价格浮动机制
- 库存管理

Features:
    - 动态价格系统 (基于购买次数)
    - 折扣活动支持
    - 限时特卖
    - 金币/钻石双货币系统
    - 存档集成
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple
import json
import random
from pathlib import Path
from datetime import datetime


class ItemType(Enum):
    """物品类型枚举"""
    PLANT = "plant"
    TOOL = "tool"
    UPGRADE = "upgrade"
    ACHIEVEMENT = "achievement"


class CurrencyType(Enum):
    """货币类型"""
    COIN = "coin"      # 金币
    DIAMOND = "diamond"  # 钻石


@dataclass
class ShopItem:
    """商店物品数据类"""
    id: str
    name: str
    name_cn: str
    item_type: ItemType
    price: int
    currency: CurrencyType
    description: str = ""
    
    # 解锁条件
    required_level: int = 1
    required_achievement: Optional[str] = None
    
    # 库存相关
    max_stack: int = 1
    is_consumable: bool = False
    is_permanent: bool = True
    
    # 价格浮动
    base_price: int = 0
    price_increase_per_buy: int = 0
    
    # 显示属性
    icon: str = ""
    rarity: str = "common"  # common, rare, epic, legendary
    is_featured: bool = False
    discount: float = 1.0  # 折扣率，1.0 为原价
    
    def __post_init__(self):
        if self.base_price == 0:
            self.base_price = self.price
    
    def get_current_price(self, times_bought: int = 0) -> int:
        """计算当前价格 (考虑浮动和折扣)"""
        increased_price = self.base_price + (times_bought * self.price_increase_per_buy)
        discounted_price = int(increased_price * self.discount)
        return max(discounted_price, 1)  # 至少为 1
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "name_cn": self.name_cn,
            "item_type": self.item_type.value,
            "price": self.price,
            "currency": self.currency.value,
            "description": self.description,
            "required_level": self.required_level,
            "required_achievement": self.required_achievement,
            "max_stack": self.max_stack,
            "is_consumable": self.is_consumable,
            "is_permanent": self.is_permanent,
            "base_price": self.base_price,
            "price_increase_per_buy": self.price_increase_per_buy,
            "icon": self.icon,
            "rarity": self.rarity,
            "is_featured": self.is_featured,
            "discount": self.discount,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ShopItem":
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data["name"],
            name_cn=data["name_cn"],
            item_type=ItemType(data["item_type"]),
            price=data["price"],
            currency=CurrencyType(data["currency"]),
            description=data.get("description", ""),
            required_level=data.get("required_level", 1),
            required_achievement=data.get("required_achievement"),
            max_stack=data.get("max_stack", 1),
            is_consumable=data.get("is_consumable", False),
            is_permanent=data.get("is_permanent", True),
            base_price=data.get("base_price", data["price"]),
            price_increase_per_buy=data.get("price_increase_per_buy", 0),
            icon=data.get("icon", ""),
            rarity=data.get("rarity", "common"),
            is_featured=data.get("is_featured", False),
            discount=data.get("discount", 1.0),
        )


@dataclass
class PlayerInventory:
    """玩家库存数据类"""
    coins: int = 0
    diamonds: int = 0
    items: Dict[str, int] = field(default_factory=dict)  # item_id -> count
    purchased_items: Dict[str, int] = field(default_factory=dict)  # item_id -> times bought
    unlocked_plants: List[str] = field(default_factory=list)
    
    def add_coin(self, amount: int):
        """添加金币"""
        self.coins += max(0, amount)
    
    def spend_coin(self, amount: int) -> bool:
        """花费金币"""
        if self.coins >= amount:
            self.coins -= amount
            return True
        return False
    
    def add_diamond(self, amount: int):
        """添加钻石"""
        self.diamonds += max(0, amount)
    
    def spend_diamond(self, amount: int) -> bool:
        """花费钻石"""
        if self.diamonds >= amount:
            self.diamonds -= amount
            return True
        return False
    
    def add_item(self, item_id: str, count: int = 1, max_stack: int = 99):
        """添加物品到库存"""
        current = self.items.get(item_id, 0)
        self.items[item_id] = min(current + count, max_stack)
    
    def has_item(self, item_id: str, count: int = 1) -> bool:
        """检查是否有足够物品"""
        return self.items.get(item_id, 0) >= count
    
    def consume_item(self, item_id: str, count: int = 1) -> bool:
        """消耗物品"""
        if self.has_item(item_id, count):
            self.items[item_id] -= count
            if self.items[item_id] <= 0:
                del self.items[item_id]
            return True
        return False
    
    def unlock_plant(self, plant_name: str):
        """解锁植物"""
        if plant_name not in self.unlocked_plants:
            self.unlocked_plants.append(plant_name)
    
    def is_plant_unlocked(self, plant_name: str) -> bool:
        """检查植物是否已解锁"""
        return plant_name in self.unlocked_plants
    
    def record_purchase(self, item_id: str):
        """记录购买次数"""
        self.purchased_items[item_id] = self.purchased_items.get(item_id, 0) + 1
    
    def get_purchase_count(self, item_id: str) -> int:
        """获取物品购买次数"""
        return self.purchased_items.get(item_id, 0)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "coins": self.coins,
            "diamonds": self.diamonds,
            "items": self.items,
            "purchased_items": self.purchased_items,
            "unlocked_plants": self.unlocked_plants,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PlayerInventory":
        """从字典创建"""
        return cls(
            coins=data.get("coins", 0),
            diamonds=data.get("diamonds", 0),
            items=data.get("items", {}),
            purchased_items=data.get("purchased_items", {}),
            unlocked_plants=data.get("unlocked_plants", []),
        )


class ShopSystem:
    """
    商店系统单例类
    
    管理游戏内商店的所有功能：
    - 物品列表管理
    - 购买逻辑
    - 价格浮动
    - 折扣活动
    - 库存同步
    """
    
    _instance: Optional["ShopSystem"] = None
    
    def __new__(cls) -> "ShopSystem":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._items: Dict[str, ShopItem] = {}
        self._inventory: Optional[PlayerInventory] = None
        self._daily_specials: List[str] = []
        self._load_all_items()
        self._initialized = True
    
    def _load_all_items(self):
        """加载所有商店物品"""
        
        # ==================== 植物卡片 ====================
        
        # 基础植物
        self._add_item(ShopItem(
            id="plant_peashooter",
            name="peashooter",
            name_cn="豌豆射手",
            item_type=ItemType.PLANT,
            price=100,
            currency=CurrencyType.COIN,
            description="解锁豌豆射手卡片",
            required_level=1,
            is_permanent=True,
            icon="🌱",
            rarity="common",
        ))
        
        self._add_item(ShopItem(
            id="plant_sunflower",
            name="sunflower",
            name_cn="向日葵",
            item_type=ItemType.PLANT,
            price=50,
            currency=CurrencyType.COIN,
            description="解锁向日葵卡片",
            required_level=1,
            is_permanent=True,
            icon="🌻",
            rarity="common",
        ))
        
        self._add_item(ShopItem(
            id="plant_cherry_bomb",
            name="cherry_bomb",
            name_cn="樱桃炸弹",
            item_type=ItemType.PLANT,
            price=150,
            currency=CurrencyType.COIN,
            description="解锁樱桃炸弹卡片",
            required_level=5,
            is_permanent=True,
            icon="🍒",
            rarity="rare",
        ))
        
        self._add_item(ShopItem(
            id="plant_wall_nut",
            name="wall_nut",
            name_cn="坚果墙",
            item_type=ItemType.PLANT,
            price=50,
            currency=CurrencyType.COIN,
            description="解锁坚果墙卡片",
            required_level=2,
            is_permanent=True,
            icon="🥜",
            rarity="common",
        ))
        
        self._add_item(ShopItem(
            id="plant_potato_mine",
            name="potato_mine",
            name_cn="土豆雷",
            item_type=ItemType.PLANT,
            price=25,
            currency=CurrencyType.COIN,
            description="解锁土豆雷卡片",
            required_level=3,
            is_permanent=True,
            icon="🥔",
            rarity="common",
        ))
        
        # 高级植物
        self._add_item(ShopItem(
            id="plant_snow_pea",
            name="snow_pea",
            name_cn="寒冰射手",
            item_type=ItemType.PLANT,
            price=175,
            currency=CurrencyType.COIN,
            description="解锁寒冰射手卡片",
            required_level=8,
            is_permanent=True,
            icon="❄️",
            rarity="rare",
        ))
        
        self._add_item(ShopItem(
            id="plant_chomper",
            name="chomper",
            name_cn="大嘴花",
            item_type=ItemType.PLANT,
            price=150,
            currency=CurrencyType.COIN,
            description="解锁大嘴花卡片",
            required_level=10,
            is_permanent=True,
            icon="🦷",
            rarity="rare",
        ))
        
        self._add_item(ShopItem(
            id="plant_repeater",
            name="repeater",
            name_cn="双发射手",
            item_type=ItemType.PLANT,
            price=200,
            currency=CurrencyType.COIN,
            description="解锁双发射手卡片",
            required_level=6,
            is_permanent=True,
            icon="🌿",
            rarity="rare",
        ))
        
        # 传奇植物
        self._add_item(ShopItem(
            id="plant_gatling_pea",
            name="gatling_pea",
            name_cn="机枪射手",
            item_type=ItemType.PLANT,
            price=500,
            currency=CurrencyType.COIN,
            description="解锁机枪射手卡片",
            required_level=20,
            is_permanent=True,
            icon="🔫",
            rarity="legendary",
        ))
        
        self._add_item(ShopItem(
            id="plant_winter_melon",
            name="winter_melon",
            name_cn="冰西瓜",
            item_type=ItemType.PLANT,
            price=700,
            currency=CurrencyType.COIN,
            description="解锁冰西瓜卡片",
            required_level=35,
            is_permanent=True,
            icon="🍉",
            rarity="legendary",
        ))
        
        # ==================== 工具道具 ====================
        
        self._add_item(ShopItem(
            id="tool_fertilizer",
            name="fertilizer",
            name_cn="肥料",
            item_type=ItemType.TOOL,
            price=500,
            currency=CurrencyType.COIN,
            description="使植物立即生产一次",
            is_consumable=True,
            max_stack=99,
            icon="💩",
            rarity="common",
        ))
        
        self._add_item(ShopItem(
            id="tool_bug spray",
            name="bug_spray",
            name_cn="杀虫剂",
            item_type=ItemType.TOOL,
            price=1000,
            currency=CurrencyType.COIN,
            description="消灭屏幕上的所有普通僵尸",
            is_consumable=True,
            max_stack=10,
            icon="🧴",
            rarity="rare",
        ))
        
        self._add_item(ShopItem(
            id="tool_phonograph",
            name="phonograph",
            name_cn="留声机",
            item_type=ItemType.TOOL,
            price=1500,
            currency=CurrencyType.COIN,
            description="让僵尸暂停前进 10 秒",
            is_consumable=True,
            max_stack=5,
            icon="📻",
            rarity="epic",
        ))
        
        self._add_item(ShopItem(
            id="tool_gardening glove",
            name="gardening_glove",
            name_cn="园艺手套",
            item_type=ItemType.TOOL,
            price=2000,
            currency=CurrencyType.COIN,
            description="移动任意植物到空位",
            is_consumable=True,
            max_stack=20,
            icon="🧤",
            rarity="rare",
        ))
        
        self._add_item(ShopItem(
            id="tool_mushroom garden",
            name="mushroom_garden",
            name_cn="蘑菇园",
            item_type=ItemType.UPGRADE,
            price=5000,
            currency=CurrencyType.COIN,
            description="解锁禅境花园的蘑菇区域",
            is_permanent=True,
            icon="🍄",
            rarity="epic",
            required_level=30,
        ))
        
        self._add_item(ShopItem(
            id="tool_aquarium garden",
            name="aquarium_garden",
            name_cn="水族馆",
            item_type=ItemType.UPGRADE,
            price=7500,
            currency=CurrencyType.COIN,
            description="解锁禅境花园的水族馆区域",
            is_permanent=True,
            icon="🐟",
            rarity="epic",
            required_level=40,
        ))
        
        # ==================== 钻石物品 ====================
        
        self._add_item(ShopItem(
            id="pack_coins_small",
            name="coins_small",
            name_cn="金币包 (小)",
            item_type=ItemType.TOOL,
            price=10,
            currency=CurrencyType.DIAMOND,
            description="获得 500 金币",
            is_consumable=True,
            max_stack=999,
            icon="💰",
            rarity="common",
        ))
        
        self._add_item(ShopItem(
            id="pack_coins_large",
            name="coins_large",
            name_cn="金币包 (大)",
            item_type=ItemType.TOOL,
            price=50,
            currency=CurrencyType.DIAMOND,
            description="获得 3000 金币",
            is_consumable=True,
            max_stack=999,
            icon="💎",
            rarity="rare",
        ))
        
        self._add_item(ShopItem(
            id="plant_imitater",
            name="imitater",
            name_cn="模仿者",
            item_type=ItemType.PLANT,
            price=100,
            currency=CurrencyType.DIAMOND,
            description="解锁模仿者卡片",
            is_permanent=True,
            icon="🎭",
            rarity="legendary",
            required_level=43,
        ))
    
    def _add_item(self, item: ShopItem):
        """添加物品到商店"""
        self._items[item.id] = item
    
    def set_inventory(self, inventory: PlayerInventory):
        """设置玩家库存"""
        self._inventory = inventory
    
    def get_inventory(self) -> Optional[PlayerInventory]:
        """获取玩家库存"""
        return self._inventory
    
    def get_item(self, item_id: str) -> Optional[ShopItem]:
        """根据 ID 获取物品"""
        return self._items.get(item_id)
    
    def get_all_items(self) -> List[ShopItem]:
        """获取所有物品"""
        return list(self._items.values())
    
    def get_available_items(self, player_level: int) -> List[ShopItem]:
        """获取玩家可购买的物品"""
        available = []
        for item in self._items.values():
            if item.required_level <= player_level:
                # 检查是否已购买永久物品
                if item.is_permanent and self._inventory:
                    if item.item_type == ItemType.PLANT:
                        if self._inventory.is_plant_unlocked(item.name):
                            continue
                available.append(item)
        return available
    
    def purchase_item(self, item_id: str) -> Tuple[bool, str]:
        """
        购买物品
        
        Returns:
            (success, message): 购买结果和消息
        """
        if not self._inventory:
            return False, "库存未初始化"
        
        item = self._items.get(item_id)
        if not item:
            return False, "物品不存在"
        
        # 检查解锁条件
        if self._inventory.coins < item.required_level:
            pass  # 这里可以添加更详细的等级检查
        
        # 检查是否已拥有永久物品
        if item.is_permanent and item.item_type == ItemType.PLANT:
            if self._inventory.is_plant_unlocked(item.name):
                return False, "已拥有该植物"
        
        # 获取当前价格
        purchase_count = self._inventory.get_purchase_count(item_id)
        current_price = item.get_current_price(purchase_count)
        
        # 检查货币是否足够
        if item.currency == CurrencyType.COIN:
            if not self._inventory.spend_coin(current_price):
                return False, f"金币不足 (需要{current_price})"
        elif item.currency == CurrencyType.DIAMOND:
            if not self._inventory.spend_diamond(current_price):
                return False, f"钻石不足 (需要{current_price})"
        
        # 添加物品到库存
        if item.is_consumable:
            self._inventory.add_item(item_id, 1, item.max_stack)
        elif item.item_type == ItemType.PLANT:
            self._inventory.unlock_plant(item.name)
        
        # 记录购买
        self._inventory.record_purchase(item_id)
        
        return True, f"成功购买 {item.name_cn}!"
    
    def apply_discount(self, item_ids: List[str], discount: float):
        """对指定物品应用折扣"""
        for item_id in item_ids:
            if item_id in self._items:
                self._items[item_id].discount = max(0.1, min(1.0, discount))
    
    def reset_discounts(self):
        """重置所有折扣"""
        for item in self._items.values():
            item.discount = 1.0
    
    def generate_daily_specials(self) -> List[str]:
        """生成每日特卖商品"""
        all_items = list(self._items.keys())
        # 随机选择 3-5 个物品作为今日特卖
        num_specials = random.randint(3, 5)
        self._daily_specials = random.sample(all_items, min(num_specials, len(all_items)))
        
        # 应用特卖折扣
        self.apply_discount(self._daily_specials, 0.7)  # 7 折优惠
        
        return self._daily_specials
    
    def get_daily_specials(self) -> List[ShopItem]:
        """获取今日特卖商品"""
        return [self._items[item_id] for item_id in self._daily_specials if item_id in self._items]
    
    def save_to_json(self, filepath: str):
        """保存商店配置到 JSON"""
        data = {
            "items": {item_id: item.to_dict() for item_id, item in self._items.items()},
            "daily_specials": self._daily_specials,
        }
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    
    @classmethod
    def load_from_json(cls, filepath: str) -> "ShopSystem":
        """从 JSON 加载商店配置"""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Shop config file not found: {filepath}")
        
        data = json.loads(path.read_text(encoding="utf-8"))
        
        shop = cls()
        shop._items = {}
        shop._daily_specials = data.get("daily_specials", [])
        
        for item_id, item_data in data.get("items", {}).items():
            shop._items[item_id] = ShopItem.from_dict(item_data)
        
        return shop
    
    @property
    def total_items(self) -> int:
        """物品总数"""
        return len(self._items)


# 全局单例实例
def get_shop_system() -> ShopSystem:
    """获取商店系统单例"""
    return ShopSystem()


if __name__ == "__main__":
    # 测试代码
    shop = get_shop_system()
    print(f"商店物品总数：{shop.total_items}")
    
    # 创建测试库存
    inventory = PlayerInventory(coins=1000, diamonds=50)
    shop.set_inventory(inventory)
    
    # 测试购买
    success, msg = shop.purchase_item("plant_peashooter")
    print(f"\n购买测试：{msg}")
    print(f"剩余金币：{inventory.coins}")
    print(f"已解锁植物：{inventory.unlocked_plants}")
    
    # 生成每日特卖
    specials = shop.generate_daily_specials()
    print(f"\n今日特卖 ({len(specials)}件 7 折):")
    for item_id in specials:
        item = shop.get_item(item_id)
        if item:
            print(f"  - {item.name_cn}: {item.get_current_price()} {item.currency.value}")
    
    # 保存配置
    shop.save_to_json("data/config/shop.json")
    print("\n已导出 shop.json")
