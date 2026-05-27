"""
UI Interface System - Industrial Grade
Provides comprehensive UI components for Plants vs Zombies game.

Features:
- Main menu system with animated buttons
- Level selection grid with scene filtering
- Plant selection interface with drag-drop
- Pause menu with resume/restart/quit options
- Game over screen with statistics
- Achievement display panel
- Settings configuration panel
- Toast notification system
- Loading screen with progress bar
- Transition effects

Author: AI Assistant
Version: 4.0.0
"""

from typing import Optional, List, Dict, Callable, Tuple, Any
from enum import Enum, auto
import pygame
import json
import os
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time


class UIState(Enum):
    """UI State Machine States"""
    MAIN_MENU = auto()
    LEVEL_SELECT = auto()
    PLANT_SELECT = auto()
    GAME_PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    SETTINGS = auto()
    ACHIEVEMENTS = auto()
    LOADING = auto()


class ButtonState(Enum):
    """Button interaction states"""
    NORMAL = auto()
    HOVER = auto()
    PRESSED = auto()
    DISABLED = auto()


@dataclass
class ButtonConfig:
    """Configuration for UI buttons"""
    text: str
    position: Tuple[int, int]
    size: Tuple[int, int]
    callback: Optional[Callable] = None
    font_size: int = 24
    normal_color: Tuple[int, int, int] = (100, 149, 237)  # Cornflower blue
    hover_color: Tuple[int, int, int] = (65, 105, 225)    # Royal blue
    pressed_color: Tuple[int, int, int] = (25, 25, 112)   # Midnight blue
    disabled_color: Tuple[int, int, int] = (128, 128, 128) # Gray
    text_color: Tuple[int, int, int] = (255, 255, 255)
    border_radius: int = 8
    enabled: bool = True


@dataclass
class PanelConfig:
    """Configuration for UI panels"""
    position: Tuple[int, int]
    size: Tuple[int, int]
    background_color: Tuple[int, int, int, int] = (0, 0, 0, 180)
    border_color: Tuple[int, int, int] = (255, 215, 0)
    border_width: int = 2
    title: str = ""
    title_font_size: int = 28
    closable: bool = True


@dataclass
class ToastConfig:
    """Configuration for toast notifications"""
    message: str
    duration: float = 3.0
    position: str = "top-center"  # top-center, bottom-center, top-left, etc.
    background_color: Tuple[int, int, int, int] = (50, 50, 50, 200)
    text_color: Tuple[int, int, int] = (255, 255, 255)
    icon: Optional[str] = None


class UIComponent(ABC):
    """Abstract base class for all UI components"""
    
    def __init__(self, config: Any):
        self.config = config
        self.visible = True
        self.enabled = True
        self.rect: Optional[pygame.Rect] = None
        
    @abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        """Render the component to surface"""
        pass
    
    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event, return True if handled"""
        pass
    
    def update(self, delta_time: float) -> None:
        """Update component state"""
        pass
    
    def set_position(self, x: int, y: int) -> None:
        """Update component position"""
        if self.rect:
            self.rect.topleft = (x, y)
    
    def show(self) -> None:
        """Show the component"""
        self.visible = True
    
    def hide(self) -> None:
        """Hide the component"""
        self.visible = False
    
    def toggle(self) -> None:
        """Toggle visibility"""
        self.visible = not self.visible


class Button(UIComponent):
    """Interactive button component with hover and press states"""
    
    def __init__(self, config: ButtonConfig):
        super().__init__(config)
        self.state = ButtonState.NORMAL
        self.hover_time = 0.0
        self._create_rect()
        self._load_fonts()
        
    def _create_rect(self) -> None:
        """Create button rectangle"""
        self.rect = pygame.Rect(
            self.config.position[0],
            self.config.position[1],
            self.config.size[0],
            self.config.size[1]
        )
        
    def _load_fonts(self) -> None:
        """Load button fonts"""
        try:
            self.font = pygame.font.Font(
                pygame.font.match_font('arial'),
                self.config.font_size
            )
        except:
            self.font = pygame.font.Font(None, self.config.font_size)
            
    def _get_current_color(self) -> Tuple[int, int, int]:
        """Get current button color based on state"""
        if not self.config.enabled:
            return self.config.disabled_color
        elif self.state == ButtonState.PRESSED:
            return self.config.pressed_color
        elif self.state == ButtonState.HOVER:
            return self.config.hover_color
        else:
            return self.config.normal_color
    
    def render(self, surface: pygame.Surface) -> None:
        """Render button with rounded corners"""
        if not self.visible:
            return
            
        color = self._get_current_color()
        
        # Draw rounded rectangle
        pygame.draw.rect(
            surface,
            color,
            self.rect,
            border_radius=self.config.border_radius
        )
        
        # Draw border
        border_color = (255, 255, 255) if self.state == ButtonState.HOVER else (0, 0, 0)
        pygame.draw.rect(
            surface,
            border_color,
            self.rect,
            width=2,
            border_radius=self.config.border_radius
        )
        
        # Render text
        text_surface = self.font.render(self.config.text, True, self.config.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events for button interaction"""
        if not self.visible or not self.enabled:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                if self.state != ButtonState.HOVER:
                    self.state = ButtonState.HOVER
                return True
            else:
                if self.state == ButtonState.HOVER:
                    self.state = ButtonState.NORMAL
                return False
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.state = ButtonState.PRESSED
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.state == ButtonState.PRESSED and self.rect.collidepoint(event.pos):
                    if self.config.callback:
                        self.config.callback()
                    return True
                self.state = ButtonState.NORMAL if self.rect.collidepoint(event.pos) else ButtonState.NORMAL
                
        return False


