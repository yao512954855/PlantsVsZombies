from data.src.PVZ import Pvz  # 导入游戏类
import sys

class Main:
    """植物大战僵尸游戏主程序入口"""
    
    def __init__(self):
        self.game = Pvz()  # 创建游戏实例
    
    def run(self):
        """启动游戏主循环"""
        self.game.start()  # 开始游戏
        self.game.choose_card()  # 选择卡牌界面
        self.game.run()  # 运行游戏主循环
        self.game.save()  # 保存游戏数据

if __name__ == '__main__':
    main = Main()
    main.run()