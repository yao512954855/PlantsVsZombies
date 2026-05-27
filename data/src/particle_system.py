"""
粒子特效引擎 - 工业级粒子系统实现
支持多种粒子效果：爆炸、烟雾、火花、水滴、落叶等
"""

import pygame
import random
import math
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ParticleType(Enum):
    """粒子类型枚举"""
    EXPLOSION = "explosion"      # 爆炸效果
    SMOKE = "smoke"              # 烟雾效果
    SPARK = "spark"              # 火花效果
    WATER_DROP = "water_drop"    # 水滴效果
    LEAF = "leaf"                # 落叶效果
    SUNBEAM = "sunbeam"          # 阳光效果
    DUST = "dust"                # 灰尘效果


@dataclass
class ParticleConfig:
    """粒子配置数据类"""
    particle_type: ParticleType
    color: Tuple[int, int, int] = (255, 255, 255)
    size: float = 5.0
    size_variance: float = 2.0
    speed: float = 100.0
    speed_variance: float = 50.0
    lifetime: float = 1.0
    lifetime_variance: float = 0.5
    gravity: float = 0.0
    spread: float = 360.0  # 扩散角度（度）
    emission_rate: int = 10  # 每秒发射数量
    max_particles: int = 100
    fade_out: bool = True
    shrink: bool = True
    rotation_speed: float = 0.0


class Particle:
    """单个粒子类"""
    
    def __init__(self, x: float, y: float, config: ParticleConfig):
        """
        初始化粒子
        
        Args:
            x: 初始X坐标
            y: 初始Y坐标
            config: 粒子配置
        """
        self.x: float = x
        self.y: float = y
        self.config: ParticleConfig = config
        
        # 随机属性
        angle = random.uniform(0, math.radians(config.spread))
        speed = config.speed + random.uniform(-config.speed_variance, config.speed_variance)
        
        self.vx: float = math.cos(angle) * speed
        self.vy: float = math.sin(angle) * speed
        
        self.size: float = config.size + random.uniform(-config.size_variance, config.size_variance)
        self.initial_size: float = self.size
        
        self.lifetime: float = config.lifetime + random.uniform(-config.lifetime_variance, config.lifetime_variance)
        self.max_lifetime: float = self.lifetime
        
        self.rotation: float = random.uniform(0, 360)
        self.rotation_speed: float = config.rotation_speed
        
        self.color: Tuple[int, int, int] = config.color
        self.alpha: int = 255
        
        self.active: bool = True
    
    def update(self, delta_time: float) -> None:
        """
        更新粒子状态
        
        Args:
            delta_time: 时间增量（秒）
        """
        if not self.active:
            return
        
        # 更新位置
        self.vy += self.config.gravity * delta_time
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time
        
        # 更新旋转
        self.rotation += self.rotation_speed * delta_time
        
        # 更新生命周期
        self.lifetime -= delta_time
        
        # 计算生命周期比例
        life_ratio = self.lifetime / self.max_lifetime
        
        # 淡出效果
        if self.config.fade_out:
            self.alpha = int(255 * life_ratio)
        
        # 收缩效果
        if self.config.shrink:
            self.size = self.initial_size * life_ratio
        
        # 检查是否死亡
        if self.lifetime <= 0:
            self.active = False
    
    def draw(self, screen: pygame.Surface) -> None:
        """
        绘制粒子
        
        Args:
            screen: 绘制目标表面
        """
        if not self.active or self.alpha <= 0:
            return
        
        # 根据粒子类型使用不同的绘制方式
        if self.config.particle_type == ParticleType.EXPLOSION:
            self._draw_explosion(screen)
        elif self.config.particle_type == ParticleType.SMOKE:
            self._draw_smoke(screen)
        elif self.config.particle_type == ParticleType.SPARK:
            self._draw_spark(screen)
        else:
            self._draw_default(screen)
    
    def _draw_explosion(self, screen: pygame.Surface) -> None:
        """绘制爆炸粒子"""
        # 创建渐变圆形
        radius = int(self.size)
        if radius <= 0:
            return
        
        # 从中心向外渐变
        for r in range(radius, 0, -1):
            alpha = int(self.alpha * (1 - r / radius))
            color = (self.color[0], self.color[1], self.color[2], alpha)
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), r)
    
    def _draw_smoke(self, screen: pygame.Surface) -> None:
        """绘制烟雾粒子"""
        radius = int(self.size * (1 + (1 - self.lifetime / self.max_lifetime) * 2))
        if radius <= 0:
            return
        
        # 创建半透明圆形
        alpha = int(self.alpha * 0.3)
        color = (100, 100, 100, alpha)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), radius)
    
    def _draw_spark(self, screen: pygame.Surface) -> None:
        """绘制火花粒子"""
        length = int(self.size * 2)
        if length <= 0:
            return
        
        # 绘制发光效果
        # 外层光晕
        glow_surface = pygame.Surface((length * 3, length * 3), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (255, 200, 100, int(self.alpha * 0.3)), 
                          (int(length * 1.5), int(length * 1.5)), int(length * 1.5))
        screen.blit(glow_surface, (int(self.x - length * 1.5), int(self.y - length * 1.5)))
        
        # 核心
        pygame.draw.circle(screen, (self.color[0], self.color[1], self.color[2], self.alpha), 
                          (int(self.x), int(self.y)), int(self.size))
    
    def _draw_default(self, screen: pygame.Surface) -> None:
        """绘制默认粒子"""
        radius = int(self.size)
        if radius <= 0:
            return
        
        color = (self.color[0], self.color[1], self.color[2], self.alpha)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), radius)


