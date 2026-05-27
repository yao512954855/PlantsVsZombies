"""
单元测试套件 - 植物大战僵尸核心系统测试

包含单元测试和集成测试，覆盖战斗、经济、存档、工厂等核心模块。
测试覆盖率目标：>85%

运行方式:
    pytest tests/ -v --cov=src
    
生成覆盖率报告:
    coverage html
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from dataclasses import asdict

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestCombatSystem:
    """战斗系统测试"""
    
    def test_plant_attack_damage_calculation(self):
        """测试植物攻击伤害计算"""
        from src.core.combat_system import DamageCalculator
        
        calculator = DamageCalculator()
        
        # 基础伤害测试
        damage = calculator.calculate_base_damage("peashooter", 1)
        assert damage > 0
        assert isinstance(damage, (int, float))
        
        # 暴击测试
        crit_damage = calculator.calculate_crit_damage(damage, 2.0)
        assert crit_damage == damage * 2.0
    
    def test_zombie_health_reduction(self):
        """测试僵尸血量减少"""
        from src.core.combat_system import CombatEntity
        
        zombie = CombatEntity(
            entity_id="zombie_1",
            entity_type="zombie",
            health=100,
            max_health=100
        )
        
        zombie.take_damage(25)
        assert zombie.health == 75
        
        zombie.take_damage(30)
        assert zombie.health == 45
        
        zombie.take_damage(50)
        assert zombie.health == 0
        assert zombie.is_defeated()
    
    def test_collision_detection(self):
        """测试碰撞检测"""
        from src.core.combat_system import CollisionDetector
        
        detector = CollisionDetector()
        
        # 重叠矩形测试
        rect1 = {"x": 0, "y": 0, "width": 50, "height": 50}
        rect2 = {"x": 25, "y": 25, "width": 50, "height": 50}
        
        assert detector.check_collision(rect1, rect2) is True
        
        # 不重叠矩形测试
        rect3 = {"x": 100, "y": 100, "width": 50, "height": 50}
        assert detector.check_collision(rect1, rect3) is False


class TestEconomySystem:
    """经济系统测试"""
    
    def test_sun_production(self):
        """测试阳光生产"""
        from src.core.economy_system import SunProducer
        
        producer = SunProducer()
        
        # 向日葵产阳光
        sun_amount = producer.produce_sun("sunflower")
        assert sun_amount >= 25
        assert sun_amount <= 50
        
        # 双子向日葵产阳光
        sun_amount = producer.produce_sun("twin_sunflower")
        assert sun_amount >= 50
    
    def test_sun_manager_balance(self):
        """测试阳光管理器余额"""
        from src.core.economy_system import SunManager
        
        manager = SunManager(initial_sun=50)
        
        # 收集阳光
        manager.collect_sun(25)
        assert manager.current_sun == 75
        
        # 消费阳光
        success = manager.spend_sun(50)
        assert success is True
        assert manager.current_sun == 25
        
        # 余额不足
        success = manager.spend_sun(100)
        assert success is False
        assert manager.current_sun == 25
    
    def test_plant_cost_calculation(self):
        """测试植物成本计算"""
        from src.core.economy_system import CostCalculator
        
        calculator = CostCalculator()
        
        costs = {
            "peashooter": 100,
            "sunflower": 50,
            "wall_nut": 50,
            "cherry_bomb": 150
        }
        
        for plant, expected_cost in costs.items():
            cost = calculator.get_plant_cost(plant)
            assert cost == expected_cost


class TestSaveSystem:
    """存档系统测试"""
    
    def test_save_data_serialization(self):
        """测试存档数据序列化"""
        from src.core.save_system import SaveData
        
        save_data = SaveData(
            player_name="TestPlayer",
            level_progress={"1-1": {"stars": 3, "completed": True}},
            unlocked_plants=["peashooter", "sunflower"],
            gold=1000
        )
        
        data_dict = save_data.to_dict()
        assert isinstance(data_dict, dict)
        assert data_dict["player_name"] == "TestPlayer"
        assert data_dict["gold"] == 1000
    
    def test_save_load_roundtrip(self):
        """测试存档加载往返"""
        from src.core.save_system import SaveSystem
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            system = SaveSystem()
            
            # 保存
            original_data = {
                "player_name": "TestPlayer",
                "level": "1-1",
                "score": 500
            }
            system.save_game(temp_path, original_data)
            
            # 加载
            loaded_data = system.load_game(temp_path)
            
            assert loaded_data["player_name"] == original_data["player_name"]
            assert loaded_data["level"] == original_data["level"]
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_checksum_validation(self):
        """测试校验和验证"""
        from src.core.save_system import SaveSystem
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            system = SaveSystem()
            test_data = {"test": "data"}
            system.save_game(temp_path, test_data)
            
            # 读取并验证校验和
            with open(temp_path, 'r') as f:
                saved = json.load(f)
            
            assert "checksum" in saved
            assert system._validate_checksum(saved) is True
        finally:
            temp_path.unlink(missing_ok=True)


class TestZombieFactory:
    """僵尸工厂测试"""
    
    def test_zombie_spawn_basic(self):
        """测试基础僵尸生成"""
        from src.core.zombie_factory import ZombieFactory
        
        factory = ZombieFactory()
        
        zombie = factory.spawn_zombie("basic", lane=2)
        
        assert zombie is not None
        assert zombie["type"] == "basic"
        assert zombie["lane"] == 2
        assert "health" in zombie
        assert "speed" in zombie
    
    def test_wave_generation(self):
        """测试波次生成"""
        from src.core.zombie_factory import WaveGenerator
        
        generator = WaveGenerator(difficulty=1.0)
        
        wave = generator.generate_wave(wave_number=1, level_id="1-1")
        
        assert isinstance(wave, list)
        assert len(wave) > 0
        assert all("spawn_time" in z for z in wave)
    
    def test_difficulty_scaling(self):
        """测试难度缩放"""
        from src.core.zombie_factory import WaveGenerator
        
        gen_easy = WaveGenerator(difficulty=0.5)
        gen_hard = WaveGenerator(difficulty=2.0)
        
        wave_easy = gen_easy.generate_wave(1, "1-1")
        wave_hard = gen_hard.generate_wave(1, "1-1")
        
        # 高难度应该生成更多僵尸
        assert len(wave_hard) >= len(wave_easy)


class TestLevelManager:
    """关卡管理器测试"""
    
    def test_level_config_loading(self):
        """测试关卡配置加载"""
        from src.core.level_manager import LevelManager
        
        manager = LevelManager()
        
        config = manager.get_level_config("1-1")
        
        assert config is not None
        assert "scene_type" in config
        assert "zombie_waves" in config
    
    def test_scene_type_validation(self):
        """测试场景类型验证"""
        from src.core.level_manager import LevelManager
        
        manager = LevelManager()
        
        valid_scenes = ["day", "night", "pool", "roof", "fog"]
        
        for scene in valid_scenes:
            assert manager.validate_scene_type(scene) is True
        
        assert manager.validate_scene_type("invalid") is False


class TestPlantDatabase:
    """植物数据库测试"""
    
    def test_plant_retrieval(self):
        """测试植物检索"""
        from src.data.plant_database import PlantDatabase
        
        db = PlantDatabase()
        
        plant = db.get_plant("peashooter")
        
        assert plant is not None
        assert plant["name"] == "Peashooter"
        assert "cost" in plant
        assert "damage" in plant
    
    def test_all_plants_present(self):
        """测试所有植物存在"""
        from src.data.plant_database import PlantDatabase
        
        db = PlantDatabase()
        all_plants = db.get_all_plants()
        
        # 应该有至少 10 种植物
        assert len(all_plants) >= 10
        
        # 检查关键植物
        required_plants = ["peashooter", "sunflower", "wall_nut", "cherry_bomb"]
        for plant_name in required_plants:
            assert any(p["id"] == plant_name for p in all_plants)


class TestZombieDatabase:
    """僵尸数据库测试"""
    
    def test_zombie_retrieval(self):
        """测试僵尸检索"""
        from src.data.zombie_database import ZombieDatabase
        
        db = ZombieDatabase()
        
        zombie = db.get_zombie("basic")
        
        assert zombie is not None
        assert "health" in zombie
        assert "speed" in zombie
    
    def test_all_zombies_present(self):
        """测试所有僵尸存在"""
        from src.data.zombie_database import ZombieDatabase
        
        db = ZombieDatabase()
        all_zombies = db.get_all_zombies()
        
        # 应该有至少 3 种僵尸
        assert len(all_zombies) >= 3


class TestShopSystem:
    """商店系统测试"""
    
    def test_shop_item_purchase(self):
        """测试商店物品购买"""
        from src.systems.shop_system import ShopSystem
        
        shop = ShopSystem(player_gold=500)
        
        # 购买成功
        success, message = shop.purchase_item("peashooter_card")
        assert success is True
        assert shop.player_gold < 500
        
        # 余额不足
        current_gold = shop.player_gold
        success, message = shop.purchase_item("expensive_item")
        assert success is False
        assert shop.player_gold == current_gold
    
    def test_shop_inventory(self):
        """测试商店库存"""
        from src.systems.shop_system import ShopSystem
        
        shop = ShopSystem()
        inventory = shop.get_available_items()
        
        assert isinstance(inventory, list)
        assert len(inventory) > 0


class TestGameModes:
    """游戏模式测试"""
    
    def test_adventure_mode_start(self):
        """测试冒险模式启动"""
        from src.modes.game_modes import AdventureMode
        
        mode = AdventureMode()
        success = mode.start_level("1-1")
        
        assert success is True
        assert mode.current_level == "1-1"
        assert mode.phase.name == "RUNNING"
    
    def test_survival_mode_wave_spawning(self):
        """测试生存模式波次生成"""
        from src.modes.game_modes import SurvivalMode
        
        mode = SurvivalMode()
        mode.start_level("survival_day")
        
        initial_wave = mode.current_wave
        mode.update(61.0)  # 超过波次间隔
        
        assert mode.current_wave >= initial_wave
    
    def test_game_mode_factory(self):
        """测试游戏模式工厂"""
        from src.modes.game_modes import GameModeFactory, GameModeType
        
        factory = GameModeFactory()
        
        adventure = factory.create(GameModeType.ADVENTURE)
        assert adventure is not None
        assert adventure.__class__.__name__ == "AdventureMode"
        
        survival = factory.create("survival")
        assert survival is not None
        assert survival.__class__.__name__ == "SurvivalMode"


class TestIntegration:
    """集成测试"""
    
    def test_full_game_loop(self):
        """测试完整游戏循环"""
        from src.core.economy_system import SunManager
        from src.core.combat_system import CombatEntity
        from src.core.zombie_factory import ZombieFactory
        
        # 初始化系统
        sun_manager = SunManager(initial_sun=100)
        factory = ZombieFactory()
        
        # 收集阳光
        sun_manager.collect_sun(50)
        assert sun_manager.current_sun == 150
        
        # 生成僵尸
        zombie_data = factory.spawn_zombie("basic", lane=1)
        zombie = CombatEntity(
            entity_id="zombie_1",
            entity_type="zombie",
            health=zombie_data["health"],
            max_health=zombie_data["health"]
        )
        
        # 战斗
        zombie.take_damage(20)
        assert zombie.health < zombie.max_health
    
    def test_save_progress_integration(self):
        """测试存档进度集成"""
        from src.core.save_system import SaveSystem
        from src.modes.game_modes import AdventureMode
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # 开始冒险模式
            mode = AdventureMode()
            mode.start_level("1-1")
            mode.end_level(success=True, score=1000, time_elapsed=60.0)
            
            # 保存进度
            mode.save_progress(temp_path)
            
            # 验证文件存在
            assert temp_path.exists()
            
            # 加载并验证
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert "1-1" in data
            assert data["1-1"]["completed"] is True
            assert data["1-1"]["stars"] >= 1
        finally:
            temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
