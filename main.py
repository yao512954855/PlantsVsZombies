from data.src.PVZ import *  # 导入游戏类

class Main: # 主函数
    def __init__(self):
        self.game = Pvz() # 创建游戏实例
    
    def run(self):
        self.game.start(self.game) # 开始游戏
        self.game.choose_card() # 选择卡牌
        self.game.run() # 运行游戏
        self.game.save() # 保存游戏

if __name__ == '__main__': # 如果是主程序
    main = Main() # 创建主函数
    main.game.main = main  # 保存主函数实例
    main.run() # 运行主函数