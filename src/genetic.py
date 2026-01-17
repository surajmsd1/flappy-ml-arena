#!/usr/bin/env python3
"""
Simple Genetic Algorithm for Flappy Bird

Features:
- Fixed neural network architecture (7 inputs -> 10 hidden -> 1 output)
- Population-based evolution with fitness = score + frames_survived/1000
- Tournament selection + crossover + mutation
- Saves replays of best performers per generation
"""

import os
import random
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from game import create_game, step
from features import extract_features
from recording import Recording, save_compact


# Neural Network Architecture
INPUT_SIZE = 7   # Features from extract_features().to_list()
HIDDEN_SIZE = 10
OUTPUT_SIZE = 1  # Jump probability


@dataclass
class NeuralNetwork:
    """Simple feedforward neural network."""
    weights_ih: List[List[float]] = field(default_factory=list)  # Input -> Hidden
    bias_h: List[float] = field(default_factory=list)            # Hidden bias
    weights_ho: List[List[float]] = field(default_factory=list)  # Hidden -> Output
    bias_o: List[float] = field(default_factory=list)            # Output bias

    def __post_init__(self):
        if not self.weights_ih:
            self._initialize_random()

    def _initialize_random(self):
        """Initialize with random weights."""
        # Xavier-like initialization
        scale_ih = math.sqrt(2.0 / INPUT_SIZE)
        scale_ho = math.sqrt(2.0 / HIDDEN_SIZE)

        self.weights_ih = [
            [random.gauss(0, scale_ih) for _ in range(INPUT_SIZE)]
            for _ in range(HIDDEN_SIZE)
        ]
        self.bias_h = [0.0] * HIDDEN_SIZE

        self.weights_ho = [
            [random.gauss(0, scale_ho) for _ in range(HIDDEN_SIZE)]
            for _ in range(OUTPUT_SIZE)
        ]
        self.bias_o = [0.0] * OUTPUT_SIZE

    def forward(self, inputs: List[float]) -> float:
        """Forward pass. Returns jump probability [0, 1]."""
        # Hidden layer
        hidden = []
        for j in range(HIDDEN_SIZE):
            activation = self.bias_h[j]
            for i in range(INPUT_SIZE):
                activation += self.weights_ih[j][i] * inputs[i]
            hidden.append(self._relu(activation))

        # Output layer
        output = self.bias_o[0]
        for j in range(HIDDEN_SIZE):
            output += self.weights_ho[0][j] * hidden[j]

        return self._sigmoid(output)

    def decide(self, inputs: List[float]) -> bool:
        """Decide whether to jump based on inputs."""
        prob = self.forward(inputs)
        return prob > 0.5

    @staticmethod
    def _relu(x: float) -> float:
        return max(0, x)

    @staticmethod
    def _sigmoid(x: float) -> float:
        if x < -500:
            return 0.0
        if x > 500:
            return 1.0
        return 1.0 / (1.0 + math.exp(-x))

    def mutate(self, rate: float = 0.1, scale: float = 0.5) -> 'NeuralNetwork':
        """Return mutated copy of this network."""
        new_net = NeuralNetwork()

        # Copy and mutate weights_ih
        new_net.weights_ih = []
        for row in self.weights_ih:
            new_row = []
            for w in row:
                if random.random() < rate:
                    new_row.append(w + random.gauss(0, scale))
                else:
                    new_row.append(w)
            new_net.weights_ih.append(new_row)

        # Copy and mutate bias_h
        new_net.bias_h = []
        for b in self.bias_h:
            if random.random() < rate:
                new_net.bias_h.append(b + random.gauss(0, scale))
            else:
                new_net.bias_h.append(b)

        # Copy and mutate weights_ho
        new_net.weights_ho = []
        for row in self.weights_ho:
            new_row = []
            for w in row:
                if random.random() < rate:
                    new_row.append(w + random.gauss(0, scale))
                else:
                    new_row.append(w)
            new_net.weights_ho.append(new_row)

        # Copy and mutate bias_o
        new_net.bias_o = []
        for b in self.bias_o:
            if random.random() < rate:
                new_net.bias_o.append(b + random.gauss(0, scale))
            else:
                new_net.bias_o.append(b)

        return new_net

    @staticmethod
    def crossover(parent1: 'NeuralNetwork', parent2: 'NeuralNetwork') -> 'NeuralNetwork':
        """Create child network by combining two parents."""
        child = NeuralNetwork()

        # Crossover weights_ih
        child.weights_ih = []
        for r, (row1, row2) in enumerate(zip(parent1.weights_ih, parent2.weights_ih)):
            new_row = []
            for w1, w2 in zip(row1, row2):
                new_row.append(w1 if random.random() < 0.5 else w2)
            child.weights_ih.append(new_row)

        # Crossover bias_h
        child.bias_h = [
            b1 if random.random() < 0.5 else b2
            for b1, b2 in zip(parent1.bias_h, parent2.bias_h)
        ]

        # Crossover weights_ho
        child.weights_ho = []
        for row1, row2 in zip(parent1.weights_ho, parent2.weights_ho):
            new_row = []
            for w1, w2 in zip(row1, row2):
                new_row.append(w1 if random.random() < 0.5 else w2)
            child.weights_ho.append(new_row)

        # Crossover bias_o
        child.bias_o = [
            b1 if random.random() < 0.5 else b2
            for b1, b2 in zip(parent1.bias_o, parent2.bias_o)
        ]

        return child


