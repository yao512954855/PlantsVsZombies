'''
战斗系统 - 植物攻击、僵尸移动、碰撞检测的核心战斗逻辑
工业级标准：类型注解、文档字符串、错误处理、事件驱动架构
'''

from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from data.src.const import *
from data.src.settings import settings
from enum import Enum
import pygame
import math

if TYPE_CHECKING:
    from data.src.Game import Game
    from data.src.plant import Plant
    from data.src.zombie import Zombie


class AttackType(Enum):
    """攻击类型枚举"""
    PEA = 'pea'
    ICE_PEA = 'ice_pea'
    CHERRY_BOMB = 'cherry_bomb'
    JALAPENO = 'jalapeno'
    POTATO_MINE = 'potato_mine'
    CHOMPER_BITE = 'chomper_bite'
    SPIKEWEED_DAMAGE = 'spikeweed_damage'
    SQUASH_SMASH = 'squash_smash'


class CombatState:
    """战斗状态数据类"""
    
    def __init__(
        self,
        attacker_id: str,
        target_id: str,
        attack_type: AttackType,
        damage: float,
        timestamp: float,
        position: Tuple[int, int],
        extra_effects: Optional[Dict[str, Any]] = None
    ):
        self.attacker_id = attacker_id
        self.target_id = target_id
        self.attack_type = attack_type
        self.damage = damage
        self.timestamp = timestamp
        self.position = position
        self.extra_effects = extra_effects or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'attacker_id': self.attacker_id,
            'target_id': self.target_id,
            'attack_type': self.attack_type.value,
            'damage': self.damage,
            'timestamp': self.timestamp,
            'position': self.position,
            'extra_effects': self.extra_effects
        }


