"""
僵尸工厂模块 - 工业级僵尸生成系统
使用工厂模式和管理者模式实现僵尸的动态生成、类型管理和行为控制
"""

import random
from typing import Dict, List, Optional, Tuple, Type
from data.src._BasicImports import *


class ZombieTypeConfig:
    """僵尸类型配置类 - 封装僵尸类型的属性"""
    
    def __init__(self, zombie_type: str, config: dict):
        """
        初始化僵尸类型配置
        
        :param zombie_type: 僵尸类型名称
        :param config: 僵尸配置字典
        """
        self.zombie_type = zombie_type
        self.name = config.get('name', zombie_type)
        self.hp = config.get('hp', 100)
        self.speed = config.get('speed', 1.0)
        self.attack_power = config.get('attack_power', 20)
        self.size = config.get('size', (110, 110))
        self.path = config.get('path', '')
        self.imageCount = config.get('imageCount', 18)
        self.eatPath = config.get('eatPath', '')
        self.eatImageCount = config.get('eatImageCount', 21)
        self.headlessPath = config.get('headlessPath', '')
        self.headlessImageCount = config.get('headlessImageCount', 18)
        self.deadPath = config.get('deadPath', '')
        self.deadImageCount = config.get('deadImageCount', 10)
        
        # 特殊能力
        self.special_abilities = config.get('special_abilities', [])
        
        # 出现场景
        self.scenes = config.get('scenes', ['day', 'night', 'pool', 'roof'])
        
        # 权重（用于随机选择）
        self.weight = config.get('weight', 100)


