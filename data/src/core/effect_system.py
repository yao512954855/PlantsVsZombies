"""
植物大战僵尸 - 特效系统模块
第五阶段：视觉特效与粒子系统

包含：
- 粒子系统（爆炸/烟雾/火花/阳光等）
- 动画效果（淡入淡出/缩放/旋转）
- 屏幕特效（震动/闪光/冻结）
- 天气效果（雨/雪/雾）
"""

from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import math
import random
import time


class ParticleType(Enum):
    """粒子类型枚举"""
    EXPLOSION = auto()      # 爆炸粒子
    SMOKE = auto()          # 烟雾粒子
    SPARK = auto()          # 火花粒子
    SUNLIGHT = auto()       # 阳光粒子
    WATER = auto()          # 水滴粒子
    ICE = auto()            # 冰晶粒子
    FIRE = auto()           # 火焰粒子
    LEAF = auto()           # 叶子粒子
    DUST = auto()           | 灰尘粒子
    BUBBLE = auto()         # 气泡粒子


class EmitterShape(Enum):
    """发射器形状枚举"""
    POINT = auto()          # 点状
    LINE = auto()           # 线状
    CIRCLE = auto()         | 圆形
    RECTANGLE = auto()      # 矩形
    CONE = auto()           # 锥形


@dataclass
class Particle:
    """粒子数据类"""
    x: float
    y: float
    vx: float               # X轴速度
    vy: float               # Y轴速度
    life: float             # 剩余寿命 (秒)
    max_life: float         # 最大寿命
    size: float             # 大小
    color: Tuple[int, int, int, int]  # RGBA颜色
    particle_type: ParticleType
    gravity: float = 0.0    # 重力影响
    drag: float = 0.0       # 阻力系数
    rotation: float = 0.0   # 旋转角度
    rotation_speed: float = 0.0  # 旋转速度
    scale_change: float = 0.0  # 缩放变化率
    alpha_change: float = 0.0  # 透明度变化率
    
    def update(self, dt: float) -> bool:
        """
        更新粒子状态
        
        Args:
            dt: 时间增量 (秒)
            
        Returns:
            bool: 粒子是否仍然存活
        """
        self.life -= dt
        if self.life <= 0:
            return False
        
        # 应用物理效果
        self.vy += self.gravity * dt
        self.vx *= (1 - self.drag * dt)
        self.vy *= (1 - self.drag * dt)
        
        # 更新位置
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # 更新旋转
        self.rotation += self.rotation_speed * dt
        
        # 更新大小和透明度
        self.size *= (1 + self.scale_change * dt)
        self.color = (
            self.color[0],
            self.color[1],
            self.color[2],
            max(0, min(255, self.color[3] + int(self.alpha_change * dt * 255)))
        )
        
        return True
    
    def is_alive(self) -> bool:
        """检查粒子是否存活"""
        return self.life > 0 and self.color[3] > 0