class CombatSystem:
    """
    战斗系统 - 单例模式
    负责管理所有植物的攻击行为、僵尸的移动和碰撞检测
    """
    
    _instance: Optional['CombatSystem'] = None
    
    def __new__(cls) -> 'CombatSystem':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.game: Optional['Game'] = None
        self.projectiles: List[Dict[str, Any]] = []  # 飞行物列表
        self.active_attacks: List[CombatState] = []  # 活跃攻击列表
        self.collision_cache: Dict[str, List[Tuple[int, int]]] = {}  # 碰撞缓存
        
        # 攻击配置
        self.attack_power_multipliers: Dict[str, float] = {
            'normal': 1.0,
            'ice_slow': 0.5,
            'explosion': 3.0,
            'instant_kill': 9999.0
        }
        
        # 僵尸速度配置
        self.zombie_base_speed: Dict[str, float] = {
            'common_zombie': 0.3,
            'cone_head_zombie': 0.3,
            'bucket_head_zombie': 0.25,
            'flag_zombie': 0.3,
            'pole_vaulting_zombie': 0.4,
            'dancing_zombie': 0.35
        }
        
        self._initialized = True
    
    def initialize(self, game: 'Game') -> None:
        """初始化战斗系统"""
        self.game = game
        self.projectiles = []
        self.active_attacks = []
        self.collision_cache = {}
    
    def spawn_projectile(
        self,
        plant: 'Plant',
        target_row: int,
        projectile_type: str = 'pea',
        damage_override: Optional[float] = None
    ) -> None:
        """
        生成飞行物（豌豆等）
        
        :param plant: 发射飞行物的植物
        :param target_row: 目标行号
        :param projectile_type: 飞行物类型 ('pea', 'ice_pea')
        :param damage_override: 覆盖默认伤害值
        """
        if not self.game:
            return
        
        # 获取飞行物基础配置
        base_damage = settings['game']['peaAttackPower']['common']['common_zombie']
        if projectile_type == 'ice_pea':
            base_damage = settings['game']['peaAttackPower']['ice']['common_zombie']
        
        damage = damage_override if damage_override else base_damage
        
        # 计算飞行物起始位置
        start_x = plant.pos[0] + plant.size[0]
        start_y = plant.pos[1] + plant.size[1] // 2
        
        projectile = {
            'id': f"{projectile_type}_{len(self.projectiles)}",
            'type': projectile_type,
            'position': [start_x, start_y],
            'target_row': target_row,
            'damage': damage,
            'speed': 8.0,  # 像素/帧
            'size': (20, 20),
            'plant_id': id(plant),
            'is_ice': projectile_type == 'ice_pea',
            'active': True
        }
        
        self.projectiles.append(projectile)
    
    def update_projectiles(self) -> List[Dict[str, Any]]:
        """
        更新所有飞行物位置和状态
        
        :return: 需要移除的飞行物列表
        """
        if not self.game:
            return []
        
        removed = []
        screen_width = SCREEN_SIZE[0]
        
        for projectile in self.projectiles:
            if not projectile['active']:
                continue
            
            # 更新位置
            projectile['position'][0] += projectile['speed']
            
            # 检查是否超出屏幕
            if projectile['position'][0] > screen_width:
                projectile['active'] = False
                removed.append(projectile)
                continue
            
            # 检测与僵尸的碰撞
            hit_zombie = self._check_projectile_zombie_collision(projectile)
            if hit_zombie:
                self._apply_projectile_damage(projectile, hit_zombie)
                projectile['active'] = False
                removed.append(projectile)
        
        # 移除不活跃的飞行物
        for proj in removed:
            if proj in self.projectiles:
                self.projectiles.remove(proj)
        
        return removed
    
    def _check_projectile_zombie_collision(
        self, 
        projectile: Dict[str, Any]
    ) -> Optional['Zombie']:
        """
        检测飞行物与僵尸的碰撞
        
        :param projectile: 飞行物数据
        :return: 被击中的僵尸对象，如果没有则返回 None
        """
        if not self.game:
            return None
        
        proj_x, proj_y = projectile['position']
        proj_w, proj_h = projectile['size']
        target_row = projectile['target_row']
        
        # 只检查同一行的僵尸
        zombies_in_row = [
            z for z in self.game.zombie_list 
            if abs(z.pos[1] - proj_y) < 50  # 粗略的行检测
        ]
        
        for zombie in zombies_in_row:
            z_x, z_y = zombie.pos
            z_w, z_h = zombie.size
            
            # AABB 碰撞检测
            if (proj_x < z_x + z_w and
                proj_x + proj_w > z_x and
                proj_y < z_y + z_h and
                proj_y + proj_h > z_y):
                return zombie
        
        return None
    
    def _apply_projectile_damage(
        self, 
        projectile: Dict[str, Any], 
        zombie: 'Zombie'
    ) -> CombatState:
        """
        应用飞行物伤害到僵尸
        
        :param projectile: 飞行物数据
        :param zombie: 被击中的僵尸
        :return: 战斗状态记录
        """
        damage = projectile['damage']
        is_ice = projectile['is_ice']
        
        # 根据僵尸类型调整伤害
        zombie_type = zombie.type
        if is_ice:
            damage *= settings['game']['peaAttackPower']['ice'].get(zombie_type, 1.0)
        else:
            damage *= settings['game']['peaAttackPower']['common'].get(zombie_type, 1.0)
        
        # 应用伤害
        zombie.hp -= damage
        
        # 冰冻效果
        if is_ice:
            zombie.apply_slow_effect(0.5, 60)  # 减速 50%，持续 60 帧
        
        # 创建战斗记录
        combat_state = CombatState(
            attacker_id=str(projectile['plant_id']),
            target_id=str(id(zombie)),
            attack_type=AttackType.ICE_PEA if is_ice else AttackType.PEA,
            damage=damage,
            timestamp=pygame.time.get_ticks() / 1000.0,
            position=tuple(projectile['position']),
            extra_effects={'slow': is_ice}
        )
        
        self.active_attacks.append(combat_state)
        
        # 检查僵尸是否死亡
        if zombie.hp <= 0:
            self._handle_zombie_death(zombie)
        
        return combat_state
    
    def _handle_zombie_death(self, zombie: 'Zombie') -> None:
        """
        处理僵尸死亡
        
        :param zombie: 死亡的僵尸
        """
        if not self.game:
            return
        
        # 播放死亡动画或音效
        # 移除僵尸头（如果血量低于阈值）
        if zombie.head and zombie.hp <= 40:
            zombie.head = False
            zombie.path = settings[zombie.type]['headlessPath']
            zombie.imageCount = settings[zombie.type]['headlessImageCount']
            
            # 生成僵尸头对象
            from data.src.ZombieHead import ZombieHead
            head_pos = (zombie.pos[0] + 30, zombie.pos[1])
            self.game.zombieHead_list.append(ZombieHead(self.game.screen, head_pos))
    
    def update_zombie_movement(self, delta_time: float = 1.0) -> None:
        """
        更新所有僵尸的移动
        
        :param delta_time: 时间增量（秒）
        """
        if not self.game:
            return
        
        for zombie in self.game.zombie_list:
            if zombie.eat:
                # 正在吃植物，不移动
                continue
            
            # 获取基础速度
            base_speed = self.zombie_base_speed.get(zombie.type, 0.3)
            
            # 应用减速效果
            speed_multiplier = zombie.get_speed_multiplier() if hasattr(zombie, 'get_speed_multiplier') else 1.0
            
            # 计算实际移动距离
            move_distance = base_speed * speed_multiplier * delta_time * 60  # 转换为帧单位
            
            # 向左移动
            zombie.pos[0] -= move_distance
            
            # 更新网格位置
            self._update_zombie_grid(zombie)
    
    def _update_zombie_grid(self, zombie: 'Zombie') -> None:
        """
        更新僵尸所在的网格位置
        
        :param zombie: 僵尸对象
        """
        if not zombie:
            return
        
        # 计算当前网格列
        grid_x = int((zombie.pos[0] - GRID_LEFT_X) / GRID_SIZE[0]) + 1
        grid_y = int((zombie.pos[1] - GRID_TOP_Y) / GRID_SIZE[1]) + 1
        
        # 限制在有效范围内
        grid_x = max(1, min(grid_x, GRID_COUNT[0]))
        grid_y = max(1, min(grid_y, GRID_COUNT[1]))
        
        zombie.grid = [grid_x, grid_y]
    
    def check_plant_zombie_collision(self) -> List[Tuple['Plant', 'Zombie']]:
        """
        检测植物与僵尸的碰撞
        
        :return: 碰撞的植物 - 僵尸对列表
        """
        if not self.game:
            return []
        
        collisions = []
        
        # 收集所有植物
        all_plants = []
        if hasattr(self.game, 'peashooter_list'):
            all_plants.extend(self.game.peashooter_list)
        if hasattr(self.game, 'sunflower_list'):
            all_plants.extend(self.game.sunflower_list)
        if hasattr(self.game, 'nut_list'):
            all_plants.extend(self.game.nut_list)
        if hasattr(self.game, 'chomper_list'):
            all_plants.extend(self.game.chomper_list)
        
        for plant in all_plants:
            for zombie in self.game.zombie_list:
                if self._check_aabb_collision(plant, zombie):
                    # 检查是否在同一行
                    if abs(plant.grid[1] - zombie.grid[1]) <= 1:
                        collisions.append((plant, zombie))
        
        return collisions
    
    def _check_aabb_collision(self, obj1: Any, obj2: Any) -> bool:
        """
        AABB 碰撞检测
        
        :param obj1: 物体 1（需有 pos 和 size 属性）
        :param obj2: 物体 2（需有 pos 和 size 属性）
        :return: 是否发生碰撞
        """
        x1, y1 = obj1.pos
        w1, h1 = obj1.size
        x2, y2 = obj2.pos
        w2, h2 = obj2.size
        
        return (x1 < x2 + w2 and x1 + w1 > x2 and
                y1 < y2 + h2 and y1 + h1 > y2)
    
    def handle_combat_frame(self) -> None:
        """
        处理单帧战斗逻辑
        包括：飞行物更新、僵尸移动、碰撞检测
        """
        if not self.game:
            return
        
        # 更新飞行物
        self.update_projectiles()
        
        # 更新僵尸移动
        self.update_zombie_movement()
        
        # 检测植物 - 僵尸碰撞
        collisions = self.check_plant_zombie_collision()
        for plant, zombie in collisions:
            self._handle_plant_zombie_interaction(plant, zombie)
        
        # 清理过期的战斗记录（保留最近 5 秒）
        current_time = pygame.time.get_ticks() / 1000.0
        self.active_attacks = [
            attack for attack in self.active_attacks
            if current_time - attack.timestamp < 5.0
        ]
    
    def _handle_plant_zombie_interaction(
        self, 
        plant: 'Plant', 
        zombie: 'Zombie'
    ) -> None:
        """
        处理植物与僵尸的交互（啃食）
        
        :param plant: 植物对象
        :param zombie: 僵尸对象
        """
        if not zombie.eat:
            zombie.eat = True
        
        # 增加植物被攻击计数
        if hasattr(plant, 'hpTime'):
            plant.hpTime += 1
        
        # 根据植物类型处理伤害
        plant_type = getattr(plant, 'name', 'unknown')
        hp_threshold = getattr(plant, 'HP_THRESHOLD', 100)
        
        if plant.hpTime >= hp_threshold:
            plant.hpTime = 0
            damage = settings[zombie.type]['attack_power']
            plant.hp -= damage
            
            # 处理植物死亡
            if plant.hp <= 0:
                self._handle_plant_death(plant, zombie)
    
    def _handle_plant_death(self, plant: 'Plant', zombie: 'Zombie') -> None:
        """
        处理植物死亡
        
        :param plant: 死亡的植物
        :param zombie: 导致植物死亡的僵尸
        """
        if not self.game:
            return
        
        # 从地图中移除
        if hasattr(self.game, 'map'):
            grid = plant.grid
            if 0 <= grid[1] < len(self.game.map) and 0 <= grid[0] < len(self.game.map[grid[1]]):
                self.game.map[grid[1]][grid[0]] = 0
        
        # 从对应列表中移除
        plant_lists = [
            'peashooter_list', 'sunflower_list', 'nut_list', 
            'chomper_list', 'snowPeashooter_list'
        ]
        
        for list_name in plant_lists:
            if hasattr(self.game, list_name):
                plant_list = getattr(self.game, list_name)
                if plant in plant_list:
                    plant_list.remove(plant)
                    break
        
        # 停止僵尸啃食
        zombie.eat = False
    
    def get_active_projectiles_count(self) -> int:
        """获取活跃飞行物数量"""
        return len([p for p in self.projectiles if p['active']])
    
    def get_combat_statistics(self) -> Dict[str, Any]:
        """获取战斗统计信息"""
        return {
            'active_projectiles': self.get_active_projectiles_count(),
            'total_zombies': len(self.game.zombie_list) if self.game else 0,
            'recent_attacks': len(self.active_attacks),
            'collision_cache_size': len(self.collision_cache)
        }


# 全局战斗系统实例
combat_system = CombatSystem()


def get_combat_system() -> CombatSystem:
    """获取全局战斗系统实例"""
    return combat_system
