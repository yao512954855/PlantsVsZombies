# Plants vs Zombies - 工业级重构项目

基于经典游戏《植物大战僵尸》的工业级重构版本，采用现代化的软件架构和开发标准。

## 🎮 游戏特性

### 核心玩法
- **50+ 关卡**：完整的冒险模式关卡设计
- **49 种植物**：包含攻击型、防御型、辅助型植物
- **26 种僵尸**：多样化的僵尸类型和行为模式
- **4 大场景**：白天、黑夜、屋顶、水池场景支持

### 游戏模式
- **冒险模式**：主线故事关卡
- **迷你游戏**：多样化的小游戏挑战
- **解谜模式**：智慧挑战关卡
- **生存模式**：无尽挑战模式
- **禅境花园**：植物养成系统

### 系统特性
- **存档系统**：ACID 合规的存档机制，支持多存档槽位
- **商店系统**：双货币系统，动态定价和折扣机制
- **音频系统**：背景音乐管理，支持音量控制
- **粒子系统**：丰富的特效效果（爆炸、烟雾、火花等）

## 🏗️ 项目架构

```
PlantsVsZombies/
├── main.py                    # 入口文件
├── data/
│   ├── src/
│   │   ├── PVZ.py             # 游戏核心类
│   │   ├── Game.py            # 游戏逻辑核心
│   │   ├── level_manager.py   # 关卡管理器
│   │   ├── scene_manager.py   # 场景管理器
│   │   ├── zombie_factory.py  # 僵尸工厂
│   │   ├── particle_system.py # 粒子特效引擎
│   │   ├── ui_components.py   # UI组件库
│   │   └── core/
│   │       ├── save_system.py # 存档系统
│   │       └── audio_system.py # 音频系统
│   └── ...
├── src/
│   ├── data/
│   │   ├── plant_database.py  # 植物数据库
│   │   └── zombie_database.py # 僵尸数据库
│   ├── modes/
│   │   └── game_modes.py      # 游戏模式系统
│   └── systems/
│       └── shop_system.py     # 商店系统
├── tests/                     # 单元测试
├── build/                     # 打包脚本
└── TODO.md                    # 开发计划
```

## 🛠️ 技术栈

- **Python 3.11+**：主开发语言
- **Pygame 2.5+**：游戏引擎
- **PyInstaller 6.5+**：打包工具
- **unittest**：单元测试框架

## 🚀 快速开始

### 环境要求
- Python 3.11 或更高版本
- Windows 10/11（推荐）

### 安装依赖

```bash
pip install -r build/requirements.txt
```

### 运行游戏

```bash
python main.py
```

### 构建可执行文件

```bash
python build/build.py
```

## 📁 文件结构说明

### 核心模块

| 文件 | 说明 |
|------|------|
| `main.py` | 应用入口，游戏初始化和主循环 |
| `data/src/PVZ.py` | 游戏核心类，管理游戏状态和界面 |
| `data/src/Game.py` | 游戏逻辑核心，碰撞检测和对象管理 |

### 管理器模块

| 文件 | 说明 |
|------|------|
| `level_manager.py` | 关卡配置和进度管理 |
| `scene_manager.py` | 场景切换和渲染管理 |
| `zombie_factory.py` | 僵尸波次生成和管理 |

### 数据模块

| 文件 | 说明 |
|------|------|
| `plant_database.py` | 49种植物属性配置 |
| `zombie_database.py` | 26种僵尸属性配置 |

### 系统模块

| 文件 | 说明 |
|------|------|
| `save_system.py` | 存档读写和校验 |
| `audio_system.py` | 背景音乐和音效管理 |
| `shop_system.py` | 商店购买和金币系统 |
| `game_modes.py` | 5种游戏模式实现 |

### 特效和UI模块

| 文件 | 说明 |
|------|------|
| `particle_system.py` | 粒子特效引擎 |
| `ui_components.py` | 专业UI组件库 |

## ✅ 工业级标准

### 代码规范
- ✅ 类型注解（Type Hints）
- ✅ 文档字符串（Docstrings）
- ✅ 错误处理机制
- ✅ 单元测试覆盖

### 架构设计
- ✅ 模块化设计
- ✅ 单例模式（管理器类）
- ✅ 策略模式（游戏模式）
- ✅ 事件驱动架构

### 数据管理
- ✅ 数据驱动设计
- ✅ 配置与代码分离
- ✅ 存档完整性校验

## 📋 开发计划

### 已完成
- [x] 第一阶段：框架搭建和核心功能
- [x] 第二阶段：关卡和场景系统
- [x] 第三阶段：植物和僵尸数据库
- [x] 第四阶段：特效和UI系统
- [x] 第五阶段：测试和打包

### 待优化
- [ ] 性能优化（渲染批处理）
- [ ] 网络功能（排行榜）
- [ ] MOD 支持

## 📝 许可证

本项目仅供学习和研究使用，不用于商业用途。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

*Plants vs Zombies is a trademark of PopCap Games. This is a fan-made project for educational purposes.*