"""
专业UI组件库 - 工业级UI组件实现
包含按钮、文本框、进度条、对话框、列表等组件
"""

import pygame
import math
from typing import List, Tuple, Optional, Callable, Any
from enum import Enum


class Alignment(Enum):
    """对齐方式枚举"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class UIComponent:
    """UI组件基类"""
    
    def __init__(self, x: float, y: float, width: float, height: float):
        """
        初始化UI组件
        
        Args:
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
        """
        self.x: float = x
        self.y: float = y
        self.width: float = width
        self.height: float = height
        
        self.visible: bool = True
        self.enabled: bool = True
        self.hovered: bool = False
        self.focused: bool = False
        
        self.parent: Optional['UIComponent'] = None
        self.children: List['UIComponent'] = []
        
        self.on_click: Optional[Callable[[], None]] = None
        self.on_hover: Optional[Callable[[bool], None]] = None
    
    def update(self, mouse_pos: Tuple[int, int], mouse_down: bool) -> None:
        """
        更新组件状态
        
        Args:
            mouse_pos: 鼠标位置
            mouse_down: 鼠标是否按下
        """
        if not self.visible or not self.enabled:
            return
        
        # 检查鼠标悬停
        prev_hovered = self.hovered
        self.hovered = self._contains_point(mouse_pos)
        
        # 触发悬停事件
        if prev_hovered != self.hovered and self.on_hover:
            self.on_hover(self.hovered)
        
        # 检查点击
        if mouse_down and self.hovered and self.on_click:
            self.on_click()
        
        # 更新子组件
        for child in self.children:
            child.update(mouse_pos, mouse_down)
    
    def draw(self, screen: pygame.Surface) -> None:
        """
        绘制组件
        
        Args:
            screen: 绘制目标表面
        """
        if not self.visible:
            return
        
        self._draw_self(screen)
        
        # 绘制子组件
        for child in self.children:
            child.draw(screen)
    
    def _draw_self(self, screen: pygame.Surface) -> None:
        """绘制自身（由子类实现）"""
        pass
    
    def _contains_point(self, point: Tuple[int, int]) -> bool:
        """
        检查点是否在组件范围内
        
        Args:
            point: 点坐标
            
        Returns:
            是否在范围内
        """
        return (self.x <= point[0] <= self.x + self.width and
                self.y <= point[1] <= self.y + self.height)
    
    def add_child(self, child: 'UIComponent') -> None:
        """
        添加子组件
        
        Args:
            child: 子组件
        """
        child.parent = self
        # 转换为相对坐标
        child.x += self.x
        child.y += self.y
        self.children.append(child)
    
    def remove_child(self, child: 'UIComponent') -> None:
        """
        移除子组件
        
        Args:
            child: 子组件
        """
        if child in self.children:
            child.parent = None
            self.children.remove(child)
    
    def get_global_position(self) -> Tuple[float, float]:
        """
        获取全局坐标
        
        Returns:
            全局X, Y坐标
        """
        if self.parent:
            parent_x, parent_y = self.parent.get_global_position()
            return parent_x + self.x, parent_y + self.y
        return self.x, self.y
    
    def set_position(self, x: float, y: float) -> None:
        """
        设置位置
        
        Args:
            x: X坐标
            y: Y坐标
        """
        self.x = x
        self.y = y
    
    def set_size(self, width: float, height: float) -> None:
        """
        设置尺寸
        
        Args:
            width: 宽度
            height: 高度
        """
        self.width = width
        self.height = height


class Button(UIComponent):
    """按钮组件"""
    
    def __init__(self, x: float, y: float, width: float, height: float, 
                 text: str = "", font_size: int = 24, 
                 normal_color: Tuple[int, int, int] = (100, 149, 237),
                 hover_color: Tuple[int, int, int] = (65, 105, 225),
                 pressed_color: Tuple[int, int, int] = (30, 58, 138),
                 text_color: Tuple[int, int, int] = (255, 255, 255)):
        """
        初始化按钮
        
        Args:
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
            text: 按钮文本
            font_size: 字体大小
            normal_color: 正常状态颜色
            hover_color: 悬停状态颜色
            pressed_color: 按下状态颜色
            text_color: 文本颜色
        """
        super().__init__(x, y, width, height)
        
        self.text: str = text
        self.font_size: int = font_size
        self.font = pygame.font.Font(None, font_size)
        
        self.normal_color: Tuple[int, int, int] = normal_color
        self.hover_color: Tuple[int, int, int] = hover_color
        self.pressed_color: Tuple[int, int, int] = pressed_color
        self.text_color: Tuple[int, int, int] = text_color
        
        self.pressed: bool = False
    
    def update(self, mouse_pos: Tuple[int, int], mouse_down: bool) -> None:
        """更新按钮状态"""
        super().update(mouse_pos, mouse_down)
        
        # 处理按下状态
        if self.hovered and mouse_down:
            self.pressed = True
        elif not mouse_down:
            self.pressed = False
    
    def _draw_self(self, screen: pygame.Surface) -> None:
        """绘制按钮"""
        # 确定当前颜色
        if self.pressed and self.hovered:
            color = self.pressed_color
        elif self.hovered:
            color = self.hover_color
        else:
            color = self.normal_color
        
        # 绘制按钮背景（圆角矩形）
        self._draw_rounded_rect(screen, color, 8)
        
        # 绘制文本
        if self.text:
            text_surface = self.font.render(self.text, True, self.text_color)
            text_rect = text_surface.get_rect(
                center=(self.x + self.width // 2, self.y + self.height // 2)
            )
            screen.blit(text_surface, text_rect)
    
    def _draw_rounded_rect(self, screen: pygame.Surface, color: Tuple[int, int, int], radius: int) -> None:
        """绘制圆角矩形"""
        rect = pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
        
        # 绘制圆角矩形
        pygame.draw.rect(screen, color, rect, border_radius=radius)


class TextBox(UIComponent):
    """文本框组件"""
    
    def __init__(self, x: float, y: float, width: float, height: float,
                 text: str = "", font_size: int = 24,
                 text_color: Tuple[int, int, int] = (0, 0, 0),
                 bg_color: Tuple[int, int, int] = (255, 255, 255),
                 border_color: Tuple[int, int, int] = (100, 100, 100),
                 border_width: int = 2,
                 alignment: Alignment = Alignment.LEFT):
        """
        初始化文本框
        
        Args:
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
            text: 文本内容
            font_size: 字体大小
            text_color: 文本颜色
            bg_color: 背景颜色
            border_color: 边框颜色
            border_width: 边框宽度
            alignment: 对齐方式
        """
        super().__init__(x, y, width, height)
        
        self.text: str = text
        self.font_size: int = font_size
        self.font = pygame.font.Font(None, font_size)
        
        self.text_color: Tuple[int, int, int] = text_color
        self.bg_color: Tuple[int, int, int] = bg_color
        self.border_color: Tuple[int, int, int] = border_color
        self.border_width: int = border_width
        self.alignment: Alignment = alignment
    
    def _draw_self(self, screen: pygame.Surface) -> None:
        """绘制文本框"""
        # 绘制背景
        pygame.draw.rect(screen, self.bg_color, 
                        (self.x, self.y, self.width, self.height))
        
        # 绘制边框
        if self.border_width > 0:
            pygame.draw.rect(screen, self.border_color, 
                            (self.x, self.y, self.width, self.height), 
                            self.border_width)
        
        # 绘制文本
        if self.text:
            text_surface = self.font.render(self.text, True, self.text_color)
            
            # 根据对齐方式确定位置
            if self.alignment == Alignment.LEFT:
                text_x = self.x + 5
                text_y = self.y + (self.height - self.font_size) // 2
            elif self.alignment == Alignment.CENTER:
                text_x = self.x + (self.width - text_surface.get_width()) // 2
                text_y = self.y + (self.height - self.font_size) // 2
            else:  # RIGHT
                text_x = self.x + self.width - text_surface.get_width() - 5
                text_y = self.y + (self.height - self.font_size) // 2
            
            screen.blit(text_surface, (text_x, text_y))
    
    def set_text(self, text: str) -> None:
        """设置文本"""
        self.text = text


class ProgressBar(UIComponent):
    """进度条组件"""
    
    def __init__(self, x: float, y: float, width: float, height: float,
                 progress: float = 0.0,
                 bg_color: Tuple[int, int, int] = (200, 200, 200),
                 bar_color: Tuple[int, int, int] = (100, 149, 237),
                 border_color: Tuple[int, int, int] = (100, 100, 100),
                 border_width: int = 2,
                 show_percent: bool = True,
                 font_size: int = 16):
        """
        初始化进度条
        
        Args:
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
            progress: 进度值（0.0-1.0）
            bg_color: 背景颜色
            bar_color: 进度条颜色
            border_color: 边框颜色
            border_width: 边框宽度
            show_percent: 是否显示百分比
            font_size: 字体大小
        """
        super().__init__(x, y, width, height)
        
        self.progress: float = max(0.0, min(1.0, progress))
        self.bg_color: Tuple[int, int, int] = bg_color
        self.bar_color: Tuple[int, int, int] = bar_color
        self.border_color: Tuple[int, int, int] = border_color
        self.border_width: int = border_width
        self.show_percent: bool = show_percent
        self.font = pygame.font.Font(None, font_size)
    
    def set_progress(self, progress: float) -> None:
        """
        设置进度
        
        Args:
            progress: 进度值（0.0-1.0）
        """
        self.progress = max(0.0, min(1.0, progress))
    
    def increment_progress(self, amount: float) -> None:
        """
        增加进度
        
        Args:
            amount: 增加量
        """
        self.set_progress(self.progress + amount)
    
    def _draw_self(self, screen: pygame.Surface) -> None:
        """绘制进度条"""
        # 绘制背景
        pygame.draw.rect(screen, self.bg_color, 
                        (self.x, self.y, self.width, self.height))
        
        # 绘制边框
        if self.border_width > 0:
            pygame.draw.rect(screen, self.border_color, 
                            (self.x, self.y, self.width, self.height), 
                            self.border_width)
        
        # 绘制进度条
        bar_width = self.width * self.progress
        pygame.draw.rect(screen, self.bar_color, 
                        (self.x, self.y, bar_width, self.height))
        
        # 绘制百分比文字
        if self.show_percent:
            percent_text = f"{int(self.progress * 100)}%"
            text_surface = self.font.render(percent_text, True, (0, 0, 0))
            text_rect = text_surface.get_rect(
                center=(self.x + self.width // 2, self.y + self.height // 2)
            )
            screen.blit(text_surface, text_rect)


class Slider(UIComponent):
    """滑块组件"""
    
    def __init__(self, x: float, y: float, width: float, height: float = 20,
                 value: float = 0.5, min_value: float = 0.0, max_value: float = 1.0,
                 bg_color: Tuple[int, int, int] = (200, 200, 200),
                 track_color: Tuple[int, int, int] = (100, 149, 237),
                 thumb_color: Tuple[int, int, int] = (65, 105, 225),
                 thumb_size: int = 16):
        """
        初始化滑块
        
        Args:
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
            value: 当前值
            min_value: 最小值
            max_value: 最大值
            bg_color: 背景颜色
            track_color: 轨道颜色
            thumb_color: 滑块颜色
            thumb_size: 滑块大小
        """
        super().__init__(x, y, width, height)
        
        self.min_value: float = min_value
        self.max_value: float = max_value
        self._value: float = self._clamp_value(value)
        
        self.bg_color: Tuple[int, int, int] = bg_color
        self.track_color: Tuple[int, int, int] = track_color
        self.thumb_color: Tuple[int, int, int] = thumb_color
        self.thumb_size: int = thumb_size
        
        self.dragging: bool = False
    
    def _clamp_value(self, value: float) -> float:
        """限制值在范围内"""
        return max(self.min_value, min(self.max_value, value))
    
    def get_value(self) -> float:
        """获取当前值"""
        return self._value
    
    def set_value(self, value: float) -> None:
        """设置当前值"""
        self._value = self._clamp_value(value)
    
    def update(self, mouse_pos: Tuple[int, int], mouse_down: bool) -> None:
        """更新滑块状态"""
        super().update(mouse_pos, mouse_down)
        
        # 处理拖拽
        if self.dragging:
            # 计算新值
            relative_x = mouse_pos[0] - self.x
            ratio = relative_x / self.width
            self._value = self.min_value + ratio * (self.max_value - self.min_value)
            self._value = self._clamp_value(self._value)
        elif self.hovered and mouse_down:
            self.dragging = True
        
        if not mouse_down:
            self.dragging = False
    
    def _draw_self(self, screen: pygame.Surface) -> None:
        """绘制滑块"""
        # 绘制背景轨道
        pygame.draw.rect(screen, self.bg_color, 
                        (self.x, self.y, self.width, self.height))
        
        # 计算已填充轨道宽度
        ratio = (self._value - self.min_value) / (self.max_value - self.min_value)
        filled_width = self.width * ratio
        
        # 绘制已填充轨道
        pygame.draw.rect(screen, self.track_color, 
                        (self.x, self.y, filled_width, self.height))
        
        # 绘制滑块
        thumb_x = self.x + filled_width - self.thumb_size // 2
        thumb_y = self.y + (self.height - self.thumb_size) // 2
        
        pygame.draw.circle(screen, self.thumb_color, 
                          (int(thumb_x + self.thumb_size // 2), int(thumb_y + self.thumb_size // 2)),
                          self.thumb_size // 2)


class DialogBox(UIComponent):
    """对话框组件"""
    
    def __init__(self, x: float, y: float, width: float, height: float,
                 title: str = "", message: str = "",
                 title_color: Tuple[int, int, int] = (255, 255, 255),
                 message_color: Tuple[int, int, int] = (0, 0, 0),
                 bg_color: Tuple[int, int, int] = (240, 240, 240),
                 title_bg_color: Tuple[int, int, int] = (100, 149, 237),
                 border_color: Tuple[int, int, int] = (100, 100, 100),
                 border_width: int = 2,
                 font_size: int = 20,
                 title_font_size: int = 24):
        """
        初始化对话框
        
        Args:
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
            title: 标题
            message: 消息内容
            title_color: 标题颜色
            message_color: 消息颜色
            bg_color: 背景颜色
            title_bg_color: 标题背景颜色
            border_color: 边框颜色
            border_width: 边框宽度
            font_size: 字体大小
            title_font_size: 标题字体大小
        """
        super().__init__(x, y, width, height)
        
        self.title: str = title
        self.message: str = message
        
        self.title_color: Tuple[int, int, int] = title_color
        self.message_color: Tuple[int, int, int] = message_color
        self.bg_color: Tuple[int, int, int] = bg_color
        self.title_bg_color: Tuple[int, int, int] = title_bg_color
        self.border_color: Tuple[int, int, int] = border_color
        self.border_width: int = border_width
        
        self.font = pygame.font.Font(None, font_size)
        self.title_font = pygame.font.Font(None, title_font_size)
        
        self.buttons: List[Button] = []
        
        # 标题高度
        self.title_height: int = 40
    
    def add_button(self, text: str, callback: Callable[[], None]) -> None:
        """
        添加按钮
        
        Args:
            text: 按钮文本
            callback: 点击回调
        """
        button_width = 100
        button_height = 35
        button_y = self.y + self.height - button_height - 15
        
        # 计算按钮位置（居中对齐）
        total_button_width = len(self.buttons) * button_width + (len(self.buttons) - 1) * 20
        start_x = self.x + (self.width - total_button_width) // 2
        
        button = Button(
            x=start_x + len(self.buttons) * (button_width + 20),
            y=button_y,
            width=button_width,
            height=button_height,
            text=text
        )
        button.on_click = callback
        
        self.buttons.append(button)
    
    def update(self, mouse_pos: Tuple[int, int], mouse_down: bool) -> None:
        """更新对话框"""
        super().update(mouse_pos, mouse_down)
        
        # 更新按钮
        for button in self.buttons:
            button.update(mouse_pos, mouse_down)
    
    def _draw_self(self, screen: pygame.Surface) -> None:
        """绘制对话框"""
        # 绘制背景
        pygame.draw.rect(screen, self.bg_color, 
                        (self.x, self.y, self.width, self.height))
        
        # 绘制边框
        if self.border_width > 0:
            pygame.draw.rect(screen, self.border_color, 
                            (self.x, self.y, self.width, self.height), 
                            self.border_width)
        
        # 绘制标题栏
        pygame.draw.rect(screen, self.title_bg_color, 
                        (self.x, self.y, self.width, self.title_height))
        
        # 绘制标题
        if self.title:
            title_surface = self.title_font.render(self.title, True, self.title_color)
            title_rect = title_surface.get_rect(
                center=(self.x + self.width // 2, self.y + self.title_height // 2)
            )
            screen.blit(title_surface, title_rect)
        
        # 绘制消息
        if self.message:
            message_surface = self.font.render(self.message, True, self.message_color)
            message_rect = message_surface.get_rect(
                center=(self.x + self.width // 2, self.y + self.title_height + (self.height - self.title_height) // 2)
            )
            screen.blit(message_surface, message_rect)
        
        # 绘制按钮
        for button in self.buttons:
            button.draw(screen)


class Panel(UIComponent):
    """面板组件"""
    
    def __init__(self, x: float, y: float, width: float, height: float,
                 bg_color: Tuple[int, int, int] = (255, 255, 255),
                 border_color: Tuple[int, int, int] = (100, 100, 100),
                 border_width: int = 2,
                 corner_radius: int = 0):
        """
        初始化面板
        
        Args:
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
            bg_color: 背景颜色
            border_color: 边框颜色
            border_width: 边框宽度
            corner_radius: 圆角半径
        """
        super().__init__(x, y, width, height)
        
        self.bg_color: Tuple[int, int, int] = bg_color
        self.border_color: Tuple[int, int, int] = border_color
        self.border_width: int = border_width
        self.corner_radius: int = corner_radius
    
    def _draw_self(self, screen: pygame.Surface) -> None:
        """绘制面板"""
        rect = pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
        
        # 绘制背景
        pygame.draw.rect(screen, self.bg_color, rect, border_radius=self.corner_radius)
        
        # 绘制边框
        if self.border_width > 0:
            pygame.draw.rect(screen, self.border_color, rect, 
                            width=self.border_width, border_radius=self.corner_radius)


class UIManager:
    """UI管理器（单例）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """初始化UI管理器"""
        self.components: List[UIComponent] = []
        self.focused_component: Optional[UIComponent] = None
    
    def add_component(self, component: UIComponent) -> None:
        """
        添加UI组件
        
        Args:
            component: UI组件
        """
        self.components.append(component)
    
    def remove_component(self, component: UIComponent) -> None:
        """
        移除UI组件
        
        Args:
            component: UI组件
        """
        if component in self.components:
            self.components.remove(component)
    
    def update(self) -> None:
        """更新所有UI组件"""
        mouse_pos = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]
        
        for component in self.components:
            component.update(mouse_pos, mouse_down)
    
    def draw(self, screen: pygame.Surface) -> None:
        """绘制所有UI组件"""
        for component in self.components:
            component.draw(screen)
    
    def clear_all(self) -> None:
        """清除所有组件"""
        self.components.clear()
    
    def show_message_box(self, title: str, message: str, 
                         ok_callback: Optional[Callable[[], None]] = None) -> DialogBox:
        """
        显示消息框
        
        Args:
            title: 标题
            message: 消息内容
            ok_callback: 确定按钮回调
            
        Returns:
            对话框实例
        """
        dialog = DialogBox(
            x=200, y=200, width=400, height=200,
            title=title, message=message
        )
        dialog.add_button("确定", ok_callback if ok_callback else lambda: self.remove_component(dialog))
        self.add_component(dialog)
        
        return dialog
    
    def show_confirm_box(self, title: str, message: str,
                         ok_callback: Optional[Callable[[], None]] = None,
                         cancel_callback: Optional[Callable[[], None]] = None) -> DialogBox:
        """
        显示确认框
        
        Args:
            title: 标题
            message: 消息内容
            ok_callback: 确定按钮回调
            cancel_callback: 取消按钮回调
            
        Returns:
            对话框实例
        """
        dialog = DialogBox(
            x=200, y=200, width=400, height=200,
            title=title, message=message
        )
        
        def ok_action():
            self.remove_component(dialog)
            if ok_callback:
                ok_callback()
        
        def cancel_action():
            self.remove_component(dialog)
            if cancel_callback:
                cancel_callback()
        
        dialog.add_button("确定", ok_action)
        dialog.add_button("取消", cancel_action)
        self.add_component(dialog)
        
        return dialog


# 全局UI管理器实例
ui_manager = UIManager()