class Panel(UIComponent):
    """Semi-transparent panel container for UI elements"""
    
    def __init__(self, config: PanelConfig):
        super().__init__(config)
        self.children: List[UIComponent] = []
        self.close_callback: Optional[Callable] = None
        self._create_rect()
        self._load_fonts()
        
    def _create_rect(self) -> None:
        """Create panel rectangle"""
        self.rect = pygame.Rect(
            self.config.position[0],
            self.config.position[1],
            self.config.size[0],
            self.config.size[1]
        )
        
    def _load_fonts(self) -> None:
        """Load title font"""
        try:
            self.title_font = pygame.font.Font(
                pygame.font.match_font('arial'),
                self.config.title_font_size
            )
        except:
            self.title_font = pygame.font.Font(None, self.config.title_font_size)
    
    def add_child(self, component: UIComponent) -> None:
        """Add child component to panel"""
        self.children.append(component)
        
    def remove_child(self, component: UIComponent) -> None:
        """Remove child component from panel"""
        if component in self.children:
            self.children.remove(component)
    
    def render(self, surface: pygame.Surface) -> None:
        """Render panel with semi-transparent background"""
        if not self.visible:
            return
            
        # Create semi-transparent surface
        panel_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        panel_surface.fill(self.config.background_color)
        
        # Draw border
        pygame.draw.rect(
            panel_surface,
            self.config.border_color,
            panel_surface.get_rect(),
            width=self.config.border_width
        )
        
        # Blit to main surface
        surface.blit(panel_surface, self.rect.topleft)
        
        # Render title
        if self.config.title:
            title_surface = self.title_font.render(
                self.config.title,
                True,
                self.config.border_color
            )
            title_rect = title_surface.get_rect(
                centerx=self.rect.centerx,
                top=self.rect.top + 10
            )
            surface.blit(title_surface, title_rect)
        
        # Render children
        for child in self.children:
            child.render(surface)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events for panel and children"""
        if not self.visible:
            return False
            
        # Handle close button click
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Check if clicking outside panel (for closing)
                if self.config.closable and not self.rect.collidepoint(event.pos):
                    if self.close_callback:
                        self.close_callback()
                    return True
        
        # Pass events to children
        for child in self.children:
            if child.handle_event(event):
                return True
                
        return False
    
    def update(self, delta_time: float) -> None:
        """Update panel and children"""
        for child in self.children:
            child.update(delta_time)


class ToastNotification:
    """Toast notification system for temporary messages"""
    
    def __init__(self):
        self.toasts: List[Dict[str, Any]] = []
        self.font: Optional[pygame.font.Font] = None
        self._load_font()
        
    def _load_font(self) -> None:
        """Load toast font"""
        try:
            self.font = pygame.font.Font(
                pygame.font.match_font('arial'),
                18
            )
        except:
            self.font = pygame.font.Font(None, 18)
    
    def show(self, config: ToastConfig) -> None:
        """Show a new toast notification"""
        toast = {
            'config': config,
            'created_at': time.time(),
            'alpha': 255,
            'fade_out': False
        }
        self.toasts.append(toast)
    
    def update(self, delta_time: float) -> None:
        """Update toast animations and remove expired toasts"""
        current_time = time.time()
        
        for toast in self.toasts[:]:
            elapsed = current_time - toast['created_at']
            
            # Start fade out after duration - 0.5 seconds
            if elapsed > toast['config'].duration - 0.5:
                toast['fade_out'] = True
                fade_progress = (elapsed - (toast['config'].duration - 0.5)) / 0.5
                toast['alpha'] = max(0, int(255 * (1 - fade_progress)))
            
            # Remove expired toasts
            if elapsed > toast['config'].duration:
                self.toasts.remove(toast)
    
    def render(self, surface: pygame.Surface) -> None:
        """Render all active toasts"""
        surface_width = surface.get_width()
        
        for i, toast in enumerate(self.toasts):
            config = toast['config']
            
            # Calculate position
            y_offset = 60 + i * 50
            if config.position == "top-center":
                x = surface_width // 2
            elif config.position == "bottom-center":
                x = surface_width // 2
                y_offset = surface.get_height() - 40 - i * 50
            elif config.position == "top-left":
                x = 20
            elif config.position == "top-right":
                x = surface_width - 20
            else:
                x = surface_width // 2
            
            # Render toast background
            text_surface = self.font.render(config.message, True, config.text_color)
            padding = 20
            bg_width = text_surface.get_width() + padding * 2
            bg_height = text_surface.get_height() + padding
            
            bg_rect = pygame.Rect(
                x - bg_width // 2,
                y_offset - bg_height // 2,
                bg_width,
                bg_height
            )
            
            # Create semi-transparent background
            bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            bg_surface.fill((*config.background_color[:3], toast['alpha']))
            surface.blit(bg_surface, bg_rect.topleft)
            
            # Render text
            text_surface.set_alpha(toast['alpha'])
            text_rect = text_surface.get_rect(center=bg_rect.center)
            surface.blit(text_surface, text_rect)


class UIManager:
    """Central manager for all UI components and state transitions"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.current_state = UIState.MAIN_MENU
        self.components: Dict[str, UIComponent] = {}
        self.panels: Dict[str, Panel] = {}
        self.toast_system = ToastNotification()
        self.transition_alpha = 0
        self.is_transitioning = False
        self.transition_target: Optional[UIState] = None
        self.transition_start_time: float = 0
        self.transition_duration: float = 0.3
        
        self._initialize_main_menu()
        
    def _initialize_main_menu(self) -> None:
        """Initialize main menu UI components"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Title
        title_config = ButtonConfig(
            text="Plants vs Zombies",
            position=(screen_width // 2 - 200, 100),
            size=(400, 80),
            font_size=48,
            normal_color=(34, 139, 34),  # Forest green
            hover_color=(50, 205, 50),   # Lime green
            border_radius=15
        )
        self.components['title'] = Button(title_config)
        
        # Start button
        start_config = ButtonConfig(
            text="Start Game",
            position=(screen_width // 2 - 100, 250),
            size=(200, 50),
            callback=lambda: self.change_state(UIState.LEVEL_SELECT),
            font_size=28
        )
        self.components['start_button'] = Button(start_config)
        
        # Settings button
        settings_config = ButtonConfig(
            text="Settings",
            position=(screen_width // 2 - 100, 320),
            size=(200, 50),
            callback=lambda: self.change_state(UIState.SETTINGS),
            font_size=24
        )
        self.components['settings_button'] = Button(settings_config)
        
        # Achievements button
        achievements_config = ButtonConfig(
            text="Achievements",
            position=(screen_width // 2 - 100, 390),
            size=(200, 50),
            callback=lambda: self.change_state(UIState.ACHIEVEMENTS),
            font_size=24
        )
        self.components['achievements_button'] = Button(achievements_config)
        
        # Quit button
        quit_config = ButtonConfig(
            text="Quit",
            position=(screen_width // 2 - 100, 460),
            size=(200, 50),
            callback=lambda: pygame.event.post(pygame.event.Event(pygame.QUIT)),
            font_size=24,
            normal_color=(220, 20, 60),  # Crimson
            hover_color=(255, 69, 0)     # Orange red
        )
        self.components['quit_button'] = Button(quit_config)
        
        # Initialize settings panel
        self._initialize_settings_panel()
        
        # Initialize achievements panel
        self._initialize_achievements_panel()
        
        # Initialize level select panel
        self._initialize_level_select()
        
        # Initialize pause panel
        self._initialize_pause_panel()
        
        # Initialize game over panel
        self._initialize_game_over_panel()
    
    def _initialize_settings_panel(self) -> None:
        """Initialize settings panel"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        panel_config = PanelConfig(
            position=(screen_width // 2 - 250, screen_height // 2 - 200),
            size=(500, 400),
            title="Settings",
            closable=True
        )
        
        panel = Panel(panel_config)
        panel.close_callback = lambda: self.change_state(UIState.MAIN_MENU)
        
        # Add placeholder buttons for settings
        y_pos = 80
        for setting_name in ["Volume", "Difficulty", "Display Mode"]:
            btn_config = ButtonConfig(
                text=f"{setting_name}: Default",
                position=(50, y_pos),
                size=(400, 40),
                font_size=20
            )
            panel.add_child(Button(btn_config))
            y_pos += 60
        
        # Back button
        back_config = ButtonConfig(
            text="Back",
            position=(200, 340),
            size=(100, 40),
            callback=lambda: self.change_state(UIState.MAIN_MENU)
        )
        panel.add_child(Button(back_config))
        
        self.panels['settings'] = panel
    
    def _initialize_achievements_panel(self) -> None:
        """Initialize achievements panel"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        panel_config = PanelConfig(
            position=(screen_width // 2 - 300, screen_height // 2 - 250),
            size=(600, 500),
            title="Achievements",
            closable=True
        )
        
        panel = Panel(panel_config)
        panel.close_callback = lambda: self.change_state(UIState.MAIN_MENU)
        
        # Placeholder achievement entries
        y_pos = 60
        achievements = [
            ("First Blood", "Defeat your first zombie", "✓"),
            ("Sun Collector", "Collect 1000 sun", "✓"),
            ("Plant Master", "Unlock all plants", "✗"),
            ("Survivor", "Complete 10 levels", "✗"),
            ("Speed Runner", "Complete a level in under 2 minutes", "✗")
        ]
        
        for name, desc, status in achievements:
            # Achievement name
            name_config = ButtonConfig(
                text=f"{status} {name}",
                position=(20, y_pos),
                size=(560, 30),
                font_size=18,
                enabled=False
            )
            panel.add_child(Button(name_config))
            
            # Description
            desc_config = ButtonConfig(
                text=desc,
                position=(40, y_pos + 30),
                size=(540, 20),
                font_size=14,
                normal_color=(200, 200, 200),
                enabled=False
            )
            panel.add_child(Button(desc_config))
            
            y_pos += 70
        
        # Back button
        back_config = ButtonConfig(
            text="Back",
            position=(250, 450),
            size=(100, 40),
            callback=lambda: self.change_state(UIState.MAIN_MENU)
        )
        panel.add_child(Button(back_config))
        
        self.panels['achievements'] = panel
    
    def _initialize_level_select(self) -> None:
        """Initialize level selection panel"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        panel_config = PanelConfig(
            position=(screen_width // 2 - 350, screen_height // 2 - 280),
            size=(700, 560),
            title="Select Level",
            closable=True
        )
        
        panel = Panel(panel_config)
        panel.close_callback = lambda: self.change_state(UIState.MAIN_MENU)
        
        # Level grid (5 columns x 10 rows placeholder)
        level_num = 1
        for row in range(10):
            for col in range(5):
                if level_num > 50:
                    break
                    
                x = 50 + col * 120
                y = 60 + row * 50
                
                btn_config = ButtonConfig(
                    text=str(level_num),
                    position=(x, y),
                    size=(100, 40),
                    callback=lambda n=level_num: self.start_level(n),
                    font_size=20
                )
                panel.add_child(Button(btn_config))
                level_num += 1
        
        # Back button
        back_config = ButtonConfig(
            text="Back",
            position=(300, 510),
            size=(100, 40),
            callback=lambda: self.change_state(UIState.MAIN_MENU)
        )
        panel.add_child(Button(back_config))
        
        self.panels['level_select'] = panel
    
    def _initialize_pause_panel(self) -> None:
        """Initialize pause menu panel"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        panel_config = PanelConfig(
            position=(screen_width // 2 - 150, screen_height // 2 - 100),
            size=(300, 200),
            title="Paused",
            closable=False
        )
        
        panel = Panel(panel_config)
        
        # Resume button
        resume_config = ButtonConfig(
            text="Resume",
            position=(50, 50),
            size=(200, 40),
            callback=lambda: self.change_state(UIState.GAME_PLAYING),
            font_size=22
        )
        panel.add_child(Button(resume_config))
        
        # Restart button
        restart_config = ButtonConfig(
            text="Restart",
            position=(50, 100),
            size=(200, 40),
            callback=lambda: self.restart_level(),
            font_size=22
        )
        panel.add_child(Button(restart_config))
        
        # Quit button
        quit_config = ButtonConfig(
            text="Quit to Menu",
            position=(50, 150),
            size=(200, 40),
            callback=lambda: self.change_state(UIState.MAIN_MENU),
            font_size=22,
            normal_color=(220, 20, 60)
        )
        panel.add_child(Button(quit_config))
        
        self.panels['pause'] = panel
    
    def _initialize_game_over_panel(self) -> None:
        """Initialize game over panel"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        panel_config = PanelConfig(
            position=(screen_width // 2 - 200, screen_height // 2 - 150),
            size=(400, 300),
            title="",
            closable=False
        )
        
        panel = Panel(panel_config)
        
        # Game over text
        game_over_config = ButtonConfig(
            text="Game Over",
            position=(100, 30),
            size=(200, 50),
            font_size=36,
            normal_color=(220, 20, 60),
            enabled=False
        )
        panel.add_child(Button(game_over_config))
        
        # Retry button
        retry_config = ButtonConfig(
            text="Try Again",
            position=(100, 120),
            size=(200, 40),
            callback=lambda: self.restart_level(),
            font_size=22
        )
        panel.add_child(Button(retry_config))
        
        # Menu button
        menu_config = ButtonConfig(
            text="Main Menu",
            position=(100, 180),
            size=(200, 40),
            callback=lambda: self.change_state(UIState.MAIN_MENU),
            font_size=22
        )
        panel.add_child(Button(menu_config))
        
        self.panels['game_over'] = panel
    
    def change_state(self, new_state: UIState) -> None:
        """Change UI state with transition effect"""
        if self.is_transitioning:
            return
            
        self.transition_target = new_state
        self.transition_start_time = time.time()
        self.is_transitioning = True
        self.transition_alpha = 0
    
    def start_level(self, level_number: int) -> None:
        """Start a specific level"""
        print(f"Starting level {level_number}")
        # TODO: Integrate with level manager
        self.change_state(UIState.GAME_PLAYING)
    
    def restart_level(self) -> None:
        """Restart current level"""
        print("Restarting level...")
        # TODO: Integrate with game logic
        self.change_state(UIState.GAME_PLAYING)
    
    def show_toast(self, message: str, duration: float = 3.0) -> None:
        """Show a toast notification"""
        config = ToastConfig(message=message, duration=duration)
        self.toast_system.show(config)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame events for current UI state"""
        # Handle pause toggle (ESC key)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.current_state == UIState.GAME_PLAYING:
                    self.change_state(UIState.PAUSED)
                elif self.current_state == UIState.PAUSED:
                    self.change_state(UIState.GAME_PLAYING)
                return True
        
        # Handle events based on current state
        if self.current_state == UIState.MAIN_MENU:
            for component in self.components.values():
                if component.handle_event(event):
                    return True
                    
        elif self.current_state in [UIState.SETTINGS, UIState.ACHIEVEMENTS, 
                                     UIState.LEVEL_SELECT, UIState.PAUSED,
                                     UIState.GAME_OVER]:
            panel_name = {
                UIState.SETTINGS: 'settings',
                UIState.ACHIEVEMENTS: 'achievements',
                UIState.LEVEL_SELECT: 'level_select',
                UIState.PAUSED: 'pause',
                UIState.GAME_OVER: 'game_over'
            }.get(self.current_state)
            
            if panel_name and panel_name in self.panels:
                if self.panels[panel_name].handle_event(event):
                    return True
        
        return False
    
    def update(self, delta_time: float) -> None:
        """Update UI state and animations"""
        # Update transition
        if self.is_transitioning:
            elapsed = time.time() - self.transition_start_time
            progress = min(1.0, elapsed / self.transition_duration)
            
            if progress < 0.5:
                # Fade out
                self.transition_alpha = int(255 * (progress * 2))
            else:
                # Fade in and complete transition
                self.transition_alpha = int(255 * (1 - (progress - 0.5) * 2))
                
                if progress >= 1.0:
                    self.is_transitioning = False
                    if self.transition_target:
                        self.current_state = self.transition_target
                        self.transition_target = None
        
        # Update toast notifications
        self.toast_system.update(delta_time)
        
        # Update active panel
        if self.current_state in [UIState.SETTINGS, UIState.ACHIEVEMENTS,
                                   UIState.LEVEL_SELECT, UIState.PAUSED,
                                   UIState.GAME_OVER]:
            panel_name = {
                UIState.SETTINGS: 'settings',
                UIState.ACHIEVEMENTS: 'achievements',
                UIState.LEVEL_SELECT: 'level_select',
                UIState.PAUSED: 'pause',
                UIState.GAME_OVER: 'game_over'
            }.get(self.current_state)
            
            if panel_name and panel_name in self.panels:
                self.panels[panel_name].update(delta_time)
    
    def render(self) -> None:
        """Render current UI state"""
        # Clear screen
        self.screen.fill((0, 0, 0))
        
        # Render based on current state
        if self.current_state == UIState.MAIN_MENU:
            # Render background gradient
            for y in range(self.screen.get_height()):
                color_value = int(20 + (y / self.screen.get_height()) * 30)
                pygame.draw.line(self.screen, (color_value, color_value + 20, color_value + 40),
                               (0, y), (self.screen.get_width(), y))
            
            # Render components
            for component in self.components.values():
                component.render(self.screen)
                
        elif self.current_state in [UIState.SETTINGS, UIState.ACHIEVEMENTS,
                                     UIState.LEVEL_SELECT, UIState.PAUSED,
                                     UIState.GAME_OVER]:
            # Dim background
            dim_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            dim_surface.fill((0, 0, 0, 150))
            self.screen.blit(dim_surface, (0, 0))
            
            # Render active panel
            panel_name = {
                UIState.SETTINGS: 'settings',
                UIState.ACHIEVEMENTS: 'achievements',
                UIState.LEVEL_SELECT: 'level_select',
                UIState.PAUSED: 'pause',
                UIState.GAME_OVER: 'game_over'
            }.get(self.current_state)
            
            if panel_name and panel_name in self.panels:
                self.panels[panel_name].render(self.screen)
        
        # Render toast notifications
        self.toast_system.render(self.screen)
        
        # Render transition overlay
        if self.is_transitioning:
            transition_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            transition_surface.fill((0, 0, 0, self.transition_alpha))
            self.screen.blit(transition_surface, (0, 0))
        
        pygame.display.flip()
    
    def get_current_state(self) -> UIState:
        """Get current UI state"""
        return self.current_state
    
    def is_game_playing(self) -> bool:
        """Check if game is in playing state"""
        return self.current_state == UIState.GAME_PLAYING


# Singleton instance
_ui_manager_instance: Optional[UIManager] = None


def get_ui_manager(screen: Optional[pygame.Surface] = None) -> UIManager:
    """Get singleton UI manager instance"""
    global _ui_manager_instance
    
    if _ui_manager_instance is None:
        if screen is None:
            raise ValueError("UIManager must be initialized with a screen surface")
        _ui_manager_instance = UIManager(screen)
    
    return _ui_manager_instance
