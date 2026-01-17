#!/usr/bin/env python3
"""
ML Feature Extraction for Flappy Bird

Extracts normalized features from game state for ML model input.
"""

from dataclasses import dataclass
from typing import Optional, List
from game import (
    GameState, SCREEN_WIDTH, SCREEN_HEIGHT, GROUND_Y,
    BIRD_START_X, BIRD_START_Y, PIPE_GAP, PIPE_WIDTH
)


@dataclass
class Features:
    """Extracted features for ML input."""
    # Bird features
    bird_y: float           # Normalized y position (0=top, 1=ground)
    bird_velocity: float    # Normalized velocity
    bird_rotation: float    # Normalized rotation (-1 to 1)

    # Next pipe features (closest pipe ahead of bird)
    pipe_distance: float    # Normalized horizontal distance to pipe
    pipe_gap_y: float       # Normalized gap center position
    pipe_gap_top: float     # Normalized top of gap
    pipe_gap_bottom: float  # Normalized bottom of gap

    # Game state
    alive: bool
    score: int
    frame: int

    def to_list(self) -> List[float]:
        """Convert to flat list for ML input."""
        return [
            self.bird_y,
            self.bird_velocity,
            self.bird_rotation,
            self.pipe_distance,
            self.pipe_gap_y,
            self.pipe_gap_top,
            self.pipe_gap_bottom,
        ]

    def to_dict(self) -> dict:
        """Convert to dict for debugging/logging."""
        return {
            'bird_y': self.bird_y,
            'bird_velocity': self.bird_velocity,
            'bird_rotation': self.bird_rotation,
            'pipe_distance': self.pipe_distance,
            'pipe_gap_y': self.pipe_gap_y,
            'pipe_gap_top': self.pipe_gap_top,
            'pipe_gap_bottom': self.pipe_gap_bottom,
            'alive': self.alive,
            'score': self.score,
            'frame': self.frame,
        }


def extract_features(state: GameState) -> Features:
    """Extract normalized features from game state.

    All spatial features normalized to [0, 1] range.
    Velocity and rotation normalized to approximately [-1, 1].
    """
    # Bird y position: 0 = top, 1 = ground
    bird_y = state.bird.y / GROUND_Y

    # Bird velocity: normalized by terminal velocity (~10)
    # Positive = falling, Negative = rising
    bird_velocity = state.bird.velocity / 10.0

    # Bird rotation: -25 to 90 degrees, normalize to ~[-1, 1]
    bird_rotation = state.bird.rotation / 90.0

    # Find next pipe (first pipe whose right edge is ahead of bird)
    # This is the pipe the bird needs to navigate through
    next_pipe = None
    for pipe in sorted(state.pipes, key=lambda p: p.x):
        pipe_right = pipe.x + PIPE_WIDTH
        if pipe_right > state.bird.x:
            next_pipe = pipe
            break

    if next_pipe is not None:
        # Horizontal distance to pipe's left edge, normalized by screen width
        pipe_distance = (next_pipe.x - state.bird.x) / SCREEN_WIDTH

        # Gap center position, normalized to [0, 1]
        pipe_gap_y = next_pipe.gap_y / GROUND_Y

        # Gap top and bottom
        pipe_gap_top = next_pipe.top_height / GROUND_Y
        pipe_gap_bottom = next_pipe.bottom_y / GROUND_Y
    else:
        # No pipe ahead - use defaults (pipe far away, gap centered)
        pipe_distance = 1.0
        pipe_gap_y = 0.5
        pipe_gap_top = 0.5 - (PIPE_GAP / 2) / GROUND_Y
        pipe_gap_bottom = 0.5 + (PIPE_GAP / 2) / GROUND_Y

    return Features(
        bird_y=bird_y,
        bird_velocity=bird_velocity,
        bird_rotation=bird_rotation,
        pipe_distance=pipe_distance,
        pipe_gap_y=pipe_gap_y,
        pipe_gap_top=pipe_gap_top,
        pipe_gap_bottom=pipe_gap_bottom,
        alive=state.alive,
        score=state.score,
        frame=state.frame,
    )


def print_features(features: Features) -> None:
    """Pretty print features for debugging."""
    print(f"Frame {features.frame:4d} | "
          f"bird_y={features.bird_y:.3f} vel={features.bird_velocity:+.2f} rot={features.bird_rotation:+.2f} | "
          f"pipe_dist={features.pipe_distance:.3f} gap_y={features.pipe_gap_y:.3f} | "
          f"score={features.score}")


def demo():
    """Demo feature extraction with a simulated game."""
    from game import create_game, step

    print("=== ML Feature Extraction Demo ===\n")
    print("Features:")
    print("  bird_y: Normalized Y position (0=top, 1=ground)")
    print("  bird_velocity: Normalized velocity (+=falling)")
    print("  bird_rotation: Normalized rotation")
    print("  pipe_distance: Distance to next pipe")
    print("  pipe_gap_y: Gap center position")
    print()

    state = create_game(seed=12345)

    # Simulate game with jumps
    jump_frames = {1, 15, 30, 45, 60}

    print("Running simulation with jumps at frames:", sorted(jump_frames))
    print("-" * 80)

    for i in range(80):
        jump = i in jump_frames
        step(state, jump=jump)

        features = extract_features(state)

        # Print every 5 frames or on jump
        if i % 5 == 0 or jump:
            prefix = "JUMP>" if jump else "     "
            print(f"{prefix} ", end="")
            print_features(features)

        if not state.alive:
            print("\nGAME OVER!")
            break

    print("-" * 80)
    print(f"Final score: {state.score}")
    print(f"\nFeature vector example: {features.to_list()}")


if __name__ == "__main__":
    demo()
