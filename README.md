# Flappy ML Arena

A Flappy Bird clone designed for ML training data generation and model comparison.

## Features

- **Deterministic Simulation**: Same seed + same inputs = identical gameplay
- **Headless Mode**: 150,000+ FPS for fast training (5000x realtime)
- **Recording System**: Capture and replay any gameplay session
- **Compact Storage**: 31x compression using seed + inputs only
- **Multi-Viewer**: Watch multiple replays side-by-side in NxN grid
- **ML Feature Extraction**: Normalized features ready for model input

## Quick Start

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install pygame

# Play (generates training data)
python src/main.py

# Play with sound
python src/main.py --sound

# View recordings
python src/viewer.py --grid=2 src/recordings/*.json

# Run headless simulation
python src/headless.py
```

## Controls

- **SPACE**: Jump / Start
- **R**: Restart
- **ESC**: Quit

## Project Structure

```
src/
├── game.py       # Core game logic (pure Python, no dependencies)
├── renderer.py   # Pygame visualization
├── main.py       # Main game with recording
├── recording.py  # Recording save/load (verbose & compact)
├── playback.py   # Replay recordings visually
├── headless.py   # Fast simulation without rendering
├── features.py   # ML feature extraction
├── sound.py      # Optional sound effects
├── viewer.py     # Multi-render grid viewer
└── recordings/   # Saved gameplay sessions
```

## Architecture

The game uses a pure Python core (`game.py`) with rendering completely decoupled. This enables:

1. **Deterministic replays**: State serializes to JSON, identical inputs produce identical outputs
2. **Headless training**: No pygame dependency for ML training loops
3. **Feature extraction**: Clean interface for ML model inputs

## ML Approaches (Planned)

- [ ] Simple Genetic Algorithm
- [ ] NEAT (NeuroEvolution of Augmenting Topologies)
- [ ] Imitation Learning (Behavioral Cloning)
- [ ] DQN (Deep Q-Network)

## Recording Format

**Verbose**: Full state every frame (for debugging)
```json
{"seed": 12345, "frames": [{"frame": 1, "jump": false, "state": {...}}, ...]}
```

**Compact**: Just seed + inputs (31x smaller)
```json
{"format": "compact", "seed": 12345, "inputs": [false, false, true, ...]}
```

## License

MIT
