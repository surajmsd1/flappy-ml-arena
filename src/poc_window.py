#!/usr/bin/env python3
"""
Proof of Concept: Pygame Window
Task 1 deliverable - verifies pygame works correctly.

Run with: python3 src/poc_window.py
Expected: Window opens, shows sky blue background, closes cleanly.
"""

import sys

try:
    import pygame
except ImportError:
    print("ERROR: pygame not installed.")
    print("Install with: pip install pygame")
    sys.exit(1)

# Game constants (from research)
SCREEN_WIDTH = 288
SCREEN_HEIGHT = 512
FPS = 30

# Colors
SKY_BLUE = (135, 206, 235)
WHITE = (255, 255, 255)


def main():
    """Open a window, display background, close cleanly."""
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Flappy Bird - POC")
    clock = pygame.time.Clock()

    font = pygame.font.Font(None, 36)

    running = True
    frame_count = 0

    print(f"Window opened: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print("Press ESC or close window to exit")

    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Draw
        screen.fill(SKY_BLUE)

        # Show frame count
        text = font.render(f"Frame: {frame_count}", True, WHITE)
        screen.blit(text, (10, 10))

        # Show instructions
        instructions = font.render("ESC to exit", True, WHITE)
        screen.blit(instructions, (10, SCREEN_HEIGHT - 40))

        pygame.display.flip()
        clock.tick(FPS)
        frame_count += 1

    pygame.quit()
    print(f"Window closed cleanly after {frame_count} frames")
    return 0


if __name__ == "__main__":
    sys.exit(main())
