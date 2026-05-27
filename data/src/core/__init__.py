'''
核心系统模块初始化文件
包含：战斗系统、经济系统、成就系统、UI 系统、音频系统、存档系统
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

from data.src.core.ui_system import (
    UIManager,
    UIState,
    Button,
    Panel,
    ToastNotification,
    ButtonConfig,
    PanelConfig,
    ToastConfig,
    get_ui_manager
)

from data.src.core.audio_system import (
    AudioManager,
    AudioCategory,
    MusicTrack,
    SoundEffect,
    AudioConfig,
    get_audio_manager,
    play_music,
    play_sound,
    set_master_volume,
    toggle_mute
)

from data.src.core.save_system import (
    SaveManager,
    SaveSlot,
    PlayerProgress,
    LevelState,
    GameSettings,
    SaveData,
    get_save_manager,
    quick_save,
    quick_load
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
    'initialize_achievements',
    
    # UI 系统
    'UIManager',
    'UIState',
    'Button',
    'Panel',
    'ToastNotification',
    'ButtonConfig',
    'PanelConfig',
    'ToastConfig',
    'get_ui_manager',
    
    # 音频系统
    'AudioManager',
    'AudioCategory',
    'MusicTrack',
    'SoundEffect',
    'AudioConfig',
    'get_audio_manager',
    'play_music',
    'play_sound',
    'set_master_volume',
    'toggle_mute',
    
    # 存档系统
    'SaveManager',
    'SaveSlot',
    'PlayerProgress',
    'LevelState',
    'GameSettings',
    'SaveData',
    'get_save_manager',
    'quick_save',
    'quick_load'
]
