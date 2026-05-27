"""
Plants vs Zombies - Main Entry Point
工业级精简入口，负责游戏初始化和主循环
"""

from typing import Optional
from data.src.PVZ import Pvz


class GameApplication:
    """游戏应用主类"""
    
    def __init__(self):
        self.game: Optional[Pvz] = None
    
    def run(self) -> None:
        """启动游戏主循环"""
        try:
            self._initialize_game()
            self._main_game_loop()
        except Exception as e:
            print(f"游戏运行异常: {e}")
            raise
        finally:
            self._cleanup()
    
    def _initialize_game(self) -> None:
        """初始化游戏实例"""
        self.game = Pvz()
    
    def _main_game_loop(self) -> None:
        """游戏主循环"""
        if not self.game:
            raise RuntimeError("游戏实例未初始化")
        
        self.game.start(self.game)
        self.game.choose_card()
        self.game.run()
        self.game.save()
    
    def _cleanup(self) -> None:
        """清理资源"""
        if self.game:
            self.game = None


if __name__ == '__main__':
    app = GameApplication()
    app.run()