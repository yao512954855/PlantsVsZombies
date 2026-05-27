from data.src.object import *

class ReallyButton(Object):
    def __init__(self, game):
        super().__init__(game.screen, settings['reallyButton']['path'], settings['reallyButton']['size'], 1)
        self.really = False
        self.reallyTime = 0
        self.game = game
        self.start = False
        self.preStartTime = 0
        self.pos = settings['reallyButton']['pos']
        self.click = False

    def run(self):
        self.update()
        if self.click:
            self.reallyTime += 1
            if self.reallyTime > 4:
                self.really = False
            if self.reallyTime > 8:
                self.really = True
            if self.reallyTime > 12:
                self.really = False
            if self.reallyTime > 16:
                self.really = True
            if self.reallyTime > 20:
                self.really = False
                self.start = True
        if pygame.mouse.get_pressed()[0] and click(self.pos, self.size, pygame.mouse.get_pos()):
            if len(self.game.selectedCard) >= 1:
                self.really = True
                self.click = True
            else:
                print("错误：请至少选择一张卡片")
        if self.really:
            self.draw()