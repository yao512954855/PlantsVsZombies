# 植物大战僵尸 - 架构设计文档

## 1. 系统概述

本项目采用**分层架构**和**领域驱动设计 (DDD)**理念，将游戏系统划分为表现层、业务层和数据层，确保高内聚低耦合。

## 2. 架构分层

### 2.1 表现层 (Presentation Layer)

负责用户界面渲染、输入处理和反馈展示。

**核心组件**:
- `ui_components.py`: UI 组件库（按钮、血条、浮动文字、网格布局）
- `particle_system.py`: 粒子特效引擎（爆炸、阳光、冰冻等特效）
- `audio_manager.py`: 音频管理系统（BGM、音效、混音）

**技术特性**:
- 弹性动画系统（贝塞尔曲线插值）
- 对象池模式（粒子复用，零 GC 压力）
- 混合渲染模式（Alpha  blending、 additive blending）

### 2.2 业务层 (Business Logic Layer)

游戏核心逻辑，包含所有游戏规则和状态管理。

**核心组件**:
- `Game.py`: 游戏主循环、状态机、碰撞检测
- `PVZ.py`: 游戏实例入口、场景切换协调
- `level_manager.py`: 关卡配置管理、进度跟踪
- `zombie_factory.py`: 僵尸生成工厂、波次调度
- `scene_manager.py`: 场景切换、环境效果
- `plant_database.py`: 植物属性数据库
- `zombie_database.py`: 僵尸属性数据库
- `shop_system.py`: 商店经济系统
- `game_modes.py`: 游戏模式策略（冒险/生存/解谜）
- `save_system.py`: 存档持久化管理

**设计模式**:
- **单例模式**: LevelManager, SceneManager, SaveSystem
- **工厂模式**: ZombieFactory
- **策略模式**: GameModeStrategy
- **观察者模式**: EventBus（事件总线）

### 2.3 数据层 (Data Access Layer)

负责数据持久化和资源配置。

**核心组件**:
- JSON 配置文件（levels.json, plants.json, zombies.json）
- 存档文件（player_data.json + 自动备份）
- 资源文件 I/O（图片、音频加载）

**特性**:
- ACID 事务保障（原子写入）
- 版本兼容机制（SaveVersionManager）
- 热加载支持（开发模式）

## 3. 核心流程图

### 3.1 游戏启动流程

```
main.py → PVZ.__init__() → PVZ.start()
    ↓
创建 Game 实例
    ↓
初始化各管理器（单例）
    ↓
加载关卡配置
    ↓
设置场景
    ↓
进入主循环
```

### 3.2 僵尸生成流程

```
Game.update() 
    ↓
ZombieSpawner.check_spawn_time()
    ↓
ZombieFactory.create_zombie(type, scene)
    ↓
Zombie.__init__(config)
    ↓
添加到 game.zombies 列表
    ↓
碰撞检测系统接管
```

### 3.3 存档保存流程

```
SaveSystem.save_player_data(data)
    ↓
创建临时文件
    ↓
序列化 JSON（带版本标记）
    ↓
原子替换原文件
    ↓
创建.bak 备份
    ↓
校验完整性
```

## 4. 数据结构设计

### 4.1 关卡配置结构

```json
{
  "level_001": {
    "scene_type": "day",
    "difficulty": 1.0,
    "initial_sun": 150,
    "initial_gold": 200,
    "available_plants": ["sunflower", "peashooter"],
    "zombie_waves": [
      {"time": 30, "types": ["normal"], "count": 3}
    ],
    "win_condition": {"type": "survival", "duration": 120},
    "rewards": {"gold": 50, "unlock_plant": null}
  }
}
```

### 4.2 植物属性结构

```python
@dataclass
class PlantConfig:
    name: str
    cost: int
    hp: int
    damage: int
    cooldown: float
    sun_production: int
    category: str  # shooter, producer, defense, explosive
    unlock_level: int
    image_path: str
```

### 4.3 玩家存档结构

```json
{
  "version": "2.5.1",
  "player_name": "Player1",
  "total_gold": 1500,
  "completed_levels": ["level_001", "level_002"],
  "unlocked_plants": ["sunflower", "peashooter", "nut"],
  "zombie_defeated_count": {"normal": 150, "conehead": 80},
  "game_modes_progress": {
    "adventure": {"current_level": "level_003"},
    "survival": {"best_record": 300}
  },
  "settings": {"volume": 0.8, "fullscreen": false}
}
```

## 5. 性能优化策略

### 5.1 渲染优化

- **批处理渲染**: 合并相同纹理的绘制调用
- **视口裁剪**: 只渲染屏幕可见区域
- **层级排序**: 按 Z-order 分组渲染

### 5.2 内存管理

- **对象池**: 预分配粒子、子弹、阳光对象
- **资源懒加载**: 按需加载图片和音频
- **垃圾回收控制**: 避免在主循环中创建临时对象

### 5.3 碰撞检测优化

- **空间分区**: 网格哈希表 (Grid Hash Table)
- **宽相/窄相分离**: 先 AABB 粗筛，再像素级精检
- **时间片轮转**: 分散碰撞计算到多帧

## 6. 扩展指南

### 6.1 添加新植物

1. 定义配置类继承 `PlantConfig`
2. 实现植物类继承 `Plant` 基类
3. 在 `plant_database.py` 注册
4. 添加 JSON 配置
5. 放置图片资源

### 6.2 添加新僵尸

1. 定义配置类继承 `ZombieConfig`
2. 实现僵尸类继承 `Zombie` 基类
3. 在 `zombie_database.py` 注册
4. 在 `zombie_factory.py` 添加工厂方法
5. 配置 AI 行为树

### 6.3 添加新场景

1. 定义 `SceneType` 枚举值
2. 实现场景类继承 `Scene` 基类
3. 在 `scene_manager.py` 注册
4. 配置场景参数（背景、光照、特殊机制）

## 7. 测试策略

### 7.1 单元测试

- 测试核心算法（碰撞、经济计算）
- 测试工厂方法（植物/僵尸生成）
- 测试存档读写（边界条件、损坏恢复）

### 7.2 集成测试

- 完整关卡流程测试
- 多系统交互测试（商店 + 存档 + 图鉴）

### 7.3 性能测试

- FPS 稳定性测试（同屏 200+ 实体）
- 内存泄漏检测（长时间运行）
- 加载时间基准测试

## 8. 部署架构

```
开发环境 → 测试环境 → 生产环境
   ↓           ↓          ↓
Git 仓库   自动化测试   PyInstaller 打包
           CI/CD       多平台分发
```

## 9. 安全考虑

- **存档校验**: SHA256 哈希验证防篡改
- **输入验证**: 所有外部输入进行类型检查
- **异常捕获**: 全局 Try-Catch 防止崩溃
- **权限控制**: 最小权限原则访问文件系统

## 10. 未来规划

- [ ] 多人联机模块（WebSocket）
- [ ] Mod 支持系统（Lua 脚本）
- [ ] 成就系统（Steam API 集成）
- [ ] 云存档同步
- [ ] VR 模式实验

---

*文档版本：v2.5.1 | 最后更新：2024-01*
