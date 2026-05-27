"""
Audio Management System - Industrial Grade
Comprehensive audio handling for Plants vs Zombies game.

Features:
- Background music management with crossfade
- Sound effect pooling and playback
- Volume control per category (music/SFX/voice)
- Audio asset preloading
- Mute/unmute functionality
- Dynamic music transitions
- Memory-efficient sound caching

Author: AI Assistant
Version: 4.0.0
"""

from typing import Dict, Optional, List, Any
from enum import Enum, auto
import pygame
import os
import json
from dataclasses import dataclass
from pathlib import Path


class AudioCategory(Enum):
    """Audio categorization for volume control"""
    MUSIC = auto()
    SFX = auto()
    VOICE = auto()
    AMBIENT = auto()


class MusicTrack(Enum):
    """Available music tracks"""
    MAIN_MENU = "main_menu"
    DAY_LEVEL = "day_level"
    NIGHT_LEVEL = "night_level"
    POOL_LEVEL = "pool_level"
    ROOF_LEVEL = "roof_level"
    FOG_LEVEL = "fog_level"
    BOSS_BATTLE = "boss_battle"
    GAME_OVER = "game_over"
    VICTORY = "victory"


class SoundEffect(Enum):
    """Available sound effects"""
    # Plant sounds
    PLANT_PLACE = "plant_place"
    PLANT_SHOOT = "plant_shoot"
    SUNFLOWER_PRODUCE = "sunflower_produce"
    CHERRY_BOMB_EXPLODE = "cherry_bomb_explode"
    JALAPENO_BURN = "jalapeno_burn"
    POTATO_MINE_ARM = "potato_mine_arm"
    POTATO_MINE_EXPLODE = "potato_mine_explode"
    
    # Zombie sounds
    ZOMBIE_GROAN = "zombie_groan"
    ZOMBIE_HURT = "zombie_hurt"
    ZOMBIE_DIE = "zombie_die"
    ZOMBIE_EAT = "zombie_eat"
    ZOMBIE_FALL = "zombie_fall"
    
    # UI sounds
    BUTTON_CLICK = "button_click"
    BUTTON_HOVER = "button_hover"
    MENU_OPEN = "menu_open"
    MENU_CLOSE = "menu_close"
    NOTIFICATION = "notification"
    
    # Game sounds
    SUN_COLLECT = "sun_collect"
    LAWNMOWER_START = "lawnmower_start"
    LAWNMOWER_RUN = "lawnmower_run"
    LAWNMOWER_HIT = "lawnmower_hit"
    LEVEL_START = "level_start"
    LEVEL_COMPLETE = "level_complete"
    WAVE_START = "wave_start"
    FINAL_WAVE = "final_wave"
    
    # Projectile sounds
    PEA_SHOOT = "pea_shoot"
    SNOW_PEA_SHOOT = "snow_pea_shoot"
    IMPACT = "impact"


@dataclass
class AudioConfig:
    """Configuration for audio system"""
    master_volume: float = 1.0
    music_volume: float = 0.7
    sfx_volume: float = 0.8
    voice_volume: float = 0.9
    ambient_volume: float = 0.5
    max_sound_channels: int = 32
    preload_all: bool = True
    audio_directory: str = "data/bgm"


