"""
植物大战僵尸 - 游戏逻辑系统模块
第五阶段：核心游戏循环与状态管理

包含：
- 游戏状态机（菜单/选择/进行/暂停/结算）
- 游戏循环管理
- 输入处理系统
- 帧率控制
- 游戏事件调度
"""

from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import json


class GameState(Enum):
    """游戏状态枚举"""
    INITIALIZING = auto()     # 初始化中
    MAIN_MENU = auto()        # 主菜单
    LEVEL_SELECT = auto()     # 关卡选择
    CARD_SELECT = auto()      # 植物选择
    PLAYING = auto()          # 游戏进行中
    PAUSED = auto()           # 暂停
    GAME_OVER = auto()        # 游戏结束
    VICTORY = auto()          # 胜利
    QUITTING = auto()         # 退出中


class GameEventType(Enum):
    """游戏事件类型枚举"""
    PLANT_PLACED = auto()       # 植物放置
    PLANT_REMOVED = auto()      # 植物移除
    SUN_COLLECTED = auto()      # 阳光收集
    ZOMBIE_SPAWNED = auto()     # 僵尸生成
    ZOMBIE_KILLED = auto()      # 僵尸消灭
    PROJECTILE_FIRED = auto()   # 子弹发射
    PROJECTILE_HIT = auto()     # 子弹命中
    DAMAGE_DEALT = auto()       # 造成伤害
    ABILITY_ACTIVATED = auto()  # 技能激活
    WAVE_STARTED = auto()       # 波次开始
    WAVE_COMPLETED = auto()     # 波次完成
    LEVEL_STARTED = auto()      # 关卡开始
    LEVEL_COMPLETED = auto()    # 关卡完成
    GAME_SAVED = auto()         # 游戏保存
    GAME_LOADED = auto()        # 游戏加载
    ACHIEVEMENT_UNLOCKED = auto()  # 成就解锁


@dataclass
class GameEvent:
    """游戏事件数据类"""
    event_type: GameEventType
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'event_type': self.event_type.name,
            'timestamp': self.timestamp,
            'data': self.data
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GameEvent':
        """从字典创建"""
        return cls(
            event_type=GameEventType[data['event_type']],
            timestamp=data['timestamp'],
            data=data.get('data', {})
        )


