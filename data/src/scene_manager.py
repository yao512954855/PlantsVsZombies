'''
场景管理系统 - 负责管理 4 大场景 (白天/夜晚/屋顶/泳池) 的切换和配置
工业级标准：类型注解、文档字符串、错误处理、配置驱动
'''

from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from data.src.const import *
from data.src.settings import settings
from enum import Enum
import pygame

if TYPE_CHECKING:
    from data.src.Game import Game


class SceneType(Enum):
    """场景类型枚举"""
    DAY = 'day'
    NIGHT = 'night'
    ROOF = 'roof'
    POOL = 'pool'
    FOG = 'fog'  # 迷雾场景 (泳池 + 迷雾)


class SceneConfig:
    """场景配置数据类"""
    
    def __init__(
        self,
        scene_type: SceneType,
        background_path: str,
        sky_color: Tuple[int, int, int],
        ambient_light: float,  # 环境亮度 (0.0-1.0)
        has_fog: bool = False,
        fog_density: float = 0.0,
        requires_flower_pot: bool = False,
        water_rows: Optional[List[int]] = None,
        special_effects: Optional[Dict[str, Any]] = None
    ):
        self.scene_type = scene_type
        self.background_path = background_path
        self.sky_color = sky_color
        self.ambient_light = ambient_light
        self.has_fog = has_fog
        self.fog_density = fog_density
        self.requires_flower_pot = requires_flower_pot
        self.water_rows = water_rows or []
        self.special_effects = special_effects or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'scene_type': self.scene_type.value,
            'background_path': self.background_path,
            'sky_color': self.sky_color,
            'ambient_light': self.ambient_light,
            'has_fog': self.has_fog,
            'fog_density': self.fog_density,
            'requires_flower_pot': self.requires_flower_pot,
            'water_rows': self.water_rows,
            'special_effects': self.special_effects
        }


