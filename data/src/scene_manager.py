"""
场景管理器模块 - 工业级多场景系统
支持白天、黑夜、泳池、屋顶四种场景的切换和管理
包含场景特效、背景变化、机制差异等完整功能
"""

import pygame
from typing import Dict, List, Optional, Tuple
from data.src._BasicImports import *


class SceneType:
    """场景类型枚举"""
    DAY = 'day'
    NIGHT = 'night'
    POOL = 'pool'
    ROOF = 'roof'


class SceneConfig:
    """场景配置类 - 封装场景的所有属性"""
    
    def __init__(self, scene_type: str, config: dict):
        """
        初始化场景配置
        
        :param scene_type: 场景类型
        :param config: 场景配置字典
        """
        self.scene_type = scene_type
        self.name = config.get('name', scene_type)
        self.background_path = config.get('background_path', '')
        self.background_music = config.get('background_music', '')
        
        # 光照效果
        self.ambient_light = config.get('ambient_light', (255, 255, 255))
        self.has_falling_sun = config.get('has_falling_sun', True)
        self.falling_sun_rate = config.get('falling_sun_rate', 900)
        
        # 特殊机制
        self.has_water = config.get('has_water', False)
        self.has_slope = config.get('has_slope', False)
        self.water_rows = config.get('water_rows', [])  # 泳池的行
        self.slope_rows = config.get('slope_rows', [])  # 屋顶的斜面行
        
        # 可用植物限制
        self.allowed_plants = config.get('allowed_plants', [])
        self.required_aquatic_plants = config.get('required_aquatic_plants', False)
        
        # 僵尸生成修正
        self.zombie_spawn_rate_modifier = config.get('zombie_spawn_rate_modifier', 1.0)
        self.special_zombies = config.get('special_zombies', [])
        
        # 割草机位置修正
        self.lawnmower_offset = config.get('lawnmower_offset', 0)


