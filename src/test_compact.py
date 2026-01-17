#!/usr/bin/env python3
"""
Test script for compact recording format.

Verifies that:
1. Compact format saves correctly
2. Expansion produces identical results to original
"""

import os
import sys
import tempfile
from recording import (
    Recording, load_recording, save_recording,
    save_compact, load_compact, expand_recording,
    is_compact_format, load_any_recording
)
from game import create_game, step


def create_test_recording(seed: int = 42, num_frames: int = 100) -> Recording:
    """Create a test recording with random jumps."""
    import random
    rng = random.Random(seed)

    state = create_game(seed=seed)
    recording = Recording(seed=seed)

    for _ in range(num_frames):
        if not state.alive:
            break
        jump = rng.random() < 0.15  # 15% chance to jump
        step(state, jump=jump)
        recording.add_frame(state.frame, jump, state)

    return recording


def test_compact_save_load():
    """Test saving and loading compact format."""
    print("Test 1: Compact save/load")

    original = create_test_recording(seed=12345, num_frames=200)
    print(f"  Created recording: {original.total_frames} frames, score {original.final_score}")

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        compact_path = f.name

    try:
        # Save compact
        save_compact(original, compact_path)

        # Load compact
        compact = load_compact(compact_path)

        # Verify metadata
        assert compact.seed == original.seed, "Seed mismatch"
        assert compact.final_score == original.final_score, "Score mismatch"
        assert compact.total_frames == original.total_frames, "Frame count mismatch"
        assert len(compact.inputs) == len(original.frames), "Input count mismatch"

        print(f"  Compact format: seed={compact.seed}, {len(compact.inputs)} inputs")
        print("  PASSED")
        return True

    finally:
        os.unlink(compact_path)


def test_expand_recording():
    """Test expanding compact recording matches original."""
    print("\nTest 2: Expand recording")

    original = create_test_recording(seed=54321, num_frames=300)
    print(f"  Original: {original.total_frames} frames, score {original.final_score}")

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        compact_path = f.name

    try:
        # Save compact
        save_compact(original, compact_path)

        # Load and expand
        compact = load_compact(compact_path)
        expanded = expand_recording(compact)

        print(f"  Expanded: {expanded.total_frames} frames, score {expanded.final_score}")

        # Compare frame by frame
        mismatches = 0
        for i, (orig_frame, exp_frame) in enumerate(zip(original.frames, expanded.frames)):
            if orig_frame.state != exp_frame.state:
                mismatches += 1
                if mismatches <= 3:
                    print(f"  Frame {i} MISMATCH:")
                    print(f"    Original: bird_y={orig_frame.state['bird']['y']}")
                    print(f"    Expanded: bird_y={exp_frame.state['bird']['y']}")

        if mismatches > 0:
            print(f"  FAILED: {mismatches} mismatches")
            return False

        print(f"  Frame-by-frame comparison: {len(original.frames)} frames match")
        print("  PASSED")
        return True

    finally:
        os.unlink(compact_path)


def test_format_detection():
    """Test format detection works correctly."""
    print("\nTest 3: Format detection")

    recording = create_test_recording(seed=99999, num_frames=50)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        verbose_path = f.name
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        compact_path = f.name

    try:
        # Save both formats
        save_recording(recording, verbose_path)
        save_compact(recording, compact_path)

        # Check format detection
        is_verbose_compact = is_compact_format(verbose_path)
        is_compact_compact = is_compact_format(compact_path)

        assert not is_verbose_compact, "Verbose format detected as compact"
        assert is_compact_compact, "Compact format not detected"

        print(f"  Verbose file detected as compact: {is_verbose_compact}")
        print(f"  Compact file detected as compact: {is_compact_compact}")
        print("  PASSED")
        return True

    finally:
        os.unlink(verbose_path)
        os.unlink(compact_path)


def test_load_any_recording():
    """Test universal loader works for both formats."""
    print("\nTest 4: Universal loader")

    original = create_test_recording(seed=11111, num_frames=100)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        verbose_path = f.name
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        compact_path = f.name

    try:
        # Save both formats
        save_recording(original, verbose_path)
        save_compact(original, compact_path)

        # Load both with universal loader
        from_verbose = load_any_recording(verbose_path)
        from_compact = load_any_recording(compact_path)

        # Both should produce equivalent recordings
        assert from_verbose.seed == from_compact.seed, "Seed mismatch"
        assert from_verbose.final_score == from_compact.final_score, "Score mismatch"
        assert len(from_verbose.frames) == len(from_compact.frames), "Frame count mismatch"

        # Compare states
        for i, (v_frame, c_frame) in enumerate(zip(from_verbose.frames, from_compact.frames)):
            if v_frame.state != c_frame.state:
                print(f"  Frame {i} differs between verbose and compact loading")
                return False

        print(f"  Loaded from verbose: {len(from_verbose.frames)} frames")
        print(f"  Loaded from compact: {len(from_compact.frames)} frames")
        print("  Both produce identical results")
        print("  PASSED")
        return True

    finally:
        os.unlink(verbose_path)
        os.unlink(compact_path)


def test_file_size_comparison():
    """Compare file sizes of verbose vs compact format."""
    print("\nTest 5: File size comparison")

    recording = create_test_recording(seed=77777, num_frames=500)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        verbose_path = f.name
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        compact_path = f.name

    try:
        # Save both formats
        save_recording(recording, verbose_path)
        save_compact(recording, compact_path)

        verbose_size = os.path.getsize(verbose_path)
        compact_size = os.path.getsize(compact_path)
        ratio = verbose_size / compact_size if compact_size > 0 else 0

        print(f"  Verbose format: {verbose_size:,} bytes")
        print(f"  Compact format: {compact_size:,} bytes")
        print(f"  Compression ratio: {ratio:.1f}x smaller")
        print("  PASSED")
        return True

    finally:
        os.unlink(verbose_path)
        os.unlink(compact_path)


def main():
    """Run all tests."""
    print("=" * 60)
    print("Compact Recording Format Tests")
    print("=" * 60)

    tests = [
        test_compact_save_load,
        test_expand_recording,
        test_format_detection,
        test_load_any_recording,
        test_file_size_comparison,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
