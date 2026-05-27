#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
植物大战僵尸游戏主类
工业级重构版本 - 核心游戏逻辑
"""

import pygame
import sys
import os
from typing import Optional, List, Dict, Any
from enum import Enum

# 导入游戏系统模块
from .level_manager import LevelManager
from .zombie_factory import ZombieFactory, ZombieSpawner
from .scene_manager import SceneManager
from .save_system import SaveSystem
from .particle_system import ParticleSystem
from .audio_manager import AudioManager
from .ui_components import UIManager
from .plant_database import PlantDatabase
from .zombie_database import ZombieDatabase
from .shop_system import ShopSystem
from .game_modes import GameMode, GameModeManager


class GameState(Enum):
    """游戏状态枚举"""
    MENU = "menu"
    LEVEL_SELECT = "level_select"
    PLANTING = "planting"  # 选卡界面
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    VICTORY = "victory"
    SHOP = "shop"
    ALMANAC = "almanac"  # 图鉴


class Pvz:
    """
    植物大战僵尸游戏主类
    
    负责管理游戏主循环、状态切换、系统初始化等核心功能
    """
    
    def __init__(self):
        """初始化游戏实例"""
        # 初始化 Pygame
        pygame.init()
        pygame.mixer.init()
        
        # 游戏窗口设置
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("植物大战僵尸 - 工业级重构版")
        
        # 时钟用于控制帧率
        self.clock = pygame.time.Clock()
        self.target_fps = 60
        
        # 游戏状态
        self.current_state = GameState.MENU
        self.running = True
        
        #  Delta Time 系统
        self.delta_time = 0.0
        self.last_frame_time = pygame.time.get_ticks()
        
        # 初始化所有子系统
        self._initialize_systems()
        
        # 加载配置和资源
        self._load_resources()
        
        # 打印初始化信息
        self._print_init_info()
    
    def _initialize_systems(self):
        """初始化所有游戏子系统"""
        # 存档系统
        self.save_system = SaveSystem()
        
        # 音频管理器
        self.audio_manager = AudioManager()
        
        # 粒子特效系统
        self.particle_system = ParticleSystem()
        
        # UI 管理器
        self.ui_manager = UIManager(self.screen)
        
        # 关卡管理器
        self.level_manager = LevelManager(self.save_system)
        
        # 场景管理器
        self.scene_manager = SceneManager(self.screen)
        
        # 僵尸工厂和生成器
        self.zombie_factory = ZombieFactory()
        self.zombie_spawner = ZombieSpawner(self.zombie_factory)
        
        # 数据库系统
        self.plant_database = PlantDatabase()
        self.zombie_database = ZombieDatabase()
        
        # 商店系统
        self.shop_system = ShopSystem(self.save_system)
        
        # 游戏模式管理器
        self.game_mode_manager = GameModeManager()
        
        # 游戏实体容器
        self.plants: List[Any] = []
        self.zombies: List[Any] = []
        self.projectiles: List[Any] = []
        self.sunflowers: List[Any] = []
        
        # 游戏资源
        self.sun_count = 50
        self.gold_count = 0
        self.selected_plant = None
        self.lawn_mowers: List[Any] = []
    
    def _load_resources(self):
        """加载游戏资源"""
        # 这里应该加载图片、音效等资源
        # 由于实际资源文件未提供，使用占位符
        pass
    
    def _print_init_info(self):
        """打印初始化信息"""
        print("[INFO] 游戏系统初始化完成")
        print(f"[INFO] 屏幕分辨率：{self.screen_width}x{self.screen_height}")
        print(f"[INFO] 目标帧率：{self.target_fps} FPS")
        print(f"[INFO] 当前状态：{self.current_state.value}")
    
    def _calculate_delta_time(self):
        """计算 Delta Time"""
        current_time = pygame.time.get_ticks()
        self.delta_time = (current_time - self.last_frame_time) / 1000.0
        self.last_frame_time = current_time
        
        # 限制最大 Delta Time，防止卡顿导致瞬移
        if self.delta_time > 0.1:
            self.delta_time = 0.1
    
    def _handle_events(self):
        """处理 Pygame 事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._handle_escape_key()
                elif event.key == pygame.K_p:
                    self._toggle_pause()
            
            # 将事件传递给 UI 管理器
            self.ui_manager.handle_event(event)
            
            # 根据当前状态处理特定事件
            if self.current_state == GameState.PLAYING:
                self._handle_playing_events(event)
    
    def _handle_escape_key(self):
        """处理 ESC 键按下"""
        if self.current_state == GameState.PLAYING:
            self.current_state = GameState.PAUSED
        elif self.current_state == GameState.PAUSED:
            self.current_state = GameState.PLAYING
        elif self.current_state in [GameState.GAME_OVER, GameState.VICTORY]:
            self.current_state = GameState.MENU
    
    def _toggle_pause(self):
        """切换暂停状态"""
        if self.current_state == GameState.PLAYING:
            self.current_state = GameState.PAUSED
        elif self.current_state == GameState.PAUSED:
            self.current_state = GameState.PLAYING
    
    def _handle_playing_events(self, event: pygame.event.Event):
        """处理游戏进行中的事件"""
        # 植物放置逻辑
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.selected_plant and self.sun_count >= self.selected_plant.sun_cost:
                self._try_place_plant(event.pos)
    
    def _try_place_plant(self, pos):
        """尝试放置植物"""
        # 实现植物放置逻辑
        pass
    
    def _update(self):
        """更新游戏逻辑"""
        # 更新 Delta Time
        self._calculate_delta_time()
        
        # 更新所有子系统
        self.particle_system.update(self.delta_time)
        self.audio_manager.update()
        self.ui_manager.update(self.delta_time)
        
        # 根据状态更新游戏逻辑
        if self.current_state == GameState.PLAYING:
            self._update_playing()
    
    def _update_playing(self):
        """更新游戏进行中的逻辑"""
        # 更新僵尸
        for zombie in self.zombies[:]:
            zombie.update(self.delta_time)
            if zombie.health <= 0:
                self.zombies.remove(zombie)
                self.gold_count += zombie.gold_reward
        
        # 更新植物
        for plant in self.plants[:]:
            plant.update(self.delta_time)
            if plant.health <= 0:
                self.plants.remove(plant)
        
        # 更新子弹
        for projectile in self.projectiles[:]:
            projectile.update(self.delta_time)
            if projectile.should_remove():
                self.projectiles.remove(projectile)
        
        # 僵尸生成
        self.zombie_spawner.update(self.delta_time, self.zombies)
        
        # 碰撞检测
        self._check_collisions()
        
        # 胜利/失败条件检测
        self._check_game_end_conditions()
    
    def _check_collisions(self):
        """碰撞检测"""
        # 简化的碰撞检测逻辑
        pass
    
    def _check_game_end_conditions(self):
        """检查游戏结束条件"""
        # 检查是否有僵尸到达左边界
        for zombie in self.zombies:
            if zombie.x <= 0:
                self.current_state = GameState.GAME_OVER
                self.audio_manager.play_sound("game_over")
                return
        
        # 检查是否所有僵尸都被消灭且生成完毕
        if self.zombie_spawner.is_wave_complete() and len(self.zombies) == 0:
            self.current_state = GameState.VICTORY
            self.audio_manager.play_sound("victory")
            self._handle_victory()
    
    def _handle_victory(self):
        """处理胜利逻辑"""
        # 发放奖励
        rewards = self.level_manager.complete_level()
        self.gold_count += rewards.get('gold', 0)
        
        # 保存进度
        self.save_system.save_game()
    
    def _render(self):
        """渲染游戏画面"""
        # 清空屏幕
        self.screen.fill((0, 0, 0))
        
        # 根据状态渲染不同内容
        if self.current_state == GameState.MENU:
            self._render_menu()
        elif self.current_state == GameState.PLAYING:
            self._render_playing()
        elif self.current_state == GameState.PAUSED:
            self._render_playing()
            self._render_pause_overlay()
        elif self.current_state == GameState.GAME_OVER:
            self._render_game_over()
        elif self.current_state == GameState.VICTORY:
            self._render_victory()
        
        # 渲染 UI
        self.ui_manager.render()
        
        # 渲染粒子特效
        self.particle_system.render(self.screen)
        
        # 更新显示
        pygame.display.flip()
    
    def _render_menu(self):
        """渲染主菜单"""
        # 渲染菜单背景
        self.scene_manager.render_background(self.screen, "menu")
        
        # 渲染菜单按钮
        self.ui_manager.draw_button("开始游戏", (640, 300))
        self.ui_manager.draw_button("图鉴", (640, 380))
        self.ui_manager.draw_button("商店", (640, 460))
        self.ui_manager.draw_button("退出", (640, 540))
    
    def _render_playing(self):
        """渲染游戏进行中画面"""
        # 渲染场景背景
        current_level = self.level_manager.get_current_level()
        self.scene_manager.render_background(self.screen, current_level.scene_type)
        
        # 渲染植物
        for plant in self.plants:
            plant.render(self.screen)
        
        # 渲染僵尸
        for zombie in self.zombies:
            zombie.render(self.screen)
        
        # 渲染子弹
        for projectile in self.projectiles:
            projectile.render(self.screen)
        
        # 渲染阳光
        # 渲染割草机
        # 渲染 UI（阳光数量、卡片栏等）
    
    def _render_pause_overlay(self):
        """渲染暂停遮罩层"""
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # 渲染暂停文字
        font = pygame.font.Font(None, 74)
        text = font.render("已暂停", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(text, text_rect)
    
    def _render_game_over(self):
        """渲染游戏结束画面"""
        self._render_playing()
        
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 74)
        text = font.render("游戏结束", True, (255, 0, 0))
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(text, text_rect)
    
    def _render_victory(self):
        """渲染胜利画面"""
        self._render_playing()
        
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 74)
        text = font.render("胜利!", True, (0, 255, 0))
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(text, text_rect)
    
    def run(self):
        """运行游戏主循环"""
        while self.running:
            # 处理事件
            self._handle_events()
            
            # 更新游戏逻辑
            self._update()
            
            # 渲染画面
            self._render()
            
            # 控制帧率
            self.clock.tick(self.target_fps)
        
        # 清理资源
        self._cleanup()
    
    def _cleanup(self):
        """清理游戏资源"""
        # 保存游戏进度
        self.save_system.save_game()
        
        # 关闭音频
        self.audio_manager.cleanup()
        
        # 退出 Pygame
        pygame.quit()
        print("[INFO] 游戏已正常退出")


# 导出主类
__all__ = ['Pvz', 'GameState']
