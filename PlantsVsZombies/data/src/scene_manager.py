"""
场景管理系统 (Scene Manager)
工业级植物大战僵尸重构项目 - 第二阶段

功能：
- 管理四种游戏场景（白天/夜晚/泳池/屋顶）
- 处理场景特有的游戏机制（水域、斜面、墓碑等）
- 场景切换特效与过渡动画
- 动态光照与环境效果

作者: AI Assistant
版本: 2.0.0
"""

import pygame
import random
from typing import Dict, List, Optional, Tuple
from data.src._BasicImports import *


class SceneType:
    """场景类型枚举"""
    DAY = "day"           # 白天草坪
    NIGHT = "night"       # 夜晚草坪
    POOL = "pool"         # 泳池场景
    ROOF = "roof"         # 屋顶场景


class SceneConfig:
    """
    场景配置类
    定义每种场景的视觉属性、游戏机制和特殊规则
    """
    
    def __init__(self, scene_type: str):
        self.scene_type = scene_type
        self._init_config()
    
    def _init_config(self):
        """初始化场景配置"""
        if self.scene_type == SceneType.DAY:
            self.background_color = (135, 206, 235)  # 天空蓝
            self.grass_color = (34, 139, 34)         # 草地绿
            self.grid_rows = 5
            self.grid_cols = 9
            self.has_water = False
            self.has_slope = False
            self.has_gravestones = False
            self.sun_fall_rate = 0.005               # 阳光掉落频率
            self.ambient_light = 1.0                 # 环境光照强度
            self.music_track = "data/sound/music_day.ogg"
            self.special_rules = []
            
        elif self.scene_type == SceneType.NIGHT:
            self.background_color = (25, 25, 112)    # 午夜蓝
            self.grass_color = (0, 100, 0)           # 深绿
            self.grid_rows = 5
            self.grid_cols = 9
            self.has_water = False
            self.has_slope = False
            self.has_gravestones = True              # 夜晚有墓碑
            self.sun_fall_rate = 0.002               # 夜晚阳光较少
            self.ambient_light = 0.6                 # 较暗
            self.music_track = "data/sound/music_night.ogg"
            self.special_rules = ["gravestone_spawn"]
            
        elif self.scene_type == SceneType.POOL:
            self.background_color = (135, 206, 235)
            self.grass_color = (34, 139, 34)
            self.water_color = (64, 164, 223)        # 水蓝色
            self.grid_rows = 6                       # 泳池多一行
            self.grid_cols = 9
            self.has_water = True
            self.water_rows = [2, 3]                 # 第3、4行是水
            self.has_slope = False
            self.has_gravestones = False
            self.sun_fall_rate = 0.004
            self.ambient_light = 1.0
            self.music_track = "data/sound/music_pool.ogg"
            self.special_rules = ["aquatic_plants_required"]
            
        elif self.scene_type == SceneType.ROOF:
            self.background_color = (139, 69, 19)    # 棕色屋顶
            self.grass_color = (101, 67, 33)
            self.grid_rows = 5
            self.grid_cols = 9
            self.has_water = False
            self.has_slope = True                    # 屋顶有斜面
            self.slope_angles = [0, 5, 10, 15, 20]   # 每行倾斜角度
            self.has_gravestones = False
            self.sun_fall_rate = 0.003
            self.ambient_light = 0.9
            self.music_track = "data/sound/music_roof.ogg"
            self.special_rules = ["flower_pots_required", "slope_physics"]
        
        # 通用配置
        self.cell_width = 80
        self.cell_height = 100
        self.offset_x = 25
        self.offset_y = 100
    
    def get_cell_rect(self, row: int, col: int) -> pygame.Rect:
        """获取指定格子的矩形区域"""
        x = self.offset_x + col * self.cell_width
        y = self.offset_y + row * self.cell_height
        
        # 屋顶斜面修正
        if self.has_slope and self.scene_type == SceneType.ROOF:
            y += self.slope_angles[row] * 2
        
        return pygame.Rect(x, y, self.cell_width, self.cell_height)
    
    def is_valid_position(self, row: int, col: int) -> bool:
        """检查位置是否有效"""
        if row < 0 or row >= self.grid_rows:
            return False
        if col < 0 or col >= self.grid_cols:
            return False
        return True
    
    def is_water(self, row: int) -> bool:
        """检查某行是否为水域"""
        if not self.has_water:
            return False
        return row in self.water_rows
    
    def needs_flower_pot(self, row: int, col: int) -> bool:
        """检查是否需要花盆（屋顶场景）"""
        return self.has_slope and self.scene_type == SceneType.ROOF


