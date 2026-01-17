"""
Flappy Bird Game Logic (Pure Python, no dependencies)

This module contains all game state and physics.
It can run completely headless without pygame.
"""

from dataclasses import dataclass, field
from typing import Optional, List
import json
import math
import random


# Game constants (from research)
SCREEN_WIDTH = 288
SCREEN_HEIGHT = 512
FPS = 30

# Bird constants
BIRD_WIDTH = 34
BIRD_HEIGHT = 24
BIRD_START_X = 50
BIRD_START_Y = 256

# Physics constants (tuned for snappier feel like real Flappy Bird)
GRAVITY = 0.8  # pixels/frame^2
JUMP_VELOCITY = -7  # pixels/frame (negative = up)
TERMINAL_VELOCITY = 10  # pixels/frame (max fall speed)
ROTATION_SPEED = 3  # degrees/frame

# Boundaries
GROUND_Y = 400
CEILING_Y = 0

# Pipe constants
PIPE_WIDTH = 52
PIPE_GAP = 100  # Vertical gap between top and bottom pipes
PIPE_SPACING = 200  # Horizontal distance between pipe pairs
PIPE_SPEED = 4  # pixels/frame (scroll left)
PIPE_MIN_HEIGHT = 50  # Minimum height for top pipe
PIPE_MAX_HEIGHT = GROUND_Y - PIPE_GAP - PIPE_MIN_HEIGHT  # Leave room for gap and bottom pipe


