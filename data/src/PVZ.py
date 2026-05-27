"""
Plants vs Zombies - Core Game Class
工业级游戏核心类，包含完善的错误处理和资源管理
"""

import json
import os
import logging
from typing import List, Dict, Optional, Any
from data.src._BasicImports import *
from data.src._GameObjectImports import *
from data.src.Game import *

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('game.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GameError(Exception):
    """游戏核心异常类"""
    pass


class ResourceLoadError(GameError):
    """资源加载异常"""
    pass


class ConfigurationError(GameError):
    """配置错误异常"""
    pass


class SaveLoadError(GameError):
    """存档读写异常"""
    pass


class Pvz:
    """
    植物大战僵尸游戏主类
    负责游戏初始化、场景管理和主循环
    """
    
    def __init__(self):
        """初始化游戏"""
        self._validate_settings()
        self._initialize_state()
        self._setup_pygame()
    
    def _validate_settings(self) -> None:
        """验证配置完整性"""
        required_keys = ['game', 'plant_name', 'cherry_bomb', 'jalapeno', 'lawnmower']
        for key in required_keys:
            if key not in settings:
                raise ConfigurationError(f"配置文件缺少必要键: {key}")
        logger.info("配置验证通过")
    
    def _initialize_state(self) -> None:
        """初始化游戏状态"""
        self.running: bool = False
        self.really: bool = False
        self.gameover: bool = False
        self.plant: bool = False
        self.plantType: int = 0
        self.plantName: str = ""
        
        # 初始化列表
        self.zombie_list: List = []
        self.sunflower_list: List = []
        self.sunlight_list: List = []
        self.peashooter_list: List = []
        self.snowPeashooter_list: List = []
        self.chomper_list: List = []
        self.pea_list: List = []
        self.zombieHead_list: List = []
        self.nut_list: List = []
        self.cherryBomb_list: List = []
        self.jalapeno_list: List = []
        self.potatoMine_list: List = []
        self.squash_list: List = []
        self.growSoil_list: List = []
        self.displayed_card_shadow_list: List = []
        self.card_shadow_list: List = []
        self.zombiePos: List[int] = [0, 0, 0, 0, 0, 0]
        self.lawnmower_list: List = []
        self.spikeweed_list: List = []
        self.lawnmowerIf: List[int] = [0, 0, 0, 0, 0, 0]
        self.card: List = []
        self.displayed_card: List = []
        self.selectedCard: List = []
        
        # 卡片位置计算
        CHOOSE_CARD_FRAME_CARD_X.append(0)
        CHOOSE_CARD_FRAME_CARD_Y.append(0)
        for i in range(1, CHOOSE_CARD_FRAME_CARD_COUNT[0] + 1):
            CHOOSE_CARD_FRAME_CARD_X.append(
                CHOOSE_CARD_FRAME_LEFT_X + (i - 1) * (CHOOSE_CARD_FRAME_CARD_SIZE[0] + CHOOSE_CARD_FRAME_CARD_X_SPACING)
            )
        for i in range(1, CHOOSE_CARD_FRAME_CARD_COUNT[1] + 1):
            CHOOSE_CARD_FRAME_CARD_Y.append(
                CHOOSE_CARD_FRAME_TOP_Y + (i - 1) * (CHOOSE_CARD_FRAME_CARD_SIZE[1] + CHOOSE_CARD_FRAME_CARD_Y_SPACING)
            )
    
    def _setup_pygame(self) -> None:
        """初始化Pygame环境"""
        try:
            pygame.init()
            icon = pygame.image.load(ICON_PATH)
            pygame.display.set_icon(icon)
            logger.info("Pygame初始化完成")
        except pygame.error as e:
            raise ResourceLoadError(f"Pygame初始化失败: {e}")
    
    def start(self, game) -> None:
        """
        游戏开始界面
        
        Args:
            game: 游戏对象引用
        """
        try:
            self.screen = pygame.display.set_mode(GAME_SIZE)
            pygame.display.set_caption(f"{GAME_TITLE}V{GAME_VERSION}")
            self.FPS = DEFAULT_FPS
            self.clock = pygame.time.Clock()
            self.game = Game(game)
            self.ObjectGame = game

            self.loading_music()
            self.initialize_instance()

            self.startTime = 0
            self.startMusic.play(-1)
            logger.info("游戏开始界面启动")

            while not self.running:
                self._handle_events()
                self._render_start_screen()
                self._check_start_condition()
                
                pygame.display.flip()
                self.clock.tick(self.FPS)
                
        except Exception as e:
            logger.error(f"开始界面初始化失败: {e}", exc_info=True)
            raise
    
    def _handle_events(self) -> None:
        """处理游戏事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._safe_exit()
    
    def _safe_exit(self) -> None:
        """安全退出游戏"""
        logger.info("用户请求退出游戏")
        pygame.quit()
        os.exit(0)
    
    def _render_start_screen(self) -> None:
        """渲染开始界面"""
        self.screen.fill(WHITE)
        self.startBackground.run()
        self.startButton.run()
    
    def _check_start_condition(self) -> None:
        """检查开始条件"""
        if self.startButton.start:
            self.startTime += 1
        if self.startTime == 20:
            self.running = True
            logger.info("开始游戏")
    
    def choose_card(self) -> None:
        """选择卡片界面"""
        try:
            self.startMusic.stop()
            self.gameMusic.play(-1)
            self.selectedCard = []
            logger.info("进入卡片选择界面")

            while not self.really:
                self._handle_events()
                self._render_card_selection()
                self._check_really_button()
                
                pygame.display.flip()
                self.clock.tick(self.FPS)
                
        except Exception as e:
            logger.error(f"卡片选择界面错误: {e}", exc_info=True)
            raise
    
    def _render_card_selection(self) -> None:
        """渲染卡片选择界面"""
        self.screen.fill(WHITE)
        self.background.run()
        self.game.run()
        self.CardFrame.run()
        self.ChooseCardFrame.run()

        for card in self.displayed_card:
            card.run()
        for card in self.selectedCard:
            card.run()
        for num in range(len(self.displayed_card_shadow_list)):
            if self.displayed_card[num].use:
                self.displayed_card_shadow_list[num].run()
        
        self.reallyButton.run()
    
    def _check_really_button(self) -> None:
        """检查确认按钮"""
        if self.reallyButton.start:
            self.really = True
            logger.info("确认选择卡片")
    
    def run(self) -> None:
        """游戏主运行界面"""
        try:
            self._initialize_game_cards()
            logger.info("进入游戏主循环")

            while self.running:
                if not self.gameover:
                    self._handle_game_events()
                    self._update_game_logic()
                    self._render_game_screen()
                    self._update_zombie_positions()
                else:
                    self._handle_gameover()
                
                self.clock.tick(self.FPS)
                pygame.display.flip()
                
        except Exception as e:
            logger.error(f"游戏主循环错误: {e}", exc_info=True)
            raise
    
    def _initialize_game_cards(self) -> None:
        """初始化游戏卡片"""
        for card in self.selectedCard:
            self.card.append(Card(self.screen, card.name, card.PosNumber))
            self.card_shadow_list.append(
                Shadow(self.screen, CARD_SIZE, 
                       [CARD_FIRST_X + (CARD_SIZE[0] + 7) * self.selectedCard.index(card), CARD_POS_Y])
            )
    
    def _handle_game_events(self) -> None:
        """处理游戏事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._safe_exit()
            elif pygame.mouse.get_pressed()[0]:
                if not self.plant:
                    self._handle_card_click()
    
    def _handle_card_click(self) -> None:
        """处理卡片点击"""
        for card in self.card:
            if card.READY and click(card.pos, card.size, pygame.mouse.get_pos()):
                if self.game.CheckPlant_Grid(card.name):
                    self._prepare_planting(card)
    
    def _prepare_planting(self, card) -> None:
        """准备种植"""
        self.plant = True
        self.plantType = card.number
        self.plantName = card.name

        self.Plant.name = self.plantName
        self.Plant.path = settings[self.plantName]['path']
        self.Plant.imageCount = settings[self.plantName]['imageCount']
        self.Plant.size = settings[self.plantName]['size']
        self.Plant.preIndexTimeNumber = settings['game']['plantPreIndexTimeNumber'][self.plantName]
        
        self.gridPlant.plantName = self.plantName
        self.gridPlant.path = settings[self.plantName]['path']
        self.gridPlant.imageCount = settings[self.plantName]['imageCount']
        self.gridPlant.size = settings[self.plantName]['size']
        self.gridPlant.preIndexTimeNumber = settings['game']['plantPreIndexTimeNumber'][self.plantName]
    
    def _update_game_logic(self) -> None:
        """更新游戏逻辑"""
        self.screen.fill(WHITE)
        self.background.run()
        self.game.run()

        self.CardFrame.run()
        for card in self.card:
            card.run()
        self.game.shovelFrame.run()

        # 绘制金币
        text_surface = pygame.font.Font(None, 33).render(str(self.game.gold), True, (0, 0, 0))
        text_rect = text_surface.get_rect()
        text_rect.center = (60, 75)
        self.screen.blit(text_surface, text_rect)

        if self.plant:
            self._handle_planting()
    
    def _handle_planting(self) -> None:
        """处理种植逻辑"""
        if self.game.CheckInGarden(pygame.mouse.get_pos()):
            self.gridPlant.run()
        if pygame.mouse.get_pressed()[0]:
            result = self.game.CheckAddPlant(pygame.mouse.get_pos(), self.plantType)
            if not result['plant']:
                return
            
            # 添加生长土壤
            for plant in settings.get("need_grow_soil_plant", []):
                if plant == self.plantName:
                    self.growSoil_list.append(GrowSoil(self.ObjectGame, result['pos']))
                    break
            
            # 根据植物类型创建实例
            self._create_plant_instance(result['pos'])
            self.game.gold -= settings[settings['plant_name'][self.plantType]]['gold']
    
    def _create_plant_instance(self, pos) -> None:
        """根据类型创建植物实例"""
        plant_map = {
            1: (Sunflower, self.sunflower_list),
            2: (Peashooter, self.peashooter_list),
            3: (Nut, self.nut_list),
            4: (PotatoMine, self.potatoMine_list),
            5: (Chomper, self.chomper_list),
            6: (CherryBomb, self.cherryBomb_list),
            7: (Jalapeno, self.jalapeno_list),
            8: (Squash, self.squash_list),
            9: (Spikeweed, self.spikeweed_list),
            10: (SnowPeashooter, self.snowPeashooter_list),
        }
        
        plant_class, plant_list = plant_map.get(self.plantType, (None, None))
        if plant_class:
            plant_list.append(plant_class(self.ObjectGame, pos))
        self.plant = False
    
    def _render_game_screen(self) -> None:
        """渲染游戏屏幕"""
        # 渲染各类游戏对象
        self._render_list(self.potatoMine_list)
        self._render_list(self.peashooter_list)
        self._render_list(self.snowPeashooter_list)
        self._render_list(self.sunflower_list)
        self._render_list(self.nut_list)
        self._render_list(self.spikeweed_list)
        
        # 渲染僵尸
        for zombie in self.zombie_list[:]:
            zombie.run()
            if zombie.delete:
                self.zombie_list.remove(zombie)
        
        # 渲染僵尸头
        for head in self.zombieHead_list[:]:
            head.run()
            if head.delete:
                self.zombieHead_list.remove(head)
        
        # 渲染其他对象
        self._render_list(self.chomper_list)
        self._render_list(self.squash_list)
        
        # 渲染子弹
        for pea in self.pea_list[:]:
            pea.run()
            if pea.delete:
                self.pea_list.remove(pea)
        
        self._render_list(self.cherryBomb_list)
        self._render_list(self.jalapeno_list)
        self._render_list(self.growSoil_list)
        
        # 渲染卡片阴影
        for shadow in self.card_shadow_list:
            number = self.card_shadow_list.index(shadow)
            if self.card[number].READY and not self.game.CheckPlant_Grid(self.card[number].name):
                shadow.run()
        
        self._render_list(self.lawnmower_list)
        self._render_list(self.sunlight_list)
        
        self.game.shovel.run()
        
        if self.plant:
            self.Plant.run()
    
    def _render_list(self, obj_list: List) -> None:
        """渲染对象列表"""
        for obj in obj_list:
            obj.run()
    
    def _update_zombie_positions(self) -> None:
        """更新僵尸位置状态"""
        for index in range(1, GRID_COUNT[1]):
            flag = False
            for zombie in self.zombie_list:
                if zombie.posY == -1:
                    continue
                if zombie.grid[1] == index:
                    flag = True
                    break
            self.zombiePos[index] = flag
    
    def _handle_gameover(self) -> None:
        """处理游戏结束"""
        self._handle_events()
        self.screen.fill(WHITE)
        self.background.run()
        self.game.run()

        self.CardFrame.run()
        for card in self.card:
            card.run()
        self.game.run()
        self.game.shovelFrame.run()
        self.game.shovel.run()
        self.gameover_text.run()
    
    def initialize_list(self) -> None:
        """初始化游戏对象列表（保留兼容性）"""
        self._initialize_state()
    
    def SetWindowAtTheTop(self) -> None:
        """设置窗口置顶"""
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.WinDLL('user32', use_last_error=True)
            SetWindowPos = user32.SetWindowPos
            SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.INT, 
                                     wintypes.INT, wintypes.INT, wintypes.INT, wintypes.UINT]
            SetWindowPos.restype = wintypes.BOOL

            HWND_TOPMOST = -1
            pygame_hwnd = pygame.display.get_wm_info()['window']
            SetWindowPos(pygame_hwnd, HWND_TOPMOST, 0, 0, 0, 0, 0x0001)
            logger.debug("窗口已置顶")
        except Exception as e:
            logger.warning(f"设置窗口置顶失败: {e}")
    
    def CancelWindowAtTheTop(self) -> None:
        """取消窗口置顶"""
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.WinDLL('user32', use_last_error=True)
            SetWindowPos = user32.SetWindowPos
            SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.INT, 
                                     wintypes.INT, wintypes.INT, wintypes.INT, wintypes.UINT]
            SetWindowPos.restype = wintypes.BOOL

            HWND_NOTOPMOST = -2
            pygame_hwnd = pygame.display.get_wm_info()['window']
            SetWindowPos(pygame_hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, 0x0001)
            logger.debug("窗口置顶已取消")
        except Exception as e:
            logger.warning(f"取消窗口置顶失败: {e}")
    
    def initialize_instance(self) -> None:
        """初始化游戏实例"""
        self.background = Background(self.screen)
        self.Plant = Plant(self.screen)
        self.gridPlant = gridPlant(self.screen)
        self.ChooseCardFrame = ChooseCardFrame(self.screen)
        self.CardFrame = CardFrame(self.screen)
        self.gameover_text = GameOverText(self.screen)

        # 初始化显示卡片
        rankY = 1
        number = 1
        UpdateYflag = 0
        for i in range(1, len(settings['plant_name'])):
            rankX = i % CHOOSE_CARD_FRAME_CARD_COUNT[0]
            if rankX == 0:
                rankX = CHOOSE_CARD_FRAME_CARD_COUNT[0]
                UpdateYflag = 1
            if UpdateYflag == 1 and rankX == 1:
                UpdateYflag = 0
                rankY += 1
            self.displayed_card.append(
                DisplayedCard(self.screen, settings['plant_name'][number], (rankX, rankY))
            )
            self.displayed_card_shadow_list.append(
                Shadow(self.screen, CHOOSE_CARD_FRAME_CARD_SIZE,
                       (CHOOSE_CARD_FRAME_CARD_X[rankX], CHOOSE_CARD_FRAME_CARD_Y[rankY]))
            )
            number += 1

        self.startBackground = StartBackground(self.screen)
        self.startButton = StartButton(self.screen)
        self.reallyButton = ReallyButton(self.ObjectGame)

        for i in range(GRID_COUNT[1]):
            self.lawnmower_list.append(Lawnmower(self.ObjectGame, i + 1))
    
    def loading_music(self) -> None:
        """加载音乐资源"""
        try:
            # 加载背景音乐
            self.gameMusic = pygame.mixer.Sound(settings['game']['bgm']['gameMusic'])
            self.gameMusic.set_volume(settings['game']['bgm']['gameMusicVolume'])

            # 加载开始音乐
            self.startMusic = pygame.mixer.Sound(settings['game']['bgm']['startMusic'])
            self.startMusic.set_volume(settings['game']['bgm']['startMusicVolume'])

            # 加载阳光音乐
            self.sunMusic = pygame.mixer.Sound(settings['game']['bgm']['sunlight'])
            self.sunMusic.set_volume(settings['game']['bgm']['sunVolume'])

            # 加载特效音乐
            self.cherryBombExplosionMusic = pygame.mixer.Sound(settings['cherry_bomb']['ExplosionSound'])
            self.cherryBombExplosionMusic.set_volume(settings['cherry_bomb']['ExplosionSoundVolume'])

            self.jalapenoExplosionMusic = pygame.mixer.Sound(settings['jalapeno']['ExplosionSound'])
            self.jalapenoExplosionMusic.set_volume(settings['jalapeno']['ExplosionSoundVolume'])

            self.lawnmowerMusic = pygame.mixer.Sound(settings['lawnmower']['Music'])
            self.lawnmowerMusic.set_volume(settings['lawnmower']['MusicVolume'])
            
            logger.info("音乐资源加载完成")
        except pygame.error as e:
            raise ResourceLoadError(f"音乐加载失败: {e}")
    
    def load(self) -> None:
        """加载游戏数据"""
        try:
            with open('data/save/map.json', 'r') as f:
                map_data = json.load(f)
                self.game.map = [list(item) for item in map_data]
            
            with open('data/save/gold.json', 'r') as f:
                self.game.gold = json.load(f)
            
            logger.info("游戏数据加载完成")
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            raise SaveLoadError(f"加载游戏数据失败: {e}")
    
    def save(self) -> None:
        """保存游戏数据"""
        try:
            # 确保保存目录存在
            os.makedirs('data/save', exist_ok=True)
            
            with open('data/save/map.json', 'w') as f:
                json.dump(self.game.map, f)
            
            with open('data/save/gold.json', 'w') as f:
                json.dump(self.game.gold, f)
            
            logger.info("游戏数据保存完成")
        except (IOError, TypeError) as e:
            raise SaveLoadError(f"保存游戏数据失败: {e}")