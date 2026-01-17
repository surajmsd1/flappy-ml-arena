# AI Requirements Document
> One task at a time. Test before moving on. Commit after each task.

## Git Protocol
- **Commit after completing each task** with message: "Task N: brief description"
- **Do NOT include** any AI/Claude/Ralph attribution in commits
- Push to origin after major milestones (every 2-3 tasks)

---

## Project Goal
Build a Flappy Bird clone that generates ML training data. End goal: train multiple ML models that play Flappy Bird and compare their performance.

---

## CURRENT TASK

### Task 24: Delete Broken Recordings
**Status:** NOT STARTED

(See full description below Task 23)

---

### Task 20: Polished Viewer & Renderer
**Status:** DONE

Make the multi-render viewer and main renderer look authentic to real Flappy Bird. The arena should be fun to watch!

**Renderer Improvements (renderer.py):**
- Add scrolling clouds in the background (parallax effect)
- Add city/buildings silhouette in background
- Improve ground with grass texture pattern
- Bird wing animation (flap when jumping)
- Better pipe shading/gradients
- Day/night color themes option

**Viewer Improvements (viewer.py):**
- **FULL SCALE**: Remove the 50% scaling - each cell should be native resolution
- Or add a `--scale=1.0` option to control cell size
- Bird should have ALL details: wing, eye, beak, rotation animation
- Pipe caps and shading (same as renderer.py)
- Clouds visible in each cell
- Smooth animations, no visual shortcuts

**Window/Grid Options:**
- `--fullscreen` option
- `--cols=N` instead of `--grid=N` (auto-calculate rows from recordings count)
- Auto-fit to screen while maintaining aspect ratio
- Minimum cell size of 200x300 pixels

**Visual Polish:**
- Score with drop shadow
- "GAME OVER" with red tint overlay
- Generation/model label with better styling
- FPS counter option (`--fps`)
- Speed controls visible on screen (current: 1x, 2x, etc.)

**Deliverables:**
- [ ] Clouds + parallax background in renderer.py
- [ ] Full-detail bird in viewer.py cells
- [ ] Full-scale or configurable scale in viewer.py
- [ ] Pipe caps and proper shading in both files
- [ ] `--fullscreen` and `--scale` options

**Verify:**
- Run viewer with 4 recordings, looks identical to main game
- Clouds scroll, bird rotates, pipes have caps
- Each cell large enough to see all details

---

### Task 21: UI Redesign - Mac-Style Tile View
**Status:** DONE

Redesign the Recording Manager UI to be sleek and Mac-like.

**Layout Changes:**
- **Tile view by default** (like Mac Finder icons view)
- Each recording as a card/tile with thumbnail preview
- Group recordings by iteration/generation with collapsible sections
- Subheadings: "Genetic Gen 0", "Genetic Gen 100", etc.

**Selection & Playback:**
- Checkbox on each tile for selection
- "Select All" button per group/subheading
- "Play Selected" button (opens viewer with selected recordings)
- "Play All in Group" button per section
- Shift+click for range selection

