"""
游戏核心逻辑类 (Game)
工业级植物大战僵尸重构项目 - 第二阶段

功能：
- 游戏主循环与状态管理
- 植物/僵尸实体管理
- 碰撞检测与战斗系统
- 阳光经济与 UI 渲染
- 关卡流程控制

作者：AI Assistant
版本：2.0.0
"""

import pygame
import random
import time
from typing import Dict, List, Optional, Tuple, Set
from data.src._BasicImports import *
from data.src.scene_manager import SceneManager, SceneType, get_scene_manager
from data.src.level_manager import LevelManager, get_level_manager
from data.src.zombie_factory import ZombieFactory, get_zombie_factory


class Plant:
    """植物基类"""
    
    def __init__(self, row: int, col: int, plant_type: str):
        self.row = row
        self.col = col
        self.plant_type = plant_type
        self.health = 100
        self.max_health = 100
        self.attack_damage = 0
        self.attack_interval = 1.0  # 秒
        self.last_attack_time = 0.0
        self.is_producing_sun = False
        self.sun_production_interval = 5.0
        self.last_sun_time = 0.0
        self.image: Optional[pygame.Surface] = None
        self.rect: Optional[pygame.Rect] = None
        self.state = "idle"  # idle, attacking, producing
    
    def update(self, dt: float, game_state: Dict):
        """更新植物状态"""
        pass
    
    def draw(self, surface: pygame.Surface, scene_manager: SceneManager):
        """绘制植物"""
        if not self.image:
            return
        
        rect = scene_manager.current_scene.get_cell_rect(self.row, self.col)
        surface.blit(self.image, rect.topleft)
        
        # 绘制血条
        if self.health < self.max_health:
            self._draw_health_bar(surface, rect)
    
    def _draw_health_bar(self, surface: pygame.Surface, rect: pygame.Rect):
        """绘制血条"""
        bar_width = rect.width
        bar_height = 5
        health_ratio = self.health / self.max_health
        
        # 背景
        pygame.draw.rect(surface, (50, 50, 50), 
                        (rect.x, rect.y - 8, bar_width, bar_height))
        # 血量
        pygame.draw.rect(surface, (0, 255, 0), 
                        (rect.x, rect.y - 8, int(bar_width * health_ratio), bar_height))
    
    def take_damage(self, damage: int):
        """受到伤害"""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            return True  # 死亡
        return False
    
    def can_attack(self, current_time: float) -> bool:
        """检查是否可以攻击"""
        return current_time - self.last_attack_time >= self.attack_interval
    
    def do_attack(self, current_time: float):
        """执行攻击"""
        self.last_attack_time = current_time


class Sunflower(Plant):
    """向日葵"""
    
    def __init__(self, row: int, col: int):
        super().__init__(row, col, "sunflower")
        self.is_producing_sun = True
        self.sun_production_interval = 5.0
        self.last_sun_time = 0.0
        self.sun_value = 25
    
    def update(self, dt: float, game_state: Dict):
        current_time = game_state.get('time', 0)
        if current_time - self.last_sun_time >= self.sun_production_interval:
            self.last_sun_time = current_time
            # 产生阳光
            sun_pos = game_state['scene_manager'].current_scene.get_cell_rect(self.row, self.col).center
            game_state.setdefault('suns_to_spawn', []).append({
                'x': sun_pos[0],
                'y': sun_pos[1],
                'value': self.sun_value,
                'is_falling': False
            })


class Peashooter(Plant):
    """豌豆射手"""
    
    def __init__(self, row: int, col: int):
        super().__init__(row, col, "peashooter")
        self.attack_damage = 20
        self.attack_interval = 1.5
        self.projectile_speed = 200
    
    def update(self, dt: float, game_state: Dict):
        current_time = game_state.get('time', 0)
        
        # 检查本行是否有僵尸
        has_zombie_in_row = any(
            z.row == self.row and z.col > self.col 
            for z in game_state.get('zombies', [])
        )
        
        if has_zombie_in_row and self.can_attack(current_time):
            self.do_attack(current_time)
            # 发射豌豆
            rect = game_state['scene_manager'].current_scene.get_cell_rect(self.row, self.col)
            game_state.setdefault('projectiles', []).append({
                'row': self.row,
                'x': rect.right,
                'y': rect.centery,
                'damage': self.attack_damage,
                'speed': self.projectile_speed,
                'type': 'pea'
            })