@dataclass
class Bird:
    """Bird state with position, velocity, and rotation."""
    x: float = BIRD_START_X
    y: float = BIRD_START_Y
    velocity: float = 0.0  # vertical velocity (positive = down)
    rotation: float = 0.0  # degrees, 0 = level, negative = up, positive = down

    def to_dict(self) -> dict:
        """Serialize bird state to dict."""
        return {
            'x': self.x,
            'y': self.y,
            'velocity': self.velocity,
            'rotation': self.rotation
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Bird':
        """Deserialize bird state from dict."""
        return cls(
            x=data['x'],
            y=data['y'],
            velocity=data['velocity'],
            rotation=data['rotation']
        )


@dataclass
class Pipe:
    """A pipe pair (top and bottom) with gap."""
    x: float  # x position of left edge
    gap_y: float  # y position of gap center
    passed: bool = False  # True if bird has passed this pipe (for scoring)

    @property
    def top_height(self) -> float:
        """Height of top pipe (from ceiling)."""
        return self.gap_y - PIPE_GAP / 2

    @property
    def bottom_y(self) -> float:
        """Y position where bottom pipe starts."""
        return self.gap_y + PIPE_GAP / 2

    def to_dict(self) -> dict:
        """Serialize pipe to dict."""
        return {
            'x': self.x,
            'gap_y': self.gap_y,
            'passed': self.passed
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Pipe':
        """Deserialize pipe from dict."""
        return cls(
            x=data['x'],
            gap_y=data['gap_y'],
            passed=data['passed']
        )


def create_pipe(x: float, rng: random.Random = None) -> Pipe:
    """Create a new pipe at given x position with random gap."""
    if rng is None:
        rng = random.Random()
    # Gap center can be anywhere that leaves room for min pipe heights
    min_gap_y = PIPE_MIN_HEIGHT + PIPE_GAP / 2
    max_gap_y = GROUND_Y - PIPE_MIN_HEIGHT - PIPE_GAP / 2
    gap_y = rng.uniform(min_gap_y, max_gap_y)
    return Pipe(x=x, gap_y=gap_y)


@dataclass
class GameState:
    """Complete game state - fully serializable."""
    bird: Bird = field(default_factory=Bird)
    pipes: List[Pipe] = field(default_factory=list)
    frame: int = 0
    score: int = 0
    alive: bool = True
    started: bool = False  # Game starts when player first jumps
    rng_seed: int = 0  # For deterministic pipe generation

    def to_dict(self) -> dict:
        """Serialize complete game state to dict."""
        return {
            'bird': self.bird.to_dict(),
            'pipes': [p.to_dict() for p in self.pipes],
            'frame': self.frame,
            'score': self.score,
            'alive': self.alive,
            'started': self.started,
            'rng_seed': self.rng_seed
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GameState':
        """Deserialize game state from dict."""
        return cls(
            bird=Bird.from_dict(data['bird']),
            pipes=[Pipe.from_dict(p) for p in data['pipes']],
            frame=data['frame'],
            score=data['score'],
            alive=data['alive'],
            started=data['started'],
            rng_seed=data.get('rng_seed', 0)
        )


def update_bird_physics(bird: Bird) -> None:
    """Apply gravity and update bird position/rotation.

    Modifies bird in place for efficiency.
    """
    # Apply gravity to velocity
    bird.velocity += GRAVITY

    # Cap at terminal velocity
    if bird.velocity > TERMINAL_VELOCITY:
        bird.velocity = TERMINAL_VELOCITY

    # Apply velocity to position
    bird.y += bird.velocity

    # Update rotation based on velocity
    # Going up: rotate toward -25 degrees
    # Going down: rotate toward 90 degrees
    if bird.velocity < 0:
        # Rising - tilt up quickly
        bird.rotation = max(-25, bird.rotation - ROTATION_SPEED * 2)
    else:
        # Falling - tilt down gradually
        bird.rotation = min(90, bird.rotation + ROTATION_SPEED)


def bird_jump(bird: Bird) -> None:
    """Make the bird jump."""
    bird.velocity = JUMP_VELOCITY
    bird.rotation = -25  # Immediate upward tilt on jump


def check_boundaries(bird: Bird) -> bool:
    """Check if bird hit ground or ceiling.

    Returns True if bird is still alive (within bounds).
    """
    # Check ground collision
    if bird.y + BIRD_HEIGHT / 2 >= GROUND_Y:
        bird.y = GROUND_Y - BIRD_HEIGHT / 2
        return False

    # Check ceiling collision
    if bird.y - BIRD_HEIGHT / 2 <= CEILING_Y:
        bird.y = CEILING_Y + BIRD_HEIGHT / 2
        return False

    return True


def update_pipes(state: GameState, rng: random.Random) -> None:
    """Update pipe positions, remove off-screen, spawn new pipes."""
    # Move pipes left
    for pipe in state.pipes:
        pipe.x -= PIPE_SPEED

    # Remove pipes that are off-screen left
    state.pipes = [p for p in state.pipes if p.x + PIPE_WIDTH > 0]

    # Spawn new pipe if needed
    # Keep at least 3 pipes in play for smooth scrolling
    if len(state.pipes) == 0:
        # First pipe spawns at screen edge
        state.pipes.append(create_pipe(SCREEN_WIDTH, rng))
    else:
        # Spawn when rightmost pipe has scrolled enough
        rightmost = max(p.x for p in state.pipes)
        if rightmost < SCREEN_WIDTH - PIPE_SPACING:
            state.pipes.append(create_pipe(SCREEN_WIDTH, rng))


def check_pipe_collision(bird: Bird, pipe: Pipe) -> bool:
    """Check if bird collides with a pipe pair.

    Returns True if collision detected.
    """
    # Bird bounding box
    bird_left = bird.x - BIRD_WIDTH / 2
    bird_right = bird.x + BIRD_WIDTH / 2
    bird_top = bird.y - BIRD_HEIGHT / 2
    bird_bottom = bird.y + BIRD_HEIGHT / 2

    # Pipe bounding box (horizontal)
    pipe_left = pipe.x
    pipe_right = pipe.x + PIPE_WIDTH

    # Check horizontal overlap first (optimization)
    if bird_right < pipe_left or bird_left > pipe_right:
        return False

    # Check collision with top pipe
    top_pipe_bottom = pipe.top_height
    if bird_top < top_pipe_bottom:
        return True

    # Check collision with bottom pipe
    bottom_pipe_top = pipe.bottom_y
    if bird_bottom > bottom_pipe_top:
        return True

    return False


def update_score(state: GameState) -> None:
    """Update score when bird passes pipes."""
    for pipe in state.pipes:
        # Bird has passed pipe if bird's x is past pipe's right edge
        if not pipe.passed and state.bird.x > pipe.x + PIPE_WIDTH:
            pipe.passed = True
            state.score += 1


def step(state: GameState, jump: bool = False) -> None:
    """Advance game by one frame.

    Args:
        state: Current game state (modified in place)
        jump: True if jump input this frame
    """
    if not state.alive:
        return

    # Handle jump input
    if jump:
        if not state.started:
            state.started = True
        bird_jump(state.bird)

    # Only apply physics once game has started
    if state.started:
        update_bird_physics(state.bird)

        # Update pipes with deterministic RNG
        rng = random.Random(state.rng_seed + state.frame)
        update_pipes(state, rng)

        # Check pipe collisions
        for pipe in state.pipes:
            if check_pipe_collision(state.bird, pipe):
                state.alive = False
                break

        # Update score
        if state.alive:
            update_score(state)

        # Check boundaries
        if not check_boundaries(state.bird):
            state.alive = False

    state.frame += 1


def create_game(seed: int = None) -> GameState:
    """Create a new game state.

    Args:
        seed: Random seed for deterministic pipe generation. If None, uses random seed.
    """
    if seed is None:
        seed = random.randint(0, 2**31)
    return GameState(rng_seed=seed)


def save_state(state: GameState, filepath: str) -> None:
    """Save game state to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(state.to_dict(), f, indent=2)


def load_state(filepath: str) -> GameState:
    """Load game state from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return GameState.from_dict(data)
