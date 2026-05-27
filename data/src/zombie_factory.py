'''
僵尸工厂系统 - 负责僵尸的波次生成、类型选择和 spawn 管理
工业级标准：类型注解、文档字符串、错误处理、配置驱动
'''

from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from data.src.const import *
from data.src.settings import settings
import random

if TYPE_CHECKING:
    from data.src.zombie import Zombie


class WaveConfig:
    """僵尸波次配置数据类"""
    
    def __init__(
        self,
        wave_number: int,
        zombie_count: int,
        zombie_types: Dict[str, float],  # zombie_type -> probability
        spawn_interval: Tuple[float, float],  # (min, max) seconds between spawns
        special_zombies: Optional[List[str]] = None
    ):
        self.wave_number = wave_number
        self.zombie_count = zombie_count
        self.zombie_types = zombie_types
        self.spawn_interval = spawn_interval
        self.special_zombies = special_zombies or []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'wave_number': self.wave_number,
            'zombie_count': self.zombie_count,
            'zombie_types': self.zombie_types,
            'spawn_interval': self.spawn_interval,
            'special_zombies': self.special_zombies
        }


class ZombieFactory:
    """
    僵尸工厂 - 单例模式
    负责根据关卡配置生成僵尸波次，管理僵尸的生成时机和类型
    """
    
    _instance: Optional['ZombieFactory'] = None
    
    def __new__(cls) -> 'ZombieFactory':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # 当前波次状态
        self._current_wave: int = 0
        self._total_waves: int = 0
        self._zombies_spawned_in_wave: int = 0
        self._zombies_to_spawn: int = 0
        self._spawn_timer: float = 0.0
        self._is_wave_active: bool = False
        self._wave_delay_timer: float = 0.0
        self._between_waves: bool = False
        
        # 僵尸生成队列
        self._spawn_queue: List[str] = []
        
        # 已生成的僵尸总数统计
        self._total_zombies_spawned: int = 0
        
        # 难度系数 (影响僵尸数量和强度)
        self._difficulty_multiplier: float = 1.0
    
    def initialize_wave(
        self, 
        total_waves: int,
        zombie_types: Dict[str, float],
        difficulty: int = 1
    ) -> None:
        """
        初始化一波僵尸生成
        
        :param total_waves: 总波次数
        :param zombie_types: 僵尸类型及概率配置
        :param difficulty: 难度等级 (1-10)
        """
        if total_waves < 1:
            raise ValueError("Total waves must be at least 1")
        
        self._total_waves = total_waves
        self._difficulty_multiplier = 1.0 + (difficulty - 1) * 0.15
        
        # 如果是新关卡的第一波
        if self._current_wave == 0:
            self._current_wave = 1
        else:
            self._current_wave += 1
        
        self._start_new_wave(zombie_types)
    
    def _start_new_wave(self, zombie_types: Dict[str, float]) -> None:
        """开始新的波次"""
        # 计算本波僵尸数量 (基础数量 + 难度加成)
        base_count = 5 + self._current_wave * 2
        self._zombies_to_spawn = int(base_count * self._difficulty_multiplier)
        self._zombies_spawned_in_wave = 0
        
        # 生成僵尸类型队列
        self._spawn_queue = self._generate_spawn_queue(
            self._zombies_to_spawn, 
            zombie_types
        )
        
        self._is_wave_active = True
        self._between_waves = False
        self._spawn_timer = 0.0
        
        print(f"Wave {self._current_wave}/{self._total_waves} started! "
              f"Spawning {self._zombies_to_spawn} zombies.")
    
    def _generate_spawn_queue(
        self, 
        count: int, 
        zombie_types: Dict[str, float]
    ) -> List[str]:
        """
        生成僵尸生成队列
        
        :param count: 需要生成的僵尸数量
        :param zombie_types: 僵尸类型及概率
        :return: 僵尸类型列表
        """
        queue = []
        
        # 归一化概率
        total_probability = sum(zombie_types.values())
        normalized_types = {
            ztype: prob / total_probability 
            for ztype, prob in zombie_types.items()
        }
        
        # 根据概率生成僵尸类型
        for _ in range(count):
            rand_value = random.random()
            cumulative_prob = 0.0
            
            selected_type = 'common_zombie'  # 默认
            
            for ztype, prob in normalized_types.items():
                cumulative_prob += prob
                if rand_value <= cumulative_prob:
                    selected_type = ztype
                    break
            
            queue.append(selected_type)
        
        # 在波次的特定位置插入特殊僵尸
        if self._current_wave % 5 == 0 and len(queue) > 10:
            # 每 5 波在中间和末尾插入特殊僵尸
            special_positions = [len(queue) // 2, len(queue) - 1]
            for pos in special_positions:
                if pos < len(queue):
                    queue[pos] = self._select_special_zombie(zombie_types)
        
        return queue
    
    def _select_special_zombie(self, zombie_types: Dict[str, float]) -> str:
        """选择特殊僵尸类型"""
        special_candidates = [
            ztype for ztype in zombie_types.keys()
            if ztype not in ['common_zombie']
        ]
        
        if special_candidates:
            return random.choice(special_candidates)
        return 'common_zombie'
    
    def update(self, delta_time: float) -> Optional[str]:
        """
        更新僵尸生成状态
        
        :param delta_time: 距离上一帧的时间 (秒)
        :return: 如果有僵尸需要生成，返回僵尸类型；否则返回 None
        """
        if not self._is_wave_active:
            return None
        
        # 波次间延迟
        if self._between_waves:
            self._wave_delay_timer -= delta_time
            if self._wave_delay_timer <= 0:
                self._between_waves = False
                self._wave_delay_timer = 0.0
            return None
        
        # 更新生成计时器
        self._spawn_timer += delta_time
        
        # 检查是否需要生成下一个僵尸
        spawn_interval = self._get_spawn_interval()
        
        if self._spawn_timer >= spawn_interval:
            self._spawn_timer = 0.0
            
            if self._spawn_queue:
                zombie_type = self._spawn_queue.pop(0)
                self._zombies_spawned_in_wave += 1
                self._total_zombies_spawned += 1
                
                # 检查波次是否完成
                if self._zombies_spawned_in_wave >= self._zombies_to_spawn:
                    self._complete_wave()
                
                return zombie_type
        
        return None
    
    def _get_spawn_interval(self) -> float:
        """
        获取当前 spawn 间隔
        
        :return: spawn 间隔 (秒)
        """
        # 基础间隔随波次减少 (越往后越快)
        base_min = max(0.5, 3.0 - self._current_wave * 0.2)
        base_max = max(1.0, 5.0 - self._current_wave * 0.3)
        
        # 难度影响 (难度越高间隔越短)
        difficulty_factor = 1.0 - (self._difficulty_multiplier - 1.0) * 0.3
        
        min_interval = base_min * difficulty_factor
        max_interval = base_max * difficulty_factor
        
        return random.uniform(min_interval, max_interval)
    
    def _complete_wave(self) -> None:
        """完成当前波次"""
        self._is_wave_active = False
        self._between_waves = True
        
        if self._current_wave >= self._total_waves:
            # 所有波次完成
            self._wave_delay_timer = 0.0
            print(f"All {self._total_waves} waves completed!")
        else:
            # 波次间延迟 (3-5 秒)
            self._wave_delay_timer = random.uniform(3.0, 5.0)
            print(f"Wave {self._current_wave} complete. "
                  f"Next wave in {self._wave_delay_timer:.1f}s")
    
    def force_spawn(self, zombie_type: str) -> None:
        """
        强制立即生成指定类型的僵尸
        
        :param zombie_type: 僵尸类型
        """
        self._spawn_queue.insert(0, zombie_type)
    
    def get_current_wave(self) -> int:
        """获取当前波次编号"""
        return self._current_wave
    
    def get_total_waves(self) -> int:
        """获取总波次数"""
        return self._total_waves
    
    def is_wave_active(self) -> bool:
        """检查是否有活跃的波次"""
        return self._is_wave_active
    
    def are_all_waves_complete(self) -> bool:
        """检查所有波次是否完成"""
        return (
            not self._is_wave_active and 
            self._current_wave >= self._total_waves
        )
    
    def get_remaining_zombies(self) -> int:
        """获取剩余待生成的僵尸数量"""
        return len(self._spawn_queue)
    
    def get_total_spawned(self) -> int:
        """获取已生成的僵尸总数"""
        return self._total_zombies_spawned
    
    def reset(self) -> None:
        """重置工厂状态"""
        self._current_wave = 0
        self._total_waves = 0
        self._zombies_spawned_in_wave = 0
        self._zombies_to_spawn = 0
        self._spawn_timer = 0.0
        self._is_wave_active = False
        self._wave_delay_timer = 0.0
        self._between_waves = False
        self._spawn_queue = []
        self._total_zombies_spawned = 0
        self._difficulty_multiplier = 1.0
    
    def set_difficulty(self, difficulty: int) -> None:
        """
        设置难度等级
        
        :param difficulty: 难度等级 (1-10)
        """
        if difficulty < 1 or difficulty > 10:
            raise ValueError("Difficulty must be between 1 and 10")
        self._difficulty_multiplier = 1.0 + (difficulty - 1) * 0.15


class ZombieSpawner:
    """
    僵尸生成器 - 与游戏场景集成
    负责在正确的位置生成僵尸实例
    """
    
    def __init__(self, zombie_factory: ZombieFactory):
        self._factory = zombie_factory
        self._spawn_positions: List[Tuple[int, int]] = []
        self._current_row: int = 1
    
    def configure_spawn_rows(self, rows: List[int]) -> None:
        """
        配置可生成的行
        
        :param rows: 行号列表 (1-5)
        """
        self._spawn_positions = [(GRID_RIGHT_X + 50, row) for row in rows]
        self._current_row = 1
    
    def get_next_spawn_position(self) -> Tuple[int, int]:
        """
        获取下一个生成位置
        
        :return: (x, y) 坐标
        """
        if not self._spawn_positions:
            # 默认所有行
            rows = list(range(1, 6))
            row = random.choice(rows)
            return (GRID_RIGHT_X + 50, row)
        
        # 循环选择行
        pos = self._spawn_positions[self._current_row - 1]
        self._current_row = (self._current_row % len(self._spawn_positions)) + 1
        
        return pos
    
    def spawn_zombie(
        self, 
        zombie_type: str, 
        game_object: Any
    ) -> Optional['Zombie']:
        """
        生成僵尸实例
        
        :param zombie_type: 僵尸类型
        :param game_object: 游戏主对象
        :return: 生成的僵尸对象，如果失败返回 None
        """
        from data.src.zombie import Zombie
        
        try:
            position = self.get_next_spawn_position()
            zombie = Zombie(game_object, zombie_type)
            # 设置位置 (需要根据实际 Zombie 类调整)
            zombie.pos = (position[0], GRID_Y[position[1]])
            zombie.posY = position[1]
            
            return zombie
            
        except Exception as e:
            print(f"Error spawning zombie: {e}")
            return None
    
    def update_and_spawn(
        self, 
        delta_time: float, 
        game_object: Any
    ) -> List['Zombie']:
        """
        更新并生成所有需要的僵尸
        
        :param delta_time: 时间增量
        :param game_object: 游戏主对象
        :return: 新生成的僵尸列表
        """
        spawned_zombies = []
        
        zombie_type = self._factory.update(delta_time)
        
        while zombie_type is not None:
            zombie = self.spawn_zombie(zombie_type, game_object)
            if zombie:
                spawned_zombies.append(zombie)
            zombie_type = self._factory.update(0)  # 继续检查队列
        
        return spawned_zombies


# 全局实例
_zombie_factory: Optional[ZombieFactory] = None
_zombie_spawner: Optional[ZombieSpawner] = None


def get_zombie_factory() -> ZombieFactory:
    """获取全局僵尸工厂实例"""
    global _zombie_factory
    if _zombie_factory is None:
        _zombie_factory = ZombieFactory()
    return _zombie_factory


def get_zombie_spawner() -> Optional[ZombieSpawner]:
    """获取全局僵尸生成器实例"""
    return _zombie_spawner


def initialize_zombie_system() -> Tuple[ZombieFactory, ZombieSpawner]:
    """初始化僵尸系统"""
    global _zombie_factory, _zombie_spawner
    _zombie_factory = ZombieFactory()
    _zombie_spawner = ZombieSpawner(_zombie_factory)
    return _zombie_factory, _zombie_spawner


def reset_zombie_system() -> None:
    """重置僵尸系统"""
    global _zombie_factory, _zombie_spawner
    if _zombie_factory:
        _zombie_factory.reset()
    if _zombie_spawner:
        _zombie_spawner.configure_spawn_rows([1, 2, 3, 4, 5])
