"""
Recording System for Flappy Bird

Records game sessions for playback and ML training data generation.
"""

import json
from dataclasses import dataclass, field
from typing import List, Optional
from game import GameState


@dataclass
class FrameRecord:
    """Record of a single frame."""
    frame: int
    jump: bool  # Input for this frame
    state: dict  # Serialized GameState after this frame

    def to_dict(self) -> dict:
        return {
            'frame': self.frame,
            'jump': self.jump,
            'state': self.state
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'FrameRecord':
        return cls(
            frame=data['frame'],
            jump=data['jump'],
            state=data['state']
        )


@dataclass
class Recording:
    """Complete recording of a game session."""
    seed: int  # RNG seed for reproducibility
    frames: List[FrameRecord] = field(default_factory=list)
    final_score: int = 0
    total_frames: int = 0

    def add_frame(self, frame: int, jump: bool, state: GameState) -> None:
        """Record a frame."""
        self.frames.append(FrameRecord(
            frame=frame,
            jump=jump,
            state=state.to_dict()
        ))
        self.total_frames = frame
        self.final_score = state.score

    def to_dict(self) -> dict:
        return {
            'seed': self.seed,
            'frames': [f.to_dict() for f in self.frames],
            'final_score': self.final_score,
            'total_frames': self.total_frames
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Recording':
        return cls(
            seed=data['seed'],
            frames=[FrameRecord.from_dict(f) for f in data['frames']],
            final_score=data['final_score'],
            total_frames=data['total_frames']
        )

    def get_inputs(self) -> List[bool]:
        """Get list of jump inputs for each frame."""
        return [f.jump for f in self.frames]


def save_recording(recording: Recording, filepath: str) -> None:
    """Save recording to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(recording.to_dict(), f)


def load_recording(filepath: str) -> Recording:
    """Load recording from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return Recording.from_dict(data)


# --- Compact Format ---
# Stores only seed + jump booleans, regenerates full state via determinism

@dataclass
class CompactRecording:
    """Compact recording: just seed and inputs."""
    seed: int
    inputs: List[bool]  # Jump input for each frame
    final_score: int = 0
    total_frames: int = 0

    def to_dict(self) -> dict:
        return {
            'format': 'compact',
            'seed': self.seed,
            'inputs': self.inputs,
            'final_score': self.final_score,
            'total_frames': self.total_frames
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CompactRecording':
        return cls(
            seed=data['seed'],
            inputs=data['inputs'],
            final_score=data['final_score'],
            total_frames=data['total_frames']
        )


def save_compact(recording: Recording, filepath: str) -> None:
    """Save recording in compact format (seed + inputs only)."""
    compact = CompactRecording(
        seed=recording.seed,
        inputs=recording.get_inputs(),
        final_score=recording.final_score,
        total_frames=recording.total_frames
    )
    with open(filepath, 'w') as f:
        json.dump(compact.to_dict(), f)


def load_compact(filepath: str) -> CompactRecording:
    """Load compact recording from file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return CompactRecording.from_dict(data)


def expand_recording(compact: CompactRecording) -> Recording:
    """Expand compact recording to full recording by re-simulating.

    Uses determinism: same seed + same inputs = same states.
    """
    from game import create_game, step

    # Create game with same seed
    state = create_game(seed=compact.seed)
    recording = Recording(seed=compact.seed)

    # Simulate each frame with recorded inputs
    for jump in compact.inputs:
        step(state, jump=jump)
        recording.add_frame(state.frame, jump, state)

    return recording


def is_compact_format(filepath: str) -> bool:
    """Check if a recording file is in compact format."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data.get('format') == 'compact'


def load_any_recording(filepath: str) -> Recording:
    """Load recording in either format, return full Recording."""
    if is_compact_format(filepath):
        compact = load_compact(filepath)
        return expand_recording(compact)
    else:
        return load_recording(filepath)
