#!/usr/bin/env python3
"""
Multi-Render Viewer for Flappy Bird recordings.

Displays NxN grid of game replays simultaneously.
Usage: python viewer.py --grid=4 recordings/*.json
"""

import argparse
import os
import sys
import math
import pygame
from typing import List, Optional

from game import (
    GameState, create_game, step,
    SCREEN_WIDTH, SCREEN_HEIGHT, GROUND_Y, FPS,
    BIRD_WIDTH, BIRD_HEIGHT, PIPE_WIDTH
)
from recording import load_any_recording, Recording


# Colors
SKY_BLUE = (135, 206, 235)
GROUND_GREEN = (124, 181, 24)
GROUND_DARK = (84, 141, 4)
BIRD_YELLOW = (255, 204, 0)
BIRD_ORANGE = (255, 140, 0)
PIPE_GREEN = (73, 153, 60)
PIPE_GREEN_DARK = (53, 133, 40)
PIPE_GREEN_LIGHT = (93, 173, 80)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LABEL_BG = (0, 0, 0, 180)


class ReplayInstance:
    """Single replay instance with its state."""

    def __init__(self, recording: Recording, label: str):
        self.recording = recording
        self.label = label
        self.state: Optional[GameState] = None
        self.frame_index = 0
        self.finished = False
        self.reset()

    def reset(self):
        """Reset replay to beginning."""
        self.state = create_game(seed=self.recording.seed)
        self.frame_index = 0
        self.finished = False

    def advance(self) -> bool:
        """Advance one frame. Returns True if still playing."""
        if self.finished or self.frame_index >= len(self.recording.frames):
            self.finished = True
            return False

        frame = self.recording.frames[self.frame_index]
        step(self.state, jump=frame.jump)
        self.frame_index += 1

        if not self.state.alive:
            self.finished = True

        return not self.finished


