"""
关卡管理器模块 - 工业级关卡系统设计
负责管理游戏关卡数据、关卡进度、难度曲线和关卡配置
"""

import json
import random
from typing import Dict, List, Optional, Tuple
from data.src._BasicImports import *


class LevelConfig:
    """关卡配置类 - 封装单个关卡的所有配置信息"""
    
    def __init__(self, level_data: dict):
        """
        初始化关卡配置
        
        :param level_data: 关卡数据字典
        """
        self.level_id = level_data.get('level_id', 1)
        self.level_name = level_data.get('level_name', f'关卡 {self.level_id}')
        self.scene_type = level_data.get('scene_type', 'day')  # day/night/pool/roof
        self.difficulty = level_data.get('difficulty', 1)  # 1-5 难度等级
        
        # 植物配置
        self.available_plants = level_data.get('available_plants', [])
        self.initial_sun = level_data.get('initial_sun', 150)
        self.initial_gold = level_data.get('initial_gold', 200)
        
        # 僵尸波次配置
        self.waves = level_data.get('waves', [])
        self.zombie_spawn_rate = level_data.get('zombie_spawn_rate', 600)
        self.max_zombies_on_screen = level_data.get('max_zombies_on_screen', 6)
        
        # 胜利条件
        self.victory_condition = level_data.get('victory_condition', 'survive')
        self.survive_time = level_data.get('survive_time', 180)  # 秒
        self.kill_zombie_count = level_data.get('kill_zombie_count', 0)
        
        # 特殊事件
        self.special_events = level_data.get('special_events', [])
        
        # 掉落奖励
        self.rewards = level_data.get('rewards', [])


