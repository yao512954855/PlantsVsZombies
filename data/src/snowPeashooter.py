from data.src.object import * # 导入对象
from data.src.pea import * # 导入豌豆

class SnowPeashooter(Object):  # 定义 SnowPeashooter 类，继承自 Object 类
    def __init__(self, game, pos):  # 初始化函数
        self.plantType = 'snowPeashooter'
        self.game = game
        super().__init__(game.screen, settings['snowPeashooter']['path'], settings['snowPeashooter']['size'], settings['snowPeashooter']['imageCount'], self.plantType)  # 调用父类初始化函数
        self.pea_list = game.pea_list  # 豌豆列表
        self.pos = list(pos)  # 保存Peashooter位置
        self.pos[0] += settings['game']['gridPlantPos'][self.plantType][0]
        self.pos[1] += settings['game']['gridPlantPos'][self.plantType][1]
        self.peaTime = 0
        self.ifAppendPea = False
        self.updateGrid(self.pos)

    def run(self):  # 运行函数
        self.update()  # 更新图片
        if self.animation: # 如果处于动画状态
            if self.peaTime < PEATIME:
                if self.game.zombiePos[self.grid[1]]: # 如果有僵尸
                    self.peaTime += 1
            elif self.peaTime == PEATIME:
                self.peaTime = 0
                self.ifAppendPea = False
        if self.peaTime == PEATIME:
            if self.imageIndex == 15 and not self.ifAppendPea:
                self.pea_list.append(Pea((self.pos[0] + 42, self.pos[1] - 3), self.screen, self.grid[1], isIcePea=True))
                self.ifAppendPea = True
        self.draw()  # 绘制图片