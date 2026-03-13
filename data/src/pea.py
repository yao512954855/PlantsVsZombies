from data.src.object import *

class Pea(Object):  # 定义Pea类，继承自Object
    def __init__(self, pos, screen, posY, isIcePea=False):  # 初始化函数
        self.isIcePea = isIcePea
        if isIcePea:
            super().__init__(screen, settings['pea']['icePeaPath'], settings['pea']['icePeaSize'], 1)
        else:
            super().__init__(screen, settings['pea']['path'], settings['pea']['size'], 1)
        self.pos = list(pos)  # 保存Pea位置
        self.posY = posY
        self.delete = False

    def run(self):  # 运行函数
        self.update()
        self.pos[0] += 8
        if self.pos[0] > 1150:
            self.delete = True
        self.draw()  # 绘制