**Visual Design (Mac-like):**
- Gray sleek color scheme (#f5f5f7 background, #1d1d1f text)
- Rounded corners on cards (12px radius)
- Subtle shadows (0 2px 8px rgba(0,0,0,0.1))
- SF-style system font stack
- Hover states with slight lift effect
- Selected state with blue border (#007aff)

**Card Contents:**
- Mini preview frame (first frame of recording)
- Model type badge (colored: genetic=green, neat=purple, etc.)
- Score prominently displayed
- Generation/epoch number
- Duration in seconds
- File size

**Deliverables:**
- [ ] Tile view layout in templates
- [ ] Group by generation with collapsible sections
- [ ] Select all per group
- [ ] Mac-like gray color scheme
- [ ] Hover/selected states

---

### Task 22: Fix ML Training - Game Start Bug
**Status:** DONE

**Problem:** ML models are not starting the game - bird just sits there, no pipes spawn.

**Root Cause:** Game requires first jump to start. Models need to:
1. Jump immediately on first frame to start the game
2. Then make decisions based on game state

**Fix in genetic.py (and all ML modules):**
```python
# First frame: always jump to start the game
if state.frame == 0 or not state.started:
    jump = True
else:
    # Normal decision making
    jump = agent.network.decide(features.to_list())
```

**Verify:**
- Run genetic training, see pipes appearing
- Birds actually fly and hit pipes (not just sitting)
- Scores should vary (not all 0)

---

### Task 23: UI Training Controls + Bootstrap from Human Recordings
**Status:** DONE

Add ability to run genetic training from the UI and use human recordings to bootstrap the network.

**UI Training Controls (ui.py + templates):**
- Add "Train" section/button in Recording Manager
- Input: Number of generations to run (default: 50)
- Input: Number of best recordings to save per generation (default: 8)
- Progress indicator showing current generation
- Live stats: best score, avg score, generation number
- "Stop Training" button

**Bootstrap from Human Recordings:**
- Use existing human recordings (`game_*_score*.json`) as training data
- Implement imitation learning to initialize network weights:
  - Extract (features, jump_decision) pairs from human recordings
  - Train initial network to mimic human decisions
  - Use this trained network as seed for genetic population
- This gives genetic algorithm a head start instead of random weights

**API Endpoints:**
- `POST /api/train` - Start training with params (generations, save_n)
- `GET /api/train/status` - Get current training status
- `POST /api/train/stop` - Stop training early

**Save Convention:**
- Clean up old broken recordings first (those with score 0 and no movement)
- Save 8 best recordings per completed training session
- Format: `genetic_gen{N}_best{M}.json`

**Verify:**
- Click Train button, see progress
- After training, 8 new recordings appear
- Bootstrapped models should score better than random initial weights

---

### Task 24: Delete Broken Recordings
**Status:** NOT STARTED

**Problem:** Old recordings from before Task 22 fix have:
- Bird not moving (y stays at 256)
- No pipes spawned
- Score = 0
- `started: false` for all frames

**Fix:**
- Add "Delete Broken" button in UI
- Scan recordings for: `started: false` on last frame OR all frames have same bird.y
- Delete these automatically OR let user confirm
- Or just delete all `genetic_gen*` files and retrain

**Verify:**
- UI shows only valid recordings
- All displayed recordings show actual gameplay

---

## TASK QUEUE (Do not start until current task is DONE)

### Task 15: Evolutionary - NEAT
> **AUTO-STOP:** Create EXIT_SIGNAL after completing this task. User will review before continuing.

- NeuroEvolution of Augmenting Topologies
- Evolves both network structure AND weights
- Use neat-python library
- **Phase 1:** 8 baseline recordings (gen 0)
- **Phase 2:** Train 100 generations
- **Phase 3:** 8 trained recordings (gen 100)
- Save as `neat_gen{N}_replay{M}.json`
- Create EXIT_SIGNAL and STOP
- **Verify:** NEAT evolves increasingly complex networks, performance improves

### Task 16: Imitation Learning
> **AUTO-STOP:** Create EXIT_SIGNAL after completing this task.

- Learn from human recordings (behavioral cloning)
- Simple neural net: features -> jump probability
- Train on existing human gameplay recordings
- Generate 8 replays showing learned behavior
- Save replays as `imitation_replay{M}.json`
- Create EXIT_SIGNAL and STOP
- **Verify:** Model mimics human-like play patterns

### Task 17: DQN Reinforcement Learning
> **AUTO-STOP:** Create EXIT_SIGNAL after completing this task.

- Deep Q-Network with experience replay
- Learn optimal policy through trial and error
- Train for 10,000 steps
- Save 8 replays as `dqn_replay{M}.json`
- Create EXIT_SIGNAL and STOP
- **Verify:** DQN learns to play, improves over time

### Task 18: Model Comparison Dashboard
- Compare performance across all approaches
- Metrics: avg score, max score, consistency (std dev)
- Visualize learning curves for each approach
- Summary table ranking approaches
- **Verify:** Run dashboard, see comparison of all trained models

---

## Gathered Requirements (Reference)

### Game Architecture
- [x] Game state must be fully serializable (JSON/dict)
- [x] Rendering decoupled from game logic
- [x] Playback any recorded/generated game data
- [x] Headless mode for fast training runs

### Bird Model
- [x] Bird has heading (angle based on velocity)
- [x] Physics match real Flappy Bird (gravity, jump velocity)
- [x] Deterministic - same inputs = same outputs

### ML Input Requirements
- [ ] Model sees serialized game state only
- [ ] Must understand: time, distance, upcoming gaps
- [ ] Features: bird position, heading, velocity
- [ ] Features: pipe distance, gap position, gap size
- [ ] Action space: JUMP or NO_OP

### Human Interaction
- [x] Human can play manually (generates training data)
- [ ] Human can spawn pipes (model unaffected)
- [x] Model works regardless of pipe source

### Data Pipeline
- [x] Record game sessions as data
- [x] Replay any session visually
- [ ] Generate training datasets from recordings

---

## ML Training Protocol
> IMPORTANT: Follow this protocol for all ML tasks

1. **ALWAYS pause before training** and ask user for parameters
2. Example prompt: "Ready to train Simple Genetic. How many generations? How many best replays to save?"
3. User controls pace: "run 5 generations and show me 16 replays"
4. **Label all outputs** with approach name and iteration number
5. **Don't proceed to next approach** until user explicitly says so
6. Save all replays in `recordings/` with descriptive names

---

## Open Questions (Resolved)
- ML approach order: Simple Genetic -> NEAT -> Imitation -> DQN
- Recording format: Compact storage, expand at training time
- Sound: Optional flag, auto-disable for multi-render (>3 games)
- Viewer: Separate app with grid display
- GitHub: flappy-ml-arena on surajmsd1

---

## Completed Tasks Log
| Task | Date | Outcome | Notes |
|------|------|---------|-------|
| 1 | 2026-01-17 | DONE | Pygame + pure Python, POC verified |
| 2 | 2026-01-17 | DONE | Bird physics, gravity=0.8, jump=-7 |
| 3 | 2026-01-17 | DONE | Pipes scroll, deterministic RNG |
| 4 | 2026-01-17 | DONE | Collision + scoring working |
| 5 | 2026-01-17 | DONE | State serialization to JSON |
| 6 | 2026-01-17 | DONE | Recording system, auto-save |
| 7 | 2026-01-17 | DONE | Playback with determinism verified |
| 8 | 2026-01-17 | DONE | Headless 150k FPS |
| 9 | 2026-01-17 | DONE | Compact recording format (31.5x compression) |
| 10 | 2026-01-17 | DONE | Sound system with lazy loading |
| 11 | 2026-01-17 | DONE | Multi-render viewer app |
| 12 | 2026-01-17 | DONE | GitHub repo flappy-ml-arena |
| 13 | 2026-01-17 | DONE | ML feature extraction |
| 14 | 2026-01-17 | DONE | Simple genetic algo, 100 gens trained |
| 19 | 2026-01-17 | DONE | Recording Manager UI (Flask) |
| 20 | 2026-01-17 | DONE | Polished viewer & renderer with visual effects |
| 21 | 2026-01-17 | DONE | Mac-style tile view UI redesign |
| 22 | 2026-01-17 | DONE | Fixed ML game start bug (jump first frame) |
| 21 | 2026-01-17 | DONE | Mac-style tile view UI redesign |
| 22 | 2026-01-17 | DONE | Fixed ML training game start bug |
| 23 | 2026-01-17 | DONE | UI training controls + bootstrap from human |

---

## Notes
- Physics tuned: GRAVITY=0.8, JUMP_VELOCITY=-7 (snappier feel)
- Headless performance: 150,660 FPS (5000x realtime)
- Determinism verified: 0 mismatches on playback
