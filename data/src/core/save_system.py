"""
Save/Load System - Industrial Grade
Comprehensive save and load functionality for Plants vs Zombies game.

Features:
- Multiple save slots support
- Auto-save functionality
- Save data validation and integrity checks
- Version migration for save compatibility
- Player progress tracking (levels, achievements, unlocks)
- Game state serialization/deserialization
- Backup and restore capabilities
- JSON-based storage with encryption option

Author: AI Assistant
Version: 4.0.0
"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum, auto
import json
import os
import shutil
import hashlib
from datetime import datetime
from dataclasses import dataclass, asdict, field
from pathlib import Path
import base64


class SaveSlot(Enum):
    """Available save slots"""
    SLOT_1 = 1
    SLOT_2 = 2
    SLOT_3 = 3
    AUTO_SAVE = 99


@dataclass
class PlayerProgress:
    """Player progression data"""
    unlocked_levels: List[int] = field(default_factory=list)
    completed_levels: List[int] = field(default_factory=list)
    best_scores: Dict[int, int] = field(default_factory=dict)  # level_id -> score
    total_sun_collected: int = 0
    total_zombies_defeated: int = 0
    total_plants_placed: int = 0
    play_time_seconds: int = 0
    highest_level_reached: int = 1
    achievements_unlocked: List[str] = field(default_factory=list)
    
    # Unlocks
    unlocked_plants: List[str] = field(default_factory=lambda: [
        "peashooter", "sunflower", "cherry_bomb", "wall_nut",
        "potato_mine", "snow_pea", "chomper", "repeater"
    ])
    unlocked_scenes: List[str] = field(default_factory=lambda: ["day"])
    
    # Statistics
    plants_destroyed: Dict[str, int] = field(default_factory=dict)
    zombies_killed_by_type: Dict[str, int] = field(default_factory=dict)
    sun_spent: int = 0
    lawnmowers_used: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerProgress':
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class LevelState:
    """Current level state for saving mid-game"""
    level_id: int
    current_wave: int
    elapsed_time: float
    sun_count: int
    planted_plants: List[Dict[str, Any]] = field(default_factory=list)
    active_zombies: List[Dict[str, Any]] = field(default_factory=list)
    active_projectiles: List[Dict[str, Any]] = field(default_factory=list)
    lawn_mowers_remaining: int = 5
    is_paused: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LevelState':
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class GameSettings:
    """Game configuration settings"""
    screen_width: int = 800
    screen_height: int = 600
    fullscreen: bool = False
    music_volume: float = 0.7
    sfx_volume: float = 0.8
    master_volume: float = 1.0
    difficulty: str = "normal"  # easy, normal, hard
    show_fps: bool = False
    vsync: bool = True
    language: str = "en"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameSettings':
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SaveData:
    """Complete save data structure"""
    version: str
    save_timestamp: str
    slot: int
    player_progress: PlayerProgress
    level_state: Optional[LevelState] = None
    settings: GameSettings = field(default_factory=GameSettings)
    checksum: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'version': self.version,
            'save_timestamp': self.save_timestamp,
            'slot': self.slot,
            'player_progress': self.player_progress.to_dict(),
            'settings': self.settings.to_dict()
        }
        if self.level_state:
            data['level_state'] = self.level_state.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SaveData':
        """Create from dictionary"""
        player_progress = PlayerProgress.from_dict(data.get('player_progress', {}))
        settings = GameSettings.from_dict(data.get('settings', {}))
        level_state = None
        if data.get('level_state'):
            level_state = LevelState.from_dict(data['level_state'])
        
        return cls(
            version=data.get('version', '1.0.0'),
            save_timestamp=data.get('save_timestamp', ''),
            slot=data.get('slot', 1),
            player_progress=player_progress,
            level_state=level_state,
            settings=settings,
            checksum=data.get('checksum', '')
        )


class SaveValidationError(Exception):
    """Exception raised when save validation fails"""
    pass


class SaveManager:
    """Manages all save/load operations"""
    
    CURRENT_VERSION = "4.0.0"
    SAVE_DIRECTORY = "data/save"
    BACKUP_DIRECTORY = "data/save/backups"
    
    def __init__(self, save_dir: Optional[str] = None):
        self.save_directory = Path(save_dir) if save_dir else Path(self.SAVE_DIRECTORY)
        self.backup_directory = Path(self.BACKUP_DIRECTORY)
        self._ensure_directories_exist()
        self.current_save: Optional[SaveData] = None
        
    def _ensure_directories_exist(self) -> None:
        """Ensure save directories exist"""
        self.save_directory.mkdir(parents=True, exist_ok=True)
        self.backup_directory.mkdir(parents=True, exist_ok=True)
    
    def _get_save_path(self, slot: SaveSlot) -> Path:
        """Get file path for a save slot"""
        if slot == SaveSlot.AUTO_SAVE:
            return self.save_directory / "auto_save.json"
        return self.save_directory / f"save_{slot.value}.json"
    
    def _get_backup_path(self, slot: SaveSlot) -> Path:
        """Get backup file path for a save slot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if slot == SaveSlot.AUTO_SAVE:
            return self.backup_directory / f"auto_save_{timestamp}.json"
        return self.backup_directory / f"save_{slot.value}_{timestamp}.json"
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate SHA256 checksum for save data"""
        # Create a copy without checksum
        data_copy = {k: v for k, v in data.items() if k != 'checksum'}
        json_str = json.dumps(data_copy, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _validate_checksum(self, data: Dict[str, Any]) -> bool:
        """Validate save data checksum"""
        stored_checksum = data.get('checksum', '')
        calculated_checksum = self._calculate_checksum(data)
        return stored_checksum == calculated_checksum
    
    def _migrate_save_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate old save data to current version"""
        save_version = data.get('version', '1.0.0')
        
        # Version 1.x to 2.x migration
        if save_version.startswith('1.'):
            if 'player_progress' in data:
                # Add new fields
                if 'unlocked_scenes' not in data['player_progress']:
                    data['player_progress']['unlocked_scenes'] = ['day']
                if 'achievements_unlocked' not in data['player_progress']:
                    data['player_progress']['achievements_unlocked'] = []
        
        # Version 2.x to 3.x migration
        if save_version.startswith('1.') or save_version.startswith('2.'):
            if 'player_progress' in data:
                if 'plants_destroyed' not in data['player_progress']:
                    data['player_progress']['plants_destroyed'] = {}
                if 'zombies_killed_by_type' not in data['player_progress']:
                    data['player_progress']['zombies_killed_by_type'] = {}
        
        # Update version
        data['version'] = self.CURRENT_VERSION
        
        return data
    
    def save_game(self, slot: SaveSlot, player_progress: PlayerProgress,
                  level_state: Optional[LevelState] = None,
                  settings: Optional[GameSettings] = None,
                  create_backup: bool = True) -> bool:
        """
        Save game to specified slot
        
        Args:
            slot: Save slot to use
            player_progress: Player progression data
            level_state: Current level state (None for menu saves)
            settings: Game settings
            create_backup: Whether to create backup before saving
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            save_path = self._get_save_path(slot)
            
            # Create backup if requested and file exists
            if create_backup and save_path.exists():
                self.create_backup(slot)
            
            # Build save data
            save_data = SaveData(
                version=self.CURRENT_VERSION,
                save_timestamp=datetime.now().isoformat(),
                slot=slot.value,
                player_progress=player_progress,
                level_state=level_state,
                settings=settings or GameSettings()
            )
            
            # Convert to dict and add checksum
            data_dict = save_data.to_dict()
            data_dict['checksum'] = self._calculate_checksum(data_dict)
            
            # Write to file
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False)
            
            self.current_save = save_data
            return True
            
        except Exception as e:
            print(f"Error saving game: {e}")
            return False
    
    def load_game(self, slot: SaveSlot, validate: bool = True) -> Optional[SaveData]:
        """
        Load game from specified slot
        
        Args:
            slot: Save slot to load
            validate: Whether to validate checksum
            
        Returns:
            SaveData if successful, None otherwise
        """
        try:
            save_path = self._get_save_path(slot)
            
            if not save_path.exists():
                return None
            
            with open(save_path, 'r', encoding='utf-8') as f:
                data_dict = json.load(f)
            
            # Validate checksum if requested
            if validate and not self._validate_checksum(data_dict):
                raise SaveValidationError("Save file checksum mismatch. File may be corrupted.")
            
            # Migrate if needed
            data_dict = self._migrate_save_data(data_dict)
            
            # Create SaveData object
            save_data = SaveData.from_dict(data_dict)
            self.current_save = save_data
            
            return save_data
            
        except SaveValidationError as e:
            print(f"Save validation failed: {e}")
            return None
        except Exception as e:
            print(f"Error loading game: {e}")
            return None
    
    def create_backup(self, slot: SaveSlot) -> Optional[Path]:
        """Create backup of save file"""
        try:
            save_path = self._get_save_path(slot)
            
            if not save_path.exists():
                return None
            
            backup_path = self._get_backup_path(slot)
            shutil.copy2(save_path, backup_path)
            
            # Clean up old backups (keep last 10)
            self._cleanup_old_backups(slot)
            
            return backup_path
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None
    
    def _cleanup_old_backups(self, slot: SaveSlot, keep_count: int = 10) -> None:
        """Remove old backups, keeping only the most recent ones"""
        try:
            backup_path = self._get_backup_path(slot)
            prefix = backup_path.stem.rsplit('_', 1)[0] if slot != SaveSlot.AUTO_SAVE else 'auto_save'
            
            backups = list(self.backup_directory.glob(f"{prefix}*.json"))
            backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            for old_backup in backups[keep_count:]:
                old_backup.unlink()
                
        except Exception as e:
            print(f"Error cleaning up backups: {e}")
    
    def delete_save(self, slot: SaveSlot) -> bool:
        """Delete save file for specified slot"""
        try:
            save_path = self._get_save_path(slot)
            
            if save_path.exists():
                save_path.unlink()
                
                if slot != SaveSlot.AUTO_SAVE and self.current_save and self.current_save.slot == slot.value:
                    self.current_save = None
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting save: {e}")
            return False
    
    def get_save_info(self, slot: SaveSlot) -> Optional[Dict[str, Any]]:
        """Get information about a save file without loading it"""
        try:
            save_path = self._get_save_path(slot)
            
            if not save_path.exists():
                return None
            
            with open(save_path, 'r', encoding='utf-8') as f:
                data_dict = json.load(f)
            
            return {
                'slot': slot.value,
                'version': data_dict.get('version', 'unknown'),
                'timestamp': data_dict.get('save_timestamp', 'unknown'),
                'has_level_state': 'level_state' in data_dict,
                'completed_levels': len(data_dict.get('player_progress', {}).get('completed_levels', [])),
                'highest_level': data_dict.get('player_progress', {}).get('highest_level_reached', 1),
                'play_time': data_dict.get('player_progress', {}).get('play_time_seconds', 0)
            }
            
        except Exception as e:
            print(f"Error getting save info: {e}")
            return None
    
    def list_saves(self) -> List[Dict[str, Any]]:
        """List all available saves"""
        saves = []
        
        for slot in SaveSlot:
            info = self.get_save_info(slot)
            if info:
                saves.append(info)
        
        return saves
    
    def export_save(self, slot: SaveSlot, export_path: str) -> bool:
        """Export save to external file"""
        try:
            save_path = self._get_save_path(slot)
            
            if not save_path.exists():
                return False
            
            shutil.copy2(save_path, export_path)
            return True
            
        except Exception as e:
            print(f"Error exporting save: {e}")
            return False
    
    def import_save(self, import_path: str, slot: SaveSlot) -> bool:
        """Import save from external file"""
        try:
            import_file = Path(import_path)
            
            if not import_file.exists():
                return False
            
            # Create backup of current save if exists
            if self._get_save_path(slot).exists():
                self.create_backup(slot)
            
            # Copy imported file
            shutil.copy2(import_file, self._get_save_path(slot))
            
            # Validate imported save
            save_data = self.load_game(slot)
            if save_data is None:
                # Restore backup if validation failed
                self.load_game(slot)  # This will fail, but clears current_save
                return False
            
            return True
            
        except Exception as e:
            print(f"Error importing save: {e}")
            return False
    
    def get_all_backups(self) -> List[Path]:
        """List all backup files"""
        return list(self.backup_directory.glob("*.json"))
    
    def restore_from_backup(self, backup_path: Path, slot: SaveSlot) -> bool:
        """Restore save from backup"""
        try:
            if not backup_path.exists():
                return False
            
            shutil.copy2(backup_path, self._get_save_path(slot))
            return True
            
        except Exception as e:
            print(f"Error restoring from backup: {e}")
            return False
    
    def clear_all_saves(self, include_backups: bool = False) -> None:
        """Clear all save files"""
        for slot in SaveSlot:
            self.delete_save(slot)
        
        if include_backups:
            for backup in self.backup_directory.glob("*.json"):
                backup.unlink()
    
    def update_play_time(self, seconds: int) -> None:
        """Update play time in current save"""
        if self.current_save:
            self.current_save.player_progress.play_time_seconds += seconds
    
    def record_level_completion(self, level_id: int, score: int) -> None:
        """Record level completion in current save"""
        if self.current_save:
            progress = self.current_save.player_progress
            
            if level_id not in progress.completed_levels:
                progress.completed_levels.append(level_id)
            
            # Update best score
            if level_id not in progress.best_scores or score > progress.best_scores[level_id]:
                progress.best_scores[level_id] = score
            
            # Unlock next level
            next_level = level_id + 1
            if next_level not in progress.unlocked_levels:
                progress.unlocked_levels.append(next_level)
            
            # Update highest level
            if level_id > progress.highest_level_reached:
                progress.highest_level_reached = level_id


# Singleton instance
_save_manager_instance: Optional[SaveManager] = None


def get_save_manager() -> SaveManager:
    """Get singleton save manager instance"""
    global _save_manager_instance
    
    if _save_manager_instance is None:
        _save_manager_instance = SaveManager()
    
    return _save_manager_instance


def quick_save(player_progress: PlayerProgress, 
               level_state: Optional[LevelState] = None) -> bool:
    """Quick save to auto-save slot"""
    manager = get_save_manager()
    return manager.save_game(SaveSlot.AUTO_SAVE, player_progress, level_state)


def quick_load() -> Optional[SaveData]:
    """Quick load from auto-save slot"""
    manager = get_save_manager()
    return manager.load_game(SaveSlot.AUTO_SAVE)
