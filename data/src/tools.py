# 导入必要的模块和常量
from data.src.const import *  # 导入游戏常量配置
from data.src.settings import *  # 导入游戏设置配置
from typing import Optional, List, Tuple, Any  # 类型注解
import math  # 导入数学计算库

# ============================================================================
# 基础工具函数 (原有功能)
# ============================================================================

def click(thingPos, thingSize, mousePos):
    """
    检测鼠标是否点击在物体范围内
    :param thingPos: 物体位置坐标 (x, y)
    :param thingSize: 物体尺寸 (width, height)
    :param mousePos: 鼠标位置坐标 (x, y)
    :return: 如果鼠标在物体范围内返回True,否则返回False
    """
    # 判断鼠标点击的x坐标是否在物体的x坐标范围内
    if mousePos[0] > thingPos[0] and mousePos[0] < thingPos[0] + thingSize[0]:
        # 判断鼠标点击的y坐标是否在物体的y坐标范围内
        if mousePos[1] > thingPos[1] and mousePos[1] < thingPos[1] + thingSize[1]:
            return True
    return False

def collision_detection(thing1, thing2):
    """
    通用碰撞检测函数
    :param thing1: 物体1,需包含pos和size属性
    :param thing2: 物体2,需包含pos和size属性
    :return: 如果两个物体发生碰撞返回True,否则返回False
    """
    # 检测物体1在物体2左侧的情况
    if thing1.pos[0] < thing2.pos[0]:
        if thing2.pos[0] > thing1.pos[0] + thing1.size[0]:
            if thing1.pos[1] < thing2.pos[1]:
                if thing2.pos[1] > thing1.pos[1] + thing1.size[1]:
                    return True
            elif thing1.pos[1] > thing2.pos[1]:
                if thing1.pos[1] < thing2.pos[1] + thing2.size[1]:
                    return True
    # 检测物体1在物体2右侧的情况
    elif thing1.pos[0] > thing2.pos[0]:
        if thing1.pos[0] < thing2.pos[0] + thing2.size[0]:
            if thing1.pos[1] < thing2.pos[1]:
                if thing2.pos[1] > thing1.pos[1] + thing1.size[1]:
                    return True
            elif thing1.pos[1] > thing2.pos[1]:
                if thing1.pos[1] < thing2.pos[1] + thing2.size[1]:
                    return True
    return False

def collision_Plant_and_Zombie_detection(plant, zombie, plant_name):
    """
    植物与僵尸的碰撞检测
    :param plant: 植物对象，需包含pos, size和grid属性
    :param zombie: 僵尸对象，需包含pos和posY属性
    :param plant_name: 植物名称，用于获取检测范围
    :return: 如果发生碰撞返回True，否则返回False
    """
    # 检测是否在同一行
    if zombie.posY == plant.grid[1]:
        # 计算植物实际碰撞盒右边界（扣除图片透明区域）
        plant_collision_right = plant.pos[0] + settings[plant_name]["collisionSize"][0]
        # 计算检测范围右边界（植物碰撞盒右边界 + 检测偏移量）
        detection_right = plant_collision_right + settings["game"]["detectionPlantXPos"][plant_name]
        # 僵尸x坐标需进入检测范围才触发碰撞
        if zombie.pos[0] <= detection_right:
            return True
    return False

def collision_Pea_add_Zombie_detection(zombie, pea):
    """
    豌豆与僵尸的碰撞检测
    :param zombie: 僵尸对象,需包含pos和posY属性
    :param pea: 豌豆对象,需包含pos, size和posY属性
    :return: 如果发生碰撞返回True,否则返回False
    """
    # 检测豌豆是否击中僵尸
    if zombie.pos[0] < pea.pos[0] + pea.size[0] - 30:
        # 检测是否在同一行
        if zombie.posY == pea.posY:
            return True
    return False

def getGrid(xy):
    """
    将屏幕坐标转换为网格坐标
    :param xy: 屏幕坐标 (x, y)
    :return: 网格坐标 [col, row]
    """
    pos = list(xy)
    grid = [0, 0]
    # 计算相对于网格起始位置的偏移量
    pos[0] -= GRID_LEFT_X
    pos[0] /= GRID_SIZE[0]
    pos[1] -= GRID_TOP_Y
    pos[1] /= GRID_SIZE[1]
    # 使用math.ceil向上取整得到网格坐标
    grid[0] = math.ceil(pos[0])
    grid[1] = math.ceil(pos[1])
    return grid