@dataclass
class Agent:
    """An agent with neural network brain and fitness tracking."""
    network: NeuralNetwork
    fitness: float = 0.0
    score: int = 0
    frames: int = 0


def evaluate_agent(agent: Agent, seed: int, max_frames: int = 3000) -> Tuple[float, int, int, Recording]:
    """
    Evaluate an agent on a game.

    Returns (fitness, score, frames, recording)
    """
    state = create_game(seed=seed)
    recording = Recording(seed=seed)

    for _ in range(max_frames):
        if not state.alive:
            break

        # First frame: always jump to start the game
        # The game only begins physics/pipes when started=True (triggered by first jump)
        if not state.started:
            jump = True
        else:
            # Normal decision making based on game features
            features = extract_features(state)
            jump = agent.network.decide(features.to_list())

        step(state, jump=jump)
        recording.add_frame(state.frame, jump, state)

    # Fitness: score + survival bonus
    fitness = state.score + state.frame / 1000.0
    return fitness, state.score, state.frame, recording


def tournament_select(population: List[Agent], tournament_size: int = 3) -> Agent:
    """Select an agent via tournament selection."""
    tournament = random.sample(population, min(tournament_size, len(population)))
    return max(tournament, key=lambda a: a.fitness)


def create_next_generation(population: List[Agent], elite_count: int = 2,
                          mutation_rate: float = 0.1) -> List[Agent]:
    """Create next generation from current population."""
    # Sort by fitness
    sorted_pop = sorted(population, key=lambda a: a.fitness, reverse=True)

    next_gen = []

    # Elitism: keep top performers unchanged
    for i in range(elite_count):
        next_gen.append(Agent(network=sorted_pop[i].network))

    # Fill rest with offspring
    while len(next_gen) < len(population):
        parent1 = tournament_select(sorted_pop)
        parent2 = tournament_select(sorted_pop)

        child_net = NeuralNetwork.crossover(parent1.network, parent2.network)
        child_net = child_net.mutate(rate=mutation_rate)

        next_gen.append(Agent(network=child_net))

    return next_gen


def run_generation(population: List[Agent], generation: int,
                   seed: int, max_frames: int = 3000) -> List[Tuple[Agent, Recording]]:
    """
    Run one generation. Evaluate all agents on same seed.

    Returns list of (agent, recording) sorted by fitness descending.
    """
    results = []

    for agent in population:
        fitness, score, frames, recording = evaluate_agent(agent, seed, max_frames)
        agent.fitness = fitness
        agent.score = score
        agent.frames = frames
        results.append((agent, recording))

    # Sort by fitness descending
    results.sort(key=lambda x: x[0].fitness, reverse=True)
    return results