@dataclass
class ParticleEmitter:
    """粒子发射器数据类"""
    x: float
    y: float
    shape: EmitterShape = EmitterShape.POINT
    shape_params: Dict = field(default_factory=dict)
    particle_type: ParticleType = ParticleType.EXPLOSION
    emit_rate: float = 10.0     # 每秒发射数量
    emit_count: int = 1         # 每次发射数量
    initial_speed_min: float = 50.0
    initial_speed_max: float = 150.0
    angle_min: float = 0.0
    angle_max: float = 360.0
    life_min: float = 0.5
    life_max: float = 2.0
    size_min: float = 5.0
    size_max: float = 15.0
    color_start: Tuple[int, int, int, int] = (255, 255, 255, 255)
    color_end: Tuple[int, int, int, int] = (255, 255, 255, 0)
    gravity: float = 0.0
    drag: float = 0.1
    active: bool = True
    duration: float = -1.0      # -1 表示无限持续
    elapsed_time: float = 0.0
    _emit_timer: float = 0.0
    
    def emit(self) -> List[Particle]:
        """
        发射粒子
        
        Returns:
            List[Particle]: 新生成的粒子列表
        """
        particles = []
        
        for _ in range(self.emit_count):
            # 根据发射器形状确定初始位置
            px, py = self._get_position()
            
            # 计算速度和方向
            speed = random.uniform(self.initial_speed_min, self.initial_speed_max)
            angle = random.uniform(self.angle_min, self.angle_max)
            angle_rad = math.radians(angle)
            
            vx = math.cos(angle_rad) * speed
            vy = math.sin(angle_rad) * speed
            
            # 计算生命周期和大小
            life = random.uniform(self.life_min, self.life_max)
            size = random.uniform(self.size_min, self.size_max)
            
            # 插值颜色
            particle = Particle(
                x=px,
                y=py,
                vx=vx,
                vy=vy,
                life=life,
                max_life=life,
                size=size,
                color=self.color_start,
                particle_type=self.particle_type,
                gravity=self.gravity,
                drag=self.drag,
                alpha_change=(self.color_end[3] - self.color_start[3]) / (life * 255) if life > 0 else 0
            )
            
            particles.append(particle)
        
        return particles
    
    def _get_position(self) -> Tuple[float, float]:
        """根据发射器形状获取发射位置"""
        if self.shape == EmitterShape.POINT:
            return self.x, self.y
        
        elif self.shape == EmitterShape.LINE:
            length = self.shape_params.get('length', 100)
            t = random.random()
            return self.x + t * length, self.y
        
        elif self.shape == EmitterShape.CIRCLE:
            radius = self.shape_params.get('radius', 50)
            angle = random.uniform(0, 2 * math.pi)
            return self.x + math.cos(angle) * radius, self.y + math.sin(angle) * radius
        
        elif self.shape == EmitterShape.RECTANGLE:
            width = self.shape_params.get('width', 100)
            height = self.shape_params.get('height', 100)
            return (
                self.x + random.uniform(-width/2, width/2),
                self.y + random.uniform(-height/2, height/2)
            )
        
        elif self.shape == EmitterShape.CONE:
            distance = random.uniform(0, self.shape_params.get('distance', 100))
            angle = random.uniform(self.angle_min, self.angle_max)
            angle_rad = math.radians(angle)
            return self.x + math.cos(angle_rad) * distance, self.y + math.sin(angle_rad) * distance
        
        return self.x, self.y
    
    def update(self, dt: float) -> bool:
        """
        更新发射器状态
        
        Args:
            dt: 时间增量 (秒)
            
        Returns:
            bool: 发射器是否仍然活跃
        """
        if not self.active:
            return False
        
        self.elapsed_time += dt
        if self.duration > 0 and self.elapsed_time >= self.duration:
            self.active = False
            return False
        
        return True


class EffectAnimation:
    """效果动画基类"""
    
    def __init__(self, duration: float = 1.0):
        self.duration = duration
        self.elapsed_time = 0.0
        self.finished = False
    
    def update(self, dt: float) -> float:
        """
        更新动画进度
        
        Args:
            dt: 时间增量 (秒)
            
        Returns:
            float: 动画进度 (0.0 - 1.0)
        """
        self.elapsed_time += dt
        if self.elapsed_time >= self.duration:
            self.finished = True
            return 1.0
        return self.elapsed_time / self.duration
    
    def get_value(self, progress: float) -> float:
        """获取动画值（子类实现）"""
        return progress


class FadeEffect(EffectAnimation):
    """淡入淡出效果"""
    
    def __init__(self, start_alpha: int, end_alpha: int, duration: float = 1.0):
        super().__init__(duration)
        self.start_alpha = start_alpha
        self.end_alpha = end_alpha
    
    def get_alpha(self) -> int:
        """获取当前透明度"""
        progress = self.elapsed_time / self.duration if self.duration > 0 else 1.0
        return int(self.start_alpha + (self.end_alpha - self.start_alpha) * progress)


class ScaleEffect(EffectAnimation):
    """缩放效果"""
    
    def __init__(self, start_scale: float, end_scale: float, duration: float = 1.0):
        super().__init__(duration)
        self.start_scale = start_scale
        self.end_scale = end_scale
    
    def get_scale(self) -> float:
        """获取当前缩放比例"""
        progress = self.elapsed_time / self.duration if self.duration > 0 else 1.0
        return self.start_scale + (self.end_scale - self.start_scale) * progress


