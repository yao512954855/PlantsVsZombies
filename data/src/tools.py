# 导入必要的模块和常量
from data.src.const import *  # 导入游戏常量配置
from data.src.settings import *  # 导入游戏设置配置
import math  # 导入数学计算库

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

def ChooseZombieType(scene: str = 'day'):
    """
    随机选择僵尸类型（兼容旧版调用）
    :param scene: 场景类型
    :return: 返回一个随机选择的僵尸类型
    """
    # 使用新的僵尸工厂系统
    from data.src.zombie_factory import zombie_factory
    
    available_types = list(settings["game"]["zombieType"])
    weights = []
    for zt in available_types:
        weight = settings["game"]["zombieChooseProbability"].get(zt, 100)
        weights.append(weight)
    
    import random
    chosen_type = random.choices(available_types, weights=weights, k=1)[0]
    return chosen_type