class SceneManager:
    """
    场景管理器 - 单例模式
    负责管理场景的加载、切换、渲染和特效
    """
    
    _instance: Optional['SceneManager'] = None
    
    def __new__(cls) -> 'SceneManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._current_scene: Optional[SceneType] = None
        self._scene_configs: Dict[SceneType, SceneConfig] = {}
        self._background_surface: Optional[pygame.Surface] = None
        self._fog_surface: Optional[pygame.Surface] = None
        self._transition_progress: float = 0.0
        self._is_transitioning: bool = False
        
        self._initialize_scene_configs()
    
    def _initialize_scene_configs(self) -> None:
        """初始化所有场景配置"""
        
        # 白天场景
        self._scene_configs[SceneType.DAY] = SceneConfig(
            scene_type=SceneType.DAY,
            background_path=settings.get('day', {}).get('background', 'data/src/background.py'),
            sky_color=(135, 206, 235),  # 天空蓝
            ambient_light=1.0,
            has_fog=False,
            requires_flower_pot=False,
            special_effects={
                'clouds': True,
                'birds': True
            }
        )
        
        # 夜晚场景
        self._scene_configs[SceneType.NIGHT] = SceneConfig(
            scene_type=SceneType.NIGHT,
            background_path=settings.get('night', {}).get('background', ''),
            sky_color=(25, 25, 112),  # 午夜蓝
            ambient_light=0.4,
            has_fog=False,
            requires_flower_pot=False,
            special_effects={
                'stars': True,
                'moon': True,
                'tombstones': True  # 墓碑生成
            }
        )
        
        # 屋顶场景
        self._scene_configs[SceneType.ROOF] = SceneConfig(
            scene_type=SceneType.ROOF,
            background_path=settings.get('roof', {}).get('background', ''),
            sky_color=(135, 206, 235),
            ambient_light=0.9,
            has_fog=False,
            requires_flower_pot=True,  # 需要花盆
            special_effects={
                'slope': True,  # 斜坡效果
                'house_edge': True
            }
        )
        
        # 泳池场景
        self._scene_configs[SceneType.POOL] = SceneConfig(
            scene_type=SceneType.POOL,
            background_path=settings.get('pool', {}).get('background', ''),
            sky_color=(135, 206, 235),
            ambient_light=1.0,
            has_fog=False,
            water_rows=[2, 3],  # 中间两行是水
            special_effects={
                'water_animation': True,
                'lily_pads': True
            }
        )
        
        # 迷雾场景 (泳池 + 迷雾)
        self._scene_configs[SceneType.FOG] = SceneConfig(
            scene_type=SceneType.FOG,
            background_path=settings.get('fog', {}).get('background', ''),
            sky_color=(70, 70, 90),
            ambient_light=0.5,
            has_fog=True,
            fog_density=0.7,
            water_rows=[2, 3],
            special_effects={
                'water_animation': True,
                'fog_movement': True,
                'plantern_reveal': True  # 三叶草揭示效果
            }
        )
    
    def load_scene(self, scene_type: SceneType) -> bool:
        """
        加载指定场景
        
        :param scene_type: 场景类型
        :return: 是否成功加载
        """
        if scene_type not in self._scene_configs:
            print(f"Error: Unknown scene type '{scene_type}'")
            return False
        
        config = self._scene_configs[scene_type]
        
        # 加载背景
        try:
            if config.background_path:
                self._background_surface = pygame.image.load(config.background_path).convert()
            else:
                # 创建纯色背景
                self._background_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                self._background_surface.fill(config.sky_color)
        except Exception as e:
            print(f"Warning: Failed to load background for {scene_type}: {e}")
            self._background_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self._background_surface.fill(config.sky_color)
        
        # 加载迷雾层 (如果需要)
        if config.has_fog:
            self._create_fog_surface(config.fog_density)
        else:
            self._fog_surface = None
        
        self._current_scene = scene_type
        print(f"Scene loaded: {scene_type.value}")
        
        return True
    
    def _create_fog_surface(self, density: float) -> None:
        """
        创建迷雾表面
        
        :param density: 迷雾密度 (0.0-1.0)
        """
        self._fog_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # 迷雾颜色 (半透明灰色)
        fog_alpha = int(255 * density)
        fog_color = (50, 50, 50, fog_alpha)
        
        self._fog_surface.fill(fog_color)
    
    def transition_to_scene(
        self, 
        target_scene: SceneType, 
        duration: float = 2.0
    ) -> None:
        """
        开始场景过渡动画
        
        :param target_scene: 目标场景
        :param duration: 过渡持续时间 (秒)
        """
        if target_scene == self._current_scene:
            return
        
        self._transition_target = target_scene
        self._transition_duration = duration
        self._transition_progress = 0.0
        self._is_transitioning = True
    
    def update_transition(self, delta_time: float) -> bool:
        """
        更新场景过渡
        
        :param delta_time: 时间增量 (秒)
        :return: 如果过渡完成返回 True，否则返回 False
        """
        if not self._is_transitioning:
            return True
        
        self._transition_progress += delta_time / self._transition_duration
        
        if self._transition_progress >= 1.0:
            self._transition_progress = 1.0
            self._is_transitioning = False
            self.load_scene(self._transition_target)
            return True
        
        return False
    
    def get_transition_progress(self) -> float:
        """获取过渡进度 (0.0-1.0)"""
        return self._transition_progress
    
    def is_transitioning(self) -> bool:
        """检查是否正在过渡"""
        return self._is_transitioning
    
    def render(self, screen: pygame.Surface, game: Optional['Game'] = None) -> None:
        """
        渲染场景
        
        :param screen: 游戏屏幕表面
        :param game: 游戏对象 (可选)
        """
        if self._background_surface:
            screen.blit(self._background_surface, (0, 0))
        
        # 应用环境亮度
        if self._current_scene:
            config = self._scene_configs[self._current_scene]
            if config.ambient_light < 1.0:
                self._apply_ambient_light(screen, config.ambient_light)
        
        # 渲染迷雾
        if self._fog_surface and self._current_scene:
            config = self._scene_configs[self._current_scene]
            if config.has_fog:
                self._render_fog(screen, game)
        
        # 渲染过渡效果
        if self._is_transitioning:
            self._render_transition(screen)
    
    def _apply_ambient_light(
        self, 
        screen: pygame.Surface, 
        light_level: float
    ) -> None:
        """
        应用环境亮度
        
        :param screen: 屏幕表面
        :param light_level: 亮度级别 (0.0-1.0)
        """
        # 创建亮度覆盖层
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        darkness = int(255 * (1.0 - light_level))
        overlay.fill((0, 0, 0, darkness))
        screen.blit(overlay, (0, 0))
    
    def _render_fog(
        self, 
        screen: pygame.Surface, 
        game: Optional['Game'] = None
    ) -> None:
        """
        渲染迷雾效果
        
        :param screen: 屏幕表面
        :param game: 游戏对象 (用于计算植物揭示区域)
        """
        if not self._fog_surface:
            return
        
        if self._current_scene != SceneType.FOG:
            screen.blit(self._fog_surface, (0, 0))
            return
        
        # 对于迷雾场景，需要揭示植物周围的区域
        config = self._scene_configs[self._current_scene]
        
        if game and config.special_effects.get('plantern_reveal'):
            # 创建临时表面进行揭示
            temp_fog = self._fog_surface.copy()
            
            # 揭示植物周围区域 (简化版)
            if hasattr(game, 'peashooter_list'):
                for plant in game.peashooter_list:
                    if hasattr(plant, 'pos'):
                        reveal_rect = pygame.Rect(
                            plant.pos[0] - 50,
                            plant.pos[1] - 50,
                            100,
                            100
                        )
                        pygame.draw.circle(
                            temp_fog,
                            (0, 0, 0, 0),
                            (int(plant.pos[0]), int(plant.pos[1])),
                            50
                        )
            
            screen.blit(temp_fog, (0, 0))
        else:
            screen.blit(self._fog_surface, (0, 0))
    
    def _render_transition(self, screen: pygame.Surface) -> None:
        """
        渲染场景过渡效果
        
        :param screen: 屏幕表面
        """
        progress = self._transition_progress
        
        # 简单的淡入淡出效果
        if progress < 0.5:
            # 渐暗
            alpha = int(255 * (progress * 2))
        else:
            # 渐亮
            alpha = int(255 * (1.0 - (progress - 0.5) * 2))
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        screen.blit(overlay, (0, 0))
    
    def get_current_scene(self) -> Optional[SceneType]:
        """获取当前场景类型"""
        return self._current_scene
    
    def get_scene_config(self, scene_type: SceneType) -> Optional[SceneConfig]:
        """获取场景配置"""
        return self._scene_configs.get(scene_type)
    
    def get_current_scene_config(self) -> Optional[SceneConfig]:
        """获取当前场景配置"""
        if self._current_scene:
            return self._scene_configs.get(self._current_scene)
        return None
    
    def requires_flower_pot(self) -> bool:
        """检查当前场景是否需要花盆"""
        if self._current_scene:
            config = self._scene_configs.get(self._current_scene)
            return config.requires_flower_pot if config else False
        return False
    
    def get_water_rows(self) -> List[int]:
        """获取水域行号列表"""
        if self._current_scene:
            config = self._scene_configs.get(self._current_scene)
            return config.water_rows if config else []
        return []
    
    def is_water_row(self, row: int) -> bool:
        """检查指定行是否为水域"""
        return row in self.get_water_rows()
    
    def get_ambient_light(self) -> float:
        """获取当前环境亮度"""
        if self._current_scene:
            config = self._scene_configs.get(self._current_scene)
            return config.ambient_light if config else 1.0
        return 1.0
    
    def has_fog(self) -> bool:
        """检查当前场景是否有迷雾"""
        if self._current_scene:
            config = self._scene_configs.get(self._current_scene)
            return config.has_fog if config else False
        return False


# 全局场景管理器实例
scene_manager: Optional[SceneManager] = None


def get_scene_manager() -> SceneManager:
    """获取全局场景管理器实例"""
    global scene_manager
    if scene_manager is None:
        scene_manager = SceneManager()
    return scene_manager


def initialize_scene_manager() -> SceneManager:
    """初始化并返回场景管理器"""
    global scene_manager
    scene_manager = SceneManager()
    return scene_manager


def load_scene(scene_type: str) -> bool:
    """
    便捷函数：加载场景
    
    :param scene_type: 场景类型字符串
    :return: 是否成功加载
    """
    manager = get_scene_manager()
    
    try:
        scene_enum = SceneType(scene_type.lower())
        return manager.load_scene(scene_enum)
    except ValueError:
        print(f"Error: Invalid scene type '{scene_type}'")
        return False
