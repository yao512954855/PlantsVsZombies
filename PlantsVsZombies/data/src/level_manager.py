#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关卡管理系统
工业级重构版本 - 负责关卡配置、进度管理、难度曲线
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime


class SceneType(Enum):
    """场景类型枚举"""
    DAY = "day"          # 白天
    NIGHT = "night"      # 夜晚
    POOL = "pool"        # 泳池
    ROOF = "roof"        # 屋顶


class GameModeType(Enum):
    """游戏模式类型"""
    ADVENTURE = "adventure"           # 冒险模式
    MINI_GAMES = "mini_games"         # 迷你游戏
    PUZZLE = "puzzle"                 # 解谜模式
    SURVIVAL = "survival"             # 生存模式
    ZEN_GARDEN = "zen_garden"         # 禅境花园


@dataclass
class LevelConfig:
    """关卡配置数据类"""
    level_id: int
    scene_type: SceneType
    game_mode: GameModeType
    available_plants: List[str]
    zombie_types: List[str]
    initial_sun: int = 50
    total_waves: int = 3
    zombie_spawn_rate: float = 5.0  # 秒
    difficulty_multiplier: float = 1.0
    victory_condition: str = "survive"  # survive/kill_all
    rewards: Dict[str, int] = field(default_factory=lambda: {"gold": 100})
    unlock_plant: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'level_id': self.level_id,
            'scene_type': self.scene_type.value,
            'game_mode': self.game_mode.value,
            'available_plants': self.available_plants,
            'zombie_types': self.zombie_types,
            'initial_sun': self.initial_sun,
            'total_waves': self.total_waves,
            'zombie_spawn_rate': self.zombie_spawn_rate,
            'difficulty_multiplier': self.difficulty_multiplier,
            'victory_condition': self.victory_condition,
            'rewards': self.rewards,
            'unlock_plant': self.unlock_plant
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LevelConfig':
        """从字典创建"""
        return cls(
            level_id=data['level_id'],
            scene_type=SceneType(data['scene_type']),
            game_mode=GameModeType(data['game_mode']),
            available_plants=data['available_plants'],
            zombie_types=data['zombie_types'],
            initial_sun=data.get('initial_sun', 50),
            total_waves=data.get('total_waves', 3),
            zombie_spawn_rate=data.get('zombie_spawn_rate', 5.0),
            difficulty_multiplier=data.get('difficulty_multiplier', 1.0),
            victory_condition=data.get('victory_condition', 'survive'),
            rewards=data.get('rewards', {"gold": 100}),
            unlock_plant=data.get('unlock_plant')
        )


