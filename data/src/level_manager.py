'''
关卡管理系统 - 负责管理50+关卡的配置、加载和进度追踪
工业级标准：类型注解、文档字符串、错误处理、配置驱动
'''

from typing import Dict, List, Optional, Tuple, Any
from data.src.const import *
from data.src.settings import settings
import json
import os


class LevelConfig:
    """关卡配置数据类"""
    
    def __init__(
        self,
        level_id: int,
        level_name: str,
        scene_type: str,
        difficulty: int,
        zombie_waves: int,
        initial_sun: int,
        available_plants: List[str],
        zombie_types: Dict[str, float],  # zombie_type -> spawn_probability
        special_conditions: Optional[Dict[str, Any]] = None
    ):
        self.level_id = level_id
        self.level_name = level_name
        self.scene_type = scene_type
        self.difficulty = difficulty
        self.zombie_waves = zombie_waves
        self.initial_sun = initial_sun
        self.available_plants = available_plants
        self.zombie_types = zombie_types
        self.special_conditions = special_conditions or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'level_id': self.level_id,
            'level_name': self.level_name,
            'scene_type': self.scene_type,
            'difficulty': self.difficulty,
            'zombie_waves': self.zombie_waves,
            'initial_sun': self.initial_sun,
            'available_plants': self.available_plants,
            'zombie_types': self.zombie_types,
            'special_conditions': self.special_conditions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LevelConfig':
        """从字典创建关卡配置"""
        return cls(
            level_id=data.get('level_id', 1),
            level_name=data.get('level_name', '未知关卡'),
            scene_type=data.get('scene_type', 'day'),
            difficulty=data.get('difficulty', 1),
            zombie_waves=data.get('zombie_waves', 5),
            initial_sun=data.get('initial_sun', 50),
            available_plants=data.get('available_plants', []),
            zombie_types=data.get('zombie_types', {}),
            special_conditions=data.get('special_conditions')
        )