class ParticleEmitter:
    """粒子发射器类"""
    
    def __init__(self, x: float, y: float, config: ParticleConfig):
        """
        初始化发射器
        
        Args:
            x: 发射器X坐标
            y: 发射器Y坐标
            config: 粒子配置
        """
        self.x: float = x
        self.y: float = y
        self.config: ParticleConfig = config
        
        self.particles: List[Particle] = []
        self.emission_timer: float = 0.0
        self.active: bool = True
        
        # 计算发射间隔
        self.emission_interval: float = 1.0 / config.emission_rate if config.emission_rate > 0 else float('inf')
    
    def update(self, delta_time: float) -> None:
        """
        更新发射器
        
        Args:
            delta_time: 时间增量（秒）
        """
        if not self.active:
            return
        
        # 发射新粒子
        self.emission_timer += delta_time
        while self.emission_timer >= self.emission_interval:
            if len(self.particles) < self.config.max_particles:
                self.particles.append(Particle(self.x, self.y, self.config))
            self.emission_timer -= self.emission_interval
        
        # 更新所有粒子
        for particle in self.particles[:]:
            particle.update(delta_time)
            if not particle.active:
                self.particles.remove(particle)
        
        # 检查是否需要销毁发射器
        if not self.particles and self.config.emission_rate == 0:
            self.active = False
    
    def draw(self, screen: pygame.Surface) -> None:
        """
        绘制所有粒子
        
        Args:
            screen: 绘制目标表面
        """
        for particle in self.particles:
            particle.draw(screen)
    
    def burst(self, count: int) -> None:
        """
        一次性发射多个粒子
        
        Args:
            count: 粒子数量
        """
        for _ in range(count):
            if len(self.particles) < self.config.max_particles:
                self.particles.append(Particle(self.x, self.y, self.config))
    
    def set_position(self, x: float, y: float) -> None:
        """
        设置发射器位置
        
        Args:
            x: 新X坐标
            y: 新Y坐标
        """
        self.x = x
        self.y = y
    
    def stop_emission(self) -> None:
        """停止发射新粒子"""
        self.config.emission_rate = 0