class LevelManager:
    """
    关卡管理器（单例模式）
    
    负责：
    - 加载和管理所有关卡配置
    - 跟踪玩家进度
    - 处理关卡完成逻辑
    - 保存/加载进度
    """
    
    _instance: Optional['LevelManager'] = None
    
    def __new__(cls, save_system=None) -> 'LevelManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, save_system=None):
        if self._initialized:
            return
        
        self.save_system = save_system
        self.levels: Dict[int, LevelConfig] = {}
        self.current_level_id: int = 1
        self.completed_levels: set = set()
        self.player_stars: Dict[int, int] = {}  # 关卡星级
        
        self._initialize_levels()
        self._initialized = True
    
    def _initialize_levels(self):
        """初始化所有关卡配置（50 个关卡）"""
        # 白天关卡 (1-10)
        for i in range(1, 11):
            self.levels[i] = LevelConfig(
                level_id=i,
                scene_type=SceneType.DAY,
                game_mode=GameModeType.ADVENTURE,
                available_plants=self._get_day_plants(i),
                zombie_types=self._get_day_zombies(i),
                initial_sun=50,
                total_waves=2 + (i // 3),
                zombie_spawn_rate=max(2.0, 6.0 - i * 0.3),
                difficulty_multiplier=1.0 + (i - 1) * 0.1,
                rewards={"gold": 100 + i * 20},
                unlock_plant=self._get_unlock_plant(i)
            )
        
        # 夜晚关卡 (11-20)
        for i in range(11, 21):
            self.levels[i] = LevelConfig(
                level_id=i,
                scene_type=SceneType.NIGHT,
                game_mode=GameModeType.ADVENTURE,
                available_plants=self._get_night_plants(i),
                zombie_types=self._get_night_zombies(i),
                initial_sun=50,
                total_waves=3 + (i - 10) // 3,
                zombie_spawn_rate=max(1.5, 5.0 - (i - 10) * 0.3),
                difficulty_multiplier=1.5 + (i - 10) * 0.15,
                rewards={"gold": 150 + (i - 10) * 25},
                unlock_plant=self._get_unlock_plant(i)
            )
        
        # 泳池关卡 (21-35)
        for i in range(21, 36):
            self.levels[i] = LevelConfig(
                level_id=i,
                scene_type=SceneType.POOL,
                game_mode=GameModeType.ADVENTURE,
                available_plants=self._get_pool_plants(i),
                zombie_types=self._get_pool_zombies(i),
                initial_sun=75,
                total_waves=4 + (i - 20) // 3,
                zombie_spawn_rate=max(1.2, 4.5 - (i - 20) * 0.25),
                difficulty_multiplier=2.0 + (i - 20) * 0.15,
                rewards={"gold": 200 + (i - 20) * 30},
                unlock_plant=self._get_unlock_plant(i)
            )
        
        # 屋顶关卡 (36-50)
        for i in range(36, 51):
            self.levels[i] = LevelConfig(
                level_id=i,
                scene_type=SceneType.ROOF,
                game_mode=GameModeType.ADVENTURE,
                available_plants=self._get_roof_plants(i),
                zombie_types=self._get_roof_zombies(i),
                initial_sun=75,
                total_waves=5 + (i - 35) // 2,
                zombie_spawn_rate=max(1.0, 4.0 - (i - 35) * 0.2),
                difficulty_multiplier=2.5 + (i - 35) * 0.15,
                rewards={"gold": 250 + (i - 35) * 35},
                unlock_plant=self._get_unlock_plant(i)
            )
    
    def _get_day_plants(self, level: int) -> List[str]:
        """获取白天关卡可用植物"""
        base_plants = ['sunflower', 'peashooter', 'wallnut', 'potatomine', 'cherrybomb']
        if level >= 2:
            base_plants.append('snowpea')
        if level >= 4:
            base_plants.append('chomper')
        if level >= 6:
            base_plants.append('squash')
        if level >= 8:
            base_plants.append('spikeweed')
        if level >= 10:
            base_plants.append('jalapeno')
        return base_plants
    
    def _get_day_zombies(self, level: int) -> List[str]:
        """获取白天关卡僵尸类型"""
        zombies = ['normal']
        if level >= 2:
            zombies.append('conehead')
        if level >= 4:
            zombies.append('buckethead')
        return zombies
    
    def _get_night_plants(self, level: int) -> List[str]:
        """获取夜晚关卡可用植物"""
        plants = self._get_day_plants(10).copy()
        plants.extend(['puffshroom', 'sunshroom', 'fumeShroom', 'gravestone'])
        return plants
    
    def _get_night_zombies(self, level: int) -> List[str]:
        """获取夜晚关卡僵尸类型"""
        zombies = self._get_day_zombies(10).copy()
        if level >= 13:
            zombies.append('screen_door')
        if level >= 16:
            zombies.append('football')
        return zombies
    
    def _get_pool_plants(self, level: int) -> List[str]:
        """获取泳池关卡可用植物"""
        plants = self._get_night_plants(20).copy()
        plants.extend(['lilypad', 'tallnut', 'kelp', 'cattail'])
        return plants
    
    def _get_pool_zombies(self, level: int) -> List[str]:
        """获取泳池关卡僵尸类型"""
        zombies = self._get_night_zombies(20).copy()
        if level >= 24:
            zombies.append('snorkel')
        if level >= 28:
            zombies.append('dolphin_rider')
        return zombies
    
    def _get_roof_plants(self, level: int) -> List[str]:
        """获取屋顶关卡可用植物"""
        plants = self._get_pool_plants(35).copy()
        plants.extend(['flowerpot', 'umbrella', 'marigold', 'melonpult'])
        return plants
    
    def _get_roof_zombies(self, level: int) -> List[str]:
        """获取屋顶关卡僵尸类型"""
        zombies = self._get_pool_zombies(35).copy()
        if level >= 40:
            zombies.append('bungee')
        if level >= 44:
            zombies.append('catapult')
        if level >= 48:
            zombies.append('gargantuar')
        return zombies
    
    def _get_unlock_plant(self, level: int) -> Optional[str]:
        """获取关卡解锁的植物"""
        unlock_map = {
            1: 'sunflower',
            3: 'peashooter',
            5: 'wallnut',
            7: 'potatomine',
            9: 'cherrybomb',
            12: 'puffshroom',
            15: 'sunshroom',
            18: 'fumeShroom',
            22: 'lilypad',
            26: 'tallnut',
            30: 'kelp',
            34: 'cattail',
            38: 'flowerpot',
            42: 'umbrella',
            46: 'marigold',
            50: 'melonpult'
        }
        return unlock_map.get(level)
    
    def get_level(self, level_id: int) -> Optional[LevelConfig]:
        """获取指定关卡配置"""
        return self.levels.get(level_id)
    
    def get_current_level(self) -> Optional[LevelConfig]:
        """获取当前关卡配置"""
        return self.get_level(self.current_level_id)
    
    def set_current_level(self, level_id: int) -> bool:
        """设置当前关卡"""
        if level_id in self.levels:
            self.current_level_id = level_id
            return True
        return False
    
    def complete_level(self) -> Dict[str, int]:
        """完成当前关卡"""
        level = self.get_current_level()
        if not level:
            return {"gold": 0}
        
        self.completed_levels.add(self.current_level_id)
        
        # 计算奖励
        rewards = level.rewards.copy()
        
        # 解锁新植物
        if level.unlock_plant:
            rewards['unlock_plant'] = level.unlock_plant
        
        # 保存到存档
        if self.save_system:
            self.save_system.save_game()
        
        return rewards
    
    def is_level_unlocked(self, level_id: int) -> bool:
        """检查关卡是否解锁"""
        if level_id == 1:
            return True
        return (level_id - 1) in self.completed_levels
    
    def get_progress(self) -> Dict[str, Any]:
        """获取进度信息"""
        return {
            'current_level': self.current_level_id,
            'completed_levels': list(self.completed_levels),
            'total_levels': len(self.levels),
            'completion_rate': len(self.completed_levels) / len(self.levels) * 100
        }
    
    def load_progress(self, progress_data: Dict[str, Any]):
        """加载进度"""
        self.current_level_id = progress_data.get('current_level', 1)
        self.completed_levels = set(progress_data.get('completed_levels', []))
    
    def export_config(self, filepath: str):
        """导出关卡配置到 JSON 文件"""
        config_data = {
            'levels': {str(k): v.to_dict() for k, v in self.levels.items()},
            'exported_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
    
    def import_config(self, filepath: str):
        """从 JSON 文件导入关卡配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        for level_id, level_dict in config_data.get('levels', {}).items():
            self.levels[int(level_id)] = LevelConfig.from_dict(level_dict)


__all__ = ['LevelManager', 'LevelConfig', 'SceneType', 'GameModeType']