class SceneManager:
    """场景管理器 - 单例模式管理场景切换和场景状态"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if SceneManager._initialized:
            return
        SceneManager._initialized = True
        
        self.current_scene: Optional[SceneConfig] = None
        self.scene_configs: Dict[str, SceneConfig] = {}
        
        # 场景特效
        self.particles = []
        self.overlays = []
        self.light_effect = None
        
        # 加载默认场景配置
        self._load_default_scenes()
    
    def _load_default_scenes(self):
        """加载默认场景配置"""
        # 白天场景
        self.register_scene(SceneConfig(SceneType.DAY, {
            'name': '白天',
            'background_path': './data/image/Background/Day.png',
            'background_music': './data/bgm/Grasswalk.mp3',
            'ambient_light': (255, 255, 255),
            'has_falling_sun': True,
            'falling_sun_rate': 900,
            'has_water': False,
            'has_slope': False,
            'water_rows': [],
            'slope_rows': [],
            'allowed_plants': [],
            'required_aquatic_plants': False,
            'zombie_spawn_rate_modifier': 1.0,
            'special_zombies': [],
            'lawnmower_offset': 0
        }))
        
        # 夜晚场景
        self.register_scene(SceneConfig(SceneType.NIGHT, {
            'name': '夜晚',
            'background_path': './data/image/Background/Night.png',
            'background_music': './data/bgm/Night.mp3',
            'ambient_light': (100, 100, 150),  # 偏蓝的暗光
            'has_falling_sun': True,
            'falling_sun_rate': 1500,  # 夜晚阳光更稀有
            'has_water': False,
            'has_slope': False,
            'water_rows': [],
            'slope_rows': [],
            'allowed_plants': [],
            'required_aquatic_plants': False,
            'zombie_spawn_rate_modifier': 1.2,  # 夜晚僵尸生成更快
            'special_zombies': [],
            'lawnmower_offset': 0
        }))
        
        # 泳池场景
        self.register_scene(SceneConfig(SceneType.POOL, {
            'name': '泳池',
            'background_path': './data/image/Background/Pool.png',
            'background_music': './data/bgm/Pool.mp3',
            'ambient_light': (255, 255, 255),
            'has_falling_sun': True,
            'falling_sun_rate': 900,
            'has_water': True,
            'has_slope': False,
            'water_rows': [2, 3, 4],  # 中间三行是水
            'slope_rows': [],
            'allowed_plants': [],
            'required_aquatic_plants': True,  # 需要睡莲才能种植
            'zombie_spawn_rate_modifier': 1.1,
            'special_zombies': ['diver_zombie'],  # 潜水僵尸
            'lawnmower_offset': 0
        }))
        
        # 屋顶场景
        self.register_scene(SceneConfig(SceneType.ROOF, {
            'name': '屋顶',
            'background_path': './data/image/Background/Roof.png',
            'background_music': './data/bgm/Roof.mp3',
            'ambient_light': (255, 255, 255),
            'has_falling_sun': True,
            'falling_sun_rate': 900,
            'has_water': False,
            'has_slope': True,
            'water_rows': [],
            'slope_rows': [1, 2, 3, 4, 5],  # 所有行都有斜面
            'allowed_plants': [],
            'required_aquatic_plants': False,
            'zombie_spawn_rate_modifier': 1.3,  # 屋顶僵尸生成最快
            'special_zombies': ['bungee_zombie'],  # 飞贼僵尸
            'lawnmower_offset': 20  # 屋顶割草机位置偏移
        }))
    
    def register_scene(self, config: SceneConfig):
        """
        注册新的场景配置
        
        :param config: 场景配置
        """
        self.scene_configs[config.scene_type] = config
    
    def set_scene(self, scene_type: str, screen=None):
        """
        切换到指定场景
        
        :param scene_type: 场景类型
        :param screen: pygame 屏幕对象（用于加载背景）
        :return: 是否切换成功
        """
        if scene_type not in self.scene_configs:
            print(f"警告：未知的场景类型 '{scene_type}'")
            return False
        
        old_scene = self.current_scene
        self.current_scene = self.scene_configs[scene_type]
        
        # 场景切换特效
        if old_scene and screen:
            self._play_transition_effect(screen, old_scene, self.current_scene)
        
        # 重置场景特效
        self.particles.clear()
        self.overlays.clear()
        
        return True
    
    def get_current_scene(self) -> Optional[SceneConfig]:
        """获取当前场景配置"""
        return self.current_scene
    
    def update(self):
        """更新场景状态 - 每帧调用"""
        if not self.current_scene:
            return
        
        # 更新粒子效果
        self._update_particles()
        
        # 更新光照效果
        self._update_light_effect()
    
    def render(self, screen):
        """渲染场景特效"""
        if not self.current_scene:
            return
        
        # 渲染粒子
        self._render_particles(screen)
        
        # 渲染光照 overlay
        self._render_light_overlay(screen)
    
    def _play_transition_effect(self, screen, old_scene: SceneConfig, new_scene: SceneConfig):
        """播放场景切换特效"""
        # 简单的淡入淡出效果
        transition_surface = pygame.Surface(GAME_SIZE)
        transition_surface.fill((0, 0, 0))
        
        for alpha in range(0, 256, 10):
            transition_surface.set_alpha(alpha)
            screen.blit(transition_surface, (0, 0))
            pygame.display.flip()
            pygame.time.wait(30)
        
        for alpha in range(255, -1, -10):
            transition_surface.set_alpha(alpha)
            screen.blit(transition_surface, (0, 0))
            pygame.display.flip()
            pygame.time.wait(30)
    
    def _update_particles(self):
        """更新粒子效果"""
        # 移除过期的粒子
        self.particles = [p for p in self.particles if p['life'] > 0]
        
        # 更新粒子位置和状态
        for particle in self.particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            particle['alpha'] = int(255 * particle['life'] / particle['max_life'])
    
    def _update_light_effect(self):
        """更新光照效果"""
        if self.current_scene.scene_type == SceneType.NIGHT:
            # 夜晚场景添加萤火虫效果
            if random.random() < 0.02:
                self.particles.append({
                    'x': random.randint(0, GAME_SIZE[0]),
                    'y': random.randint(0, GAME_SIZE[1]),
                    'vx': random.uniform(-0.5, 0.5),
                    'vy': random.uniform(-0.5, 0.5),
                    'life': 120,
                    'max_life': 120,
                    'alpha': 200,
                    'color': (200, 255, 150),
                    'size': 3
                })
    
    def _render_particles(self, screen):
        """渲染粒子效果"""
        for particle in self.particles:
            surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surface, (*particle['color'], particle['alpha']), 
                             (particle['size'], particle['size']), particle['size'])
            screen.blit(surface, (particle['x'], particle['y']))
    
    def _render_light_overlay(self, screen):
        """渲染光照覆盖层"""
        if not self.current_scene:
            return
        
        if self.current_scene.scene_type == SceneType.NIGHT:
            # 夜晚场景添加蓝色覆盖层
            overlay = pygame.Surface(GAME_SIZE, pygame.SRCALPHA)
            overlay.fill((20, 20, 60, 80))
            screen.blit(overlay, (0, 0))
    
    def is_water_row(self, row: int) -> bool:
        """检查某行是否是水域"""
        if not self.current_scene or not self.current_scene.has_water:
            return False
        return row in self.current_scene.water_rows
    
    def is_slope_row(self, row: int) -> bool:
        """检查某行是否有斜面"""
        if not self.current_scene or not self.current_scene.has_slope:
            return False
        return row in self.current_scene.slope_rows
    
    def can_plant_here(self, plant_type: str, row: int, col: int) -> bool:
        """
        检查是否可以在指定位置种植物
        
        :param plant_type: 植物类型
        :param row: 行号
        :param col: 列号
        :return: 是否可以种植
        """
        if not self.current_scene:
            return True
        
        # 检查水域限制
        if self.is_water_row(row):
            # 水生植物可以直接种在水里
            aquatic_plants = ['lily_pad', 'tangle_kelp', 'cattail']
            if plant_type not in aquatic_plants:
                # 非水生植物需要睡莲
                return False
        
        return True
    
    def get_lawnmower_x(self, row: int) -> int:
        """获取某行割草机的 X 坐标"""
        base_x = LAWNMOWER_POS_X
        if self.current_scene:
            base_x += self.current_scene.lawnmower_offset
        return base_x


# 全局场景管理器实例
scene_manager = SceneManager()