class Zombie:
    """僵尸基类"""
    
    def __init__(self, row: int, zombie_type: str = "normal"):
        self.row = row
        self.col = 9  # 从最右侧进入
        self.zombie_type = zombie_type
        self.health = 100
        self.max_health = 100
        self.speed = 30  # 像素/秒
        self.damage = 10
        self.attack_interval = 1.0
        self.last_attack_time = 0.0
        self.state = "walking"  # walking, eating, frozen
        self.freeze_timer = 0.0
        self.image: Optional[pygame.Surface] = None
        self.rect: Optional[pygame.Rect] = None
    
    def update(self, dt: float, game_state: Dict):
        """更新僵尸状态"""
        scene = game_state['scene_manager'].current_scene
        
        # 冰冻效果
        if self.state == "frozen":
            self.freeze_timer -= dt
            if self.freeze_timer <= 0:
                self.state = "walking"
            return
        
        # 检查是否遇到植物
        cell_rect = scene.get_cell_rect(self.row, int(self.col))
        for plant in game_state.get('plants', []):
            if plant.row == self.row:
                plant_rect = scene.get_cell_rect(plant.row, plant.col)
                if cell_rect.colliderect(plant_rect) and plant.health > 0:
                    # 吃植物
                    self.state = "eating"
                    current_time = game_state.get('time', 0)
                    if current_time - self.last_attack_time >= self.attack_interval:
                        self.last_attack_time = current_time
                        if plant.take_damage(self.damage):
                            # 植物死亡
                            pass
                    return
        
        # 移动
        self.state = "walking"
        self.col -= self.speed * dt / scene.cell_width
        
        # 检查是否到达左侧
        if self.col < 0:
            game_state['zombies_reached_end'] = True
    
    def draw(self, surface: pygame.Surface, scene_manager: SceneManager):
        """绘制僵尸"""
        rect = scene_manager.current_scene.get_cell_rect(self.row, int(max(0, self.col)))
        
        if self.image:
            surface.blit(self.image, rect.topleft)
        else:
            # 默认绘制
            pygame.draw.rect(surface, (100, 200, 100), rect)
        
        # 冰冻效果
        if self.state == "frozen":
            overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            overlay.fill((100, 100, 255, 100))
            surface.blit(overlay, rect.topleft)
        
        # 血条
        if self.health < self.max_health:
            bar_width = rect.width
            bar_height = 4
            health_ratio = self.health / self.max_health
            
            pygame.draw.rect(surface, (50, 50, 50), 
                           (rect.x, rect.y - 6, bar_width, bar_height))
            pygame.draw.rect(surface, (255, 0, 0), 
                           (rect.x, rect.y - 6, int(bar_width * health_ratio), bar_height))
    
    def take_damage(self, damage: int):
        """受到伤害"""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            return True
        return False
    
    def apply_freeze(self, duration: float):
        """应用冰冻效果"""
        self.state = "frozen"
        self.freeze_timer = duration