class ShakeEffect(EffectAnimation):
    """震动效果"""
    
    def __init__(self, intensity: float = 10.0, duration: float = 0.5):
        super().__init__(duration)
        self.intensity = intensity
        self.offset_x = 0.0
        self.offset_y = 0.0
    
    def update(self, dt: float) -> float:
        """更新震动偏移"""
        progress = super().update(dt)
        if not self.finished:
            remaining = 1.0 - progress
            decay = remaining * remaining  # 平方衰减
            self.offset_x = random.uniform(-self.intensity, self.intensity) * decay
            self.offset_y = random.uniform(-self.intensity, self.intensity) * decay
        else:
            self.offset_x = 0.0
            self.offset_y = 0.0
        return progress
    
    def get_offset(self) -> Tuple[float, float]:
        """获取当前震动偏移"""
        return self.offset_x, self.offset_y


class FlashEffect(EffectAnimation):
    """闪光效果"""
    
    def __init__(self, color: Tuple[int, int, int] = (255, 255, 255), 
                 duration: float = 0.3, fade_out: bool = True):
        super().__init__(duration)
        self.color = color
        self.fade_out = fade_out
        self.alpha = 0
    
    def update(self, dt: float) -> float:
        """更新闪光透明度"""
        progress = super().update(dt)
        if self.fade_out:
            # 立即显示，然后淡出
            if progress < 0.1:
                self.alpha = 255
            else:
                self.alpha = int(255 * (1 - (progress - 0.1) / 0.9))
        else:
            # 淡入然后淡出
            if progress < 0.5:
                self.alpha = int(255 * progress * 2)
            else:
                self.alpha = int(255 * (1 - progress) * 2)
        return progress
    
    def get_color(self) -> Tuple[int, int, int, int]:
        """获取当前颜色（含透明度）"""
        return (*self.color, self.alpha)


class WeatherEffect:
    """天气效果基类"""
    
    def __init__(self):
        self.active = False
        self.intensity = 0.0  # 0.0 - 1.0
    
    def start(self, intensity: float = 1.0):
        """启动天气效果"""
        self.active = True
        self.intensity = max(0.0, min(1.0, intensity))
    
    def stop(self):
        """停止天气效果"""
        self.active = False
        self.intensity = 0.0
    
    def update(self, dt: float):
        """更新天气效果"""
        pass
    
    def render(self, surface):
        """渲染天气效果（子类实现）"""
        pass


class RainEffect(WeatherEffect):
    """雨天效果"""
    
    def __init__(self, screen_width: int, screen_height: int):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.drops: List[Dict] = []
        self.max_drops = 1000
    
    def start(self, intensity: float = 1.0):
        super().start(intensity)
        # 初始化雨滴
        drop_count = int(self.max_drops * intensity)
        self.drops = [
            {
                'x': random.randint(0, self.screen_width),
                'y': random.randint(0, self.screen_height),
                'speed': random.uniform(300, 500),
                'length': random.uniform(10, 20)
            }
            for _ in range(drop_count)
        ]
    
    def update(self, dt: float):
        if not self.active:
            return
        
        for drop in self.drops:
            drop['y'] += drop['speed'] * dt
            if drop['y'] > self.screen_height:
                drop['y'] = -drop['length']
                drop['x'] = random.randint(0, self.screen_width)
    
    def render(self, surface):
        """渲染雨滴（需要 pygame surface）"""
        if not self.active:
            return
        
        try:
            import pygame
            for drop in self.drops:
                alpha = int(100 + 155 * self.intensity)
                color = (150, 180, 220, alpha)
                # 实际渲染需要 pygame 的 draw.line
                # 这里仅做逻辑演示
        except ImportError:
            pass


