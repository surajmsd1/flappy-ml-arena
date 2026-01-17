#!/usr/bin/env python3
"""
Headless Mode for Flappy Bird

Runs game simulation without rendering for fast ML training.
"""

import sys
import time
import random
from game import create_game, step, GameState


def run_headless(seed: int = None, max_frames: int = 10000,
                 jump_strategy: callable = None) -> GameState:
    """Run game headlessly with given jump strategy.

    Args:
        seed: Random seed for determinism
        max_frames: Maximum frames to simulate
        jump_strategy: Function(state) -> bool, returns True to jump

    Returns:
        Final game state
    """
    state = create_game(seed=seed)

    # Default strategy: random jumps
    if jump_strategy is None:
        rng = random.Random(seed)
        jump_strategy = lambda s: rng.random() < 0.1  # 10% chance to jump

    while state.alive and state.frame < max_frames:
        jump = jump_strategy(state)
        step(state, jump=jump)

    return state


def benchmark(num_runs: int = 10, frames_per_run: int = 1000) -> None:
    """Benchmark headless performance."""
    print(f"Benchmarking: {num_runs} runs x {frames_per_run} frames")

    total_frames = 0
    start_time = time.perf_counter()

    for i in range(num_runs):
        state = run_headless(seed=i, max_frames=frames_per_run)
        total_frames += state.frame

    elapsed = time.perf_counter() - start_time
    fps = total_frames / elapsed

    print(f"\nResults:")
    print(f"  Total frames: {total_frames:,}")
    print(f"  Time elapsed: {elapsed:.3f} seconds")
    print(f"  Performance: {fps:,.0f} frames/second")
    print(f"  Speedup vs 30 FPS: {fps/30:.0f}x realtime")

    # Check if we meet the requirement
    if frames_per_run / (elapsed / num_runs) >= 1000:
        print(f"\n  1000 frames in < 1 second: PASS")
    else:
        print(f"\n  1000 frames in < 1 second: FAIL")


def simulate_recording(inputs: list, seed: int) -> GameState:
    """Simulate a game from recorded inputs.

    Args:
        inputs: List of bool (jump per frame)
        seed: RNG seed

    Returns:
        Final game state
    """
    state = create_game(seed=seed)

    for jump in inputs:
        if not state.alive:
            break
        step(state, jump=jump)

    return state


def main():
    """Run headless benchmark."""
    print("=== Flappy Bird Headless Mode ===\n")

    # Quick test
    print("Quick test: 1000 frames...")
    start = time.perf_counter()
    state = run_headless(seed=12345, max_frames=1000)
    elapsed = time.perf_counter() - start
    print(f"  Completed in {elapsed*1000:.2f} ms")
    print(f"  Final frame: {state.frame}, Score: {state.score}, Alive: {state.alive}")

    print()

    # Full benchmark
    benchmark(num_runs=100, frames_per_run=1000)

    return 0


if __name__ == "__main__":
    sys.exit(main())
