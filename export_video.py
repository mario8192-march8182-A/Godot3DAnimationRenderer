"""
export_video.py
----------------
Renders the 3D scene in this Godot project headlessly using Godot's
built-in Movie Maker mode (deterministic, frame-exact capture -- not a
screen recording), then encodes the resulting video into an .mp4 with
ffmpeg, since Godot's movie writer itself only produces an uncompressed
.avi or a PNG sequence, not .mp4 directly.

Usage:
    python export_video.py
    python export_video.py --duration 12 --fps 60 --resolution 1920x1080
    python export_video.py --color 0.1,0.6,0.9 --output out/clip.mp4
    python export_video.py --godot /path/to/godot --ffmpeg /path/to/ffmpeg

Requirements:
    - Godot 4.x, with the executable named "godot" (or "godot4") on
      PATH, or passed explicitly via --godot.
    - ffmpeg on PATH, or passed explicitly via --ffmpeg.

Linux headless servers without a GPU: if Godot fails to start under
--headless with a rendering-driver error, try running this script
under Xvfb instead:
    xvfb-run --auto-servernum python export_video.py
"""

import argparse
import math
import os
import shutil
import subprocess
import sys
import tempfile

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def find_executable(name, explicit):
    if explicit:
        return explicit
    return shutil.which(name)


def main():
    parser = argparse.ArgumentParser(description="Render this Godot 3D scene to an .mp4")
    parser.add_argument("--duration", type=float, default=8.0, help="Clip length in seconds (default: 8)")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second (default: 30)")
    parser.add_argument("--resolution", default="1280x720", help="WxH, e.g. 1920x1080 (default: 1280x720)")
    parser.add_argument("--color", default=None,
                         help="Subject color as R,G,B floats 0-1, e.g. 0.1,0.6,0.9")
    parser.add_argument("--godot", default=None,
                         help="Path to the Godot executable (defaults to 'godot'/'godot4' on PATH)")
    parser.add_argument("--ffmpeg", default=None,
                         help="Path to ffmpeg (defaults to 'ffmpeg' on PATH)")
    parser.add_argument("--output", default=os.path.join(PROJECT_DIR, "output", "animation.mp4"),
                         help="Final .mp4 path")
    parser.add_argument("--keep-avi", action="store_true",
                         help="Also keep the intermediate .avi Godot produces, next to --output")
    args = parser.parse_args()

    godot_bin = find_executable("godot", args.godot) or find_executable("godot4", None)
    if not godot_bin:
        print("ERROR: Godot executable not found. Install Godot 4.x and make sure "
              "'godot' (or 'godot4') is on PATH, or pass --godot /path/to/godot.")
        sys.exit(1)

    ffmpeg_bin = find_executable("ffmpeg", args.ffmpeg)
    if not ffmpeg_bin:
        print("ERROR: ffmpeg not found. Install ffmpeg and make sure it's on PATH, "
              "or pass --ffmpeg /path/to/ffmpeg.")
        sys.exit(1)

    if "x" not in args.resolution.lower():
        print(f"ERROR: --resolution must look like WIDTHxHEIGHT, got '{args.resolution}'.")
        sys.exit(1)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    user_args = [f"--duration={args.duration}"]
    if args.color:
        user_args.append(f"--color={args.color}")

    # Safety net: even though Main.gd quits itself after duration_seconds,
    # --quit-after forces the process to stop after an exact iteration
    # count in case the scene script ever fails to self-terminate.
    frame_count_estimate = max(1, math.ceil(args.duration * args.fps) + args.fps)  # +1s margin

    with tempfile.TemporaryDirectory() as tmp:
        avi_path = os.path.join(tmp, "movie.avi")

        cmd = [
            godot_bin,
            "--headless",
            "--path", PROJECT_DIR,
            "--resolution", args.resolution,
            "--write-movie", avi_path,
            "--fixed-fps", str(args.fps),
            "--quit-after", str(frame_count_estimate),
            "--",
        ] + user_args

        print("[export_video] Rendering frames with Godot (Movie Maker mode):")
        print("  " + " ".join(cmd))
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"[export_video] Godot exited with code {result.returncode}. "
                  "See its output above for details.")
            sys.exit(result.returncode)

        if not os.path.isfile(avi_path):
            print("[export_video] ERROR: Godot did not produce the expected .avi file. "
                  "Check the Godot output above for errors (e.g. a rendering-driver issue "
                  "on a headless/no-GPU server -- try running this script under xvfb-run).")
            sys.exit(1)

        if args.keep_avi:
            kept_path = os.path.join(os.path.dirname(args.output) or ".", "movie.avi")
            shutil.copy2(avi_path, kept_path)
            print(f"[export_video] Kept intermediate file at {kept_path}")

        print("[export_video] Encoding to .mp4 with ffmpeg ...")
        ffmpeg_cmd = [
            ffmpeg_bin, "-y",
            "-i", avi_path,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-r", str(args.fps),
            args.output,
        ]
        print("  " + " ".join(ffmpeg_cmd))
        result = subprocess.run(ffmpeg_cmd)
        if result.returncode != 0:
            print(f"[export_video] ffmpeg exited with code {result.returncode}.")
            sys.exit(result.returncode)

    print(f"[export_video] Done. Wrote {args.output}")


if __name__ == "__main__":
    main()
