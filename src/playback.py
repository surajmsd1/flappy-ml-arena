#!/usr/bin/env python3
"""
Playback System for Flappy Bird

Replays recorded game sessions with visual rendering.
"""

import sys
import os
from game import GameState, create_game, step
from renderer import Renderer, get_input
from recording import load_recording, Recording


def playback_from_states(recording: Recording):
    """Playback by rendering saved states directly."""
    renderer = Renderer()

    print(f"Playing recording: {recording.total_frames} frames, score {recording.final_score}")
    print("Controls: SPACE=pause/resume, ESC=quit")

    frame_idx = 0
    paused = False
    running = True

    while running and frame_idx < len(recording.frames):
        inputs = get_input()

        if inputs['quit']:
            running = False
            continue

        if inputs['jump']:
            paused = not paused
            print("PAUSED" if paused else "RESUMED")

        if not paused:
            # Get state from recording
            frame_record = recording.frames[frame_idx]
            state = GameState.from_dict(frame_record.state)

            # Render
            renderer.draw(state)
            frame_idx += 1

        renderer.tick()

    renderer.quit()
    print(f"Playback complete: {frame_idx} frames")


def playback_deterministic(recording: Recording):
    """Playback by re-simulating with recorded inputs (verifies determinism)."""
    renderer = Renderer()

    # Create fresh game with same seed
    state = create_game(seed=recording.seed)

    print(f"Re-simulating recording: seed={recording.seed}, {recording.total_frames} frames")
    print("Controls: SPACE=pause/resume, ESC=quit")

    frame_idx = 0
    paused = False
    running = True
    mismatches = 0

    while running and frame_idx < len(recording.frames):
        inputs = get_input()

        if inputs['quit']:
            running = False
            continue

        if inputs['jump']:
            paused = not paused
            print("PAUSED" if paused else "RESUMED")

        if not paused:
            # Get recorded input for this frame
            frame_record = recording.frames[frame_idx]
            jump = frame_record.jump

            # Step the simulation
            step(state, jump=jump)

            # Verify against recorded state (check key values)
            recorded_state = frame_record.state
            if (state.bird.y != recorded_state['bird']['y'] or
                state.score != recorded_state['score']):
                mismatches += 1
                if mismatches <= 5:
                    print(f"Frame {frame_idx}: MISMATCH!")
                    print(f"  Simulated: y={state.bird.y}, score={state.score}")
                    print(f"  Recorded:  y={recorded_state['bird']['y']}, score={recorded_state['score']}")

            # Render current simulated state
            renderer.draw(state)
            frame_idx += 1

        renderer.tick()

    renderer.quit()
    print(f"\nPlayback complete: {frame_idx} frames")
    print(f"Mismatches: {mismatches}")
    if mismatches == 0:
        print("DETERMINISM VERIFIED!")


def main():
    """Main entry point for playback."""
    if len(sys.argv) < 2:
        # Find most recent recording
        recordings_dir = "recordings"
        if os.path.exists(recordings_dir):
            files = sorted(os.listdir(recordings_dir), reverse=True)
            json_files = [f for f in files if f.endswith('.json')]
            if json_files:
                filepath = os.path.join(recordings_dir, json_files[0])
                print(f"Using most recent recording: {filepath}")
            else:
                print("No recordings found. Play a game first!")
                return 1
        else:
            print("Usage: python playback.py <recording.json>")
            print("   or: python playback.py  (plays most recent recording)")
            return 1
    else:
        filepath = sys.argv[1]

    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return 1

    recording = load_recording(filepath)
    print(f"Loaded: {filepath}")
    print(f"  Seed: {recording.seed}")
    print(f"  Frames: {recording.total_frames}")
    print(f"  Final score: {recording.final_score}")
    print()

    # Use deterministic playback to verify
    playback_deterministic(recording)
    return 0


if __name__ == "__main__":
    sys.exit(main())
