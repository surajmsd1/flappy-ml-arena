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

### Task 9: Compact Recording Format
**Status:** NOT STARTED

**What to do:**
1. Add `save_compact(recording, filepath)` - stores only seed + list of jump booleans
2. Add `load_compact(filepath)` - loads compact format
3. Add `expand_recording(compact)` - regenerates full state from seed + inputs (uses determinism)
4. Keep verbose format available for debugging

**Deliverables:**
- [ ] Compact save/load functions in recording.py
- [ ] expand_recording() that regenerates full state
- [ ] Test: save compact, expand, verify identical to original

**How to verify:**
- Save a recording in compact format
- Load and expand it
- Compare frame-by-frame with original - should match exactly

---

## TASK QUEUE (Do not start until current task is DONE)

### Task 10: Sound System (Optional)
- Add sound effects using pygame.mixer (flap, score, death)
- Sound only enabled via `--sound` flag or `sound=True` parameter
- Auto-disable sound when >3 game renders are active
- No sound in headless mode
- Efficient: don't even load sound files if flag is off
- **Verify:** Play game with --sound, hear effects. Play without flag, no sound loaded.

### Task 11: Multi-Render Viewer App
- Create separate app: `src/viewer.py`
- Display NxN grid of game replays simultaneously
- Usage: `python viewer.py --grid=4 recordings/*.json`
- Shows training progress across iterations
- Label each render with filename/approach/generation
- **Verify:** Run viewer with 4+ recordings, see them play in grid

### Task 12: GitHub Repository Setup
- Initialize git if not already done
- Create repo `flappy-ml-arena` on github.com/surajmsd1
- Add .gitignore for Python, venv, __pycache__, etc.
- Push initial code
- Add README.md with project description
- **Verify:** Repo visible at github.com/surajmsd1/flappy-ml-arena

### Task 13: ML Feature Extraction
- Extract features from GameState for ML input
- Features: bird_y, bird_velocity, bird_rotation
- Features: next_pipe_distance, next_pipe_gap_y, next_pipe_gap_size
- Normalize all features to 0-1 range
- Add `get_features(state) -> List[float]` function
- **Verify:** Print features each frame, values in 0-1 range, make sense

### Task 14: Evolutionary - Simple Genetic (Interactive)
- Fixed neural net architecture (features -> hidden -> jump probability)
- Population of N agents with random weights
- Fitness = score achieved (or frames survived)
- Selection: keep top performers, mutate to create next generation
- **STOP and ask user** before running generations
- User specifies: how many generations, how many replays to save
- Save replays as `genetic_gen{N}_best{M}.json`
- **Verify:** Ask user, run generations, save labeled replays

### Task 15: Evolutionary - NEAT (Interactive)
- NeuroEvolution of Augmenting Topologies
- Evolves both network structure AND weights
- Use neat-python library
- **STOP and ask user** before major milestones
- Save as `neat_gen{N}_best{M}.json`
- **Verify:** NEAT evolves increasingly complex networks, performance improves

### Task 16: Imitation Learning (Interactive)
- Learn from human recordings (behavioral cloning)
- Simple neural net: features -> jump probability
- Train on human gameplay data
- **STOP and ask user** before training
- User specifies: epochs, replays to generate
- Save replays as `imitation_epoch{N}_replay{M}.json`
- **Verify:** Model mimics human-like play patterns

### Task 17: DQN Reinforcement Learning (Interactive)
- Deep Q-Network with experience replay
- Learn optimal policy through trial and error
- **STOP and ask user** for training duration
- Save as `dqn_step{N}_replay{M}.json`
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

---

## Notes
- Physics tuned: GRAVITY=0.8, JUMP_VELOCITY=-7 (snappier feel)
- Headless performance: 150,660 FPS (5000x realtime)
- Determinism verified: 0 mismatches on playback