class LevelManager:
    """关卡管理器 - 单例模式管理所有关卡"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if LevelManager._initialized:
            return
        LevelManager._initialized = True
        
        self.current_level = 1
        self.max_unlocked_level = 1
        self.completed_levels = set()
        self.level_configs: Dict[int, LevelConfig] = {}
        
        # 加载默认关卡配置
        self._load_default_levels()
    
    def _load_default_levels(self):
        """加载默认关卡配置 - 包含 50 个关卡的完整设计"""
        default_levels = self._generate_default_level_data()
        for level_data in default_levels:
            config = LevelConfig(level_data)
            self.level_configs[config.level_id] = config
    
    def _generate_default_level_data(self) -> List[dict]:
        """生成默认关卡数据 - 50 个关卡的完整配置"""
        levels = []
        
        # 第 1 关 - 教学关卡
        levels.append({
            'level_id': 1,
            'level_name': '教程关卡',
            'scene_type': 'day',
            'difficulty': 1,
            'available_plants': ['sunflower', 'peashooter'],
            'initial_sun': 200,
            'initial_gold': 200,
            'waves': [
                {'time': 30, 'zombies': [('common_zombie', 2)]},
                {'time': 60, 'zombies': [('common_zombie', 3)]},
                {'time': 90, 'zombies': [('common_zombie', 4)]},
            ],
            'zombie_spawn_rate': 800,
            'max_zombies_on_screen': 3,
            'victory_condition': 'survive',
            'survive_time': 120,
            'special_events': [],
            'rewards': ['unlock_new_plant:walnut']
        })
        
        # 第 2-10 关 - 白天基础关卡
        for i in range(2, 11):
            difficulty = min((i - 1) // 2 + 1, 3)
            zombie_types = ['common_zombie']
            if i >= 3:
                zombie_types.append('conehead_zombie')
            if i >= 5:
                zombie_types.append('buckethead_zombie')
            
            waves = []
            wave_count = 3 + i // 2
            for j in range(wave_count):
                zombie_count = 2 + j + i // 3
                zombie_composition = []
                for zt in zombie_types:
                    count = max(1, zombie_count // len(zombie_types))
                    zombie_composition.append((zt, count))
                waves.append({'time': 40 * (j + 1), 'zombies': zombie_composition})
            
            levels.append({
                'level_id': i,
                'level_name': f'白天关卡 {i-1}',
                'scene_type': 'day',
                'difficulty': difficulty,
                'available_plants': self._get_available_plants_for_level(i),
                'initial_sun': 150,
                'initial_gold': 200,
                'waves': waves,
                'zombie_spawn_rate': max(400, 800 - i * 50),
                'max_zombies_on_screen': min(6, 3 + i // 3),
                'victory_condition': 'survive',
                'survive_time': 120 + i * 10,
                'special_events': [],
                'rewards': self._get_level_rewards(i)
            })
        
        # 第 11-20 关 - 夜晚关卡
        for i in range(11, 21):
            difficulty = min((i - 1) // 2 + 1, 4)
            zombie_types = ['common_zombie', 'conehead_zombie']
            if i >= 13:
                zombie_types.append('buckethead_zombie')
            
            waves = []
            wave_count = 4 + i // 3
            for j in range(wave_count):
                zombie_count = 3 + j + i // 4
                zombie_composition = []
                for zt in zombie_types:
                    count = max(1, zombie_count // len(zombie_types))
                    zombie_composition.append((zt, count))
                waves.append({'time': 35 * (j + 1), 'zombies': zombie_composition})
            
            levels.append({
                'level_id': i,
                'level_name': f'夜晚关卡 {i-10}',
                'scene_type': 'night',
                'difficulty': difficulty,
                'available_plants': self._get_available_plants_for_level(i),
                'initial_sun': 100,  # 夜晚初始阳光较少
                'initial_gold': 200,
                'waves': waves,
                'zombie_spawn_rate': max(300, 700 - i * 40),
                'max_zombies_on_screen': min(8, 4 + i // 4),
                'victory_condition': 'survive',
                'survive_time': 150 + i * 8,
                'special_events': ['falling_sun_rare'],  # 夜晚阳光稀有
                'rewards': self._get_level_rewards(i)
            })
        
        # 第 21-35 关 - 泳池关卡
        for i in range(21, 36):
            difficulty = min((i - 15) // 2 + 2, 5)
            zombie_types = ['common_zombie', 'conehead_zombie', 'buckethead_zombie']
            
            waves = []
            wave_count = 5 + i // 4
            for j in range(wave_count):
                zombie_count = 4 + j + i // 5
                zombie_composition = []
                for zt in zombie_types:
                    count = max(1, zombie_count // len(zombie_types))
                    zombie_composition.append((zt, count))
                waves.append({'time': 30 * (j + 1), 'zombies': zombie_composition})
            
            levels.append({
                'level_id': i,
                'level_name': f'泳池关卡 {i-20}',
                'scene_type': 'pool',
                'difficulty': difficulty,
                'available_plants': self._get_available_plants_for_level(i),
                'initial_sun': 150,
                'initial_gold': 250,
                'waves': waves,
                'zombie_spawn_rate': max(250, 600 - i * 30),
                'max_zombies_on_screen': min(10, 5 + i // 5),
                'victory_condition': 'survive',
                'survive_time': 180 + i * 6,
                'special_events': ['diver_zombie'],  # 潜水僵尸事件
                'rewards': self._get_level_rewards(i)
            })
        
        # 第 36-50 关 - 屋顶关卡
        for i in range(36, 51):
            difficulty = min((i - 30) // 2 + 3, 5)
            zombie_types = ['common_zombie', 'conehead_zombie', 'buckethead_zombie']
            
            waves = []
            wave_count = 6 + i // 5
            for j in range(wave_count):
                zombie_count = 5 + j + i // 6
                zombie_composition = []
                for zt in zombie_types:
                    count = max(1, zombie_count // len(zombie_types))
                    zombie_composition.append((zt, count))
                waves.append({'time': 25 * (j + 1), 'zombies': zombie_composition})
            
            levels.append({
                'level_id': i,
                'level_name': f'屋顶关卡 {i-35}',
                'scene_type': 'roof',
                'difficulty': difficulty,
                'available_plants': self._get_available_plants_for_level(i),
                'initial_sun': 200,
                'initial_gold': 300,
                'waves': waves,
                'zombie_spawn_rate': max(200, 500 - i * 20),
                'max_zombies_on_screen': min(12, 6 + i // 6),
                'victory_condition': 'survive',
                'survive_time': 200 + i * 5,
                'special_events': ['bungee_zombie'],  # 飞贼僵尸事件
                'rewards': self._get_level_rewards(i)
            })
        
        return levels
    
    def _get_available_plants_for_level(self, level_id: int) -> List[str]:
        """根据关卡 ID 获取可用植物列表"""
        base_plants = ['sunflower', 'peashooter']
        
        unlock_schedule = {
            1: ['sunflower', 'peashooter'],
            2: ['sunflower', 'peashooter', 'nut'],
            3: ['sunflower', 'peashooter', 'nut', 'snowPeashooter'],
            4: ['sunflower', 'peashooter', 'nut', 'snowPeashooter', 'potato_mine'],
            5: ['sunflower', 'peashooter', 'nut', 'snowPeashooter', 'potato_mine', 'chomper'],
            7: ['sunflower', 'peashooter', 'nut', 'snowPeashooter', 'potato_mine', 'chomper', 'cherry_bomb'],
            9: ['sunflower', 'peashooter', 'nut', 'snowPeashooter', 'potato_mine', 'chomper', 'cherry_bomb', 'jalapeno'],
            11: ['sunflower', 'peashooter', 'nut', 'snowPeashooter', 'potato_mine', 'chomper', 'cherry_bomb', 'jalapeno', 'squash'],
            15: ['sunflower', 'peashooter', 'nut', 'snowPeashooter', 'potato_mine', 'chomper', 'cherry_bomb', 'jalapeno', 'squash', 'spikeweed'],
        }
        
        unlocked = base_plants[:]
        for threshold, plants in unlock_schedule.items():
            if level_id >= threshold:
                unlocked = plants[:]
        
        return unlocked
    
    def _get_level_rewards(self, level_id: int) -> List[str]:
        """获取关卡奖励"""
        rewards = []
        
        # 每 5 关解锁新植物
        if level_id % 5 == 0 and level_id <= 25:
            plant_map = {
                5: 'unlock_new_plant:walnut',
                10: 'unlock_new_plant:torchwood',
                15: 'unlock_new_plant:tall_nut',
                20: 'unlock_new_plant:starfruit',
                25: 'unlock_new_plant:pumpkin',
            }
            if level_id in plant_map:
                rewards.append(plant_map[level_id])
        
        # 每 10 关给予金币奖励
        if level_id % 10 == 0:
            rewards.append(f'gold_reward:{100 * level_id}')
        
        return rewards
    
    def get_level_config(self, level_id: int) -> Optional[LevelConfig]:
        """获取指定关卡的配置"""
        return self.level_configs.get(level_id)
    
    def get_current_level_config(self) -> Optional[LevelConfig]:
        """获取当前关卡配置"""
        return self.get_level_config(self.current_level)
    
    def complete_level(self, level_id: int):
        """标记关卡为已完成"""
        self.completed_levels.add(level_id)
        if level_id == self.current_level:
            self.max_unlocked_level = max(self.max_unlocked_level, level_id + 1)
            self.current_level = level_id + 1
    
    def is_level_unlocked(self, level_id: int) -> bool:
        """检查关卡是否已解锁"""
        return level_id <= self.max_unlocked_level
    
    def is_level_completed(self, level_id: int) -> bool:
        """检查关卡是否已完成"""
        return level_id in self.completed_levels
    
    def get_progress(self) -> dict:
        """获取游戏进度信息"""
        return {
            'current_level': self.current_level,
            'max_unlocked_level': self.max_unlocked_level,
            'completed_levels': list(self.completed_levels),
            'total_levels': len(self.level_configs)
        }
    
    def save_progress(self, filepath: str = './data/user/progress.json'):
        """保存游戏进度到文件"""
        progress_data = self.get_progress()
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存进度失败：{e}")
    
    def load_progress(self, filepath: str = './data/user/progress.json'):
        """从文件加载游戏进度"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            self.current_level = progress_data.get('current_level', 1)
            self.max_unlocked_level = progress_data.get('max_unlocked_level', 1)
            self.completed_levels = set(progress_data.get('completed_levels', []))
        except FileNotFoundError:
            pass  # 首次运行，使用默认进度
        except Exception as e:
            print(f"加载进度失败：{e}")


# 全局关卡管理器实例
level_manager = LevelManager()