class LevelManager:
    """
    关卡管理器 - 单例模式
    负责管理所有关卡的配置、加载、进度保存
    """
    
    _instance: Optional['LevelManager'] = None
    
    def __new__(cls) -> 'LevelManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._levels: Dict[int, LevelConfig] = {}
        self._current_level: int = 1
        self._completed_levels: List[int] = []
        self._save_file_path: str = "data/save/level_progress.json"
        
        self._initialize_default_levels()
        self._load_progress()
    
    def _initialize_default_levels(self) -> None:
        """初始化默认50+关卡配置"""
        # 场景类型映射
        scene_mapping = {
            1: 'day',           # 白天场景 (1-10关)
            2: 'night',         # 夜晚场景 (11-20关)
            3: 'roof',          # 屋顶场景 (21-30关)
            4: 'pool',          # 泳池场景 (31-40关)
            5: 'fog',           # 迷雾场景 (41-50关)
        }
        
        # 植物解锁进度
        plant_unlocks = {
            1: ['peashooter', 'sunflower', 'cherry_bomb', 'wall_nut'],
            5: ['potato_mine', 'snow_pea'],
            10: ['chomper', 'repeater'],
            15: ['puff_shroom', 'sun_shroom', 'fume_shroom'],
            20: ['grave_buster', 'hypno_shroom'],
            25: ['flower_pot', 'threepeater'],
            30: ['split_pea', 'starfruit'],
            35: ['lily_pad', 'tangle_kelp'],
            40: ['jalapeno', 'spikeweed'],
            45: ['torchwood', 'tall_nut'],
            50: ['sea_shroom', 'plantern'],
        }
        
        for level_id in range(1, 51):
            # 确定场景类型
            scene_group = (level_id - 1) // 10 + 1
            scene_type = scene_mapping.get(scene_group, 'day')
            
            # 计算难度 (1-10)
            difficulty = min(10, ((level_id - 1) % 10) + 1)
            
            # 僵尸波数随难度增加
            zombie_waves = 5 + difficulty * 2
            
            # 初始阳光
            initial_sun = 50 + (difficulty * 10)
            
            # 可用植物 (根据关卡进度解锁)
            available_plants = ['peashooter', 'sunflower', 'cherry_bomb', 'wall_nut']
            for unlock_level, plants in plant_unlocks.items():
                if level_id >= unlock_level:
                    available_plants.extend(plants)
            available_plants = list(set(available_plants))  # 去重
            
            # 僵尸类型及概率 (随难度变化)
            zombie_types = self._generate_zombie_types(level_id, difficulty, scene_type)
            
            # 特殊条件
            special_conditions = self._generate_special_conditions(level_id, scene_type)
            
            level_config = LevelConfig(
                level_id=level_id,
                level_name=f"关卡 {level_id}-{self._get_level_suffix(level_id)}",
                scene_type=scene_type,
                difficulty=difficulty,
                zombie_waves=zombie_waves,
                initial_sun=initial_sun,
                available_plants=available_plants,
                zombie_types=zombie_types,
                special_conditions=special_conditions
            )
            
            self._levels[level_id] = level_config
    
    def _get_level_suffix(self, level_id: int) -> str:
        """获取关卡后缀名称"""
        suffixes = [
            '初战', '试探', '进攻', '激斗', '苦战',
            '突围', '防守', '反击', '决战', '终章'
        ]
        index = (level_id - 1) % 10
        return suffixes[index]
    
    def _generate_zombie_types(
        self, 
        level_id: int, 
        difficulty: int,
        scene_type: str
    ) -> Dict[str, float]:
        """生成关卡的僵尸类型及概率配置"""
        zombie_types = {'common_zombie': 100.0}
        
        # 基础僵尸概率调整
        if difficulty >= 2:
            zombie_types['conehead_zombie'] = min(50.0, difficulty * 5)
        if difficulty >= 4:
            zombie_types['buckethead_zombie'] = min(30.0, difficulty * 3)
        if difficulty >= 6:
            zombie_types['pole_vaulting_zombie'] = min(20.0, difficulty * 2)
        if difficulty >= 8:
            zombie_types['screen_door_zombie'] = min(15.0, difficulty * 1.5)
        
        # 场景特定僵尸
        if scene_type == 'night':
            if difficulty >= 3:
                zombie_types['newspaper_zombie'] = min(25.0, difficulty * 3)
        
        elif scene_type == 'roof':
            if difficulty >= 3:
                zombie_types['ladder_zombie'] = min(25.0, difficulty * 3)
            if difficulty >= 5:
                zombie_types['catapult_zombie'] = min(15.0, difficulty * 2)
        
        elif scene_type == 'pool':
            if difficulty >= 3:
                zombie_types['snorkel_zombie'] = min(25.0, difficulty * 3)
            if difficulty >= 5:
                zombie_types['dolphin_rider_zombie'] = min(15.0, difficulty * 2)
        
        elif scene_type == 'fog':
            if difficulty >= 4:
                zombie_types['balloon_zombie'] = min(20.0, difficulty * 2)
            if difficulty >= 7:
                zombie_types['digger_zombie'] = min(15.0, difficulty * 1.5)
        
        return zombie_types
    
    def _generate_special_conditions(
        self, 
        level_id: int, 
        scene_type: str
    ) -> Dict[str, Any]:
        """生成关卡特殊条件"""
        conditions = {}
        
        # 每10关的特殊条件
        if level_id % 10 == 0:
            conditions['last_stand'] = True  # 坚壁清野模式
            conditions['initial_plants'] = ['wall_nut', 'wall_nut', 'wall_nut']
        
        # 夜晚关卡有墓碑
        if scene_type == 'night' and level_id % 5 == 0:
            conditions['has_graves'] = True
        
        # 迷雾关卡能见度降低
        if scene_type == 'fog':
            conditions['fog_density'] = min(0.9, 0.3 + (level_id // 10) * 0.1)
        
        # 屋顶关卡需要花盆
        if scene_type == 'roof':
            conditions['requires_flower_pot'] = True
        
        return conditions
    
    def get_level_config(self, level_id: int) -> Optional[LevelConfig]:
        """获取指定关卡的配置"""
        if level_id < 1 or level_id > 50:
            raise ValueError(f"Invalid level ID: {level_id}. Must be between 1 and 50.")
        return self._levels.get(level_id)
    
    def get_current_level_config(self) -> LevelConfig:
        """获取当前关卡配置"""
        config = self._levels.get(self._current_level)
        if config is None:
            raise ValueError(f"Current level {self._current_level} not found.")
        return config
    
    def set_current_level(self, level_id: int) -> None:
        """设置当前关卡"""
        if level_id < 1 or level_id > 50:
            raise ValueError(f"Invalid level ID: {level_id}. Must be between 1 and 50.")
        self._current_level = level_id
    
    def get_current_level_id(self) -> int:
        """获取当前关卡ID"""
        return self._current_level
    
    def mark_level_completed(self, level_id: int) -> None:
        """标记关卡为已完成"""
        if level_id not in self._completed_levels:
            self._completed_levels.append(level_id)
            self._save_progress()
    
    def is_level_completed(self, level_id: int) -> bool:
        """检查关卡是否已完成"""
        return level_id in self._completed_levels
    
    def get_completed_levels(self) -> List[int]:
        """获取已完成的关卡列表"""
        return self._completed_levels.copy()
    
    def get_next_level_id(self) -> int:
        """获取下一个可解锁的关卡ID"""
        if not self._completed_levels:
            return 1
        max_completed = max(self._completed_levels)
        return min(max_completed + 1, 50)
    
    def _save_progress(self) -> None:
        """保存关卡进度到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self._save_file_path), exist_ok=True)
            
            progress_data = {
                'current_level': self._current_level,
                'completed_levels': self._completed_levels
            }
            
            with open(self._save_file_path, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Warning: Failed to save level progress: {e}")
    
    def _load_progress(self) -> None:
        """从文件加载关卡进度"""
        try:
            if os.path.exists(self._save_file_path):
                with open(self._save_file_path, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                
                self._current_level = progress_data.get('current_level', 1)
                self._completed_levels = progress_data.get('completed_levels', [])
                
        except Exception as e:
            print(f"Warning: Failed to load level progress: {e}")
            self._current_level = 1
            self._completed_levels = []
    
    def reset_progress(self) -> None:
        """重置关卡进度"""
        self._current_level = 1
        self._completed_levels = []
        self._save_progress()
    
    def get_all_levels(self) -> Dict[int, LevelConfig]:
        """获取所有关卡配置"""
        return self._levels.copy()
    
    def get_levels_by_scene(self, scene_type: str) -> List[LevelConfig]:
        """获取指定场景类型的所有关卡"""
        return [
            level for level in self._levels.values()
            if level.scene_type == scene_type
        ]
    
    def get_levels_by_difficulty(self, min_diff: int, max_diff: int) -> List[LevelConfig]:
        """获取指定难度范围内的所有关卡"""
        return [
            level for level in self._levels.values()
            if min_diff <= level.difficulty <= max_diff
        ]


# 全局关卡管理器实例
level_manager: Optional[LevelManager] = None


def get_level_manager() -> LevelManager:
    """获取全局关卡管理器实例"""
    global level_manager
    if level_manager is None:
        level_manager = LevelManager()
    return level_manager


def initialize_level_manager() -> LevelManager:
    """初始化并返回关卡管理器"""
    global level_manager
    level_manager = LevelManager()
    return level_manager
