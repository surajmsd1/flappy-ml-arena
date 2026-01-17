"""
Sound system for Flappy Bird.

Features:
- Lazy loading: sounds only loaded when enabled
- Auto-disable: when >3 game renders are active
- No dependencies on pygame unless sound is enabled
"""

from typing import Optional
import os

# Sound state
_sound_enabled = False
_sounds_loaded = False
_mixer_initialized = False
_active_renders = 0

# Sound objects (only populated when enabled)
_sounds = {
    'flap': None,
    'score': None,
    'death': None,
}

# Sound file paths (relative to src/)
SOUND_DIR = os.path.join(os.path.dirname(__file__), 'assets', 'sounds')


def init_sound(enabled: bool = False) -> bool:
    """
    Initialize sound system.

    Args:
        enabled: Whether to enable sound

    Returns:
        True if sound was successfully initialized
    """
    global _sound_enabled, _sounds_loaded, _mixer_initialized

    if not enabled:
        _sound_enabled = False
        return False

    try:
        import pygame.mixer

        if not _mixer_initialized:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            _mixer_initialized = True

        _sound_enabled = True
        _load_sounds()
        return True

    except Exception as e:
        print(f"Warning: Could not initialize sound: {e}")
        _sound_enabled = False
        return False


def _load_sounds():
    """Load sound files. Only called if sound is enabled."""
    global _sounds_loaded, _sounds

    if _sounds_loaded:
        return

    try:
        import pygame.mixer

        # Try to load sounds, use generated sounds if files don't exist
        sound_files = {
            'flap': 'flap.wav',
            'score': 'score.wav',
            'death': 'death.wav',
        }

        for name, filename in sound_files.items():
            filepath = os.path.join(SOUND_DIR, filename)
            if os.path.exists(filepath):
                _sounds[name] = pygame.mixer.Sound(filepath)
            else:
                # Generate simple placeholder sounds
                _sounds[name] = _generate_sound(name)

        _sounds_loaded = True

    except Exception as e:
        print(f"Warning: Could not load sounds: {e}")


def _generate_sound(name: str):
    """Generate a simple placeholder sound."""
    try:
        import pygame.mixer
        import array

        # Generate simple sine wave beeps
        sample_rate = 22050

        if name == 'flap':
            # Short high-pitched chirp
            duration = 0.05
            frequency = 800
        elif name == 'score':
            # Medium pleasant tone
            duration = 0.1
            frequency = 600
        elif name == 'death':
            # Longer low tone
            duration = 0.2
            frequency = 200
        else:
            duration = 0.1
            frequency = 440

        n_samples = int(sample_rate * duration)

        # Generate sine wave
        import math
        samples = array.array('h', [
            int(32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate))
            for i in range(n_samples)
        ])

        # Create stereo sound (duplicate mono to both channels)
        stereo_samples = array.array('h')
        for sample in samples:
            stereo_samples.append(sample)  # Left
            stereo_samples.append(sample)  # Right

        sound = pygame.mixer.Sound(buffer=stereo_samples)
        return sound

    except Exception:
        return None


def register_render():
    """Register an active game render. Auto-disables sound if >3 renders."""
    global _active_renders, _sound_enabled
    _active_renders += 1

    if _active_renders > 3 and _sound_enabled:
        _sound_enabled = False


def unregister_render():
    """Unregister an active game render."""
    global _active_renders
    _active_renders = max(0, _active_renders - 1)


def play_flap():
    """Play flap sound effect."""
    _play('flap')


def play_score():
    """Play score sound effect."""
    _play('score')


def play_death():
    """Play death sound effect."""
    _play('death')


def _play(name: str):
    """Play a sound by name."""
    if not _sound_enabled or _sounds.get(name) is None:
        return

    try:
        _sounds[name].play()
    except Exception:
        pass  # Silently ignore playback errors


def is_enabled() -> bool:
    """Check if sound is currently enabled."""
    return _sound_enabled


def shutdown():
    """Shut down the sound system."""
    global _sound_enabled, _sounds_loaded, _mixer_initialized, _sounds

    if _mixer_initialized:
        try:
            import pygame.mixer
            pygame.mixer.quit()
        except Exception:
            pass

    _sound_enabled = False
    _sounds_loaded = False
    _mixer_initialized = False
    _sounds = {k: None for k in _sounds}
