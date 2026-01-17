"""
Pygame Renderer for Flappy Bird

Handles all visualization - completely separate from game logic.
"""

import pygame
import math
from game import (
    GameState, SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BIRD_WIDTH, BIRD_HEIGHT, GROUND_Y, PIPE_WIDTH, PIPE_GAP
)


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


class Renderer:
    """Pygame-based renderer for the game."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Bird")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)

    def draw(self, state: GameState) -> None:
        """Draw the current game state."""
        # Sky background
        self.screen.fill(SKY_BLUE)

        # Pipes (draw before ground so ground covers pipe bottoms)
        for pipe in state.pipes:
            self._draw_pipe(pipe)

        # Ground
        pygame.draw.rect(self.screen, GROUND_GREEN,
                        (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))
        pygame.draw.rect(self.screen, GROUND_DARK,
                        (0, GROUND_Y, SCREEN_WIDTH, 5))

        # Bird
        self._draw_bird(state.bird.x, state.bird.y, state.bird.rotation)

        # Score
        score_text = self.font.render(str(state.score), True, WHITE)
        score_rect = score_text.get_rect(centerx=SCREEN_WIDTH // 2, top=50)
        # Shadow
        shadow = self.font.render(str(state.score), True, BLACK)
        self.screen.blit(shadow, (score_rect.x + 2, score_rect.y + 2))
        self.screen.blit(score_text, score_rect)

        # Instructions if not started
        if not state.started:
            instr = self.small_font.render("Press SPACE to start", True, WHITE)
            instr_rect = instr.get_rect(centerx=SCREEN_WIDTH // 2,
                                        centery=SCREEN_HEIGHT // 2 + 50)
            self.screen.blit(instr, instr_rect)

        # Game over message
        if not state.alive:
            go_text = self.font.render("GAME OVER", True, WHITE)
            go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            # Shadow
            go_shadow = self.font.render("GAME OVER", True, BLACK)
            self.screen.blit(go_shadow, (go_rect.x + 2, go_rect.y + 2))
            self.screen.blit(go_text, go_rect)

            restart = self.small_font.render("Press R to restart", True, WHITE)
            restart_rect = restart.get_rect(centerx=SCREEN_WIDTH // 2,
                                           centery=SCREEN_HEIGHT // 2 + 40)
            self.screen.blit(restart, restart_rect)

        # Debug info
        debug_y = self.small_font.render(
            f"y:{state.bird.y:.0f} v:{state.bird.velocity:.1f} r:{state.bird.rotation:.0f}",
            True, BLACK
        )
        self.screen.blit(debug_y, (5, 5))

        pygame.display.flip()

    def _draw_bird(self, x: float, y: float, rotation: float) -> None:
        """Draw the bird at given position with rotation."""
        # Create bird surface
        bird_surf = pygame.Surface((BIRD_WIDTH, BIRD_HEIGHT), pygame.SRCALPHA)

        # Body (ellipse)
        pygame.draw.ellipse(bird_surf, BIRD_YELLOW,
                           (0, 0, BIRD_WIDTH, BIRD_HEIGHT))

        # Wing
        wing_rect = (5, BIRD_HEIGHT // 2 - 3, 12, 8)
        pygame.draw.ellipse(bird_surf, BIRD_ORANGE, wing_rect)

        # Eye
        pygame.draw.circle(bird_surf, WHITE, (BIRD_WIDTH - 10, 8), 5)
        pygame.draw.circle(bird_surf, BLACK, (BIRD_WIDTH - 8, 8), 2)

        # Beak
        beak_points = [
            (BIRD_WIDTH - 2, BIRD_HEIGHT // 2 - 2),
            (BIRD_WIDTH + 6, BIRD_HEIGHT // 2),
            (BIRD_WIDTH - 2, BIRD_HEIGHT // 2 + 2)
        ]
        pygame.draw.polygon(bird_surf, BIRD_ORANGE, beak_points)

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