def train_genetic(
    generations: int,
    population_size: int = 50,
    save_best_n: int = 4,
    mutation_rate: float = 0.1,
    max_frames: int = 3000,
    output_dir: str = "recordings",
    verbose: bool = True
) -> List[dict]:
    """
    Run genetic algorithm training.

    Args:
        generations: Number of generations to run
        population_size: Size of population
        save_best_n: How many best replays to save per generation
        mutation_rate: Probability of mutating each weight
        max_frames: Max frames per game
        output_dir: Directory to save recordings
        verbose: Print progress

    Returns:
        List of generation stats
    """
    os.makedirs(output_dir, exist_ok=True)

    # Initialize population
    population = [Agent(network=NeuralNetwork()) for _ in range(population_size)]

    stats = []

    for gen in range(generations):
        # Use different seed each generation for diversity
        seed = gen * 1000 + 42

        # Evaluate generation
        results = run_generation(population, gen, seed, max_frames)

        # Collect stats
        fitnesses = [r[0].fitness for r in results]
        scores = [r[0].score for r in results]
        best_agent, best_recording = results[0]

        gen_stats = {
            'generation': gen + 1,
            'best_fitness': best_agent.fitness,
            'best_score': best_agent.score,
            'best_frames': best_agent.frames,
            'avg_fitness': sum(fitnesses) / len(fitnesses),
            'avg_score': sum(scores) / len(scores),
            'max_score': max(scores),
        }
        stats.append(gen_stats)

        if verbose:
            print(f"Gen {gen+1:3d} | Best: {best_agent.score:3d} pts, {best_agent.frames:4d} frames | "
                  f"Avg: {gen_stats['avg_score']:.1f} pts | Max: {gen_stats['max_score']}")

        # Save best recordings
        for i in range(min(save_best_n, len(results))):
            agent, recording = results[i]
            filename = f"genetic_gen{gen+1}_best{i+1}.json"
            filepath = os.path.join(output_dir, filename)
            save_compact(recording, filepath)

        # Create next generation
        population = create_next_generation(
            [r[0] for r in results],
            elite_count=2,
            mutation_rate=mutation_rate
        )

    return stats


def main():
    """Interactive entry point - asks user for parameters."""
    print("=" * 60)
    print("Flappy Bird - Simple Genetic Algorithm")
    print("=" * 60)
    print()
    print("This will train neural networks to play Flappy Bird")
    print("using a simple genetic algorithm (selection + mutation).")
    print()
    print("The networks have:")
    print("  - 7 input neurons (game features)")
    print("  - 10 hidden neurons (ReLU activation)")
    print("  - 1 output neuron (jump probability)")
    print()

    # Get user parameters
    try:
        generations = int(input("How many generations to run? [10]: ").strip() or "10")
        population_size = int(input("Population size? [50]: ").strip() or "50")
        save_best_n = int(input("How many best replays to save per generation? [4]: ").strip() or "4")
    except ValueError:
        print("Invalid input, using defaults")
        generations = 10
        population_size = 50
        save_best_n = 4

    print()
    print(f"Training with:")
    print(f"  Generations: {generations}")
    print(f"  Population: {population_size}")
    print(f"  Saving: {save_best_n} best per generation")
    print()

    confirm = input("Start training? [Y/n]: ").strip().lower()
    if confirm in ('n', 'no'):
        print("Training cancelled.")
        return

    print()
    print("Starting training...")
    print("-" * 60)

    stats = train_genetic(
        generations=generations,
        population_size=population_size,
        save_best_n=save_best_n,
        output_dir="recordings"
    )

    print("-" * 60)
    print()
    print("Training complete!")
    print()
    print(f"Best overall: {max(s['max_score'] for s in stats)} pts")
    print(f"Recordings saved to: recordings/genetic_gen*_best*.json")
    print()
    print(f"View replays with: python viewer.py --grid=2 recordings/genetic_gen*.json")


if __name__ == "__main__":
    main()