class EventDispatcher:
    """
    事件分发器
    
    实现观察者模式，用于游戏内事件的通知和处理
    """
    
    def __init__(self):
        self._listeners: Dict[GameEventType, List[Callable]] = {}
        self._global_listeners: List[Callable] = []
        self._event_queue: List[GameEvent] = []
        self._event_history: List[GameEvent] = []
        self._max_history = 100
    
    def subscribe(self, event_type: GameEventType, callback: Callable):
        """
        订阅特定类型的事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数 (接收 GameEvent 参数)
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        if callback not in self._listeners[event_type]:
            self._listeners[event_type].append(callback)
    
    def unsubscribe(self, event_type: GameEventType, callback: Callable):
        """
        取消订阅
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self._listeners:
            if callback in self._listeners[event_type]:
                self._listeners[event_type].remove(callback)
    
    def subscribe_all(self, callback: Callable):
        """订阅所有类型的事件"""
        if callback not in self._global_listeners:
            self._global_listeners.append(callback)
    
    def dispatch(self, event: GameEvent):
        """
        分发事件
        
        Args:
            event: 要分发的事件
        """
        # 添加到历史记录
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # 通知特定类型的监听器
        if event.event_type in self._listeners:
            for callback in self._listeners[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in event callback: {e}")
        
        # 通知全局监听器
        for callback in self._global_listeners:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in global event callback: {e}")
    
    def queue_event(self, event: GameEvent):
        """将事件加入队列（延迟处理）"""
        self._event_queue.append(event)
    
    def process_queue(self):
        """处理队列中的所有事件"""
        while self._event_queue:
            event = self._event_queue.pop(0)
            self.dispatch(event)
    
    def get_history(self, event_type: Optional[GameEventType] = None,
                    limit: int = 10) -> List[GameEvent]:
        """
        获取事件历史
        
        Args:
            event_type: 可选的事件类型过滤
            limit: 最大返回数量
            
        Returns:
            List[GameEvent]: 事件列表
        """
        if event_type is None:
            return self._event_history[-limit:]
        
        filtered = [e for e in self._event_history if e.event_type == event_type]
        return filtered[-limit:]
    
    def clear_history(self):
        """清空事件历史"""
        self._event_history.clear()


class InputHandler:
    """
    输入处理器
    
    统一处理键盘、鼠标等输入设备
    """
    
    def __init__(self):
        self.keys_pressed: Dict[int, bool] = {}
        self.keys_just_pressed: Dict[int, bool] = {}
        self.keys_just_released: Dict[int, bool] = {}
        self.mouse_x: float = 0
        self.mouse_y: float = 0
        self.mouse_buttons: Dict[int, bool] = {}
        self.mouse_just_pressed: Dict[int, bool] = {}
        self.mouse_just_released: Dict[int, bool] = {}
        self.scroll_delta: float = 0
        self.input_callbacks: List[Callable] = []
    
    def key_down(self, key: int):
        """处理按键按下"""
        if not self.keys_pressed.get(key, False):
            self.keys_just_pressed[key] = True
        self.keys_pressed[key] = True
    
    def key_up(self, key: int):
        """处理按键释放"""
        self.keys_pressed[key] = False
        self.keys_just_released[key] = True
    
    def mouse_move(self, x: float, y: float):
        """处理鼠标移动"""
        self.mouse_x = x
        self.mouse_y = y
    
    def mouse_button_down(self, button: int):
        """处理鼠标按钮按下"""
        if not self.mouse_buttons.get(button, False):
            self.mouse_just_pressed[button] = True
        self.mouse_buttons[button] = True
    
    def mouse_button_up(self, button: int):
        """处理鼠标按钮释放"""
        self.mouse_buttons[button] = False
        self.mouse_just_released[button] = True
    
    def mouse_scroll(self, delta: float):
        """处理鼠标滚轮"""
        self.scroll_delta = delta
    
    def is_key_pressed(self, key: int) -> bool:
        """检查按键是否按下"""
        return self.keys_pressed.get(key, False)
    
    def is_key_just_pressed(self, key: int) -> bool:
        """检查按键是否刚按下"""
        return self.keys_just_pressed.get(key, False)
    
    def is_mouse_button_pressed(self, button: int) -> bool:
        """检查鼠标按钮是否按下"""
        return self.mouse_buttons.get(button, False)
    
    def is_mouse_button_just_pressed(self, button: int) -> bool:
        """检查鼠标按钮是否刚按下"""
        return self.mouse_just_pressed.get(button, False)
    
    def get_mouse_position(self) -> Tuple[float, float]:
        """获取鼠标位置"""
        return (self.mouse_x, self.mouse_y)
    
    def update(self):
        """更新输入状态（每帧调用）"""
        # 清除"刚按下/刚释放"状态
        self.keys_just_pressed.clear()
        self.keys_just_released.clear()
        self.mouse_just_pressed.clear()
        self.mouse_just_released.clear()
        self.scroll_delta = 0
        
        # 调用回调
        for callback in self.input_callbacks:
            try:
                callback(self)
            except Exception as e:
                print(f"Error in input callback: {e}")


class FPSCounter:
    """
    帧率计数器
    
    计算并显示当前帧率和帧时间
    """
    
    def __init__(self, sample_count: int = 30):
        self.sample_count = sample_count
        self.frame_times: List[float] = []
        self.fps: float = 0.0
        self.frame_time: float = 0.0
        self.total_frames: int = 0
        self.start_time: float = time.time()
    
    def tick(self) -> float:
        """
        记录一帧的时间
        
        Returns:
            float: 帧时间（秒）
        """
        current_time = time.time()
        
        if self.frame_times:
            self.frame_time = current_time - self.frame_times[-1]
        else:
            self.frame_time = 0
        
        self.frame_times.append(current_time)
        self.total_frames += 1
        
        # 保持采样数量
        if len(self.frame_times) > self.sample_count:
            self.frame_times.pop(0)
        
        # 计算 FPS
        if len(self.frame_times) >= 2:
            elapsed = self.frame_times[-1] - self.frame_times[0]
            if elapsed > 0:
                self.fps = (len(self.frame_times) - 1) / elapsed
        
        return self.frame_time
    
    def get_fps(self) -> float:
        """获取当前 FPS"""
        return self.fps
    
    def get_frame_time(self) -> float:
        """获取当前帧时间（毫秒）"""
        return self.frame_time * 1000
    
    def get_average_fps(self) -> float:
        """获取平均 FPS"""
        if len(self.frame_times) < 2:
            return 0.0
        elapsed = self.frame_times[-1] - self.frame_times[0]
        if elapsed > 0:
            return (len(self.frame_times) - 1) / elapsed
        return 0.0
    
    def get_total_frames(self) -> int:
        """获取总帧数"""
        return self.total_frames
    
    def get_elapsed_time(self) -> float:
        """获取运行总时间（秒）"""
        return time.time() - self.start_time
    
    def reset(self):
        """重置计数器"""
        self.frame_times.clear()
        self.fps = 0.0
        self.frame_time = 0.0
        self.total_frames = 0
        self.start_time = time.time()


@dataclass
class GameConfig:
    """游戏配置数据类"""
    screen_width: int = 800
    screen_height: int = 600
    fullscreen: bool = False
    vsync: bool = True
    target_fps: int = 60
    audio_enabled: bool = True
    music_volume: float = 0.5
    sfx_volume: float = 0.7
    show_fps: bool = False
    language: str = 'zh_CN'
    difficulty: str = 'normal'
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'screen_width': self.screen_width,
            'screen_height': self.screen_height,
            'fullscreen': self.fullscreen,
            'vsync': self.vsync,
            'target_fps': self.target_fps,
            'audio_enabled': self.audio_enabled,
            'music_volume': self.music_volume,
            'sfx_volume': self.sfx_volume,
            'show_fps': self.show_fps,
            'language': self.language,
            'difficulty': self.difficulty
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GameConfig':
        """从字典创建"""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
    
    def save(self, filepath: str):
        """保存到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, filepath: str) -> 'GameConfig':
        """从文件加载"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return cls()


class GameLogicSystem:
    """
    游戏逻辑系统单例类
    
    管理游戏核心逻辑，包括状态机、事件系统、输入处理和帧率控制
    """
    
    _instance: Optional['GameLogicSystem'] = None
    
    def __new__(cls) -> 'GameLogicSystem':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # 游戏状态
        self.state = GameState.INITIALIZING
        self.previous_state = GameState.INITIALIZING
        self.state_stack: List[GameState] = []
        
        # 核心组件
        self.event_dispatcher = EventDispatcher()
        self.input_handler = InputHandler()
        self.fps_counter = FPSCounter()
        self.config = GameConfig()
        
        # 游戏数据
        self.current_level: Optional[int] = None
        self.game_data: Dict[str, Any] = {}
        
        # 回调函数
        self.state_change_callbacks: List[Callable] = []
        self.update_callbacks: List[Callable] = []
        
        # 时间控制
        self.last_update_time = time.time()
        self.accumulator = 0.0
        self.fixed_timestep = 1.0 / 60.0  # 固定更新时间步长
        
        # 性能统计
        self.update_time = 0.0
        self.render_time = 0.0
    
    def change_state(self, new_state: GameState):
        """
        改变游戏状态
        
        Args:
            new_state: 新的游戏状态
        """
        if self.state == new_state:
            return
        
        self.previous_state = self.state
        self.state = new_state
        
        # 通知状态变化
        event = GameEvent(
            event_type=GameEventType.LEVEL_STARTED if new_state == GameState.PLAYING else GameEventType.GAME_LOADED,
            timestamp=time.time(),
            data={'new_state': new_state.name, 'previous_state': self.previous_state.name}
        )
        self.event_dispatcher.dispatch(event)
        
        # 调用回调
        for callback in self.state_change_callbacks:
            try:
                callback(new_state, self.previous_state)
            except Exception as e:
                print(f"Error in state change callback: {e}")
    
    def push_state(self, state: GameState):
        """
        压入状态（用于暂停等临时状态）
        
        Args:
            state: 要压入的状态
        """
        self.state_stack.append(self.state)
        self.change_state(state)
    
    def pop_state(self) -> Optional[GameState]:
        """
        弹出状态（恢复之前的状态）
        
        Returns:
            Optional[GameState]: 恢复的状态，如果栈为空则返回 None
        """
        if self.state_stack:
            previous = self.state_stack.pop()
            self.change_state(previous)
            return previous
        return None
    
    def set_current_level(self, level: int):
        """设置当前关卡"""
        self.current_level = level
    
    def get_game_data(self, key: str, default: Any = None) -> Any:
        """获取游戏数据"""
        return self.game_data.get(key, default)
    
    def set_game_data(self, key: str, value: Any):
        """设置游戏数据"""
        self.game_data[key] = value
    
    def register_state_change_callback(self, callback: Callable):
        """注册状态变化回调"""
        self.state_change_callbacks.append(callback)
    
    def register_update_callback(self, callback: Callable):
        """注册更新回调"""
        self.update_callbacks.append(callback)
    
    def update(self, dt: float):
        """
        更新游戏逻辑
        
        Args:
            dt: 时间增量（秒）
        """
        # 更新 FPS 计数器
        self.fps_counter.tick()
        
        # 更新输入处理器
        self.input_handler.update()
        
        # 处理事件队列
        self.event_dispatcher.process_queue()
        
        # 调用更新回调
        for callback in self.update_callbacks:
            try:
                callback(dt, self.state)
            except Exception as e:
                print(f"Error in update callback: {e}")
        
        # 更新性能统计
        self.last_update_time = time.time()
    
    def fixed_update(self):
        """固定时间步长更新（用于物理等）"""
        # 这里可以添加需要固定时间步长的逻辑
        pass
    
    def get_delta_time(self) -> float:
        """获取上一帧的时间增量"""
        return self.fps_counter.frame_time
    
    def get_target_delta_time(self) -> float:
        """获取目标时间增量"""
        return 1.0 / self.config.target_fps
    
    def is_playing(self) -> bool:
        """检查是否在游戏进行中"""
        return self.state == GameState.PLAYING
    
    def is_paused(self) -> bool:
        """检查是否暂停"""
        return self.state == GameState.PAUSED
    
    def is_in_menu(self) -> bool:
        """检查是否在菜单中"""
        return self.state in [GameState.MAIN_MENU, GameState.LEVEL_SELECT, GameState.CARD_SELECT]
    
    def quit_game(self):
        """标记游戏退出"""
        self.change_state(GameState.QUITTING)
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计信息"""
        return {
            'fps': self.fps_counter.get_fps(),
            'frame_time_ms': self.fps_counter.get_frame_time(),
            'average_fps': self.fps_counter.get_average_fps(),
            'total_frames': self.fps_counter.get_total_frames(),
            'elapsed_time': self.fps_counter.get_elapsed_time(),
            'state': self.state.name,
            'current_level': self.current_level
        }
    
    def load_config(self, filepath: str):
        """加载配置文件"""
        self.config = GameConfig.load(filepath)
    
    def save_config(self, filepath: str):
        """保存配置文件"""
        self.config.save(filepath)


# 工具函数
def create_event(event_type: GameEventType, **kwargs) -> GameEvent:
    """
    创建游戏事件的快捷函数
    
    Args:
        event_type: 事件类型
        **kwargs: 事件数据
        
    Returns:
        GameEvent: 创建的事件
    """
    return GameEvent(
        event_type=event_type,
        timestamp=time.time(),
        data=kwargs
    )


def dispatch_event(event_type: GameEventType, **kwargs):
    """
    快速分发事件的快捷函数
    
    Args:
        event_type: 事件类型
        **kwargs: 事件数据
    """
    system = GameLogicSystem()
    event = create_event(event_type, **kwargs)
    system.event_dispatcher.dispatch(event)


# 模块导出
__all__ = [
    # 枚举类
    'GameState',
    'GameEventType',
    
    # 数据类
    'GameEvent',
    'GameConfig',
    
    # 核心类
    'EventDispatcher',
    'InputHandler',
    'FPSCounter',
    'GameLogicSystem',
    
    # 工具函数
    'create_event',
    'dispatch_event'
]
