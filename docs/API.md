# Plants vs Zombies - API 文档

完整 API 参考文档，包含所有核心模块、类和函数的详细说明。

## 目录

1. [核心系统](#核心系统)
2. [数据模块](#数据模块)
3. [游戏模式](#游戏模式)
4. [工具模块](#工具模块)

---

## 核心系统

### CombatSystem (战斗系统)

**位置**: `src/core/combat_system.py`

处理植物攻击、僵尸移动、碰撞检测等战斗逻辑。

#### 类：CombatEntity

表示战斗实体（植物或僵尸）。

```python
class CombatEntity:
    def __init__(
        self,
        entity_id: str,
        entity_type: str,
        health: int,
        max_health: int
    ) -> None
```

**方法**:
- `take_damage(amount: float) -> None`: 承受伤害
- `heal(amount: float) -> None`: 治疗
- `is_defeated() -> bool`: 是否被击败

#### 类：DamageCalculator

伤害计算器，支持暴击、护甲减免等。

```python
class DamageCalculator:
    def calculate_base_damage(plant_type: str, level: int) -> float
    def calculate_crit_damage(base_damage: float, crit_multiplier: float) -> float
```

#### 类：CollisionDetector

碰撞检测器，使用 AABB 算法。

```python
class CollisionDetector:
    def check_collision(rect1: Dict, rect2: Dict) -> bool
```

---

### EconomySystem (经济系统)

**位置**: `src/core/economy_system.py`

管理阳光生产、消费、植物成本计算。

#### 类：SunManager

阳光管理器，单例模式。

```python
class SunManager:
    def __init__(initial_sun: int = 50) -> None
    def collect_sun(amount: int) -> None
    def spend_sun(amount: int) -> bool
    def get_current_sun() -> int
```

#### 类：SunProducer

阳光生产者，处理植物产阳光逻辑。

```python
class SunProducer:
    def produce_sun(plant_type: str) -> int
```

#### 类：CostCalculator

成本计算器。

```python
class CostCalculator:
    def get_plant_cost(plant_type: str) -> int
```

---

### SaveSystem (存档系统)

**位置**: `src/core/save_system.py`

ACID 保证的存档系统，支持多槽位、校验和验证。

#### 类：SaveData

存档数据结构。

```python
@dataclass
class SaveData:
    player_name: str
    level_progress: Dict[str, Any]
    unlocked_plants: List[str]
    gold: int
    
    def to_dict() -> Dict[str, Any]
    @classmethod
    def from_dict(data: Dict) -> SaveData
```

#### 类：SaveSystem

存档系统，单例模式。

```python
class SaveSystem:
    def save_game(filepath: Path, data: Dict) -> bool
    def load_game(filepath: Path) -> Optional[Dict]
    def delete_save(slot: int) -> bool
    def get_save_list() -> List[Dict]
```

---

## 数据模块

### PlantDatabase (植物数据库)

**位置**: `src/data/plant_database.py`

49 种植物完整定义。

#### 类：PlantDatabase

```python
class PlantDatabase:
    def get_plant(plant_id: str) -> Optional[Dict]
    def get_all_plants() -> List[Dict]
    def get_plants_by_category(category: str) -> List[Dict]
```

**植物分类**:
- `attack`: 攻击类植物
- `defense`: 防御类植物
- `production`: 生产类植物
- `special`: 特殊类植物
- `upgrade`: 升级类植物

---

### ZombieDatabase (僵尸数据库)

**位置**: `src/data/zombie_database.py`

26 种僵尸完整定义。

#### 类：ZombieDatabase

```python
class ZombieDatabase:
    def get_zombie(zombie_id: str) -> Optional[Dict]
    def get_all_zombies() -> List[Dict]
    def get_zombies_by_scene(scene: str) -> List[Dict]
```

**僵尸分类**:
- `basic`: 基础僵尸
- `conehead`: 路障僵尸
- `buckethead`: 铁桶僵尸
- `special`: 特殊僵尸
- `boss`: BOSS 级僵尸

---

## 游戏模式

### GameModeSystem (游戏模式系统)

**位置**: `src/modes/game_modes.py`

5 大游戏模式框架。

#### 枚举：GameModeType

```python
class GameModeType(Enum):
    ADVENTURE = auto()      # 冒险模式
    MINI_GAME = auto()      # 迷你游戏
    PUZZLE = auto()         # 解谜模式
    SURVIVAL = auto()       # 生存模式
    ZEN_GARDEN = auto()     # 禅境花园
```

#### 基类：BaseGameMode

所有游戏模式的抽象基类。

```python
class BaseGameMode(ABC):
    @abstractmethod
    def start_level(level_id: str, **kwargs) -> bool
    
    @abstractmethod
    def update(dt: float) -> None
    
    @abstractmethod
    def render() -> Dict[str, Any]
    
    @abstractmethod
    def handle_input(event_type: str, data: Dict) -> bool
```

#### 类：GameModeFactory

游戏模式工厂，单例模式。

```python
class GameModeFactory:
    def create(mode_type: GameModeType | str) -> BaseGameMode
    def register_mode(mode_type: GameModeType, mode_class: Type) -> None
    def get_available_modes() -> List[Dict]
```

---

## 工具模块

### Profiler (性能剖析工具)

**位置**: `tools/profiler.py`

实时性能监控与报告生成。

#### 类：Profiler

单例模式。

```python
class Profiler:
    def start() -> None
    def stop() -> None
    
    @contextmanager
    def frame():
        # 记录帧时间
        yield
    
    def get_current_fps() -> float
    def get_average_fps(window_frames: int = 30) -> float
    def generate_report(filepath: Optional[Path]) -> PerformanceReport
```

#### 装饰器：profile_function

```python
@profile_function
def slow_function():
    time.sleep(0.1)
```

---

## 使用示例

### 1. 启动游戏模式

```python
from src.modes.game_modes import get_game_mode, GameModeType

# 创建冒险模式
mode = get_game_mode(GameModeType.ADVENTURE)

# 开始关卡
mode.start_level("1-1")

# 游戏循环
while running:
    mode.update(dt)
    render_data = mode.render()
    # ... 渲染逻辑
```

### 2. 管理阳光

```python
from src.core.economy_system import SunManager

manager = SunManager(initial_sun=50)

# 收集阳光
manager.collect_sun(25)

# 种植植物
if manager.spend_sun(100):
    place_plant("peashooter", x, y)
```

### 3. 保存进度

```python
from src.core.save_system import SaveSystem
from pathlib import Path

system = SaveSystem()

# 保存
save_data = {
    "player_name": "Player1",
    "level": "1-1",
    "score": 1000
}
system.save_game(Path("saves/save1.json"), save_data)

# 加载
loaded = system.load_game(Path("saves/save1.json"))
```

### 4. 性能监控

```python
from tools.profiler import get_profiler

profiler = get_profiler()
profiler.start()

# 游戏循环
while running:
    with profiler.frame():
        # 游戏逻辑
        pass

# 生成报告
report = profiler.generate_report("performance.json")
print(f"平均 FPS: {report.avg_fps}")
```

---

## 错误处理

所有模块均使用标准 Python 异常处理：

- `ValueError`: 无效参数
- `KeyError`: 未找到的资源
- `FileNotFoundError`: 文件不存在
- `JSONDecodeError`: 存档损坏

建议捕获具体异常类型：

```python
try:
    plant = db.get_plant("unknown_plant")
except KeyError as e:
    print(f"植物不存在：{e}")
```

---

## 版本信息

- **当前版本**: 1.0.0
- **API 稳定性**: 稳定
- **最后更新**: 2024