class ParticleSystem:
    """粒子系统管理器（单例）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """初始化粒子系统"""
        self.emitters: List[ParticleEmitter] = []
        self.particle_configs: Dict[str, ParticleConfig] = {}
        
        # 预定义粒子配置
        self._register_default_configs()
    
    def _register_default_configs(self) -> None:
        """注册默认粒子配置"""
        # 爆炸配置
        self.particle_configs['explosion'] = ParticleConfig(
            particle_type=ParticleType.EXPLOSION,
            color=(255, 150, 50),
            size=8.0,
            size_variance=4.0,
            speed=200.0,
            speed_variance=100.0,
            lifetime=0.8,
            lifetime_variance=0.3,
            gravity=500.0,
            spread=360.0,
            emission_rate=0,
            max_particles=50,
            fade_out=True,
            shrink=True
        )
        
        # 烟雾配置
        self.particle_configs['smoke'] = ParticleConfig(
            particle_type=ParticleType.SMOKE,
            color=(100, 100, 100),
            size=15.0,
            size_variance=5.0,
            speed=30.0,
            speed_variance=10.0,
            lifetime=3.0,
            lifetime_variance=1.0,
            gravity=-20.0,  # 向上飘
            spread=60.0,
            emission_rate=5,
            max_particles=30,
            fade_out=True,
            shrink=False
        )
        
        # 火花配置
        self.particle_configs['spark'] = ParticleConfig(
            particle_type=ParticleType.SPARK,
            color=(255, 200, 50),
            size=3.0,
            size_variance=1.0,
            speed=300.0,
            speed_variance=100.0,
            lifetime=0.5,
            lifetime_variance=0.2,
            gravity=300.0,
            spread=180.0,
            emission_rate=0,
            max_particles=40,
            fade_out=True,
            shrink=True
        )
        
        # 水滴配置
        self.particle_configs['water_drop'] = ParticleConfig(
            particle_type=ParticleType.WATER_DROP,
            color=(100, 150, 255),
            size=4.0,
            size_variance=2.0,
            speed=150.0,
            speed_variance=30.0,
            lifetime=1.5,
            lifetime_variance=0.5,
            gravity=400.0,
            spread=30.0,
            emission_rate=8,
            max_particles=20,
            fade_out=True,
            shrink=False
        )
        
        # 落叶配置
        self.particle_configs['leaf'] = ParticleConfig(
            particle_type=ParticleType.LEAF,
            color=(200, 150, 50),
            size=8.0,
            size_variance=3.0,
            speed=50.0,
            speed_variance=20.0,
            lifetime=5.0,
            lifetime_variance=2.0,
            gravity=80.0,
            spread=360.0,
            emission_rate=3,
            max_particles=15,
            fade_out=True,
            shrink=False,
            rotation_speed=90.0
        )
        
        # 阳光配置
        self.particle_configs['sunbeam'] = ParticleConfig(
            particle_type=ParticleType.SUNBEAM,
            color=(255, 255, 200),
            size=10.0,
            size_variance=5.0,
            speed=80.0,
            speed_variance=20.0,
            lifetime=2.0,
            lifetime_variance=0.5,
            gravity=-50.0,
            spread=20.0,
            emission_rate=4,
            max_particles=25,
            fade_out=True,
            shrink=True
        )
        
        # 灰尘配置
        self.particle_configs['dust'] = ParticleConfig(
            particle_type=ParticleType.DUST,
            color=(200, 200, 200),
            size=2.0,
            size_variance=1.0,
            speed=20.0,
            speed_variance=10.0,
            lifetime=4.0,
            lifetime_variance=1.0,
            gravity=-10.0,
            spread=360.0,
            emission_rate=6,
            max_particles=50,
            fade_out=True,
            shrink=False
        )
    
    def create_emitter(self, x: float, y: float, config_name: str) -> ParticleEmitter:
        """
        创建粒子发射器
        
        Args:
            x: 发射器X坐标
            y: 发射器Y坐标
            config_name: 配置名称
            
        Returns:
            粒子发射器实例
        """
        if config_name not in self.particle_configs:
            raise ValueError(f"未知的粒子配置: {config_name}")
        
        config = self.particle_configs[config_name]
        emitter = ParticleEmitter(x, y, config)
        self.emitters.append(emitter)
        
        return emitter
    
    def create_custom_emitter(self, x: float, y: float, config: ParticleConfig) -> ParticleEmitter:
        """
        使用自定义配置创建粒子发射器
        
        Args:
            x: 发射器X坐标
            y: 发射器Y坐标
            config: 自定义粒子配置
            
        Returns:
            粒子发射器实例
        """
        emitter = ParticleEmitter(x, y, config)
        self.emitters.append(emitter)
        
        return emitter
    
    def trigger_explosion(self, x: float, y: float, intensity: float = 1.0) -> None:
        """
        触发爆炸效果
        
        Args:
            x: 爆炸中心X坐标
            y: 爆炸中心Y坐标
            intensity: 爆炸强度（1.0为默认）
        """
        emitter = self.create_emitter(x, y, 'explosion')
        emitter.burst(int(int(30 * intensity)))
        
        # 同时创建烟雾效果
        smoke_config = self.particle_configs['smoke']
        smoke_emitter = self.create_custom_emitter(x, y, smoke_config)
        smoke_emitter.burst(int(10 * intensity))
    
    def trigger_spark(self, x: float, y: float, count: int = 20) -> None:
        """
        触发火花效果
        
        Args:
            x: 火花起点X坐标
            y: 火花起点Y坐标
            count: 火花数量
        """
        emitter = self.create_emitter(x, y, 'spark')
        emitter.burst(count)
    
    def create_continuous_emitter(self, x: float, y: float, config_name: str) -> ParticleEmitter:
        """
        创建持续发射的粒子发射器
        
        Args:
            x: 发射器X坐标
            y: 发射器Y坐标
            config_name: 配置名称
            
        Returns:
            粒子发射器实例
        """
        emitter = self.create_emitter(x, y, config_name)
        return emitter
    
    def update(self, delta_time: float) -> None:
        """
        更新所有发射器
        
        Args:
            delta_time: 时间增量（秒）
        """
        for emitter in self.emitters[:]:
            emitter.update(delta_time)
            if not emitter.active:
                self.emitters.remove(emitter)
    
    def draw(self, screen: pygame.Surface) -> None:
        """
        绘制所有粒子
        
        Args:
            screen: 绘制目标表面
        """
        for emitter in self.emitters:
            emitter.draw(screen)
    
    def clear_all(self) -> None:
        """清除所有发射器和粒子"""
        self.emitters.clear()
    
    def get_emitter_count(self) -> int:
        """获取发射器数量"""
        return len(self.emitters)
    
    def get_total_particle_count(self) -> int:
        """获取总粒子数量"""
        return sum(len(e.particles) for e in self.emitters)


# 全局粒子系统实例
particle_system = ParticleSystem()