class Game:
    """
    游戏主逻辑类
    管理游戏状态、实体、碰撞和渲染
    """
    
    def __init__(self, level_id: int = 1):
        print("[Game] 初始化游戏...")
        
        # 核心管理器
        self.scene_manager = get_scene_manager()
        self.level_manager = get_level_manager()
        self.zombie_factory = get_zombie_factory()
        
        # 游戏状态
        self.level_id = level_id
        self.level_config = self.level_manager.get_level_config(level_id)
        self.scene_type = self.level_config['scene_type']
        
        # 设置场景
        self.scene_manager.set_scene(self.scene_type)
        
        # 实体列表
        self.plants: List[Plant] = []
        self.zombies: List[Zombie] = []
        self.projectiles: List[Dict] = []
        self.suns: List[Dict] = []
        
        # 游戏数据
        self.sun_count = 50
        self.selected_plant: Optional[str] = None
        self.game_time = 0.0
        self.zombies_killed = 0
        self.zombies_reached_end = False
        self.is_paused = False
        self.is_game_over = False
        self.has_won = False
        
        # 生成器状态
        self.zombie_spawn_timer = 0.0
        self.sun_spawn_timer = 0.0
        
        # UI 状态
        self.shovel_selected = False
        self.card_cooldowns: Dict[str, float] = {}
        
        # 资源加载
        self._load_resources()
        
        print(f"[Game] 关卡 {level_id} 初始化完成")
    
    def _load_resources(self):
        """加载游戏资源"""
        # 这里应该加载实际的图片资源
        # 暂时使用占位色块
        self.plant_images: Dict[str, pygame.Surface] = {}
        self.zombie_images: Dict[str, pygame.Surface] = {}
        
        # 创建占位图片
        for plant_type in ["sunflower", "peashooter"]:
            surf = pygame.Surface((60, 80))
            surf.fill((0, 255, 0) if plant_type == "sunflower" else (0, 200, 0))
            self.plant_images[plant_type] = surf
        
        for zombie_type in ["normal", "conehead", "buckethead"]:
            surf = pygame.Surface((60, 80))
            surf.fill((100, 200, 100))
            self.zombie_images[zombie_type] = surf
    
    def handle_event(self, event: pygame.event.Event):
        """处理输入事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键
                self._handle_left_click(pygame.mouse.get_pos())
            elif event.button == 3:  # 右键
                self.shovel_selected = False
                self.selected_plant = None
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.is_paused = not self.is_paused
            elif event.key == pygame.K_s:
                self.shovel_selected = True
                self.selected_plant = None
    
    def _handle_left_click(self, pos: Tuple[int, int]):
        """处理左键点击"""
        # 检查是否点击了卡片栏
        card_y = 550
        if pos[1] < card_y + 60:
            # 卡片选择逻辑（简化）
            if 50 < pos[0] < 130:
                self.selected_plant = "sunflower"
                self.shovel_selected = False
            elif 140 < pos[0] < 220:
                self.selected_plant = "peashooter"
                self.shovel_selected = False
            return
        
        # 检查是否点击了游戏区域
        grid_pos = self.scene_manager.get_click_grid_pos(pos)
        if grid_pos:
            row, col = grid_pos
            
            if self.shovel_selected:
                # 铲子移除植物
                for plant in self.plants[:]:
                    if plant.row == row and plant.col == col:
                        self.plants.remove(plant)
                        break
                self.shovel_selected = False
            elif self.selected_plant:
                # 种植植物
                cost = 50 if self.selected_plant == "sunflower" else 100
                if self.sun_count >= cost:
                    # 检查位置是否为空
                    if not any(p.row == row and p.col == col for p in self.plants):
                        self.sun_count -= cost
                        if self.selected_plant == "sunflower":
                            self.plants.append(Sunflower(row, col))
                        elif self.selected_plant == "peashooter":
                            self.plants.append(Peashooter(row, col))
                        self.selected_plant = None
    
    def update(self, dt: float):
        """更新游戏状态"""
        if self.is_paused or self.is_game_over:
            return
        
        self.game_time += dt
        
        # 更新场景
        self.scene_manager.update(dt)
        
        # 生成掉落阳光
        self.sun_spawn_timer += dt
        if self.sun_spawn_timer >= 10.0:  # 每 10 秒生成一个
            self.sun_spawn_timer = 0.0
            self.scene_manager.spawn_falling_sun()
        
        # 生成僵尸
        self._spawn_zombies(dt)
        
        # 更新植物
        game_state = {
            'time': self.game_time,
            'scene_manager': self.scene_manager,
            'zombies': self.zombies,
            'plants': self.plants,
            'suns_to_spawn': []
        }
        
        for plant in self.plants:
            plant.update(dt, game_state)
        
        # 添加植物产生的阳光
        for sun_data in game_state.get('suns_to_spawn', []):
            self.suns.append({
                **sun_data,
                'timer': 0.0,
                'lifetime': 8.0
            })
        
        # 更新僵尸
        for zombie in self.zombies[:]:
            zombie.update(dt, game_state)
            if zombie.health <= 0:
                self.zombies.remove(zombie)
                self.zombies_killed += 1
        
        # 更新投射物
        self._update_projectiles(dt)
        
        # 更新阳光
        self._update_suns(dt)
        
        # 检查胜利/失败条件
        self._check_game_state()
    
    def _spawn_zombies(self, dt: float):
        """生成僵尸"""
        self.zombie_spawn_timer += dt
        
        spawn_interval = max(2.0, 10.0 - self.game_time / 30)  # 随时间缩短间隔
        
        if self.zombie_spawn_timer >= spawn_interval:
            self.zombie_spawn_timer = 0.0
            
            # 根据关卡配置生成僵尸
            max_zombies = min(5 + int(self.game_time / 20), 10)
            
            if len(self.zombies) < max_zombies:
                row = random.randint(0, self.scene_manager.current_scene.grid_rows - 1)
                zombie_type = self.zombie_factory.get_available_types(self.level_id)
                zombie = Zombie(row, random.choice(zombie_type))
                self.zombies.append(zombie)
    
    def _update_projectiles(self, dt: float):
        """更新投射物"""
        scene = self.scene_manager.current_scene
        
        for proj in self.projectiles[:]:
            proj['x'] += proj['speed'] * dt
            
            # 检查是否击中僵尸
            hit = False
            for zombie in self.zombies:
                if zombie.row == proj['row']:
                    zombie_rect = scene.get_cell_rect(zombie.row, int(max(0, zombie.col)))
                    if zombie_rect.left <= proj['x'] <= zombie_rect.right:
                        zombie.take_damage(proj['damage'])
                        if proj['type'] == 'ice_pea':
                            zombie.apply_freeze(2.0)
                        hit = True
                        break
            
            # 移除出界的投射物
            if hit or proj['x'] > SCREEN_WIDTH:
                self.projectiles.remove(proj)
    
    def _update_suns(self, dt: float):
        """更新阳光"""
        for sun in self.suns[:]:
            sun['timer'] += dt
            if sun['timer'] >= sun['lifetime']:
                self.suns.remove(sun)
    
    def _check_game_state(self):
        """检查游戏状态"""
        # 失败条件：僵尸到达左侧
        if self.zombies_reached_end:
            self.is_game_over = True
            self.has_won = False
            return
        
        # 胜利条件：生存时间达到要求或击杀足够僵尸
        required_kills = self.level_config.get('required_kills', 0)
        survival_time = self.level_config.get('survival_time', 0)
        
        if required_kills > 0 and self.zombies_killed >= required_kills:
            self.is_game_over = True
            self.has_won = True
        elif survival_time > 0 and self.game_time >= survival_time:
            self.is_game_over = True
            self.has_won = True
    
    def draw(self, surface: pygame.Surface):
        """绘制游戏画面"""
        # 绘制场景
        self.scene_manager.draw(surface)
        
        # 绘制植物
        for plant in self.plants:
            plant.draw(surface, self.scene_manager)
        
        # 绘制僵尸
        for zombie in self.zombies:
            zombie.draw(surface, self.scene_manager)
        
        # 绘制投射物
        for proj in self.projectiles:
            pygame.draw.circle(surface, (0, 255, 0), 
                             (int(proj['x']), int(proj['y'])), 8)
        
        # 绘制阳光
        for sun in self.suns:
            sun_rect = pygame.Rect(sun['x'] - 25, sun['y'], 50, 50)
            pygame.draw.circle(surface, (255, 255, 0), sun_rect.center, 20)
            pygame.draw.circle(surface, (255, 255, 200), sun_rect.center, 15)
        
        # 绘制 UI
        self._draw_ui(surface)
        
        # 绘制暂停/游戏结束覆盖层
        if self.is_paused:
            self._draw_overlay(surface, "暂停", "按 ESC 继续")
        elif self.is_game_over:
            if self.has_won:
                self._draw_overlay(surface, "胜利!", "关卡完成")
            else:
                self._draw_overlay(surface, "游戏结束", "僵尸吃掉了你的脑子!")
    
    def _draw_ui(self, surface: pygame.Surface):
        """绘制 UI"""
        # 阳光计数
        font = pygame.font.SysFont('Arial', 24, bold=True)
        sun_text = font.render(f"☀️ {self.sun_count}", True, (255, 255, 0))
        surface.blit(sun_text, (10, 10))
        
        # 卡片栏
        card_y = 550
        pygame.draw.rect(surface, (100, 100, 100), (0, card_y, SCREEN_WIDTH, 70))
        
        # 向日葵卡片
        sunflower_cost = 50
        rect1 = pygame.Rect(50, card_y + 5, 75, 60)
        color1 = (100, 255, 100) if self.sun_count >= sunflower_cost else (100, 100, 100)
        pygame.draw.rect(surface, color1, rect1)
        pygame.draw.rect(surface, (255, 255, 255), rect1, 2)
        text1 = font.render(f"${sunflower_cost}", True, (0, 0, 0))
        surface.blit(text1, (rect1.x + 5, rect1.y + 35))
        
        # 豌豆射手卡片
        peashooter_cost = 100
        rect2 = pygame.Rect(140, card_y + 5, 75, 60)
        color2 = (100, 255, 100) if self.sun_count >= peashooter_cost else (100, 100, 100)
        pygame.draw.rect(surface, color2, rect2)
        pygame.draw.rect(surface, (255, 255, 255), rect2, 2)
        text2 = font.render(f"${peashooter_cost}", True, (0, 0, 0))
        surface.blit(text2, (rect2.x + 5, rect2.y + 35))
        
        # 铲子
        shovel_rect = pygame.Rect(250, card_y + 5, 60, 60)
        shovel_color = (255, 100, 100) if self.shovel_selected else (150, 150, 150)
        pygame.draw.rect(surface, shovel_color, shovel_rect)
        pygame.draw.rect(surface, (255, 255, 255), shovel_rect, 2)
        shovel_text = font.render("🔧", True, (0, 0, 0))
        surface.blit(shovel_text, (shovel_rect.x + 20, rect2.y + 15))
        
        # 关卡信息
        level_text = font.render(f"关卡：{self.level_id}", True, (255, 255, 255))
        surface.blit(level_text, (SCREEN_WIDTH - 150, 10))
        
        kill_text = font.render(f"击杀：{self.zombies_killed}", True, (255, 255, 255))
        surface.blit(kill_text, (SCREEN_WIDTH - 150, 40))
    
    def _draw_overlay(self, surface: pygame.Surface, title: str, subtitle: str):
        """绘制覆盖层"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        font_large = pygame.font.SysFont('Arial', 48, bold=True)
        font_small = pygame.font.SysFont('Arial', 24)
        
        title_text = font_large.render(title, True, (255, 255, 255))
        subtitle_text = font_small.render(subtitle, True, (200, 200, 200))
        
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        
        surface.blit(title_text, title_rect)
        surface.blit(subtitle_text, subtitle_rect)
    
    def collect_sun(self, pos: Tuple[int, int]) -> bool:
        """收集阳光"""
        for i, sun in enumerate(self.suns):
            sun_rect = pygame.Rect(sun['x'] - 25, sun['y'] - 25, 50, 50)
            if sun_rect.collidepoint(pos):
                self.sun_count += sun['value']
                self.suns.pop(i)
                return True
        return False
    
    def run(self):
        """运行游戏主循环"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            dt = clock.tick(60) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        # 尝试收集阳光
                        if not self.collect_sun(pygame.mouse.get_pos()):
                            self.handle_event(event)
                    else:
                        self.handle_event(event)
                else:
                    self.handle_event(event)
            
            self.update(dt)
            
            # 清屏
            SCREEN.fill((0, 0, 0))
            
            # 绘制
            self.draw(SCREEN)
            
            # 显示 FPS
            fps_text = pygame.font.SysFont('Arial', 16).render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
            SCREEN.blit(fps_text, (10, SCREEN_HEIGHT - 20))
            
            pygame.display.flip()
        
        return self.has_won


# 全局游戏实例访问
_current_game: Optional[Game] = None


def get_current_game() -> Optional[Game]:
    """获取当前游戏实例"""
    return _current_game


if __name__ == "__main__":
    # 测试代码
    pygame.init()
    SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Game Test")
    
    game = Game(level_id=1)
    result = game.run()
    
    print(f"游戏结果：{'胜利' if result else '失败'}")
    pygame.quit()
