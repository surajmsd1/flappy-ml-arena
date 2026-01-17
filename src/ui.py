#!/usr/bin/env python3
"""
Recording Manager UI - Flask web app for managing Flappy Bird recordings.

Features:
- List all recordings with stats
- Filter by model type, generation, score
- Sort by various criteria
- Play recordings via viewer.py
- Delete recordings
- View analytics
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from flask import Flask, jsonify, render_template, request, send_from_directory

app = Flask(__name__)

RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")


def parse_recording_filename(filename: str) -> Dict:
    """Parse recording filename to extract metadata."""
    info = {
        "filename": filename,
        "model_type": "unknown",
        "generation": None,
        "replay_num": None,
        "score_from_name": None,
        "timestamp": None,
    }

    # genetic_gen0_replay1.json or genetic_gen100_replay8.json
    genetic_match = re.match(r"genetic_gen(\d+)_replay(\d+)\.json", filename)
    if genetic_match:
        info["model_type"] = "genetic"
        info["generation"] = int(genetic_match.group(1))
        info["replay_num"] = int(genetic_match.group(2))
        return info

    # neat_gen5_best1.json
    neat_match = re.match(r"neat_gen(\d+)_best(\d+)\.json", filename)
    if neat_match:
        info["model_type"] = "neat"
        info["generation"] = int(neat_match.group(1))
        info["replay_num"] = int(neat_match.group(2))
        return info

    # imitation_epoch10_replay1.json
    imitation_match = re.match(r"imitation_epoch(\d+)_replay(\d+)\.json", filename)
    if imitation_match:
        info["model_type"] = "imitation"
        info["generation"] = int(imitation_match.group(1))  # epoch as generation
        info["replay_num"] = int(imitation_match.group(2))
        return info

    # dqn_step1000_replay1.json
    dqn_match = re.match(r"dqn_step(\d+)_replay(\d+)\.json", filename)
    if dqn_match:
        info["model_type"] = "dqn"
        info["generation"] = int(dqn_match.group(1))  # step as generation
        info["replay_num"] = int(dqn_match.group(2))
        return info

    # game_20260117_095256_score9.json (human/manual play)
    game_match = re.match(r"game_(\d{8})_(\d{6})_score(\d+)\.json", filename)
    if game_match:
        info["model_type"] = "human"
        info["timestamp"] = f"{game_match.group(1)}_{game_match.group(2)}"
        info["score_from_name"] = int(game_match.group(3))
        return info

    return info


def get_recording_stats(filepath: str) -> Dict:
    """Get stats from a recording file."""
    stats = {
        "score": 0,
        "frames": 0,
        "duration_sec": 0,
        "jumps": 0,
        "file_size": 0,
        "format": "unknown",
    }

    try:
        stats["file_size"] = os.path.getsize(filepath)

        with open(filepath, "r") as f:
            data = json.load(f)

        # Check format
        if data.get("format") == "compact":
            stats["format"] = "compact"
            stats["frames"] = data.get("total_frames", len(data.get("inputs", [])))
            stats["score"] = data.get("final_score", 0)
            stats["jumps"] = sum(1 for inp in data.get("inputs", []) if inp)
        else:
            stats["format"] = "verbose"
            frames = data.get("frames", [])
            stats["frames"] = len(frames)
            if frames:
                last_frame = frames[-1]
                state = last_frame.get("state", {})
                stats["score"] = state.get("score", 0)
                stats["jumps"] = sum(1 for f in frames if f.get("jump", False))

        # Duration at 30 FPS
        stats["duration_sec"] = round(stats["frames"] / 30.0, 2)

    except Exception as e:
        stats["error"] = str(e)

    return stats


def get_all_recordings() -> List[Dict]:
    """Get all recordings with their metadata and stats."""
    recordings = []

    if not os.path.exists(RECORDINGS_DIR):
        return recordings

    for filename in os.listdir(RECORDINGS_DIR):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(RECORDINGS_DIR, filename)
        info = parse_recording_filename(filename)
        stats = get_recording_stats(filepath)

        recording = {
            **info,
            **stats,
            "filepath": filepath,
            "mtime": os.path.getmtime(filepath),
        }
        recordings.append(recording)

    return recordings


@app.route("/")
def index():
    """Main page."""
    return render_template("index.html")


@app.route("/api/recordings")
def api_recordings():
    """API endpoint to get all recordings."""
    recordings = get_all_recordings()

    # Apply filters
    model_type = request.args.get("model_type")
    if model_type and model_type != "all":
        recordings = [r for r in recordings if r["model_type"] == model_type]

    min_score = request.args.get("min_score", type=int)
    if min_score is not None:
        recordings = [r for r in recordings if r["score"] >= min_score]

    max_score = request.args.get("max_score", type=int)
    if max_score is not None:
        recordings = [r for r in recordings if r["score"] <= max_score]

    min_gen = request.args.get("min_gen", type=int)
    if min_gen is not None:
        recordings = [r for r in recordings if r["generation"] is not None and r["generation"] >= min_gen]

    max_gen = request.args.get("max_gen", type=int)
    if max_gen is not None:
        recordings = [r for r in recordings if r["generation"] is not None and r["generation"] <= max_gen]

    # Apply sorting
    sort_by = request.args.get("sort", "mtime")
    reverse = request.args.get("order", "desc") == "desc"

    if sort_by == "score":
        recordings.sort(key=lambda r: r["score"], reverse=reverse)
    elif sort_by == "frames":
        recordings.sort(key=lambda r: r["frames"], reverse=reverse)
    elif sort_by == "generation":
        recordings.sort(key=lambda r: (r["generation"] or 0), reverse=reverse)
    elif sort_by == "size":
        recordings.sort(key=lambda r: r["file_size"], reverse=reverse)
    elif sort_by == "name":
        recordings.sort(key=lambda r: r["filename"], reverse=reverse)
    else:  # mtime
        recordings.sort(key=lambda r: r["mtime"], reverse=reverse)

    return jsonify(recordings)


@app.route("/api/stats")
def api_stats():
    """API endpoint to get aggregate stats."""
    recordings = get_all_recordings()

    # Group by model type
    by_model = {}
    for r in recordings:
        model = r["model_type"]
        if model not in by_model:
            by_model[model] = []
        by_model[model].append(r)

    stats = {
        "total_recordings": len(recordings),
        "total_frames": sum(r["frames"] for r in recordings),
        "total_size_mb": round(sum(r["file_size"] for r in recordings) / 1024 / 1024, 2),
        "by_model": {},
    }

    for model, recs in by_model.items():
        scores = [r["score"] for r in recs]
        stats["by_model"][model] = {
            "count": len(recs),
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
        }

    return jsonify(stats)


@app.route("/api/delete", methods=["POST"])
def api_delete():
    """Delete a recording."""
    data = request.get_json()
    filename = data.get("filename")

    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    filepath = os.path.join(RECORDINGS_DIR, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    # Safety check - only delete .json files in recordings dir
    if not filepath.endswith(".json") or not os.path.abspath(filepath).startswith(
        os.path.abspath(RECORDINGS_DIR)
    ):
        return jsonify({"error": "Invalid file"}), 400

    try:
        os.remove(filepath)
        return jsonify({"success": True, "deleted": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/play", methods=["POST"])
def api_play():
    """Launch viewer.py to play recordings."""
    data = request.get_json()
    filenames = data.get("filenames", [])
    grid_size = data.get("grid", 2)

    if not filenames:
        return jsonify({"error": "No files selected"}), 400

    # Build command
    filepaths = [os.path.join(RECORDINGS_DIR, f) for f in filenames if f.endswith(".json")]

    # Validate files exist
    for fp in filepaths:
        if not os.path.exists(fp):
            return jsonify({"error": f"File not found: {fp}"}), 404

    viewer_path = os.path.join(os.path.dirname(__file__), "viewer.py")
    cmd = [sys.executable, viewer_path, f"--grid={grid_size}"] + filepaths

    try:
        # Launch viewer in background
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return jsonify({"success": True, "playing": len(filepaths), "grid": grid_size})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/learning_curve")
def api_learning_curve():
    """Get learning curve data for a model type."""
    model_type = request.args.get("model_type", "genetic")
    recordings = get_all_recordings()

    # Filter by model type
    filtered = [r for r in recordings if r["model_type"] == model_type and r["generation"] is not None]

    # Group by generation
    by_gen = {}
    for r in filtered:
        gen = r["generation"]
        if gen not in by_gen:
            by_gen[gen] = []
        by_gen[gen].append(r["score"])

    # Calculate stats per generation
    curve = []
    for gen in sorted(by_gen.keys()):
        scores = by_gen[gen]
        curve.append({
            "generation": gen,
            "avg_score": round(sum(scores) / len(scores), 2),
            "max_score": max(scores),
            "min_score": min(scores),
            "count": len(scores),
        })

    return jsonify(curve)


def main():
    """Run the Flask app."""
    print("=" * 60)
    print("Flappy Bird Recording Manager")
    print("=" * 60)
    print()
    print(f"Recordings directory: {RECORDINGS_DIR}")
    print()
    print("Opening browser at http://localhost:5000")
    print("Press Ctrl+C to stop")
    print()

    # Open browser
    import webbrowser
    webbrowser.open("http://localhost:5000")

    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
