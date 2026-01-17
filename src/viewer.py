#!/usr/bin/env python3
"""
Multi-Render Viewer for Flappy Bird recordings.

Displays NxN grid of game replays simultaneously with full visual polish.
Usage: python viewer.py --grid=4 recordings/*.json
       python viewer.py --scale=1.0 --fullscreen recordings/*.json
"""

import argparse
import os
import sys
import math
import random
import pygame
from typing import List, Optional

from game import (
    GameState, create_game, step, PIPE_GAP,
    SCREEN_WIDTH, SCREEN_HEIGHT, GROUND_Y, FPS,
    BIRD_WIDTH, BIRD_HEIGHT, PIPE_WIDTH
)
from recording import load_any_recording, Recording


# Colors - Day theme (matching renderer.py)
SKY_BLUE = (135, 206, 235)
SKY_BLUE_TOP = (100, 180, 255)
CLOUD_WHITE = (255, 255, 255)
CLOUD_SHADOW = (230, 230, 240)
CITY_DARK = (50, 60, 80)
CITY_WINDOW = (255, 255, 180)
GROUND_GREEN = (124, 181, 24)
GROUND_DARK = (84, 141, 4)
GROUND_STRIPE = (100, 160, 20)
BIRD_YELLOW = (255, 204, 0)
BIRD_ORANGE = (255, 140, 0)
BIRD_RED = (230, 100, 50)
PIPE_GREEN = (73, 153, 60)
PIPE_GREEN_DARK = (53, 133, 40)
PIPE_GREEN_LIGHT = (93, 173, 80)
PIPE_HIGHLIGHT = (120, 180, 100)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LABEL_BG = (0, 0, 0, 180)


class Cloud:
    """A simple cloud for parallax background."""
    def __init__(self, x, y, size, speed, cell_width):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
        self.cell_width = cell_width

    def update(self):
        self.x -= self.speed
        if self.x < -self.size * 3:
            self.x = self.cell_width + random.randint(50, 150)
            self.y = random.randint(20, 100)


class ReplayInstance:
    """Single replay instance with its state."""

    def __init__(self, recording: Recording, label: str, cell_width: int):
        self.recording = recording
        self.label = label
        self.state: Optional[GameState] = None
        self.frame_index = 0
        self.finished = False
        self.wing_frame = 0
        self.ground_offset = 0
        self.cell_width = cell_width
        # Create clouds for this instance
        self.clouds = []
        for _ in range(3):
            x = random.randint(0, cell_width)
            y = random.randint(20, 100)
            size = random.randint(15, 35)
            speed = 0.3 + random.random() * 0.3
            self.clouds.append(Cloud(x, y, size, speed, cell_width))
        # Generate city silhouette
        self.buildings = self._generate_city(cell_width)
        self.reset()

    def _generate_city(self, cell_width):
        """Generate city silhouette buildings."""
        buildings = []
        x = 0
        while x < cell_width:
            width = random.randint(15, 35)
            height = random.randint(20, 70)
            buildings.append((x, height, width))
            x += width + random.randint(3, 10)
        return buildings

    def reset(self):
        """Reset replay to beginning."""
        self.state = create_game(seed=self.recording.seed)
        self.frame_index = 0
        self.finished = False
        self.wing_frame = 0
        self.ground_offset = 0

    def advance(self) -> bool:
        """Advance one frame. Returns True if still playing."""
        if self.finished or self.frame_index >= len(self.recording.frames):
            self.finished = True
            return False

        frame = self.recording.frames[self.frame_index]
        step(self.state, jump=frame.jump)
        self.frame_index += 1
        self.wing_frame = (self.wing_frame + 1) % 20
        self.ground_offset = (self.ground_offset + 2) % 20

        # Update clouds
        for cloud in self.clouds:
            cloud.update()

        if not self.state.alive:
            self.finished = True

        return not self.finished


