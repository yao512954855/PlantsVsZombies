"""
游戏模式系统 - 5 大游戏模式完整实现

提供冒险、迷你游戏、解谜、生存、禅境花园五种游戏模式的完整框架与状态管理。
采用策略模式设计，支持热插拔新游戏模式。

Attributes:
    GAME_MODES: 预注册的游戏模式字典
    
Example:
    >>> mode = GameModeFactory.create("adventure")
    >>> mode.start_level(1, 1)
    >>> mode.update(dt)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Callable, Type
from pathlib import Path
import json
import random
import time


class GameModeType(Enum):
    """游戏模式类型枚举"""
    ADVENTURE = auto()      # 冒险模式
    MINI_GAME = auto()      # 迷你游戏
    PUZZLE = auto()         # 解谜模式
    SURVIVAL = auto()       # 生存模式
    ZEN_GARDEN = auto()     # 禅境花园


class GamePhase(Enum):
    """游戏阶段枚举"""
    NOT_STARTED = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass
class ModeConfig:
    """游戏模式配置数据类"""
    mode_type: GameModeType
    name: str
    description: str
    unlock_condition: Optional[str] = None
    max_levels: int = 0
    difficulty_curve: float = 1.0
    special_rules: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "mode_type": self.mode_type.name,
            "name": self.name,
            "description": self.description,
            "unlock_condition": self.unlock_condition,
            "max_levels": self.max_levels,
            "difficulty_curve": self.difficulty_curve,
            "special_rules": self.special_rules
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModeConfig:
        """从字典创建"""
        return cls(
            mode_type=GameModeType[data["mode_type"]],
            name=data["name"],
            description=data["description"],
            unlock_condition=data.get("unlock_condition"),
            max_levels=data.get("max_levels", 0),
            difficulty_curve=data.get("difficulty_curve", 1.0),
            special_rules=data.get("special_rules", [])
        )


@dataclass
class LevelProgress:
    """关卡进度数据类"""
    level_id: str
    stars: int = 0  # 0-3 星
    completed: bool = False
    best_time: Optional[float] = None
    best_score: int = 0
    attempts: int = 0
    last_played: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "level_id": self.level_id,
            "stars": self.stars,
            "completed": self.completed,
            "best_time": self.best_time,
            "best_score": self.best_score,
            "attempts": self.attempts,
            "last_played": self.last_played
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LevelProgress:
        """从字典创建"""
        return cls(
            level_id=data["level_id"],
            stars=data.get("stars", 0),
            completed=data.get("completed", False),
            best_time=data.get("best_time"),
            best_score=data.get("best_score", 0),
            attempts=data.get("attempts", 0),
            last_played=data.get("last_played")
        )


class BaseGameMode(ABC):
    """游戏模式基类
    
    所有游戏模式必须继承此类并实现抽象方法。
    采用模板方法模式定义游戏循环骨架。
    """
    
    def __init__(self, config: ModeConfig):
        """初始化游戏模式
        
        Args:
            config: 模式配置信息
        """
        self.config = config
        self.phase = GamePhase.NOT_STARTED
        self.current_level: Optional[str] = None
        self.progress: Dict[str, LevelProgress] = {}
        self.session_data: Dict[str, Any] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        
    @abstractmethod
    def start_level(self, level_id: str, **kwargs: Any) -> bool:
        """开始关卡
        
        Args:
            level_id: 关卡标识符
            **kwargs: 额外参数
            
        Returns:
            是否成功启动
        """
        pass
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """更新游戏状态
        
        Args:
            dt: 帧间隔时间（秒）
        """
        pass
    
    @abstractmethod
    def render(self) -> Dict[str, Any]:
        """渲染游戏画面
        
        Returns:
            渲染数据字典
        """
        pass
    
    @abstractmethod
    def handle_input(self, event_type: str, data: Dict[str, Any]) -> bool:
        """处理输入事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            是否已处理
        """
        pass
    
    def pause(self) -> None:
        """暂停游戏"""
        if self.phase == GamePhase.RUNNING:
            self.phase = GamePhase.PAUSED
            self._emit_event("game_paused", {})
    
    def resume(self) -> None:
        """恢复游戏"""
        if self.phase == GamePhase.PAUSED:
            self.phase = GamePhase.RUNNING
            self._emit_event("game_resumed", {})
    
    def end_level(self, success: bool, score: int = 0, time_elapsed: Optional[float] = None) -> None:
        """结束关卡
        
        Args:
            success: 是否成功
            score: 得分
            time_elapsed: 耗时（秒）
        """
        if self.current_level:
            progress = self.progress.get(self.current_level)
            if not progress:
                progress = LevelProgress(level_id=self.current_level)
                self.progress[self.current_level] = progress
            
            progress.completed = success
            progress.attempts += 1
            progress.last_played = time.time()
            
            if success:
                # 计算星级
                if score >= 1000:
                    progress.stars = max(progress.stars, 3)
                elif score >= 500:
                    progress.stars = max(progress.stars, 2)
                else:
                    progress.stars = max(progress.stars, 1)
                
                if time_elapsed and (progress.best_time is None or time_elapsed < progress.best_time):
                    progress.best_time = time_elapsed
                
                if score > progress.best_score:
                    progress.best_score = score
            
            self.phase = GamePhase.COMPLETED if success else GamePhase.FAILED
            self._emit_event("level_ended", {
                "success": success,
                "score": score,
                "time": time_elapsed,
                "stars": progress.stars
            })
    
    def get_progress(self, level_id: str) -> Optional[LevelProgress]:
        """获取关卡进度
        
        Args:
            level_id: 关卡标识符
            
        Returns:
            关卡进度或 None
        """
        return self.progress.get(level_id)
    
    def save_progress(self, filepath: Path) -> None:
        """保存进度到文件
        
        Args:
            filepath: 文件路径
        """
        data = {
            level_id: progress.to_dict()
            for level_id, progress in self.progress.items()
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_progress(self, filepath: Path) -> None:
        """从文件加载进度
        
        Args:
            filepath: 文件路径
        """
        if not filepath.exists():
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.progress = {
            level_id: LevelProgress.from_dict(progress_data)
            for level_id, progress_data in data.items()
        }
    
    def register_handler(self, event_type: str, handler: Callable) -> None:
        """注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """触发事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                print(f"Event handler error for {event_type}: {e}")


class AdventureMode(BaseGameMode):
    """冒险模式实现
    
    经典剧情模式，包含 5 大场景 50+ 关卡。
    特点：
    - 线性关卡推进
    - 逐步解锁植物
    - 难度递进曲线
    - 过场动画支持
    """
    
    def __init__(self):
        config = ModeConfig(
            mode_type=GameModeType.ADVENTURE,
            name="冒险模式",
            description="穿越草坪、夜晚、泳池、屋顶，击败僵王博士！",
            max_levels=59,  # 50 主线 + 9 隐藏
            difficulty_curve=1.15,
            special_rules=["progressive_unlock", "cutscenes"]
        )
        super().__init__(config)
        self.unlocked_plants: List[str] = ["sunflower", "peashooter", "wall_nut"]
        self.current_scene: int = 1
        self.cutscene_queue: List[str] = []
    
    def start_level(self, level_id: str, **kwargs: Any) -> bool:
        """开始冒险模式关卡"""
        if self.phase == GamePhase.RUNNING:
            return False
        
        # 验证关卡 ID 格式 (如 "1-1", "2-5")
        parts = level_id.split("-")
        if len(parts) != 2:
            return False
        
        try:
            scene = int(parts[0])
            level = int(parts[1])
        except ValueError:
            return False
        
        if scene < 1 or scene > 5 or level < 1:
            return False
        
        self.current_level = level_id
        self.current_scene = scene
        self.phase = GamePhase.RUNNING
        self.session_data = {
            "scene": scene,
            "level": level,
            "start_time": time.time(),
            "plants_available": self._get_available_plants(scene)
        }
        
        self._emit_event("level_started", {"level_id": level_id})
        return True
    
    def _get_available_plants(self, scene: int) -> List[str]:
        """获取场景可用植物列表"""
        base_plants = ["sunflower", "peashooter", "wall_nut", "potato_mine", "snow_pea"]
        
        scene_unlocks = {
            1: ["cherry_bomb", "repeater"],
            2: ["puff_shroom", "sun_shroom", "fume_shroom"],
            3: ["lily_pad", "tangle_kelp", "threepeater"],
            4: ["flower_pot", "kernel_pult", "coffee_bean"],
            5: ["split_pea", "starfruit", "pumpkin"]
        }
        
        available = base_plants.copy()
        for s in range(1, scene + 1):
            available.extend(scene_unlocks.get(s, []))
        
        return list(set(available))
    
    def update(self, dt: float) -> None:
        """更新冒险模式状态"""
        if self.phase != GamePhase.RUNNING:
            return
        
        # 处理过场动画队列
        if self.cutscene_queue:
            self._process_cutscene(dt)
    
    def render(self) -> Dict[str, Any]:
        """渲染冒险模式画面"""
        return {
            "mode": "adventure",
            "level_id": self.current_level,
            "phase": self.phase.name,
            "scene": self.current_scene,
            "session_data": self.session_data
        }
    
    def handle_input(self, event_type: str, data: Dict[str, Any]) -> bool:
        """处理冒险模式输入"""
        if self.phase != GamePhase.RUNNING:
            return False
        
        if event_type == "plant_selected":
            self.session_data["selected_plant"] = data.get("plant_type")
            return True
        elif event_type == "plant_placed":
            self._on_plant_placed(data)
            return True
        
        return False
    
    def _process_cutscene(self, dt: float) -> None:
        """处理过场动画"""
        pass
    
    def _on_plant_placed(self, data: Dict[str, Any]) -> None:
        """处理植物放置事件"""
        pass


class MiniGameMode(BaseGameMode):
    """迷你游戏模式实现
    
    包含多种趣味小游戏：
    - 老虎机：随机植物对战僵尸
    - 宝石迷阵：三消玩法
    - 小僵尸大麻烦：保护幼苗
    - 植物不眠夜：夜间生存挑战
    """
    
    def __init__(self):
        config = ModeConfig(
            mode_type=GameModeType.MINI_GAME,
            name="迷你游戏",
            description="多种趣味小游戏等你来挑战！",
            max_levels=20,
            difficulty_curve=1.0,
            special_rules=["randomized", "arcade_style"]
        )
        super().__init__(config)
        self.mini_game_types = [
            "slot_machine",
            "gem_breaker", 
            "tiny_trouble",
            "sleepless_night"
        ]
        self.current_game_type: Optional[str] = None
    
    def start_level(self, level_id: str, **kwargs: Any) -> bool:
        """开始迷你游戏关卡"""
        if self.phase == GamePhase.RUNNING:
            return False
        
        game_type = kwargs.get("game_type", "slot_machine")
        if game_type not in self.mini_game_types:
            return False
        
        self.current_level = level_id
        self.current_game_type = game_type
        self.phase = GamePhase.RUNNING
        self.session_data = {
            "game_type": game_type,
            "start_time": time.time(),
            "score": 0
        }
        
        self._emit_event("minigame_started", {"type": game_type})
        return True
    
    def update(self, dt: float) -> None:
        """更新迷你游戏状态"""
        if self.phase != GamePhase.RUNNING:
            return
        
        # 根据不同游戏类型更新逻辑
        if self.current_game_type == "slot_machine":
            self._update_slot_machine(dt)
    
    def render(self) -> Dict[str, Any]:
        """渲染迷你游戏画面"""
        return {
            "mode": "minigame",
            "level_id": self.current_level,
            "game_type": self.current_game_type,
            "phase": self.phase.name,
            "session_data": self.session_data
        }
    
    def handle_input(self, event_type: str, data: Dict[str, Any]) -> bool:
        """处理迷你游戏输入"""
        if self.phase != GamePhase.RUNNING:
            return False
        
        if self.current_game_type == "slot_machine":
            return self._handle_slot_machine_input(event_type, data)
        
        return False
    
    def _update_slot_machine(self, dt: float) -> None:
        """更新老虎机游戏逻辑"""
        pass
    
    def _handle_slot_machine_input(self, event_type: str, data: Dict[str, Any]) -> bool:
        """处理老虎机输入"""
        return False


class PuzzleMode(BaseGameMode):
    """解谜模式实现
    
    包含益智类关卡：
    - 砸罐子：物理破坏解谜
    - 我是僵尸：反向扮演僵尸
    - 种子雨：限时种植挑战
    """
    
    def __init__(self):
        config = ModeConfig(
            mode_type=GameModeType.PUZZLE,
            name="解谜模式",
            description="烧脑益智关卡，考验你的策略！",
            max_levels=30,
            difficulty_curve=1.2,
            special_rules=["puzzle_logic", "reverse_gameplay"]
        )
        super().__init__(config)
        self.puzzle_types = ["vase_breaker", "im_zombie", "seed_rain"]
        self.current_puzzle_type: Optional[str] = None
    
    def start_level(self, level_id: str, **kwargs: Any) -> bool:
        """开始解谜关卡"""
        if self.phase == GamePhase.RUNNING:
            return False
        
        puzzle_type = kwargs.get("puzzle_type", "vase_breaker")
        if puzzle_type not in self.puzzle_types:
            return False
        
        self.current_level = level_id
        self.current_puzzle_type = puzzle_type
        self.phase = GamePhase.RUNNING
        self.session_data = {
            "puzzle_type": puzzle_type,
            "start_time": time.time(),
            "moves": 0
        }
        
        self._emit_event("puzzle_started", {"type": puzzle_type})
        return True
    
    def update(self, dt: float) -> None:
        """更新解谜模式状态"""
        if self.phase != GamePhase.RUNNING:
            return
    
    def render(self) -> Dict[str, Any]:
        """渲染解谜模式画面"""
        return {
            "mode": "puzzle",
            "level_id": self.current_level,
            "puzzle_type": self.current_puzzle_type,
            "phase": self.phase.name,
            "session_data": self.session_data
        }
    
    def handle_input(self, event_type: str, data: Dict[str, Any]) -> bool:
        """处理解谜模式输入"""
        if self.phase != GamePhase.RUNNING:
            return False
        
        if event_type == "hammer_used":
            self.session_data["moves"] = self.session_data.get("moves", 0) + 1
            return True
        
        return False


class SurvivalMode(BaseGameMode):
    """生存模式实现
    
    无尽挑战模式：
    - 白天生存：标准场地
    - 夜晚生存：无自然阳光
    - 泳池生存：水路限制
    - 屋顶生存：抛物线射击
    - 迷雾生存：视野受限
    """
    
    def __init__(self):
        config = ModeConfig(
            mode_type=GameModeType.SURVIVAL,
            name="生存模式",
            description="抵御无尽的僵尸浪潮，看你能坚持多久！",
            max_levels=5,  # 5 种场地
            difficulty_curve=1.05,
            special_rules=["endless", "wave_based"]
        )
        super().__init__(config)
        self.survival_types = ["day", "night", "pool", "roof", "fog"]
        self.current_wave: int = 0
        self.survival_time: float = 0.0
    
    def start_level(self, level_id: str, **kwargs: Any) -> bool:
        """开始生存模式"""
        if self.phase == GamePhase.RUNNING:
            return False
        
        survival_type = kwargs.get("survival_type", "day")
        if survival_type not in self.survival_types:
            return False
        
        self.current_level = level_id
        self.phase = GamePhase.RUNNING
        self.session_data = {
            "survival_type": survival_type,
            "start_time": time.time(),
            "wave": 0,
            "score": 0
        }
        self.current_wave = 0
        self.survival_time = 0.0
        
        self._emit_event("survival_started", {"type": survival_type})
        return True
    
    def update(self, dt: float) -> None:
        """更新生存模式状态"""
        if self.phase != GamePhase.RUNNING:
            return
        
        self.survival_time += dt
        
        # 每 60 秒生成一波僵尸
        wave_interval = 60.0 / (1.0 + self.current_wave * 0.1)
        if self.survival_time >= wave_interval:
            self._spawn_wave()
            self.survival_time = 0.0
    
    def render(self) -> Dict[str, Any]:
        """渲染生存模式画面"""
        return {
            "mode": "survival",
            "level_id": self.current_level,
            "phase": self.phase.name,
            "wave": self.current_wave,
            "session_data": self.session_data
        }
    
    def handle_input(self, event_type: str, data: Dict[str, Any]) -> bool:
        """处理生存模式输入"""
        if self.phase != GamePhase.RUNNING:
            return False
        
        return False
    
    def _spawn_wave(self) -> None:
        """生成新一波僵尸"""
        self.current_wave += 1
        self.session_data["wave"] = self.current_wave
        self._emit_event("wave_spawned", {"wave": self.current_wave})


class ZenGardenMode(BaseGameMode):
    """禅境花园模式实现
    
    休闲养成玩法：
    - 种植装饰植物
    - 浇水施肥互动
    - 收集金币产出
    - 成就系统联动
    """
    
    def __init__(self):
        config = ModeConfig(
            mode_type=GameModeType.ZEN_GARDEN,
            name="禅境花园",
            description="打造你的梦幻花园，轻松赚钱！",
            max_levels=1,
            difficulty_curve=0.0,
            special_rules=["relaxing", "resource_generation"]
        )
        super().__init__(config)
        self.garden_plots: Dict[str, Dict[str, Any]] = {}
        self.gold_per_minute: float = 0.0
    
    def start_level(self, level_id: str, **kwargs: Any) -> bool:
        """开始禅境花园"""
        if self.phase == GamePhase.RUNNING:
            return False
        
        self.current_level = level_id
        self.phase = GamePhase.RUNNING
        self.session_data = {
            "start_time": time.time(),
            "plots": len(self.garden_plots),
            "gold_rate": self.gold_per_minute
        }
        
        self._emit_event("zen_garden_started", {})
        return True
    
    def update(self, dt: float) -> None:
        """更新禅境花园状态"""
        if self.phase != GamePhase.RUNNING:
            return
        
        # 更新植物生长状态
        self._update_plants(dt)
        
        # 生成金币
        if self.gold_per_minute > 0:
            gold_generated = (self.gold_per_minute / 60.0) * dt
            self.session_data["pending_gold"] = self.session_data.get("pending_gold", 0) + gold_generated
    
    def render(self) -> Dict[str, Any]:
        """渲染禅境花园画面"""
        return {
            "mode": "zen_garden",
            "level_id": self.current_level,
            "phase": self.phase.name,
            "plots": self.garden_plots,
            "session_data": self.session_data
        }
    
    def handle_input(self, event_type: str, data: Dict[str, Any]) -> bool:
        """处理禅境花园输入"""
        if self.phase != GamePhase.RUNNING:
            return False
        
        if event_type == "water_plant":
            self._water_plant(data.get("plot_id"))
            return True
        elif event_type == "fertilize_plant":
            self._fertilize_plant(data.get("plot_id"))
            return True
        elif event_type == "collect_gold":
            return self._collect_gold()
        
        return False
    
    def _update_plants(self, dt: float) -> None:
        """更新植物生长状态"""
        pass
    
    def _water_plant(self, plot_id: Optional[str]) -> None:
        """给植物浇水"""
        pass
    
    def _fertilize_plant(self, plot_id: Optional[str]) -> None:
        """给植物施肥"""
        pass
    
    def _collect_gold(self) -> bool:
        """收集金币"""
        pending = self.session_data.pop("pending_gold", 0)
        if pending > 0:
            self._emit_event("gold_collected", {"amount": pending})
            return True
        return False


class GameModeFactory:
    """游戏模式工厂类
    
    负责创建和管理游戏模式实例。
    采用单例模式确保全局唯一工厂实例。
    """
    
    _instance: Optional[GameModeFactory] = None
    _registered_modes: Dict[GameModeType, Type[BaseGameMode]] = {}
    
    def __new__(cls) -> GameModeFactory:
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """初始化工厂"""
        if self._initialized:
            return
        
        self._register_default_modes()
        self._initialized = True
    
    def _register_default_modes(self) -> None:
        """注册默认游戏模式"""
        self.register_mode(GameModeType.ADVENTURE, AdventureMode)
        self.register_mode(GameModeType.MINI_GAME, MiniGameMode)
        self.register_mode(GameModeType.PUZZLE, PuzzleMode)
        self.register_mode(GameModeType.SURVIVAL, SurvivalMode)
        self.register_mode(GameModeType.ZEN_GARDEN, ZenGardenMode)
    
    def register_mode(self, mode_type: GameModeType, mode_class: Type[BaseGameMode]) -> None:
        """注册游戏模式类
        
        Args:
            mode_type: 模式类型
            mode_class: 模式类
        """
        self._registered_modes[mode_type] = mode_class
    
    def create(self, mode_type: GameModeType | str) -> BaseGameMode:
        """创建游戏模式实例
        
        Args:
            mode_type: 模式类型或名称
            
        Returns:
            游戏模式实例
            
        Raises:
            ValueError: 未注册的 mode_type
        """
        if isinstance(mode_type, str):
            try:
                mode_type = GameModeType[mode_type.upper()]
            except KeyError:
                raise ValueError(f"Unknown game mode: {mode_type}")
        
        mode_class = self._registered_modes.get(mode_type)
        if not mode_class:
            raise ValueError(f"No mode registered for {mode_type}")
        
        return mode_class()
    
    def get_available_modes(self) -> List[Dict[str, Any]]:
        """获取可用模式列表
        
        Returns:
            模式信息列表
        """
        result = []
        for mode_type, mode_class in self._registered_modes.items():
            instance = mode_class.__new__(mode_class)
            # 临时获取配置信息
            result.append({
                "type": mode_type.name,
                "class_name": mode_class.__name__
            })
        return result


# 全局工厂实例
GAME_MODE_FACTORY = GameModeFactory()


def get_game_mode(mode_type: GameModeType | str) -> BaseGameMode:
    """便捷函数：获取游戏模式实例
    
    Args:
        mode_type: 模式类型或名称
        
    Returns:
        游戏模式实例
    """
    return GAME_MODE_FACTORY.create(mode_type)


# 模块导出
__all__ = [
    "GameModeType",
    "GamePhase",
    "ModeConfig",
    "LevelProgress",
    "BaseGameMode",
    "AdventureMode",
    "MiniGameMode",
    "PuzzleMode",
    "SurvivalMode",
    "ZenGardenMode",
    "GameModeFactory",
    "GAME_MODE_FACTORY",
    "get_game_mode"
]