class ZombieFactory:
    """僵尸工厂类 - 负责创建各种类型的僵尸实例"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if ZombieFactory._initialized:
            return
        ZombieFactory._initialized = True
        
        self.zombie_types: Dict[str, ZombieTypeConfig] = {}
        self.scene_zombie_map: Dict[str, List[str]] = {
            'day': [],
            'night': [],
            'pool': [],
            'roof': []
        }
        
        # 注册默认僵尸类型
        self._register_default_zombies()
    
    def _register_default_zombies(self):
        """注册默认僵尸类型配置"""
        from data.src.settings import settings
        
        # 从 settings 中加载已有僵尸配置
        default_zombies = ['common_zombie', 'conehead_zombie', 'buckethead_zombie']
        
        for zombie_type in default_zombies:
            if zombie_type in settings:
                config = settings[zombie_type]
                zombie_config = ZombieTypeConfig(zombie_type, config)
                self.register_zombie_type(zombie_config)
    
    def register_zombie_type(self, config: ZombieTypeConfig):
        """
        注册新的僵尸类型
        
        :param config: 僵尸类型配置
        """
        self.zombie_types[config.zombie_type] = config
        
        # 添加到对应场景列表
        for scene in config.scenes:
            if scene not in self.scene_zombie_map:
                self.scene_zombie_map[scene] = []
            if config.zombie_type not in self.scene_zombie_map[scene]:
                self.scene_zombie_map[scene].append(config.zombie_type)
    
    def create_zombie(self, zombie_type: str, game, row: int = None) -> Optional[object]:
        """
        创建指定类型的僵尸实例
        
        :param zombie_type: 僵尸类型名称
        :param game: 游戏主对象
        :param row: 僵尸出现的行（1-5），None 表示随机
        :return: 僵尸实例，如果类型不存在返回 None
        """
        if zombie_type not in self.zombie_types:
            print(f"警告：未知的僵尸类型 '{zombie_type}'")
            return None
        
        if row is None:
            row = random.randint(1, 5)
        
        # 动态导入 Zombie 类
        from data.src.zombie import Zombie
        
        # 创建僵尸实例
        zombie = Zombie(game, zombie_type, row)
        return zombie
    
    def create_random_zombie(self, game, scene: str = 'day', 
                             exclude_types: List[str] = None,
                             row: int = None) -> Optional[object]:
        """
        根据场景创建一个随机类型的僵尸
        
        :param game: 游戏主对象
        :param scene: 场景类型
        :param exclude_types: 排除的僵尸类型列表
        :param row: 僵尸出现的行，None 表示随机
        :return: 僵尸实例
        """
        available_types = self.scene_zombie_map.get(scene, [])
        
        if exclude_types:
            available_types = [t for t in available_types if t not in exclude_types]
        
        if not available_types:
            # 如果没有可用类型，回退到普通僵尸
            available_types = ['common_zombie']
        
        # 根据权重选择僵尸类型
        weights = []
        for zt in available_types:
            config = self.zombie_types.get(zt)
            weight = config.weight if config else 100
            weights.append(weight)
        
        chosen_type = random.choices(available_types, weights=weights, k=1)[0]
        return self.create_zombie(chosen_type, game, row)
    
    def create_zombie_wave(self, game, wave_config: List[Tuple[str, int]], 
                           scene: str = 'day') -> List[object]:
        """
        创建一波僵尸
        
        :param game: 游戏主对象
        :param wave_config: 波次配置 [(僵尸类型，数量), ...]
        :param scene: 场景类型
        :return: 僵尸列表
        """
        zombies = []
        for zombie_type, count in wave_config:
            for _ in range(count):
                zombie = self.create_random_zombie(game, scene, row=None)
                if zombie:
                    zombies.append(zombie)
        return zombies
    
    def get_available_types_for_scene(self, scene: str) -> List[str]:
        """获取指定场景可用的僵尸类型列表"""
        return self.scene_zombie_map.get(scene, [])
    
    def get_zombie_config(self, zombie_type: str) -> Optional[ZombieTypeConfig]:
        """获取僵尸类型配置"""
        return self.zombie_types.get(zombie_type)


class ZombieSpawner:
    """僵尸生成器 - 管理僵尸的定时生成和波次生成"""
    
    def __init__(self, game, level_config=None):
        """
        初始化僵尸生成器
        
        :param game: 游戏主对象
        :param level_config: 关卡配置
        """
        self.game = game
        self.level_config = level_config
        self.factory = ZombieFactory()
        
        # 生成计时器
        self.spawn_timer = 0
        self.default_spawn_rate = 600  # 默认生成间隔（帧）
        
        # 波次管理
        self.current_wave = 0
        self.wave_configs = []
        self.wave_timer = 0
        self.wave_active = False
        
        # 屏幕上最大僵尸数量
        self.max_zombies_on_screen = 6
        
        # 场景类型
        self.scene = 'day'
        if level_config:
            self.scene = level_config.scene_type
            self.wave_configs = level_config.waves
            self.default_spawn_rate = level_config.zombie_spawn_rate
            self.max_zombies_on_screen = level_config.max_zombies_on_screen
        
        # 已生成的僵尸总数
        self.total_spawned = 0
        
        # 特殊事件状态
        self.special_events_active = set()
    
    def update(self):
        """更新生成器状态 - 每帧调用"""
        if self.gameover or not self.game.really:
            return
        
        # 检查是否达到最大僵尸数量
        current_zombies = len(self.game.zombie_list)
        if current_zombies >= self.max_zombies_on_screen:
            return
        
        # 处理波次生成
        if self.wave_configs and self.current_wave < len(self.wave_configs):
            self._handle_wave_spawning()
        else:
            # 常规生成模式
            self._handle_regular_spawning()
    
    def _handle_wave_spawning(self):
        """处理波次生成逻辑"""
        wave_config = self.wave_configs[self.current_wave]
        wave_time = wave_config.get('time', 60) * 60  # 转换为帧数
        
        self.wave_timer += 1
        
        if self.wave_timer >= wave_time and not self.wave_active:
            self.wave_active = True
            # 生成该波次的僵尸
            zombies_config = wave_config.get('zombies', [])
            for zombie_type, count in zombies_config:
                for _ in range(count):
                    if len(self.game.zombie_list) < self.max_zombies_on_screen:
                        zombie = self.factory.create_random_zombie(self.game, self.scene)
                        if zombie:
                            self.game.zombie_list.append(zombie)
                            self.total_spawned += 1
            
            # 移动到下一波
            self.current_wave += 1
            self.wave_active = False
            self.wave_timer = 0
    
    def _handle_regular_spawning(self):
        """处理常规生成逻辑"""
        self.spawn_timer += 1
        
        if self.spawn_timer >= self.default_spawn_rate:
            self.spawn_timer = 0
            
            # 选择一个随机行
            available_rows = self._get_available_rows()
            if available_rows:
                row = random.choice(available_rows)
                zombie = self.factory.create_random_zombie(self.game, self.scene, row=row)
                if zombie:
                    self.game.zombie_list.append(zombie)
                    self.total_spawned += 1
    
    def _get_available_rows(self) -> List[int]:
        """获取可以生成僵尸的行"""
        available = []
        for row in range(1, 6):
            # 检查该行是否已经有僵尸在生成点附近
            has_nearby_zombie = False
            for zombie in self.game.zombie_list:
                if zombie.grid[1] == row and zombie.pos[0] > ZONBIE_FIRST_X - 100:
                    has_nearby_zombie = True
                    break
            
            if not has_nearby_zombie:
                available.append(row)
        
        return available if available else list(range(1, 6))
    
    def trigger_special_event(self, event_type: str):
        """触发特殊事件"""
        if event_type in self.special_events_active:
            return
        
        self.special_events_active.add(event_type)
        
        if event_type == 'diver_zombie':
            # 潜水僵尸事件 - 从泳池出现
            pass
        elif event_type == 'bungee_zombie':
            # 飞贼僵尸事件 - 从天而降
            pass
        elif event_type == 'zombie_rush':
            # 僵尸 Rush 事件 - 短时间内大量生成
            self.default_spawn_rate = max(100, self.default_spawn_rate // 3)
    
    def end_special_event(self, event_type: str):
        """结束特殊事件"""
        if event_type in self.special_events_active:
            self.special_events_active.remove(event_type)
            
            if event_type == 'zombie_rush':
                # 恢复正常的生成速率
                if self.level_config:
                    self.default_spawn_rate = self.level_config.zombie_spawn_rate
    
    def reset(self):
        """重置生成器状态"""
        self.spawn_timer = 0
        self.current_wave = 0
        self.wave_timer = 0
        self.wave_active = False
        self.total_spawned = 0
        self.special_events_active.clear()


# 全局工厂实例
zombie_factory = ZombieFactory()