class SnowEffect(WeatherEffect):
    """雪天效果"""
    
    def __init__(self, screen_width: int, screen_height: int):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.flakes: List[Dict] = []
        self.max_flakes = 500
    
    def start(self, intensity: float = 1.0):
        super().start(intensity)
        flake_count = int(self.max_flakes * intensity)
        self.flakes = [
            {
                'x': random.randint(0, self.screen_width),
                'y': random.randint(0, self.screen_height),
                'vx': random.uniform(-20, 20),
                'vy': random.uniform(50, 100),
                'size': random.uniform(2, 5),
                'sway': random.uniform(0, 2 * math.pi)
            }
            for _ in range(flake_count)
        ]
    
    def update(self, dt: float):
        if not self.active:
            return
        
        for flake in self.flakes:
            flake['sway'] += dt * 2
            flake['x'] += flake['vx'] * dt + math.sin(flake['sway']) * 20 * dt
            flake['y'] += flake['vy'] * dt
            
            # 边界检查
            if flake['x'] < 0:
                flake['x'] = self.screen_width
            elif flake['x'] > self.screen_width:
                flake['x'] = 0
            
            if flake['y'] > self.screen_height:
                flake['y'] = -10
                flake['x'] = random.randint(0, self.screen_width)


class EffectSystem:
    """
    特效系统单例类
    
    管理所有游戏特效，包括粒子系统、动画效果和天气效果
    """
    
    _instance: Optional['EffectSystem'] = None
    
    def __new__(cls) -> 'EffectSystem':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.particles: List[Particle] = []
        self.emitters: List[ParticleEmitter] = []
        self.animations: List[EffectAnimation] = []
        self.weather_effects: Dict[str, WeatherEffect] = {}
        
        self.screen_width = 800
        self.screen_height = 600
        
        # 预设配置
        self._setup_presets()
    
    def _setup_presets(self):
        """设置预设特效配置"""
        self.presets = {
            'explosion': {
                'particle_type': ParticleType.EXPLOSION,
                'emit_count': 50,
                'initial_speed_min': 100,
                'initial_speed_max': 300,
                'angle_min': 0,
                'angle_max': 360,
                'life_min': 0.3,
                'life_max': 0.8,
                'size_min': 8,
                'size_max': 20,
                'color_start': (255, 200, 50, 255),
                'color_end': (255, 50, 0, 0),
                'gravity': 200,
                'drag': 0.5
            },
            'smoke': {
                'particle_type': ParticleType.SMOKE,
                'emit_count': 5,
                'initial_speed_min': 20,
                'initial_speed_max': 50,
                'angle_min': 270,
                'angle_max': 90,
                'life_min': 1.0,
                'life_max': 2.0,
                'size_min': 10,
                'size_max': 30,
                'color_start': (100, 100, 100, 150),
                'color_end': (50, 50, 50, 0),
                'gravity': -50,
                'drag': 0.2
            },
            'spark': {
                'particle_type': ParticleType.SPARK,
                'emit_count': 20,
                'initial_speed_min': 150,
                'initial_speed_max': 400,
                'angle_min': 0,
                'angle_max': 360,
                'life_min': 0.2,
                'life_max': 0.5,
                'size_min': 2,
                'size_max': 5,
                'color_start': (255, 255, 100, 255),
                'color_end': (255, 100, 0, 0),
                'gravity': 300,
                'drag': 0.1
            },
            'sunlight': {
                'particle_type': ParticleType.SUNLIGHT,
                'emit_count': 10,
                'initial_speed_min': 30,
                'initial_speed_max': 80,
                'angle_min': 0,
                'angle_max': 360,
                'life_min': 0.5,
                'life_max': 1.0,
                'size_min': 3,
                'size_max': 8,
                'color_start': (255, 255, 200, 255),
                'color_end': (255, 255, 200, 0),
                'gravity': 0,
                'drag': 0.3
            },
            'water_splash': {
                'particle_type': ParticleType.WATER,
                'emit_count': 30,
                'initial_speed_min': 100,
                'initial_speed_max': 250,
                'angle_min': 270,
                'angle_max': 90,
                'life_min': 0.4,
                'life_max': 0.8,
                'size_min': 3,
                'size_max': 8,
                'color_start': (100, 150, 255, 255),
                'color_end': (50, 100, 200, 0),
                'gravity': 400,
                'drag': 0.1
            },
            'ice_crystal': {
                'particle_type': ParticleType.ICE,
                'emit_count': 15,
                'initial_speed_min': 80,
                'initial_speed_max': 200,
                'angle_min': 0,
                'angle_max': 360,
                'life_min': 0.5,
                'life_max': 1.0,
                'size_min': 4,
                'size_max': 10,
                'color_start': (200, 230, 255, 255),
                'color_end': (150, 200, 255, 0),
                'gravity': 100,
                'drag': 0.2
            }
        }
    
    def set_screen_size(self, width: int, height: int):
        """设置屏幕尺寸"""
        self.screen_width = width
        self.screen_height = height
        
        # 重新初始化天气效果
        self.weather_effects['rain'] = RainEffect(width, height)
        self.weather_effects['snow'] = SnowEffect(width, height)
    
    def create_emitter(self, x: float, y: float, preset: str = 'explosion',
                       duration: float = -1.0, **kwargs) -> ParticleEmitter:
        """
        创建粒子发射器
        
        Args:
            x: X坐标
            y: Y坐标
            preset: 预设名称
            duration: 持续时间 (-1 表示无限)
            **kwargs: 覆盖预设的参数
            
        Returns:
            ParticleEmitter: 创建的发射器
        """
        config = self.presets.get(preset, self.presets['explosion']).copy()
        config.update(kwargs)
        
        emitter = ParticleEmitter(
            x=x,
            y=y,
            particle_type=config['particle_type'],
            emit_count=config.get('emit_count', 1),
            initial_speed_min=config.get('initial_speed_min', 50),
            initial_speed_max=config.get('initial_speed_max', 150),
            angle_min=config.get('angle_min', 0),
            angle_max=config.get('angle_max', 360),
            life_min=config.get('life_min', 0.5),
            life_max=config.get('life_max', 2.0),
            size_min=config.get('size_min', 5),
            size_max=config.get('size_max', 15),
            color_start=tuple(config.get('color_start', (255, 255, 255, 255))),
            color_end=tuple(config.get('color_end', (255, 255, 255, 0))),
            gravity=config.get('gravity', 0),
            drag=config.get('drag', 0.1),
            duration=duration
        )
        
        self.emitters.append(emitter)
        return emitter
    
    def emit_once(self, x: float, y: float, preset: str = 'explosion', **kwargs):
        """
        一次性发射粒子
        
        Args:
            x: X坐标
            y: Y坐标
            preset: 预设名称
            **kwargs: 额外参数
        """
        emitter = self.create_emitter(x, y, preset, duration=0.01, **kwargs)
        # 立即发射
        self.particles.extend(emitter.emit())
        # 移除发射器
        if emitter in self.emitters:
            self.emitters.remove(emitter)
    
    def add_animation(self, animation: EffectAnimation):
        """添加动画效果"""
        self.animations.append(animation)
    
    def shake_screen(self, intensity: float = 10.0, duration: float = 0.5):
        """
        震动屏幕
        
        Args:
            intensity: 震动强度
            duration: 持续时间
        """
        shake = ShakeEffect(intensity, duration)
        self.add_animation(shake)
        return shake
    
    def flash_screen(self, color: Tuple[int, int, int] = (255, 255, 255),
                     duration: float = 0.3):
        """
        屏幕闪光
        
        Args:
            color: 闪光颜色
            duration: 持续时间
        """
        flash = FlashEffect(color, duration)
        self.add_animation(flash)
        return flash
    
    def start_weather(self, weather_type: str, intensity: float = 1.0):
        """
        启动天气效果
        
        Args:
            weather_type: 天气类型 ('rain' 或 'snow')
            intensity: 强度 (0.0 - 1.0)
        """
        if weather_type in self.weather_effects:
            self.weather_effects[weather_type].start(intensity)
    
    def stop_weather(self, weather_type: str):
        """停止天气效果"""
        if weather_type in self.weather_effects:
            self.weather_effects[weather_type].stop()
    
    def update(self, dt: float):
        """
        更新所有特效
        
        Args:
            dt: 时间增量 (秒)
        """
        # 更新发射器并发射粒子
        for emitter in self.emitters[:]:
            if emitter.update(dt):
                self._emit_timer = getattr(emitter, '_emit_timer', 0) + dt
                emit_interval = 1.0 / emitter.emit_rate if emitter.emit_rate > 0 else 0
                if self._emit_timer >= emit_interval:
                    self._emit_timer %= emit_interval
                    self.particles.extend(emitter.emit())
            else:
                self.emitters.remove(emitter)
        
        # 更新粒子
        for particle in self.particles[:]:
            if not particle.update(dt):
                self.particles.remove(particle)
        
        # 更新动画
        for animation in self.animations[:]:
            if animation.finished:
                self.animations.remove(animation)
            else:
                animation.update(dt)
        
        # 更新天气效果
        for weather in self.weather_effects.values():
            if weather.active:
                weather.update(dt)
    
    def get_screen_shake_offset(self) -> Tuple[float, float]:
        """获取当前屏幕震动偏移"""
        for anim in self.animations:
            if isinstance(anim, ShakeEffect) and not anim.finished:
                return anim.get_offset()
        return (0.0, 0.0)
    
    def get_flash_color(self) -> Optional[Tuple[int, int, int, int]]:
        """获取当前闪光颜色"""
        for anim in self.animations:
            if isinstance(anim, FlashEffect) and not anim.finished:
                return anim.get_color()
        return None
    
    def clear_all(self):
        """清除所有特效"""
        self.particles.clear()
        self.emitters.clear()
        self.animations.clear()
        for weather in self.weather_effects.values():
            weather.stop()
    
    def get_particle_count(self) -> int:
        """获取当前粒子数量"""
        return len(self.particles)
    
    def get_active_effects_count(self) -> int:
        """获取活跃特效数量"""
        return (
            len(self.emitters) +
            len(self.animations) +
            sum(1 for w in self.weather_effects.values() if w.active)
        )


