#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
僵尸工厂系统
工业级重构版本 - 负责僵尸生成、波次管理、AI 行为
"""

import random
import time
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field
from enum import Enum


class ZombieType(Enum):
    """僵尸类型枚举"""
    NORMAL = "normal"
    CONEHEAD = "conehead"
    BUCKETHEAD = "buckethead"
    SCREEN_DOOR = "screen_door"
    FOOTBALL = "football"
    DANCER = "dancer"
    SNORKEL = "snorkel"
    DOLPHIN_RIDER = "dolphin_rider"
    BUNGEE = "bungee"
    CATAPULT = "catapult"
    GARGANTUAR = "gargantuar"


@dataclass
class ZombieTypeConfig:
    """僵尸类型配置"""
    zombie_type: ZombieType
    health: int
    speed: float
    damage: int
    gold_reward: int
    special_abilities: List[str] = field(default_factory=list)
    spawn_weight: float = 1.0


class ZombieFactory:
    """
    僵尸工厂（工厂模式）
    
    负责根据配置创建不同类型的僵尸实例
    """
    
    def __init__(self):
        self.zombie_configs: Dict[ZombieType, ZombieTypeConfig] = {}
        self._initialize_configs()
    
    def _initialize_configs(self):
        """初始化僵尸类型配置"""
        self.zombie_configs = {
            ZombieType.NORMAL: ZombieTypeConfig(
                zombie_type=ZombieType.NORMAL,
                health=100,
                speed=0.05,
                damage=10,
                gold_reward=10,
                spawn_weight=1.0
            ),
            ZombieType.CONEHEAD: ZombieTypeConfig(
                zombie_type=ZombieType.CONEHEAD,
                health=200,
                speed=0.05,
                damage=10,
                gold_reward=20,
                spawn_weight=0.8
            ),
            ZombieType.BUCKETHEAD: ZombieTypeConfig(
                zombie_type=ZombieType.BUCKETHEAD,
                health=350,
                speed=0.04,
                damage=10,
                gold_reward=30,
                spawn_weight=0.6
            ),
            ZombieType.SCREEN_DOOR: ZombieTypeConfig(
                zombie_type=ZombieType.SCREEN_DOOR,
                health=300,
                speed=0.05,
                damage=10,
                gold_reward=25,
                special_abilities=['shield_front'],
                spawn_weight=0.7
            ),
            ZombieType.FOOTBALL: ZombieTypeConfig(
                zombie_type=ZombieType.FOOTBALL,
                health=400,
                speed=0.08,
                damage=15,
                gold_reward=35,
                spawn_weight=0.5
            ),
            ZombieType.DANCER: ZombieTypeConfig(
                zombie_type=ZombieType.DANCER,
                health=150,
                speed=0.06,
                damage=10,
                gold_reward=25,
                special_abilities=['summon_backup_dancers'],
                spawn_weight=0.4
            ),
            ZombieType.SNORKEL: ZombieTypeConfig(
                zombie_type=ZombieType.SNORKEL,
                health=150,
                speed=0.06,
                damage=10,
                gold_reward=20,
                special_abilities=['underwater_movement'],
                spawn_weight=0.6
            ),
            ZombieType.DOLPHIN_RIDER: ZombieTypeConfig(
                zombie_type=ZombieType.DOLPHIN_RIDER,
                health=200,
                speed=0.12,
                damage=10,
                gold_reward=30,
                special_abilities=['jump_over_plants'],
                spawn_weight=0.5
            ),
            ZombieType.BUNGEE: ZombieTypeConfig(
                zombie_type=ZombieType.BUNGEE,
                health=100,
                speed=0.0,
                damage=0,
                gold_reward=15,
                special_abilities=['steal_plants', 'aerial_drop'],
                spawn_weight=0.4
            ),
            ZombieType.CATAPULT: ZombieTypeConfig(
                zombie_type=ZombieType.CATAPULT,
                health=300,
                speed=0.03,
                damage=30,
                gold_reward=40,
                special_abilities=['ranged_attack', 'ice_ball'],
                spawn_weight=0.4
            ),
            ZombieType.GARGANTUAR: ZombieTypeConfig(
                zombie_type=ZombieType.GARGANTUAR,
                health=1200,
                speed=0.02,
                damage=50,
                gold_reward=100,
                special_abilities=['throw_imp', 'smash_plants'],
                spawn_weight=0.2
            )
        }
    
    def create_zombie(self, zombie_type: ZombieType, x: float, y: float, 
                      difficulty_multiplier: float = 1.0) -> Dict[str, Any]:
        """创建僵尸实例"""
        config = self.zombie_configs.get(zombie_type)
        if not config:
            raise ValueError(f"Unknown zombie type: {zombie_type}")
        
        return {
            'type': zombie_type,
            'x': x,
            'y': y,
            'health': int(config.health * difficulty_multiplier),
            'max_health': int(config.health * difficulty_multiplier),
            'speed': config.speed,
            'damage': config.damage,
            'gold_reward': config.gold_reward,
            'special_abilities': config.special_abilities.copy(),
            'state': 'walking',
            'frozen': False,
            'freeze_timer': 0.0,
            'animation_frame': 0
        }
    
    def get_config(self, zombie_type: ZombieType) -> Optional[ZombieTypeConfig]:
        """获取僵尸类型配置"""
        return self.zombie_configs.get(zombie_type)
    
    def get_available_types(self, difficulty: float = 1.0) -> List[ZombieType]:
        """根据难度获取可用的僵尸类型"""
        available = []
        for ztype, config in self.zombie_configs.items():
            if config.spawn_weight >= (1.0 - difficulty * 0.5):
                available.append(ztype)
        return available


class ZombieSpawner:
    """
    僵尸生成器
    
    负责：
    - 波次生成管理
    - 常规生成逻辑
    - 特殊事件触发
    """
    
    def __init__(self, factory: ZombieFactory):
        self.factory = factory
        self.current_wave = 0
        self.total_waves = 3
        self.zombies_per_wave = 5
        self.spawn_timer = 0.0
        self.spawn_interval = 5.0
        self.wave_started = False
        self.wave_complete = False
        self.special_event_active = False
    
    def start_wave(self, wave_number: int, zombies_count: int, 
                   spawn_interval: float = 5.0):
        """开始一波僵尸生成"""
        self.current_wave = wave_number
        self.zombies_per_wave = zombies_count
        self.spawn_interval = spawn_interval
        self.spawn_timer = 0.0
        self.wave_started = True
        self.wave_complete = False
    
    def update(self, delta_time: float, current_zombies: List[Dict]) -> List[Dict]:
        """更新生成器状态，返回新生成的僵尸"""
        if not self.wave_started or self.wave_complete:
            return []
        
        self.spawn_timer += delta_time
        
        # 检查是否可以生成新僵尸
        spawned_zombies = []
        if self.spawn_timer >= self.spawn_interval:
            if len(current_zombies) + len(spawned_zombies) < self.zombies_per_wave:
                zombie = self._spawn_zombie()
                if zombie:
                    spawned_zombies.append(zombie)
                self.spawn_timer = 0.0
        
        # 检查波次是否完成
        if len(current_zombies) == 0 and self.spawn_timer > self.spawn_interval * 2:
            self.wave_complete = True
            self.wave_started = False
        
        return spawned_zombies
    
    def _spawn_zombie(self) -> Optional[Dict[str, Any]]:
        """生成单个僵尸"""
        # 随机选择生成行（5 行）
        row = random.randint(0, 4)
        y_position = 100 + row * 100
        
        # 根据当前波次选择僵尸类型
        zombie_type = self._select_zombie_type()
        
        # 创建僵尸
        zombie = self.factory.create_zombie(
            zombie_type=zombie_type,
            x=1200,  # 从屏幕右侧生成
            y=y_position
        )
        
        return zombie
    
    def _select_zombie_type(self) -> ZombieType:
        """选择僵尸类型"""
        # 简单权重随机
        types = list(ZombieType)
        weights = [self.factory.zombie_configs[t].spawn_weight for t in types]
        return random.choices(types, weights=weights)[0]
    
    def is_wave_complete(self) -> bool:
        """检查当前波次是否完成"""
        return self.wave_complete and not self.wave_started
    
    def trigger_special_event(self, event_type: str) -> bool:
        """触发特殊事件"""
        if self.special_event_active:
            return False
        
        self.special_event_active = True
        # 特殊事件逻辑将在游戏主循环中处理
        return True


__all__ = ['ZombieFactory', 'ZombieSpawner', 'ZombieType', 'ZombieTypeConfig']
