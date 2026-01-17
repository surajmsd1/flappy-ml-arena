"""
Pygame Renderer for Flappy Bird

Handles all visualization - completely separate from game logic.
Features: parallax clouds, city silhouette, animated bird, polished pipes.
"""

import pygame
import math
import random
from game import (
    GameState, SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BIRD_WIDTH, BIRD_HEIGHT, GROUND_Y, PIPE_WIDTH, PIPE_GAP
)


# Colors - Day theme
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
RED_TINT = (255, 0, 0, 80)


class Cloud:
    """A simple cloud for parallax background."""
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed

    def update(self):
        self.x -= self.speed
        if self.x < -self.size * 3:
            self.x = SCREEN_WIDTH + random.randint(50, 150)
            self.y = random.randint(20, 150)


class Renderer:
    """Pygame-based renderer for the game."""

    def __init__(self, theme='day'):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Bird")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        self.theme = theme

        # Parallax clouds
        self.clouds = []
        for i in range(5):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(20, 150)
            size = random.randint(30, 60)
            speed = 0.3 + random.random() * 0.4
            self.clouds.append(Cloud(x, y, size, speed))

        # City buildings (static silhouette)
        self.buildings = self._generate_city()

        # Ground scroll offset
        self.ground_offset = 0

        # Wing animation frame
        self.wing_frame = 0

    def _generate_city(self):
        """Generate city silhouette buildings."""
        buildings = []
        x = 0
        while x < SCREEN_WIDTH:
            width = random.randint(30, 60)
            height = random.randint(40, 120)
            buildings.append((x, height, width))
            x += width + random.randint(5, 15)
        return buildings

    def _draw_sky_gradient(self):
        """Draw gradient sky background."""
        for y in range(GROUND_Y):
            ratio = y / GROUND_Y
            r = int(SKY_BLUE_TOP[0] + (SKY_BLUE[0] - SKY_BLUE_TOP[0]) * ratio)
            g = int(SKY_BLUE_TOP[1] + (SKY_BLUE[1] - SKY_BLUE_TOP[1]) * ratio)
            b = int(SKY_BLUE_TOP[2] + (SKY_BLUE[2] - SKY_BLUE_TOP[2]) * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    def _draw_clouds(self):
        """Draw and update parallax clouds."""
        for cloud in self.clouds:
            cloud.update()
            # Draw cloud as overlapping circles
            cx, cy, size = int(cloud.x), int(cloud.y), cloud.size
            # Shadow
            pygame.draw.circle(self.screen, CLOUD_SHADOW, (cx + 2, cy + 2), size)
            pygame.draw.circle(self.screen, CLOUD_SHADOW, (cx + size + 2, cy + 2), size - 5)
            pygame.draw.circle(self.screen, CLOUD_SHADOW, (cx + size // 2 + 2, cy - size // 3 + 2), size - 8)
            # Cloud
            pygame.draw.circle(self.screen, CLOUD_WHITE, (cx, cy), size)
            pygame.draw.circle(self.screen, CLOUD_WHITE, (cx + size, cy), size - 5)
            pygame.draw.circle(self.screen, CLOUD_WHITE, (cx + size // 2, cy - size // 3), size - 8)

    def _draw_city(self):
        """Draw city silhouette in background."""
        city_y = GROUND_Y - 10
        for bx, bh, bw in self.buildings:
            # Building
            pygame.draw.rect(self.screen, CITY_DARK, (bx, city_y - bh, bw, bh))
            # Windows (some lit)
            for wy in range(city_y - bh + 8, city_y - 10, 12):
                for wx in range(bx + 5, bx + bw - 5, 10):
                    if random.random() > 0.7:
                        pygame.draw.rect(self.screen, CITY_WINDOW, (wx, wy, 5, 6))

    def _draw_ground(self):
        """Draw ground with grass texture."""
        # Main ground
        pygame.draw.rect(self.screen, GROUND_GREEN,
                        (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))
        # Dark top line
        pygame.draw.rect(self.screen, GROUND_DARK, (0, GROUND_Y, SCREEN_WIDTH, 5))

        # Grass stripe pattern (scrolling)
        stripe_width = 20
        self.ground_offset = (self.ground_offset + 2) % stripe_width
        for x in range(-stripe_width + int(self.ground_offset), SCREEN_WIDTH, stripe_width * 2):
            pygame.draw.rect(self.screen, GROUND_STRIPE,
                           (x, GROUND_Y + 5, stripe_width, SCREEN_HEIGHT - GROUND_Y - 5))

    def draw(self, state: GameState) -> None:
        """Draw the current game state."""
        # Sky gradient background
        self._draw_sky_gradient()

        # Clouds (parallax - slowest)
        self._draw_clouds()

        # City silhouette
        self._draw_city()

        # Pipes (draw before ground so ground covers pipe bottoms)
        for pipe in state.pipes:
            self._draw_pipe(pipe)

        # Ground with texture
        self._draw_ground()

        # Bird with wing animation
        self.wing_frame = (self.wing_frame + 1) % 20
        wing_up = self.wing_frame < 10
        self._draw_bird(state.bird.x, state.bird.y, state.bird.rotation, wing_up)

        # Score with drop shadow
        score_text = self.font.render(str(state.score), True, WHITE)
        score_rect = score_text.get_rect(centerx=SCREEN_WIDTH // 2, top=50)
        shadow = self.font.render(str(state.score), True, BLACK)
        self.screen.blit(shadow, (score_rect.x + 3, score_rect.y + 3))
        self.screen.blit(score_text, score_rect)

        # Instructions if not started
        if not state.started:
            instr = self.small_font.render("Press SPACE to start", True, WHITE)
            instr_rect = instr.get_rect(centerx=SCREEN_WIDTH // 2,
                                        centery=SCREEN_HEIGHT // 2 + 50)
            self.screen.blit(instr, instr_rect)

        # Game over message with red tint
        if not state.alive:
            # Red overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 0, 0, 40))
            self.screen.blit(overlay, (0, 0))

            go_text = self.font.render("GAME OVER", True, WHITE)
            go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            # Shadow
            go_shadow = self.font.render("GAME OVER", True, BLACK)
            self.screen.blit(go_shadow, (go_rect.x + 3, go_rect.y + 3))
            self.screen.blit(go_text, go_rect)

            restart = self.small_font.render("Press R to restart", True, WHITE)
            restart_rect = restart.get_rect(centerx=SCREEN_WIDTH // 2,
                                           centery=SCREEN_HEIGHT // 2 + 40)
            self.screen.blit(restart, restart_rect)

        pygame.display.flip()

    def _draw_bird(self, x: float, y: float, rotation: float, wing_up: bool = False) -> None:
        """Draw the bird at given position with rotation and wing animation."""
        # Create bird surface (slightly larger for beak)
        surf_size = max(BIRD_WIDTH + 10, BIRD_HEIGHT + 10)
        bird_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        offset_x = (surf_size - BIRD_WIDTH) // 2
        offset_y = (surf_size - BIRD_HEIGHT) // 2

        # Body (ellipse with slight gradient effect)
        pygame.draw.ellipse(bird_surf, BIRD_YELLOW,
                           (offset_x, offset_y, BIRD_WIDTH, BIRD_HEIGHT))
        # Body highlight
        pygame.draw.ellipse(bird_surf, (255, 220, 50),
                           (offset_x + 3, offset_y + 2, BIRD_WIDTH - 10, BIRD_HEIGHT // 2))

        # Wing with animation
        wing_y_offset = -4 if wing_up else 2
        wing_rect = (offset_x + 5, offset_y + BIRD_HEIGHT // 2 + wing_y_offset, 14, 10)
        pygame.draw.ellipse(bird_surf, BIRD_ORANGE, wing_rect)
        # Wing highlight
        pygame.draw.ellipse(bird_surf, BIRD_RED,
                           (offset_x + 7, offset_y + BIRD_HEIGHT // 2 + wing_y_offset + 2, 8, 5))

        # Eye white
        eye_x = offset_x + BIRD_WIDTH - 10
        eye_y = offset_y + 8
        pygame.draw.circle(bird_surf, WHITE, (eye_x, eye_y), 6)
        # Eye pupil
        pygame.draw.circle(bird_surf, BLACK, (eye_x + 2, eye_y), 3)
        # Eye highlight
        pygame.draw.circle(bird_surf, WHITE, (eye_x + 3, eye_y - 1), 1)

        # Beak (two-tone)
        beak_x = offset_x + BIRD_WIDTH - 2
        beak_y = offset_y + BIRD_HEIGHT // 2
        # Top beak
        beak_top = [
            (beak_x, beak_y - 3),
            (beak_x + 10, beak_y),
            (beak_x, beak_y)
        ]
        pygame.draw.polygon(bird_surf, BIRD_ORANGE, beak_top)
        # Bottom beak
        beak_bottom = [
            (beak_x, beak_y),
            (beak_x + 10, beak_y),
            (beak_x, beak_y + 3)
        ]
        pygame.draw.polygon(bird_surf, BIRD_RED, beak_bottom)

        # Rotate
        rotated = pygame.transform.rotate(bird_surf, -rotation)
        rect = rotated.get_rect(center=(x, y))
        self.screen.blit(rotated, rect)

    def _draw_pipe(self, pipe) -> None:
        """Draw a pipe pair (top and bottom)."""
        x = int(pipe.x)
        top_height = int(pipe.top_height)
        bottom_y = int(pipe.bottom_y)
        cap_height = 20  # Height of the pipe cap

        # Top pipe body
        if top_height > cap_height:
            pygame.draw.rect(self.screen, PIPE_GREEN,
                           (x, 0, PIPE_WIDTH, top_height - cap_height))

        # Top pipe cap (wider)
        cap_width = PIPE_WIDTH + 6
        cap_x = x - 3
        pygame.draw.rect(self.screen, PIPE_GREEN,
                        (cap_x, top_height - cap_height, cap_width, cap_height))
        # Cap highlight
        pygame.draw.rect(self.screen, PIPE_GREEN_LIGHT,
                        (cap_x + 2, top_height - cap_height + 2, 4, cap_height - 4))
        # Cap shadow
        pygame.draw.rect(self.screen, PIPE_GREEN_DARK,
                        (cap_x + cap_width - 6, top_height - cap_height + 2, 4, cap_height - 4))

        # Bottom pipe body
        bottom_height = GROUND_Y - bottom_y
        if bottom_height > cap_height:
            pygame.draw.rect(self.screen, PIPE_GREEN,
                           (x, bottom_y + cap_height, PIPE_WIDTH, bottom_height - cap_height))

        # Bottom pipe cap
        pygame.draw.rect(self.screen, PIPE_GREEN,
                        (cap_x, bottom_y, cap_width, cap_height))
        # Cap highlight
        pygame.draw.rect(self.screen, PIPE_GREEN_LIGHT,
                        (cap_x + 2, bottom_y + 2, 4, cap_height - 4))
        # Cap shadow
        pygame.draw.rect(self.screen, PIPE_GREEN_DARK,
                        (cap_x + cap_width - 6, bottom_y + 2, 4, cap_height - 4))

    def tick(self) -> None:
        """Maintain frame rate."""
        self.clock.tick(FPS)

    def quit(self) -> None:
        """Clean up pygame."""
        pygame.quit()


def get_input() -> dict:
    """Get current input state.

    Returns dict with:
        - quit: True if should exit
        - jump: True if jump pressed this frame
        - restart: True if restart pressed
    """
    result = {'quit': False, 'jump': False, 'restart': False}

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            result['quit'] = True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                result['quit'] = True
            elif event.key == pygame.K_SPACE:
                result['jump'] = True
            elif event.key == pygame.K_r:
                result['restart'] = True

    return result