class Particle:
    """简易粒子类，用于场景特效"""
    
    def __init__(self, x: float, y: float, vx: float, vy: float, 
                 color: Tuple[int, int, int], lifetime: float):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.age = 0.0
        self.alpha = 255
    
    def update(self, dt: float):
        """更新粒子状态"""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 200 * dt  # 重力
        self.age += dt
        self.alpha = max(0, int(255 * (1 - self.age / self.lifetime)))
    
    def draw(self, surface: pygame.Surface):
        """绘制粒子"""
        if self.alpha > 0:
            size = max(1, int(5 * (1 - self.age / self.lifetime)))
            s = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, self.alpha), (size//2, size//2), size//2)
            surface.blit(s, (int(self.x), int(self.y)))
    
    def is_dead(self) -> bool:
        """检查粒子是否死亡"""
        return self.age >= self.lifetime


class SceneManager:
    """
    场景管理器单例类
    负责场景切换、特效渲染、环境更新
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
        
        self.current_scene: Optional[SceneConfig] = None
        self.transition_progress: float = 0.0
        self.is_transitioning: bool = False
        self.transition_from: Optional[str] = None
        self.transition_to: Optional[str] = None
        
        # 特效系统
        self.particles: List[Particle] = []
        self.falling_suns: List[Dict] = []
        
        # 环境效果
        self.wind_offset: float = 0.0
        self.lightning_timer: float = 0.0
        self.should_flash: bool = False
        
        # 资源缓存
        self.background_cache: Dict[str, pygame.Surface] = {}
        self.overlay_cache: Dict[str, pygame.Surface] = {}
        
        print(f"[SceneManager] 初始化完成")
    
    def set_scene(self, scene_type: str) -> SceneConfig:
        """设置当前场景"""
        self.current_scene = SceneConfig(scene_type)
        print(f"[SceneManager] 切换到场景: {scene_type}")
        return self.current_scene
    
    def start_transition(self, from_scene: str, to_scene: str, duration: float = 2.0):
        """开始场景过渡动画"""
        self.is_transitioning = True
        self.transition_from = from_scene
        self.transition_to = to_scene
        self.transition_progress = 0.0
        self.transition_duration = duration
        
        # 创建过渡特效
        self._create_transition_effects()
        
        print(f"[SceneManager] 开始过渡: {from_scene} -> {to_scene}")
    
    def _create_transition_effects(self):
        """创建过渡特效粒子"""
        for _ in range(50):
            x = random.uniform(0, SCREEN_WIDTH)
            y = random.uniform(-50, 0)
            vx = random.uniform(-100, 100)
            vy = random.uniform(100, 300)
            color = (255, 255, 255) if random.random() > 0.5 else (200, 200, 255)
            lifetime = random.uniform(1.0, 2.5)
            self.particles.append(Particle(x, y, vx, vy, color, lifetime))
    
    def update(self, dt: float):
        """更新场景状态"""
        # 更新过渡动画
        if self.is_transitioning:
            self.transition_progress += dt / self.transition_duration
            if self.transition_progress >= 1.0:
                self.is_transitioning = False
                self.transition_progress = 1.0
                self.transition_from = None
                # 应用新场景
                if self.transition_to:
                    self.set_scene(self.transition_to)
                    self.transition_to = None
        
        # 更新粒子
        for particle in self.particles[:]:
            particle.update(dt)
            if particle.is_dead():
                self.particles.remove(particle)
        
        # 更新掉落阳光
        for sun in self.falling_suns[:]:
            sun['y'] += sun['vy'] * dt
            sun['rotation'] += sun['vr'] * dt
            if sun['y'] > SCREEN_HEIGHT:
                self.falling_suns.remove(sun)
        
        # 更新环境效果
        self.wind_offset += dt * 50
        if self.current_scene and self.current_scene.scene_type == SceneType.NIGHT:
            self.lightning_timer += dt
            if self.lightning_timer > random.uniform(5.0, 15.0):
                self.should_flash = True
                self.lightning_timer = 0.0
    
    def spawn_falling_sun(self, x: Optional[float] = None):
        """生成掉落阳光"""
        if not self.current_scene:
            return
        
        if x is None:
            x = random.uniform(100, SCREEN_WIDTH - 100)
        
        self.falling_suns.append({
            'x': x,
            'y': -50,
            'vy': random.uniform(50, 100),
            'rotation': 0,
            'vr': random.uniform(-30, 30),
            'value': 25,
            'rect': pygame.Rect(x - 25, -50, 50, 50)
        })
    
    def draw(self, surface: pygame.Surface):
        """绘制场景"""
        if not self.current_scene:
            surface.fill((0, 0, 0))
            return
        
        # 绘制背景
        surface.fill(self.current_scene.background_color)
        
        # 绘制草地网格
        self._draw_grid(surface)
        
        # 绘制水域（如果有）
        if self.current_scene.has_water:
            self._draw_water(surface)
        
        # 绘制过渡遮罩
        if self.is_transitioning:
            self._draw_transition_overlay(surface)
        
        # 绘制粒子
        for particle in self.particles:
            particle.draw(surface)
        
        # 绘制掉落阳光
        self._draw_falling_suns(surface)
        
        # 绘制环境覆盖层
        self._draw_environment_overlay(surface)
    
    def _draw_grid(self, surface: pygame.Surface):
        """绘制草地网格"""
        for row in range(self.current_scene.grid_rows):
            for col in range(self.current_scene.grid_cols):
                rect = self.current_scene.get_cell_rect(row, col)
                
                # 交错颜色
                color = self.current_scene.grass_color
                if (row + col) % 2 == 0:
                    color = tuple(max(0, c - 20) for c in color)
                
                pygame.draw.rect(surface, color, rect)
                
                # 网格线
                pygame.draw.rect(surface, (0, 0, 0), rect, 1)
    
    def _draw_water(self, surface: pygame.Surface):
        """绘制水域"""
        water_color = self.current_scene.water_color
        for row in self.current_scene.water_rows:
            for col in range(self.current_scene.grid_cols):
                rect = self.current_scene.get_cell_rect(row, col)
                
                # 波浪效果
                offset = math.sin(self.wind_offset * 0.002 + col * 0.5) * 3
                water_rect = pygame.Rect(rect.x, rect.y + offset, rect.width, rect.height)
                
                # 半透明水
                water_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.rect(water_surface, (*water_color, 180), water_rect)
                surface.blit(water_surface, (rect.x, rect.y))
    
    def _draw_transition_overlay(self, surface: pygame.Surface):
        """绘制过渡遮罩"""
        progress = self.transition_progress
        
        # 淡出旧场景
        if progress < 0.5:
            alpha = int(255 * (progress * 2))
        else:
            alpha = int(255 * (1 - (progress - 0.5) * 2))
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        surface.blit(overlay, (0, 0))
    
    def _draw_falling_suns(self, surface: pygame.Surface):
        """绘制掉落阳光"""
        for sun in self.falling_suns:
            sun_rect = pygame.Rect(sun['x'] - 25, sun['y'], 50, 50)
            
            # 旋转表面
            rotated_surface = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(rotated_surface, (255, 255, 0), (25, 25), 20)
            pygame.draw.circle(rotated_surface, (255, 255, 200), (25, 25), 15)
            
            rotated_surface = pygame.transform.rotate(rotated_surface, sun['rotation'])
            new_rect = rotated_surface.get_rect(center=sun_rect.center)
            
            surface.blit(rotated_surface, new_rect.topleft)
    
    def _draw_environment_overlay(self, surface: pygame.Surface):
        """绘制环境覆盖层（夜晚黑暗、闪电等）"""
        if not self.current_scene:
            return
        
        # 夜晚黑暗覆盖
        if self.current_scene.ambient_light < 1.0:
            darkness = int(255 * (1 - self.current_scene.ambient_light))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, darkness // 2))
            surface.blit(overlay, (0, 0))
        
        # 闪电效果
        if self.should_flash:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 100))
            surface.blit(flash, (0, 0))
            self.should_flash = False
    
    def get_click_grid_pos(self, mouse_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """将鼠标点击转换为网格坐标"""
        if not self.current_scene:
            return None
        
        mx, my = mouse_pos
        for row in range(self.current_scene.grid_rows):
            for col in range(self.current_scene.grid_cols):
                rect = self.current_scene.get_cell_rect(row, col)
                if rect.collidepoint(mx, my):
                    return (row, col)
        return None
    
    def clear_particles(self):
        """清除所有粒子"""
        self.particles.clear()
    
    def clear_falling_suns(self):
        """清除所有掉落阳光"""
        self.falling_suns.clear()


# 全局单例访问函数
def get_scene_manager() -> SceneManager:
    """获取场景管理器单例"""
    return SceneManager()


if __name__ == "__main__":
    # 测试代码
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    
    manager = get_scene_manager()
    manager.set_scene(SceneType.DAY)
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pos = manager.get_click_grid_pos(pygame.mouse.get_pos())
                    if pos:
                        print(f"点击格子: {pos}")
                elif event.button == 3:
                    manager.spawn_falling_sun()
        
        manager.update(dt)
        
        screen.fill((0, 0, 0))
        manager.draw(screen)
        
        # 显示FPS
        fps_text = pygame.font.SysFont('Arial', 24).render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
        screen.blit(fps_text, (10, 10))
        
        pygame.display.flip()
    
    pygame.quit()