def IsInRightVirtualGrid(xy):
    """
    检查坐标是否在右侧虚拟网格范围内
    :param xy: 屏幕坐标 (x, y)
    :return: 如果在右侧虚拟网格范围内返回True,否则返回False
    """
    pos = list(xy)
    grid = [0, 0]
    # 计算相对于网格起始位置的偏移量
    pos[0] -= GRID_LEFT_X
    pos[0] /= GRID_SIZE[0]
    pos[1] -= GRID_TOP_Y
    pos[1] /= GRID_SIZE[1]
    # 使用math.ceil向上取整得到网格坐标
    grid[0] = math.ceil(pos[0])
    grid[1] = math.ceil(pos[1])
    return grid[0] == GRID_COUNT[0] + 2 and grid[1] >= 1 and grid[1] <= GRID_COUNT[1]

def getGridPos(xy):
    """
    获取指定坐标对应的网格位置
    :param xy: 屏幕坐标 (x, y)
    :return: 如果坐标在花园内返回网格位置,否则返回False
    """
    # 首先检查坐标是否在花园范围内
    if not CheckInGarden(xy):
        return {"if": False, "pos": []}
    # 获取网格坐标
    grid = getGrid(xy)
    # 检查网格坐标是否超出范围
    if grid[0] > 9 or grid[1] > 5:
        return {"if": False, "pos": []}
    # 返回网格的实际位置坐标
    return {"if": True, "pos": [GRID_X[grid[0]], GRID_Y[grid[1]]]}

def CheckInGarden(pos):
    """
    检查坐标是否在花园范围内
    :param pos: 屏幕坐标 (x, y)
    :return: 如果在花园范围内返回True,否则返回False
    """
    # 检查x坐标是否在花园左右边界之间
    # 检查y坐标是否在花园上下边界之间
    return pos[0] > GRID_LEFT_X and pos[0] < GRID_RIGHT_X and pos[1] > GRID_TOP_Y and pos[1] < GRID_DOWN_Y

def ChooseZombieType():
    """
    随机选择僵尸类型
    :return: 返回一个随机选择的僵尸类型
    """
    # 导入random模块，用于生成随机数
    import random
    # 初始化随机数生成器，使用系统默认的种子（通常基于当前时间）
    random.seed()
    # 生成一个1到100之间的随机整数，用于后续的概率判断
    randNumber = random.randint(1, 100)
    # 遍历游戏设置中定义的所有僵尸类型
    for zombieType in settings["game"]["zombieType"]:
        # 从游戏设置中获取当前僵尸类型被选中的概率
        # 若生成的随机数小于等于该概率值，则表示选中该僵尸类型
        if randNumber <= settings["game"]["zombieChooseProbability"][zombieType]:
            # 返回当前被选中的僵尸类型
            return zombieType

# ============================================================================
# 场景感知工具函数 (第二阶段新增)
# ============================================================================

def get_scene_aware_spawn_position(
    scene_type: str,
    row: int
) -> Tuple[int, int]:
    """
    根据场景类型获取僵尸生成位置
    
    :param scene_type: 场景类型 ('day', 'night', 'roof', 'pool', 'fog')
    :param row: 行号 (1-5)
    :return: (x, y) 生成坐标
    """
    base_x = GRID_RIGHT_X + 50
    base_y = GRID_Y[row] if row <= len(GRID_Y) else GRID_TOP_Y
    
    # 屋顶场景需要调整 Y 坐标 (斜坡效果)
    if scene_type == 'roof':
        slope_offset = (row - 1) * 20
        base_y -= slope_offset
    
    return (base_x, base_y)


def is_plantable_position(
    grid: List[int],
    plant_type: str,
    scene_type: str,
    game_map: List[List[Any]]
) -> bool:
    """
    检查位置是否可种植植物 (考虑场景限制)
    
    :param grid: 网格坐标 [col, row]
    :param plant_type: 植物类型
    :param scene_type: 场景类型
    :param game_map: 游戏地图
    :return: 是否可种植
    """
    col, row = grid[0], grid[1]
    
    # 检查边界
    if row < 1 or row > GRID_COUNT[1] or col < 1 or col > GRID_COUNT[0]:
        return False
    
    # 检查该位置是否已有植物
    if game_map[row][col] != 0:
        return False
    
    # 屋顶场景需要花盆 (除了花盆本身)
    if scene_type == 'roof' and plant_type not in ['flower_pot']:
        # 检查是否有花盆
        if not _has_flower_pot_at(grid, game_map):
            return False
    
    # 泳池场景需要睡莲 (除了睡莲和水生植物)
    if scene_type in ['pool', 'fog']:
        water_rows = [2, 3]  # 中间两行是水
        if row in water_rows and plant_type not in ['lily_pad', 'tangle_kelp', 'sea_shroom']:
            # 检查是否有睡莲
            if not _has_lily_pad_at(grid, game_map):
                return False
    
    return True


