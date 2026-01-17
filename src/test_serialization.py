#!/usr/bin/env python3
"""
Test script for Task 5: Game State Serialization

Verifies that game state can be saved and loaded correctly.
"""

import os
import sys
from game import create_game, step, save_state, load_state


def test_serialization():
    """Test save/load of game state."""
    print("=== Task 5: Serialization Test ===\n")

    # Create a game with fixed seed for reproducibility
    state = create_game(seed=12345)
    print(f"Created game with seed: {state.rng_seed}")

    # Simulate some gameplay
    inputs = [True, False, False, False, False,  # Jump, then fall
              True, False, False, False, False,   # Jump again
              True, False, False, False, False,   # Jump again
              True, False, False, False, False]   # Jump again

    for i, jump in enumerate(inputs):
        step(state, jump=jump)

    print(f"After {len(inputs)} frames:")
    print(f"  Frame: {state.frame}")
    print(f"  Bird y: {state.bird.y:.1f}")
    print(f"  Bird velocity: {state.bird.velocity:.1f}")
    print(f"  Pipes: {len(state.pipes)}")
    print(f"  Score: {state.score}")
    print(f"  Alive: {state.alive}")

    # Save state
    save_path = "/tmp/flappy_test_save.json"
    save_state(state, save_path)
    print(f"\nSaved state to: {save_path}")

    # Record current state for comparison
    saved_frame = state.frame
    saved_bird_y = state.bird.y
    saved_velocity = state.bird.velocity
    saved_score = state.score
    saved_alive = state.alive
    saved_pipe_count = len(state.pipes)
    saved_pipe_x = state.pipes[0].x if state.pipes else None

    # Load state into new object
    loaded_state = load_state(save_path)
    print("Loaded state from file")

    # Verify loaded state matches
    print("\n=== Verification ===")
    checks = [
        ("Frame", loaded_state.frame, saved_frame),
        ("Bird y", loaded_state.bird.y, saved_bird_y),
        ("Velocity", loaded_state.bird.velocity, saved_velocity),
        ("Score", loaded_state.score, saved_score),
        ("Alive", loaded_state.alive, saved_alive),
        ("Pipe count", len(loaded_state.pipes), saved_pipe_count),
    ]

    if saved_pipe_x is not None:
        checks.append(("First pipe x", loaded_state.pipes[0].x, saved_pipe_x))

    all_passed = True
    for name, loaded, expected in checks:
        match = loaded == expected
        status = "PASS" if match else "FAIL"
        print(f"  {name}: {status} (loaded={loaded}, expected={expected})")
        if not match:
            all_passed = False

    # Continue playing from loaded state
    print("\n=== Continue from loaded state ===")
    for i in range(10):
        step(loaded_state, jump=(i % 3 == 0))

    print(f"After 10 more frames:")
    print(f"  Frame: {loaded_state.frame}")
    print(f"  Bird y: {loaded_state.bird.y:.1f}")
    print(f"  Alive: {loaded_state.alive}")

    # Verify determinism: same seed + same inputs = same result
    print("\n=== Determinism Test ===")
    state1 = create_game(seed=99999)
    state2 = create_game(seed=99999)

    test_inputs = [True, False, False, True, False, False, True, False]
    for jump in test_inputs:
        step(state1, jump=jump)
        step(state2, jump=jump)

    determinism_pass = (
        state1.bird.y == state2.bird.y and
        state1.bird.velocity == state2.bird.velocity and
        state1.frame == state2.frame
    )
    print(f"  Same seed + inputs = same result: {'PASS' if determinism_pass else 'FAIL'}")

    # Cleanup
    os.remove(save_path)
    print(f"\nCleaned up: {save_path}")

    # Summary
    print("\n=== SUMMARY ===")
    if all_passed and determinism_pass:
        print("All tests PASSED!")
        return 0
    else:
        print("Some tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(test_serialization())