# 工具函数
def create_explosion(x: float, y: float, size: str = 'normal') -> Dict:
    """
    创建爆炸特效快捷函数
    
    Args:
        x: X坐标
        y: Y坐标
        size: 大小 ('small', 'normal', 'large')
        
    Returns:
        Dict: 特效配置
    """
    configs = {
        'small': {'emit_count': 20, 'size_min': 5, 'size_max': 12},
        'normal': {'emit_count': 50, 'size_min': 8, 'size_max': 20},
        'large': {'emit_count': 100, 'size_min': 15, 'size_max': 35}
    }
    return {'x': x, 'y': y, **configs.get(size, configs['normal'])}


def create_smoke_puff(x: float, y: float, count: int = 1) -> Dict:
    """
    创建烟雾特效快捷函数
    
    Args:
        x: X坐标
        y: Y坐标
        count: 烟雾团数量
        
    Returns:
        Dict: 特效配置
    """
    return {
        'x': x,
        'y': y,
        'preset': 'smoke',
        'emit_count': count * 5,
        'size_min': 15,
        'size_max': 40
    }


def create_spark_burst(x: float, y: float, intensity: str = 'normal') -> Dict:
    """
    创建火花特效快捷函数
    
    Args:
        x: X坐标
        y: Y坐标
        intensity: 强度 ('low', 'normal', 'high')
        
    Returns:
        Dict: 特效配置
    """
    configs = {
        'low': {'emit_count': 10, 'initial_speed_max': 200},
        'normal': {'emit_count': 20, 'initial_speed_max': 400},
        'high': {'emit_count': 40, 'initial_speed_max': 600}
    }
    return {'x': x, 'y': y, 'preset': 'spark', **configs.get(intensity, configs['normal'])}


# 模块导出
__all__ = [
    # 枚举类
    'ParticleType',
    'EmitterShape',
    
    # 数据类
    'Particle',
    'ParticleEmitter',
    
    # 动画类
    'EffectAnimation',
    'FadeEffect',
    'ScaleEffect',
    'ShakeEffect',
    'FlashEffect',
    
    # 天气类
    'WeatherEffect',
    'RainEffect',
    'SnowEffect',
    
    # 主系统
    'EffectSystem',
    
    # 工具函数
    'create_explosion',
    'create_smoke_puff',
    'create_spark_burst'
]
