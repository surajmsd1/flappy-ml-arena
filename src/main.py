#!/usr/bin/env python3
"""
Flappy Bird - Main Game Loop

Features:
- Bird falls with gravity
- Press SPACE to jump
- Press R to restart after game over
- Press ESC to quit
- Automatically records gameplay to recordings/ folder
- Optional sound effects with --sound flag
"""

import argparse
import os
import sys
from datetime import datetime
from game import create_game, step
from renderer import Renderer, get_input
from recording import Recording, save_recording
import sound


RECORDINGS_DIR = "recordings"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Flappy Bird with ML training data recording")
    parser.add_argument('--sound', action='store_true', help='Enable sound effects')
    return parser.parse_args()


def main():
    """Run the game with recording."""
    args = parse_args()

    # Create recordings directory if needed
    os.makedirs(RECORDINGS_DIR, exist_ok=True)

    # Initialize sound if requested
    if args.sound:
        if sound.init_sound(enabled=True):
            print("Sound enabled")
        else:
            print("Sound initialization failed, continuing without sound")

    renderer = Renderer()
    sound.register_render()  # Track active render
    state = create_game()
    recording = Recording(seed=state.rng_seed)
    prev_score = 0

    print("Flappy Bird")
    print("Controls:")
    print("  SPACE - Jump")
    print("  R     - Restart")
    print("  ESC   - Quit")
    print()
    print("Recording gameplay...")

    running = True
    while running:
        # Get input
        inputs = get_input()

        if inputs['quit']:
            running = False
            continue

        if inputs['restart']:
            # Save current recording before restart
            if recording.total_frames > 0:
                save_current_recording(recording)

            # Start fresh
            state = create_game()
            recording = Recording(seed=state.rng_seed)
            prev_score = 0
            continue

        # Record input before step
        jump = inputs['jump']
        was_alive = state.alive

        # Play flap sound on jump
        if jump and state.alive:
            sound.play_flap()

        # Update game
        step(state, jump=jump)

        # Check for score increase
        if state.score > prev_score:
            sound.play_score()
            prev_score = state.score

        # Check for death
        if was_alive and not state.alive:
            sound.play_death()

        # Record state after step
        recording.add_frame(state.frame, jump, state)

        # Render
        renderer.draw(state)
        renderer.tick()

    # Save final recording
    if recording.total_frames > 0:
        filepath = save_current_recording(recording)
        print(f"Recording saved: {filepath}")

    # Cleanup
    sound.unregister_render()
    sound.shutdown()
    renderer.quit()
    print(f"Final score: {state.score}")
    print(f"Total frames: {state.frame}")
    return 0


def save_current_recording(recording: Recording) -> str:
    """Save recording with timestamp filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"game_{timestamp}_score{recording.final_score}.json"
    filepath = os.path.join(RECORDINGS_DIR, filename)
    save_recording(recording, filepath)
    return filepath


if __name__ == "__main__":
    sys.exit(main())