class AudioManager:
    """Central manager for all audio operations"""
    
    _instance: Optional['AudioManager'] = None
    
    def __init__(self, config: Optional[AudioConfig] = None):
        if AudioManager._instance is not None:
            raise RuntimeError("AudioManager is a singleton. Use get_instance() instead.")
        
        self.config = config or AudioConfig()
        self.music_tracks: Dict[MusicTrack, Any] = {}
        self.sound_effects: Dict[SoundEffect, Any] = {}
        self.current_music: Optional[MusicTrack] = None
        self.is_music_playing = False
        self.is_muted = False
        self.volume_levels: Dict[AudioCategory, float] = {}
        self._channel_pool: List[int] = []
        self._active_channels: Dict[int, SoundEffect] = {}
        
        self._initialize_volumes()
        self._initialize_channel_pool()
        
    def _initialize_volumes(self) -> None:
        """Initialize volume levels for each category"""
        self.volume_levels = {
            AudioCategory.MUSIC: self.config.music_volume,
            AudioCategory.SFX: self.config.sfx_volume,
            AudioCategory.VOICE: self.config.voice_volume,
            AudioCategory.AMBIENT: self.config.ambient_volume
        }
        
    def _initialize_channel_pool(self) -> None:
        """Initialize sound channel pool"""
        pygame.mixer.set_num_channels(self.config.max_sound_channels)
        self._channel_pool = list(range(self.config.max_sound_channels))
        
    @classmethod
    def get_instance(cls, config: Optional[AudioConfig] = None) -> 'AudioManager':
        """Get singleton instance of AudioManager"""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    def initialize(self, audio_dir: Optional[str] = None) -> None:
        """Initialize audio system and load assets"""
        pygame.mixer.init()
        
        if audio_dir:
            self.config.audio_directory = audio_dir
            
        if self.config.preload_all:
            self._preload_all_assets()
            
        self.apply_master_volume(self.config.master_volume)
    
    def _preload_all_assets(self) -> None:
        """Preload all audio assets"""
        self._load_music_tracks()
        self._load_sound_effects()
    
    def _load_music_tracks(self) -> None:
        """Load all music tracks"""
        music_dir = Path(self.config.audio_directory) / "music"
        
        if not music_dir.exists():
            print(f"Warning: Music directory not found: {music_dir}")
            return
        
        for track in MusicTrack:
            try:
                # Try multiple file extensions
                for ext in ['.mp3', '.ogg', '.wav']:
                    file_path = music_dir / f"{track.value}{ext}"
                    if file_path.exists():
                        self.music_tracks[track] = str(file_path)
                        break
            except Exception as e:
                print(f"Warning: Failed to load music track {track.value}: {e}")
    
    def _load_sound_effects(self) -> None:
        """Load all sound effects"""
        sfx_dir = Path(self.config.audio_directory) / "sfx"
        
        if not sfx_dir.exists():
            print(f"Warning: SFX directory not found: {sfx_dir}")
            return
        
        for sfx in SoundEffect:
            try:
                # Try multiple file extensions
                for ext in ['.mp3', '.ogg', '.wav']:
                    file_path = sfx_dir / f"{sfx.value}{ext}"
                    if file_path.exists():
                        self.sound_effects[sfx] = pygame.mixer.Sound(str(file_path))
                        break
            except Exception as e:
                print(f"Warning: Failed to load sound effect {sfx.value}: {e}")
    
    def play_music(self, track: MusicTrack, fade_ms: int = 1000, loops: int = -1) -> None:
        """
        Play a music track with optional crossfade
        
        Args:
            track: Music track to play
            fade_ms: Fade-in duration in milliseconds
            loops: Number of loops (-1 for infinite)
        """
        if self.is_muted or self.volume_levels[AudioCategory.MUSIC] <= 0:
            return
        
        if track not in self.music_tracks:
            print(f"Warning: Music track {track.value} not loaded")
            return
        
        try:
            if self.current_music == track and self.is_music_playing:
                return  # Already playing this track
            
            # Fade out current music
            if self.is_music_playing:
                pygame.mixer.music.fadeout(fade_ms // 2)
            
            # Load and play new track
            pygame.mixer.music.load(self.music_tracks[track])
            pygame.mixer.music.play(loops, fade_ms)
            
            self.current_music = track
            self.is_music_playing = True
            
        except Exception as e:
            print(f"Error playing music {track.value}: {e}")
    
    def stop_music(self, fade_ms: int = 500) -> None:
        """Stop currently playing music with fade-out"""
        if self.is_music_playing:
            pygame.mixer.music.fadeout(fade_ms)
            self.is_music_playing = False
            self.current_music = None
    
    def pause_music(self) -> None:
        """Pause currently playing music"""
        if self.is_music_playing:
            pygame.mixer.music.pause()
    
    def unpause_music(self) -> None:
        """Unpause paused music"""
        if self.is_music_playing:
            pygame.mixer.music.unpause()
    
    def play_sound(self, sfx: SoundEffect, volume: Optional[float] = None,
                   channel: Optional[int] = None) -> Optional[int]:
        """
        Play a sound effect
        
        Args:
            sfx: Sound effect to play
            volume: Override volume (0.0 to 1.0)
            channel: Specific channel to use (optional)
            
        Returns:
            Channel ID if played successfully, None otherwise
        """
        if self.is_muted or self.volume_levels[AudioCategory.SFX] <= 0:
            return None
        
        if sfx not in self.sound_effects:
            return None
        
        try:
            sound = self.sound_effects[sfx]
            
            # Determine volume
            base_volume = self.volume_levels[AudioCategory.SFX]
            final_volume = volume if volume is not None else base_volume
            sound.set_volume(final_volume)
            
            # Get available channel
            if channel is not None:
                ch = channel
            else:
                ch = self._get_available_channel()
            
            if ch == -1:
                # No available channel, use find_channel to steal one
                ch = pygame.mixer.find_channel()
            
            if ch != -1:
                sound.play(channel=ch)
                self._active_channels[ch] = sfx
                return ch
                
        except Exception as e:
            print(f"Error playing sound effect {sfx.value}: {e}")
        
        return None
    
    def _get_available_channel(self) -> int:
        """Get an available sound channel"""
        # Check pool for free channels
        for ch in self._channel_pool[:]:
            if not pygame.mixer.Channel(ch).get_busy():
                return ch
            self._channel_pool.remove(ch)
        
        # Find any free channel
        for ch in range(self.config.max_sound_channels):
            if not pygame.mixer.Channel(ch).get_busy():
                return ch
        
        return -1  # No free channels
    
    def stop_sound(self, channel: int) -> None:
        """Stop sound on specific channel"""
        if 0 <= channel < self.config.max_sound_channels:
            pygame.mixer.Channel(channel).stop()
            if channel in self._active_channels:
                del self._active_channels[channel]
    
    def stop_all_sounds(self) -> None:
        """Stop all sound effects"""
        pygame.mixer.stop()
        self._active_channels.clear()
    
    def set_volume(self, category: AudioCategory, volume: float) -> None:
        """
        Set volume for a specific category
        
        Args:
            category: Audio category
            volume: Volume level (0.0 to 1.0)
        """
        volume = max(0.0, min(1.0, volume))
        self.volume_levels[category] = volume
        
        # Update music volume if applicable
        if category == AudioCategory.MUSIC and self.is_music_playing:
            pygame.mixer.music.set_volume(volume)
    
    def set_master_volume(self, volume: float) -> None:
        """
        Set master volume affecting all categories
        
        Args:
            volume: Master volume level (0.0 to 1.0)
        """
        self.config.master_volume = max(0.0, min(1.0, volume))
        self.apply_master_volume(self.config.master_volume)
    
    def apply_master_volume(self, volume: float) -> None:
        """Apply master volume multiplier to all categories"""
        base_volumes = {
            AudioCategory.MUSIC: self.config.music_volume,
            AudioCategory.SFX: self.config.sfx_volume,
            AudioCategory.VOICE: self.config.voice_volume,
            AudioCategory.AMBIENT: self.config.ambient_volume
        }
        
        for category, base in base_volumes.items():
            actual_volume = base * volume
            self.volume_levels[category] = actual_volume
        
        if self.is_music_playing:
            pygame.mixer.music.set_volume(self.volume_levels[AudioCategory.MUSIC])
    
    def mute(self) -> None:
        """Mute all audio"""
        self.is_muted = True
        pygame.mixer.pause()
    
    def unmute(self) -> None:
        """Unmute all audio"""
        self.is_muted = False
        pygame.mixer.unpause()
    
    def toggle_mute(self) -> bool:
        """Toggle mute state"""
        if self.is_muted:
            self.unmute()
        else:
            self.mute()
        return self.is_muted
    
    def is_sound_playing(self, channel: int) -> bool:
        """Check if sound is playing on specific channel"""
        if 0 <= channel < self.config.max_sound_channels:
            return pygame.mixer.Channel(channel).get_busy()
        return False
    
    def get_music_position(self) -> float:
        """Get current music position in seconds"""
        try:
            return pygame.mixer.music.get_pos() / 1000.0
        except:
            return 0.0
    
    def save_settings(self, filepath: str) -> None:
        """Save audio settings to file"""
        settings = {
            'master_volume': self.config.master_volume,
            'music_volume': self.config.music_volume,
            'sfx_volume': self.config.sfx_volume,
            'voice_volume': self.config.voice_volume,
            'ambient_volume': self.config.ambient_volume,
            'is_muted': self.is_muted
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving audio settings: {e}")
    
    def load_settings(self, filepath: str) -> bool:
        """Load audio settings from file"""
        try:
            with open(filepath, 'r') as f:
                settings = json.load(f)
            
            self.config.master_volume = settings.get('master_volume', 1.0)
            self.config.music_volume = settings.get('music_volume', 0.7)
            self.config.sfx_volume = settings.get('sfx_volume', 0.8)
            self.config.voice_volume = settings.get('voice_volume', 0.9)
            self.config.ambient_volume = settings.get('ambient_volume', 0.5)
            self.is_muted = settings.get('is_muted', False)
            
            self.apply_master_volume(self.config.master_volume)
            
            if self.is_muted:
                self.mute()
            
            return True
            
        except Exception as e:
            print(f"Error loading audio settings: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up audio resources"""
        self.stop_music()
        self.stop_all_sounds()
        pygame.mixer.quit()


# Convenience functions for global access
def get_audio_manager() -> AudioManager:
    """Get the global audio manager instance"""
    return AudioManager.get_instance()


def play_music(track: MusicTrack, fade_ms: int = 1000) -> None:
    """Play music track"""
    get_audio_manager().play_music(track, fade_ms)


def play_sound(sfx: SoundEffect, volume: Optional[float] = None) -> None:
    """Play sound effect"""
    get_audio_manager().play_sound(sfx, volume)


def set_master_volume(volume: float) -> None:
    """Set master volume"""
    get_audio_manager().set_master_volume(volume)


def toggle_mute() -> bool:
    """Toggle mute"""
    return get_audio_manager().toggle_mute()