class GridViewer:
    """Viewer that displays multiple replays in a grid."""

    def __init__(self, grid_size: int, recordings: List[Recording], labels: List[str],
                 scale: float = 0.5, fullscreen: bool = False):
        pygame.init()

        self.grid_size = grid_size
        self.scale = scale
        self.cell_width = int(SCREEN_WIDTH * scale)
        self.cell_height = int(SCREEN_HEIGHT * scale)
        self.padding = 2

        # Window size based on grid
        self.window_width = grid_size * self.cell_width + (grid_size + 1) * self.padding
        self.window_height = grid_size * self.cell_height + (grid_size + 1) * self.padding

        # Fullscreen mode
        flags = pygame.FULLSCREEN if fullscreen else 0
        if fullscreen:
            # Get display info for fullscreen
            info = pygame.display.Info()
            self.window_width = info.current_w
            self.window_height = info.current_h
            # Recalculate cell size to fit
            max_cell_w = (self.window_width - (grid_size + 1) * self.padding) // grid_size
            max_cell_h = (self.window_height - (grid_size + 1) * self.padding) // grid_size
            # Maintain aspect ratio
            aspect = SCREEN_WIDTH / SCREEN_HEIGHT
            if max_cell_w / max_cell_h > aspect:
                self.cell_height = max_cell_h
                self.cell_width = int(max_cell_h * aspect)
            else:
                self.cell_width = max_cell_w
                self.cell_height = int(max_cell_w / aspect)

        self.screen = pygame.display.set_mode((self.window_width, self.window_height), flags)
        pygame.display.set_caption(f"Flappy Bird Viewer - {len(recordings)} recordings")
        self.clock = pygame.time.Clock()

        # Scale fonts based on cell size
        font_scale = max(0.5, self.scale)
        self.font = pygame.font.Font(None, int(18 * font_scale * 2))
        self.score_font = pygame.font.Font(None, int(24 * font_scale * 2))

        # Create replay instances
        self.replays: List[ReplayInstance] = []
        for i, (rec, label) in enumerate(zip(recordings, labels)):
            self.replays.append(ReplayInstance(rec, label, self.cell_width))

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
        """Draw a single replay cell with full visual polish."""
        state = replay.state
        if state is None:
            return

        # Create cell surface
        cell = pygame.Surface((self.cell_width, self.cell_height))

        # Scale coordinates
        sx = self.scale_x
        sy = self.scale_y
        ground_y = int(GROUND_Y * sy)

        # Draw sky gradient
        for row in range(ground_y):
            ratio = row / ground_y
            r = int(SKY_BLUE_TOP[0] + (SKY_BLUE[0] - SKY_BLUE_TOP[0]) * ratio)
            g = int(SKY_BLUE_TOP[1] + (SKY_BLUE[1] - SKY_BLUE_TOP[1]) * ratio)
            b = int(SKY_BLUE_TOP[2] + (SKY_BLUE[2] - SKY_BLUE_TOP[2]) * ratio)
            pygame.draw.line(cell, (r, g, b), (0, row), (self.cell_width, row))

        # Draw clouds (parallax)
        for cloud in replay.clouds:
            cx, cy, size = int(cloud.x), int(cloud.y * sy), int(cloud.size * sx)
            # Shadow
            pygame.draw.circle(cell, CLOUD_SHADOW, (cx + 1, cy + 1), size)
            pygame.draw.circle(cell, CLOUD_SHADOW, (cx + size + 1, cy + 1), size - 3)
            # Cloud
            pygame.draw.circle(cell, CLOUD_WHITE, (cx, cy), size)
            pygame.draw.circle(cell, CLOUD_WHITE, (cx + size, cy), size - 3)

        # Draw city silhouette
        city_y = ground_y - 5
        for bx, bh, bw in replay.buildings:
            scaled_bh = int(bh * sy)
            scaled_bw = int(bw * sx)
            pygame.draw.rect(cell, CITY_DARK, (bx, city_y - scaled_bh, scaled_bw, scaled_bh))
            # Random windows
            for wy in range(city_y - scaled_bh + 4, city_y - 5, 8):
                for wx in range(bx + 3, bx + scaled_bw - 3, 6):
                    if random.random() > 0.7:
                        pygame.draw.rect(cell, CITY_WINDOW, (wx, wy, 3, 4))

        # Draw pipes with caps
        for pipe in state.pipes:
            self._draw_pipe_scaled(cell, pipe, sx, sy)

        # Draw ground with texture
        pygame.draw.rect(cell, GROUND_GREEN,
                        (0, ground_y, self.cell_width, self.cell_height - ground_y))
        pygame.draw.rect(cell, GROUND_DARK,
                        (0, ground_y, self.cell_width, max(2, int(3 * sy))))
        # Grass stripes
        stripe_width = int(15 * sx)
        if stripe_width > 0:
            offset = int(replay.ground_offset * sx)
            for stripe_x in range(-stripe_width + offset, self.cell_width, stripe_width * 2):
                pygame.draw.rect(cell, GROUND_STRIPE,
                               (stripe_x, ground_y + int(3 * sy), stripe_width,
                                self.cell_height - ground_y - int(3 * sy)))

        # Draw bird with full detail
        wing_up = replay.wing_frame < 10
        self._draw_bird_detailed(cell, state, sx, sy, wing_up)

        # Draw score with shadow
        score_text = self.score_font.render(str(state.score), True, WHITE)
        score_shadow = self.score_font.render(str(state.score), True, BLACK)
        cell.blit(score_shadow, (self.cell_width // 2 - score_text.get_width() // 2 + 2, 12))
        cell.blit(score_text, (self.cell_width // 2 - score_text.get_width() // 2, 10))

        # Draw game over with red tint
        if not state.alive:
            overlay = pygame.Surface((self.cell_width, self.cell_height), pygame.SRCALPHA)
            overlay.fill((255, 0, 0, 40))
            cell.blit(overlay, (0, 0))
            go_text = self.font.render("GAME OVER", True, WHITE)
            go_shadow = self.font.render("GAME OVER", True, BLACK)
            cell.blit(go_shadow, (self.cell_width // 2 - go_text.get_width() // 2 + 2,
                                 self.cell_height // 2 - go_text.get_height() // 2 + 2))
            cell.blit(go_text, (self.cell_width // 2 - go_text.get_width() // 2,
                               self.cell_height // 2 - go_text.get_height() // 2))

        # Draw label at bottom
        label_height = max(20, int(25 * sy))
        label_text = self.font.render(replay.label, True, WHITE)
        label_bg = pygame.Surface((self.cell_width, label_height), pygame.SRCALPHA)
        label_bg.fill((0, 0, 0, 150))
        cell.blit(label_bg, (0, self.cell_height - label_height))
        cell.blit(label_text, (5, self.cell_height - label_height + 2))

        # Blit cell to screen
        self.screen.blit(cell, (x, y))

    def _draw_pipe_scaled(self, surface: pygame.Surface, pipe, sx: float, sy: float):
        """Draw a scaled pipe with caps and shading."""
        x = int(pipe.x * sx)
        pipe_w = max(int(PIPE_WIDTH * sx), 6)
        top_h = int(pipe.top_height * sy)
        bottom_y = int(pipe.bottom_y * sy)
        cap_height = max(int(15 * sy), 6)
        cap_extra = max(int(3 * sx), 2)  # Cap is wider than pipe

        # Top pipe body
        if top_h > cap_height:
            pygame.draw.rect(surface, PIPE_GREEN, (x, 0, pipe_w, top_h - cap_height))

        # Top pipe cap
        cap_x = x - cap_extra
        cap_w = pipe_w + cap_extra * 2
        if top_h > 0:
            pygame.draw.rect(surface, PIPE_GREEN,
                            (cap_x, top_h - cap_height, cap_w, cap_height))
            # Cap highlight (left edge)
            pygame.draw.rect(surface, PIPE_GREEN_LIGHT,
                            (cap_x + 1, top_h - cap_height + 1, 2, cap_height - 2))
            # Cap shadow (right edge)
            pygame.draw.rect(surface, PIPE_GREEN_DARK,
                            (cap_x + cap_w - 3, top_h - cap_height + 1, 2, cap_height - 2))

        # Bottom pipe body
        if self.cell_height - bottom_y > cap_height:
            pygame.draw.rect(surface, PIPE_GREEN,
                            (x, bottom_y + cap_height, pipe_w,
                             self.cell_height - bottom_y - cap_height))

        # Bottom pipe cap
        pygame.draw.rect(surface, PIPE_GREEN,
                        (cap_x, bottom_y, cap_w, cap_height))
        # Cap highlight
        pygame.draw.rect(surface, PIPE_GREEN_LIGHT,
                        (cap_x + 1, bottom_y + 1, 2, cap_height - 2))
        # Cap shadow
        pygame.draw.rect(surface, PIPE_GREEN_DARK,
                        (cap_x + cap_w - 3, bottom_y + 1, 2, cap_height - 2))

    def _draw_bird_detailed(self, surface: pygame.Surface, state: GameState,
                            sx: float, sy: float, wing_up: bool):
        """Draw bird with full visual details."""
        bird_x = int(state.bird.x * sx)
        bird_y = int(state.bird.y * sy)
        bird_w = max(int(BIRD_WIDTH * sx), 10)
        bird_h = max(int(BIRD_HEIGHT * sy), 8)

        # Create bird surface for rotation
        surf_size = max(bird_w + 8, bird_h + 8)
        bird_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        offset_x = (surf_size - bird_w) // 2
        offset_y = (surf_size - bird_h) // 2

        # Body
        pygame.draw.ellipse(bird_surf, BIRD_YELLOW,
                           (offset_x, offset_y, bird_w, bird_h))
        # Body highlight
        highlight_h = max(bird_h // 2, 3)
        pygame.draw.ellipse(bird_surf, (255, 220, 50),
                           (offset_x + 2, offset_y + 1, bird_w - 6, highlight_h))

        # Wing with animation
        wing_y_off = -2 if wing_up else 1
        wing_w = max(bird_w // 3, 4)
        wing_h = max(bird_h // 3, 3)
        wing_rect = (offset_x + 3, offset_y + bird_h // 2 + wing_y_off, wing_w, wing_h)
        pygame.draw.ellipse(bird_surf, BIRD_ORANGE, wing_rect)

        # Eye
        eye_x = offset_x + bird_w - max(bird_w // 4, 4)
        eye_y = offset_y + max(bird_h // 4, 3)
        eye_r = max(bird_w // 6, 2)
        pygame.draw.circle(bird_surf, WHITE, (eye_x, eye_y), eye_r)
        pygame.draw.circle(bird_surf, BLACK, (eye_x + 1, eye_y), max(eye_r // 2, 1))

        # Beak
        beak_x = offset_x + bird_w - 1
        beak_y = offset_y + bird_h // 2
        beak_size = max(bird_w // 4, 3)
        # Top beak
        pygame.draw.polygon(bird_surf, BIRD_ORANGE, [
            (beak_x, beak_y - 1),
            (beak_x + beak_size, beak_y),
            (beak_x, beak_y)
        ])
        # Bottom beak
        pygame.draw.polygon(bird_surf, BIRD_RED, [
            (beak_x, beak_y),
            (beak_x + beak_size, beak_y),
            (beak_x, beak_y + 1)
        ])

        # Rotate based on bird's rotation
        rotated = pygame.transform.rotate(bird_surf, -state.bird.rotation)
        rect = rotated.get_rect(center=(bird_x, bird_y))
        surface.blit(rotated, rect)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-Render Viewer for Flappy Bird recordings"
    )
    parser.add_argument('--grid', type=int, default=2,
                       help='Grid size NxN (default: 2)')
    parser.add_argument('--scale', type=float, default=1.0,
                       help='Scale factor for each cell (default: 1.0 = full size)')
    parser.add_argument('--fullscreen', action='store_true',
                       help='Run in fullscreen mode')
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

    print(f"\nViewer settings: grid={args.grid}x{args.grid}, scale={args.scale}, fullscreen={args.fullscreen}")

    # Create and run viewer
    viewer = GridViewer(args.grid, recordings, labels,
                        scale=args.scale, fullscreen=args.fullscreen)
    viewer.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
