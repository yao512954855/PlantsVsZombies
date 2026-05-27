'''
核心系统模块初始化文件
包含：战斗系统、经济系统、成就系统
'''

from data.src.core.combat_system import (
    CombatSystem,
    CombatState,
    AttackType,
    combat_system,
    get_combat_system
)

from data.src.core.economy_system import (
    EconomySystem,
    SunlightManager,
    PlantCostCalculator,
    CurrencyType,
    EconomyEvent,
    initialize_economy,
    get_economy_system
)

from data.src.core.achievement_system import (
    AchievementTracker,
    Achievement,
    AchievementCategory,
    AchievementTier,
    achievement_tracker,
    get_achievement_tracker,
    initialize_achievements
)

__all__ = [
    # 战斗系统
    'CombatSystem',
    'CombatState',
    'AttackType',
    'combat_system',
    'get_combat_system',
    
    # 经济系统
    'EconomySystem',
    'SunlightManager',
    'PlantCostCalculator',
    'CurrencyType',
    'EconomyEvent',
    'initialize_economy',
    'get_economy_system',
    
    # 成就系统
    'AchievementTracker',
    'Achievement',
    'AchievementCategory',
    'AchievementTier',
    'achievement_tracker',
    'get_achievement_tracker',
    'initialize_achievements'
]
