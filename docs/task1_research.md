# Task 1: Research & Engine Selection

## Flappy Bird Game Mechanics

Based on analysis of the original game and popular open-source clones:

### Screen Dimensions
- **Width:** 288 pixels
- **Height:** 512 pixels
- Aspect ratio: ~0.56 (portrait orientation)

### Bird Properties
- **Size:** 34x24 pixels (width x height)
- **Starting position:** x=50, y=256 (center height)
- **Rotation range:** -25° (up) to 90° (down)

### Physics Constants
| Property | Value | Unit |
|----------|-------|------|
| Gravity | 0.5 | pixels/frame² |
| Jump velocity | -9 | pixels/frame (upward) |
| Terminal velocity | 10 | pixels/frame (downward) |
| Rotation speed | 3 | degrees/frame |

At 30 FPS:
- Gravity: ~450 pixels/sec²
- Jump velocity: ~270 pixels/sec upward

### Pipe Properties
| Property | Value | Notes |
|----------|-------|-------|
| Width | 52 pixels | Both upper and lower |
| Gap size | 100-120 pixels | Vertical opening between pipes |
| Horizontal spacing | 200-250 pixels | Distance between pipe pairs |
| Scroll speed | 4 pixels/frame | Constant throughout game |
| Spawn position | x=288 (off-screen right) | |

### Collision Zones
- **Ground:** y >= 400 pixels (death)
- **Ceiling:** y <= 0 pixels (death)
- **Pipes:** Rectangle collision with hitbox

### Scoring
- +1 point when bird's x position passes pipe's right edge
- No difficulty progression in original (speed stays constant)

### Game Loop
- Fixed timestep: 30 FPS
- Each frame:
  1. Apply gravity to velocity
  2. Apply velocity to position
  3. Check for jump input
  4. Scroll pipes
  5. Check collisions
  6. Update score

---

## Engine Evaluation

### Requirements Checklist
- [x] Python-based (for ML integration)
- [x] Headless mode support
- [x] Rendering decoupled from logic
- [x] Deterministic simulation
- [x] Simple to install/use

### Options Compared

#### 1. Pygame
**Pros:**
- Mature, stable, well-documented
- Easy to install (`pip install pygame`)
- Simple 2D rendering
- Can run without display (headless via `SDL_VIDEODRIVER=dummy`)
- Large community, many Flappy Bird examples
- Direct control over game loop

**Cons:**
- No built-in physics (but we want custom physics anyway)
- Must manage own game loop

**Headless support:** Yes, via `os.environ['SDL_VIDEODRIVER'] = 'dummy'`

#### 2. Arcade
**Pros:**
- Modern Python game library
- Nice sprite handling
- Good documentation

**Cons:**
- Requires OpenGL (problematic for headless)
- Heavier dependency
- Less flexible for custom game loops
- Headless mode is more complex

**Headless support:** Limited, requires pyglet modifications

#### 3. Custom (Pure Python + Optional Rendering)
**Pros:**
- Complete control
- No dependencies for logic
- Guaranteed determinism
- Easy headless (logic is separate)

**Cons:**
- Must build everything from scratch
- Rendering requires some library anyway

#### 4. Hybrid: Custom Logic + Pygame Rendering
**Pros:**
- Game state completely independent
- Pygame only for visualization
- Easy to toggle headless
- Best of both worlds

**Cons:**
- Slight complexity in architecture

---

## Decision: Hybrid Approach (Custom Logic + Pygame Rendering)

### Rationale
1. **Determinism:** Pure Python game logic guarantees same inputs = same outputs
2. **Headless:** Game can run without importing pygame at all
3. **Serialization:** Game state as plain dict, easy JSON serialization
4. **Speed:** Headless mode will be very fast (no rendering overhead)
5. **ML-friendly:** Clean separation between game and visualization

### Architecture
```
┌─────────────────────────────────────────┐
│              Game Logic                  │
│  (Pure Python, no dependencies)          │
│  - GameState dataclass                   │
│  - Physics simulation                    │
│  - Collision detection                   │
│  - Score tracking                        │
└─────────────────────────────────────────┘
                    │
                    ▼ (optional)
┌─────────────────────────────────────────┐
│            Pygame Renderer               │
│  - Draws current GameState               │
│  - Handles input                         │
│  - Only imported when needed             │
└─────────────────────────────────────────┘
```

---

## Proof of Concept Plan

Create a minimal script that:
1. Opens a pygame window (288x512)
2. Displays a colored background
3. Closes cleanly on window close or ESC

This verifies pygame works and establishes the rendering pattern.

---

## Next Steps
1. Create proof-of-concept script
2. Verify it runs without errors
3. Mark Task 1 complete