class GridViewer:
    """Viewer that displays multiple replays in a grid."""

    def __init__(self, grid_size: int, recordings: List[Recording], labels: List[str]):
        pygame.init()

        self.grid_size = grid_size
        self.cell_width = SCREEN_WIDTH // 2  # Scale down for grid
        self.cell_height = SCREEN_HEIGHT // 2
        self.padding = 2

        # Window size based on grid
        self.window_width = grid_size * self.cell_width + (grid_size + 1) * self.padding
        self.window_height = grid_size * self.cell_height + (grid_size + 1) * self.padding

        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption(f"Flappy Bird Viewer - {len(recordings)} recordings")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 18)
        self.score_font = pygame.font.Font(None, 24)

        # Create replay instances
        self.replays: List[ReplayInstance] = []
        for i, (rec, label) in enumerate(zip(recordings, labels)):
            self.replays.append(ReplayInstance(rec, label))

        # Scale factor for rendering
        self.scale_x = self.cell_width / SCREEN_WIDTH
        self.scale_y = self.cell_height / SCREEN_HEIGHT

    def run(self):
        """Main viewer loop."""
        running = True
        paused = False
        all_finished = False

        print("Controls:")
        print("  SPACE - Pause/Resume")
        print("  R     - Restart all")
        print("  ESC   - Quit")

        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                    elif event.key == pygame.K_r:
                        for replay in self.replays:
                            replay.reset()
                        all_finished = False

            # Advance replays if not paused
            if not paused and not all_finished:
                still_playing = False
                for replay in self.replays:
                    if replay.advance():
                        still_playing = True
                if not still_playing:
                    all_finished = True

            # Draw
            self.screen.fill(BLACK)

            for i, replay in enumerate(self.replays):
                row = i // self.grid_size
                col = i % self.grid_size
                if row >= self.grid_size:
                    break  # Don't draw beyond grid

                x = self.padding + col * (self.cell_width + self.padding)
                y = self.padding + row * (self.cell_height + self.padding)
                self._draw_cell(replay, x, y)

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

    def _draw_cell(self, replay: ReplayInstance, x: int, y: int):
        """Draw a single replay cell."""
        state = replay.state
        if state is None:
            return

        # Create cell surface
        cell = pygame.Surface((self.cell_width, self.cell_height))
        cell.fill(SKY_BLUE)

        # Scale coordinates
        sx = self.scale_x
        sy = self.scale_y

        # Draw pipes
        for pipe in state.pipes:
            self._draw_pipe_scaled(cell, pipe, sx, sy)

        # Draw ground
        ground_y = int(GROUND_Y * sy)
        pygame.draw.rect(cell, GROUND_GREEN,
                        (0, ground_y, self.cell_width, self.cell_height - ground_y))
        pygame.draw.rect(cell, GROUND_DARK,
                        (0, ground_y, self.cell_width, 2))

        # Draw bird
        bird_x = int(state.bird.x * sx)
        bird_y = int(state.bird.y * sy)
        bird_w = max(int(BIRD_WIDTH * sx), 8)
        bird_h = max(int(BIRD_HEIGHT * sy), 6)
        pygame.draw.ellipse(cell, BIRD_YELLOW,
                           (bird_x - bird_w // 2, bird_y - bird_h // 2, bird_w, bird_h))

        # Draw score
        score_text = self.score_font.render(str(state.score), True, WHITE)
        score_shadow = self.score_font.render(str(state.score), True, BLACK)
        cell.blit(score_shadow, (self.cell_width // 2 - score_text.get_width() // 2 + 1, 11))
        cell.blit(score_text, (self.cell_width // 2 - score_text.get_width() // 2, 10))

        # Draw game over indicator
        if not state.alive:
            overlay = pygame.Surface((self.cell_width, self.cell_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            cell.blit(overlay, (0, 0))
            go_text = self.font.render("GAME OVER", True, WHITE)
            cell.blit(go_text, (self.cell_width // 2 - go_text.get_width() // 2,
                               self.cell_height // 2 - go_text.get_height() // 2))

        # Draw label at bottom
        label_text = self.font.render(replay.label, True, WHITE)
        label_bg = pygame.Surface((self.cell_width, 20), pygame.SRCALPHA)
        label_bg.fill((0, 0, 0, 150))
        cell.blit(label_bg, (0, self.cell_height - 20))
        cell.blit(label_text, (5, self.cell_height - 18))

        # Blit cell to screen
        self.screen.blit(cell, (x, y))

    def _draw_pipe_scaled(self, surface: pygame.Surface, pipe, sx: float, sy: float):
        """Draw a scaled pipe."""
        x = int(pipe.x * sx)
        pipe_w = max(int(PIPE_WIDTH * sx), 6)
        top_h = int(pipe.top_height * sy)
        bottom_y = int(pipe.bottom_y * sy)

        # Top pipe
        if top_h > 0:
            pygame.draw.rect(surface, PIPE_GREEN, (x, 0, pipe_w, top_h))

        # Bottom pipe
        pygame.draw.rect(surface, PIPE_GREEN,
                        (x, bottom_y, pipe_w, self.cell_height - bottom_y))


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-Render Viewer for Flappy Bird recordings"
    )
    parser.add_argument('--grid', type=int, default=2,
                       help='Grid size NxN (default: 2)')
    parser.add_argument('recordings', nargs='+',
                       help='Recording files to display')
    return parser.parse_args()


def extract_label(filepath: str) -> str:
    """Extract a display label from filepath."""
    basename = os.path.basename(filepath)
    name = os.path.splitext(basename)[0]

    # Try to make it more readable
    # genetic_gen5_best1.json -> "Genetic G5 #1"
    # neat_gen10_best2.json -> "NEAT G10 #2"
    # game_20260117_score5.json -> "Game score:5"

    if name.startswith('genetic_'):
        parts = name.replace('genetic_', '').split('_')
        gen = parts[0].replace('gen', 'G') if parts else ''
        best = parts[1].replace('best', '#') if len(parts) > 1 else ''
        return f"Genetic {gen} {best}".strip()
    elif name.startswith('neat_'):
        parts = name.replace('neat_', '').split('_')
        gen = parts[0].replace('gen', 'G') if parts else ''
        best = parts[1].replace('best', '#') if len(parts) > 1 else ''
        return f"NEAT {gen} {best}".strip()
    elif name.startswith('imitation_'):
        parts = name.replace('imitation_', '').split('_')
        epoch = parts[0].replace('epoch', 'E') if parts else ''
        replay = parts[1].replace('replay', '#') if len(parts) > 1 else ''
        return f"Imitation {epoch} {replay}".strip()
    elif name.startswith('dqn_'):
        parts = name.replace('dqn_', '').split('_')
        step_num = parts[0].replace('step', 'S') if parts else ''
        replay = parts[1].replace('replay', '#') if len(parts) > 1 else ''
        return f"DQN {step_num} {replay}".strip()
    elif 'score' in name:
        # Extract score from game_YYYYMMDD_HHMMSS_scoreN.json
        try:
            score = name.split('score')[1]
            return f"Score: {score}"
        except (IndexError, ValueError):
            pass

    # Fallback: just use filename
    return name[:20] if len(name) > 20 else name


def main():
    """Main entry point."""
    args = parse_args()

    # Load recordings
    recordings = []
    labels = []

    for filepath in args.recordings:
        try:
            rec = load_any_recording(filepath)
            recordings.append(rec)
            labels.append(extract_label(filepath))
            print(f"Loaded: {filepath} ({rec.total_frames} frames, score {rec.final_score})")
        except Exception as e:
            print(f"Warning: Could not load {filepath}: {e}")

    if not recordings:
        print("Error: No recordings loaded")
        return 1

    # Limit to grid size squared
    max_cells = args.grid * args.grid
    if len(recordings) > max_cells:
        print(f"Note: Showing first {max_cells} of {len(recordings)} recordings")
        recordings = recordings[:max_cells]
        labels = labels[:max_cells]

    # Create and run viewer
    viewer = GridViewer(args.grid, recordings, labels)
    viewer.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
