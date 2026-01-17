#!/usr/bin/env python3
"""
Training Pipeline for Flappy Bird

Converts recordings into training data and provides a simple training loop.
"""

import os
import json
import sys
from typing import List, Tuple
from dataclasses import dataclass

from game import GameState
from recording import load_recording, Recording
from features import extract_features, Features


@dataclass
class TrainingExample:
    """Single training example: features -> action."""
    features: List[float]  # Input features
    action: int            # 0 = no jump, 1 = jump
    reward: float          # Reward signal
    next_features: List[float]  # Features after action
    done: bool             # Episode ended


def recording_to_training_data(recording: Recording) -> List[TrainingExample]:
    """Convert a recording to training examples.

    Each frame becomes one example:
    - features: state before action
    - action: what the player did
    - reward: +1 for surviving, +10 for scoring, -100 for dying
    - next_features: state after action
    - done: True if game ended
    """
    examples = []

    for i in range(len(recording.frames) - 1):
        frame = recording.frames[i]
        next_frame = recording.frames[i + 1]

        # Get states
        state = GameState.from_dict(frame.state)
        next_state = GameState.from_dict(next_frame.state)

        # Extract features
        features = extract_features(state)
        next_features = extract_features(next_state)

        # Determine action (from next frame's input that led to this transition)
        action = 1 if next_frame.jump else 0

        # Calculate reward
        if not next_state.alive:
            reward = -100.0  # Died
        elif next_state.score > state.score:
            reward = 10.0    # Scored a point
        else:
            reward = 0.1     # Survived

        examples.append(TrainingExample(
            features=features.to_list(),
            action=action,
            reward=reward,
            next_features=next_features.to_list(),
            done=not next_state.alive
        ))

    return examples


def load_all_recordings(recordings_dir: str = "recordings") -> List[Recording]:
    """Load all recordings from directory."""
    recordings = []
    if not os.path.exists(recordings_dir):
        return recordings

    for filename in os.listdir(recordings_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(recordings_dir, filename)
            try:
                recording = load_recording(filepath)
                recordings.append(recording)
            except Exception as e:
                print(f"Error loading {filename}: {e}")

    return recordings


def generate_training_dataset(recordings_dir: str = "recordings") -> Tuple[List[List[float]], List[int]]:
    """Generate X, y training data from all recordings.

    Returns:
        X: List of feature vectors
        y: List of actions (0 or 1)
    """
    recordings = load_all_recordings(recordings_dir)
    print(f"Loaded {len(recordings)} recordings")

    X = []
    y = []

    for recording in recordings:
        examples = recording_to_training_data(recording)
        for ex in examples:
            X.append(ex.features)
            y.append(ex.action)

    return X, y


def save_dataset(X: List[List[float]], y: List[int], filepath: str) -> None:
    """Save dataset to JSON file."""
    data = {'X': X, 'y': y}
    with open(filepath, 'w') as f:
        json.dump(data, f)
    print(f"Saved {len(X)} examples to {filepath}")


def load_dataset(filepath: str) -> Tuple[List[List[float]], List[int]]:
    """Load dataset from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data['X'], data['y']


def demo_simple_model():
    """Demo: train a simple rule-based 'model' and test it."""
    print("=== Training Pipeline Demo ===\n")

    # Generate training data
    X, y = generate_training_dataset()
    print(f"Training examples: {len(X)}")

    if len(X) == 0:
        print("\nNo training data! Play some games first with main.py")
        return

    # Show class distribution
    jumps = sum(y)
    no_jumps = len(y) - jumps
    print(f"Actions: {jumps} jumps ({100*jumps/len(y):.1f}%), {no_jumps} no-jumps")

    # Calculate average features for each action
    jump_features = [X[i] for i in range(len(X)) if y[i] == 1]
    nojump_features = [X[i] for i in range(len(X)) if y[i] == 0]

    if jump_features:
        avg_jump = [sum(f[i] for f in jump_features) / len(jump_features)
                    for i in range(7)]
        print(f"\nAvg features when jumping:")
        print(f"  bird_y={avg_jump[0]:.3f}, vel={avg_jump[1]:.3f}, pipe_dist={avg_jump[3]:.3f}")

    if nojump_features:
        avg_nojump = [sum(f[i] for f in nojump_features) / len(nojump_features)
                      for i in range(7)]
        print(f"Avg features when NOT jumping:")
        print(f"  bird_y={avg_nojump[0]:.3f}, vel={avg_nojump[1]:.3f}, pipe_dist={avg_nojump[3]:.3f}")

    # Save dataset
    save_dataset(X, y, "training_data.json")

    # Verify we can load it
    X_loaded, y_loaded = load_dataset("training_data.json")
    print(f"\nVerification: loaded {len(X_loaded)} examples")

    print("\n=== Pipeline Ready ===")
    print("Next steps:")
    print("1. Use X, y for supervised learning (imitation)")
    print("2. Or use TrainingExample with rewards for RL")


if __name__ == "__main__":
    demo_simple_model()
