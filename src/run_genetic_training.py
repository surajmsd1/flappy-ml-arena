#!/usr/bin/env python3
"""
Run genetic algorithm training as specified in Task 14.

Phase 1: Generate 8 baseline recordings with untrained network
Phase 2: Train for 100 generations
Phase 3: Generate 8 recordings with best trained network
Phase 4: Print summary
"""

import os
import sys
from typing import List

from genetic import (
    NeuralNetwork, Agent, evaluate_agent,
    create_next_generation, run_generation
)
from recording import save_compact


RECORDINGS_DIR = "recordings"


def run_games_with_network(network: NeuralNetwork, seeds: List[int],
                           prefix: str, max_frames: int = 3000) -> List[int]:
    """
    Run multiple games with the same network on different seeds.

    Returns list of scores achieved.
    """
    scores = []

    for i, seed in enumerate(seeds, 1):
        agent = Agent(network=network)
        fitness, score, frames, recording = evaluate_agent(agent, seed, max_frames)

        filename = f"{prefix}{i}.json"
        filepath = os.path.join(RECORDINGS_DIR, filename)
        save_compact(recording, filepath)

        scores.append(score)
        print(f"  {filename}: score={score}, frames={frames}")

    return scores


def main():
    os.makedirs(RECORDINGS_DIR, exist_ok=True)

    seeds = list(range(1, 9))  # Seeds 1-8

    # =========================================
    # Phase 1: Baseline (Generation 0)
    # =========================================
    print("=" * 60)
    print("PHASE 1: Generating baseline recordings (untrained network)")
    print("=" * 60)

    # Create one random network
    untrained_network = NeuralNetwork()

    gen0_scores = run_games_with_network(
        untrained_network,
        seeds,
        "genetic_gen0_replay",
        max_frames=3000
    )

    gen0_avg = sum(gen0_scores) / len(gen0_scores)
    print(f"\nGen0 scores: {gen0_scores}")
    print(f"Gen0 average: {gen0_avg:.2f}")

    # =========================================
    # Phase 2: Train for 100 generations
    # =========================================
    print("\n" + "=" * 60)
    print("PHASE 2: Training for 100 generations")
    print("=" * 60)

    population_size = 50
    population = [Agent(network=NeuralNetwork()) for _ in range(population_size)]

    best_network = None
    best_fitness = 0

    for gen in range(100):
        # Use different seed each generation
        seed = (gen + 1) * 1000 + 42

        # Evaluate generation
        results = run_generation(population, gen, seed, max_frames=3000)

        # Track best
        best_agent = results[0][0]
        if best_agent.fitness > best_fitness:
            best_fitness = best_agent.fitness
            best_network = best_agent.network

        # Print progress every 10 generations
        if (gen + 1) % 10 == 0:
            scores = [r[0].score for r in results]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            print(f"Gen {gen+1:3d} | Best fitness: {best_agent.fitness:.2f} | "
                  f"Best score: {best_agent.score} | Avg score: {avg_score:.1f} | Max: {max_score}")

        # Create next generation
        population = create_next_generation(
            [r[0] for r in results],
            elite_count=2,
            mutation_rate=0.1
        )

    print(f"\nTraining complete. Best fitness achieved: {best_fitness:.2f}")

    # =========================================
    # Phase 3: Generate trained recordings
    # =========================================
    print("\n" + "=" * 60)
    print("PHASE 3: Generating trained recordings (gen100 best network)")
    print("=" * 60)

    gen100_scores = run_games_with_network(
        best_network,
        seeds,
        "genetic_gen100_replay",
        max_frames=3000
    )

    gen100_avg = sum(gen100_scores) / len(gen100_scores)
    print(f"\nGen100 scores: {gen100_scores}")
    print(f"Gen100 average: {gen100_avg:.2f}")

    # =========================================
    # Phase 4: Summary
    # =========================================
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Gen0 avg score: {gen0_avg:.2f}, Gen100 avg score: {gen100_avg:.2f}")
    print(f"Improvement: {gen100_avg - gen0_avg:.2f} points")
    print()
    print("Recordings saved:")
    print("  - genetic_gen0_replay1.json through genetic_gen0_replay8.json (untrained)")
    print("  - genetic_gen100_replay1.json through genetic_gen100_replay8.json (trained)")

    # Create EXIT_SIGNAL
    with open("EXIT_SIGNAL", "w") as f:
        f.write(f"Task 14 complete\n")
        f.write(f"Gen0 avg score: {gen0_avg:.2f}\n")
        f.write(f"Gen100 avg score: {gen100_avg:.2f}\n")

    print("\nEXIT_SIGNAL created.")
    print("Task 14 complete - STOPPING as requested.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