def _has_flower_pot_at(
    grid: List[int],
    game_map: List[List[Any]]
) -> bool:
    """检查指定位置是否有花盆"""
    col, row = grid[0], grid[1]
    return game_map[row][col] == 'flower_pot'


def _has_lily_pad_at(
    grid: List[int],
    game_map: List[List[Any]]
) -> bool:
    """检查指定位置是否有睡莲"""
    col, row = grid[0], grid[1]
    return game_map[row][col] == 'lily_pad'


def get_available_plants_for_level(
    level_id: int,
    scene_type: str
) -> List[str]:
    """
    根据关卡 ID 和场景类型获取可用植物列表
    
    :param level_id: 关卡 ID (1-50)
    :param scene_type: 场景类型
    :return: 可用植物类型列表
    """
    # 基础植物 (所有关卡可用)
    available = ['peashooter', 'sunflower', 'cherry_bomb', 'wall_nut']
    
    # 根据关卡进度解锁植物
    unlock_schedule = {
        5: ['potato_mine', 'snow_pea'],
        10: ['chomper', 'repeater'],
        15: ['puff_shroom', 'sun_shroom', 'fume_shroom'],
        20: ['grave_buster', 'hypno_shroom'],
        25: ['flower_pot', 'threepeater'],
        30: ['split_pea', 'starfruit'],
        35: ['lily_pad', 'tangle_kelp'],
        40: ['jalapeno', 'spikeweed'],
        45: ['torchwood', 'tall_nut'],
        50: ['sea_shroom', 'plantern'],
    }
    
    for unlock_level, plants in unlock_schedule.items():
        if level_id >= unlock_level:
            available.extend(plants)
    
    # 根据场景类型过滤植物
    scene_specific_requirements = {
        'roof': ['flower_pot'],  # 屋顶必须解锁花盆
        'pool': ['lily_pad'],    # 泳池必须解锁睡莲
        'fog': ['lily_pad', 'plantern'],  # 迷雾需要睡莲和三叶草
    }
    
    if scene_type in scene_specific_requirements:
        required = scene_specific_requirements[scene_type]
        # 如果场景需要的植物还没解锁，则限制可用植物
        for req_plant in required:
            if req_plant not in available:
                # 场景需要的植物未解锁，提供最低限度的替代方案
                pass
    
    return list(set(available))  # 去重


def calculate_zombie_spawn_rate(
    current_wave: int,
    total_waves: int,
    difficulty: int
) -> float:
    """
    计算僵尸生成速率
    
    :param current_wave: 当前波次
    :param total_waves: 总波次
    :param difficulty: 难度等级 (1-10)
    :return: 生成间隔 (秒)
    """
    # 基础间隔随波次减少
    base_min = max(0.5, 3.0 - current_wave * 0.2)
    base_max = max(1.0, 5.0 - current_wave * 0.3)
    
    # 难度影响
    difficulty_factor = 1.0 - (difficulty - 1) * 0.03
    
    min_interval = base_min * difficulty_factor
    max_interval = base_max * difficulty_factor
    
    import random
    return random.uniform(min_interval, max_interval)


def get_scene_background_color(scene_type: str) -> Tuple[int, int, int]:
    """
    获取场景背景颜色
    
    :param scene_type: 场景类型
    :return: RGB 颜色值
    """
    colors = {
        'day': (135, 206, 235),      # 天空蓝
        'night': (25, 25, 112),      # 午夜蓝
        'roof': (135, 206, 235),     # 天空蓝
        'pool': (135, 206, 235),     # 天空蓝
        'fog': (70, 70, 90),         # 灰蓝色
    }
    return colors.get(scene_type.lower(), (135, 206, 235))


def get_scene_ambient_light(scene_type: str) -> float:
    """
    获取场景环境亮度
    
    :param scene_type: 场景类型
    :return: 亮度值 (0.0-1.0)
    """
    light_levels = {
        'day': 1.0,
        'night': 0.4,
        'roof': 0.9,
        'pool': 1.0,
        'fog': 0.5,
    }
    return light_levels.get(scene_type.lower(), 1.0)
