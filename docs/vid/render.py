"""Stitch timeline images and GIFs into a captioned MP4 and GIF.

Requires Pillow (python -m pip install Pillow) and ffmpeg on PATH.
Run from any directory: python docs/vid/render.py
"""

import argparse
import json
import shutil
import subprocess
import textwrap
from itertools import pairwise
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, ImageFont, ImageOps


def render(timeline_path: Path, output: str = "walkthrough") -> None:
    root = timeline_path.resolve().parent
    timeline = json.loads(timeline_path.read_text())
    clips = timeline["frames"]
    end = timeline["duration"]
    if not clips or clips[0]["timestamp"] != 0:
        raise ValueError("The timeline must start at zero.")
    times = [clip["timestamp"] for clip in clips] + [end]
    if any(b <= a for a, b in pairwise(times)):
        raise ValueError("Timestamps and duration must increase strictly.")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("Install ffmpeg and make it available on PATH.")
    font_path = timeline.get("font")
    font = (
        ImageFont.truetype(str(root / font_path), 25)
        if font_path
        else ImageFont.load_default(size=25)
    )
    fps = timeline["fps"]
    width, height = timeline["size"]
    process = subprocess.Popen(
        [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{width}x{height}",
            "-r",
            str(fps),
            "-i",
            "pipe:0",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(root / f"{output}.mp4"),
        ],
        stdin=subprocess.PIPE,
    )
    assert process.stdin is not None
    try:
        for index, clip in enumerate(clips):
            source = (root / clip["file_path"]).resolve()
            if not source.is_relative_to(root):
                raise ValueError("Media paths must stay inside the vid folder.")
            with Image.open(source) as media:
                animation = []
                elapsed = 0
                for frame_index in range(getattr(media, "n_frames", 1)):
                    media.seek(frame_index)
                    elapsed += media.info.get("duration", 100)
                    animation.append((elapsed, media.convert("RGB").copy()))
                count = round(times[index + 1] * fps) - round(times[index] * fps)
                for step in range(count):
                    position = (step * 1000 / fps) % elapsed
                    image = next(
                        frame for until, frame in animation if position < until
                    )
                    canvas = Image.new("RGB", (width, height), "#102e36")
                    fitted = ImageOps.contain(image, (width, height - 100))
                    canvas.paste(
                        fitted,
                        (
                            (width - fitted.width) // 2,
                            (height - 100 - fitted.height) // 2,
                        ),
                    )
                    draw = ImageDraw.Draw(canvas)
                    caption = "\n".join(textwrap.wrap(clip["caption"], width=85))
                    draw.multiline_text(
                        (30, height - 80), caption, font=font, fill="white", spacing=8
                    )
                    process.stdin.write(canvas.tobytes())
    finally:
        process.stdin.close()
        returncode = process.wait()
    if returncode:
        raise RuntimeError(f"ffmpeg failed with exit code {returncode}.")
    # Two passes avoid buffering a complete, multi-minute recording in memory.
    with TemporaryDirectory(prefix="palette-") as temporary:
        palette = str(Path(temporary) / "palette.png")
        filters = "fps=6,scale=800:-1:flags=lanczos"
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(root / f"{output}.mp4"),
                "-vf",
                f"{filters},palettegen",
                "-frames:v",
                "1",
                palette,
            ],
            check=True,
        )
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(root / f"{output}.mp4"),
                "-i",
                palette,
                "-filter_complex",
                f"[0:v]{filters}[v];[v][1:v]paletteuse",
                "-loop",
                "0",
                str(root / f"{output}.gif"),
            ],
            check=True,
        )
    print(f"Created {output}.mp4 and {output}.gif from {timeline_path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timeline", type=Path, default=Path(__file__).with_name("timeline.json")
    )
    parser.add_argument(
        "--showcases", action="store_true", help="Also render each recorded chapter"
    )
    args = parser.parse_args()
    render(args.timeline)
    if not args.showcases:
        return
    timeline = json.loads(args.timeline.read_text())
    frames = timeline["frames"]
    chapters: dict[str, list[dict]] = {}
    durations: dict[str, float] = {}
    for index, frame in enumerate(frames):
        chapter = frame.get("chapter")
        if not chapter:
            raise ValueError("Every frame needs a chapter to build showcases.")
        # Chapter names are used as filenames; only allow simple local names.
        if not chapter.replace("-", "").isalnum() or not chapter.isascii():
            raise ValueError("Invalid chapter filename.")
        until = (
            frames[index + 1]["timestamp"]
            if index + 1 < len(frames)
            else timeline["duration"]
        )
        offset = durations.get(chapter, 0)
        chapters.setdefault(chapter, []).append(
            {**frame, "timestamp": round(offset, 2)}
        )
        durations[chapter] = offset + until - frame["timestamp"]
    for chapter, chapter_frames in chapters.items():
        path = args.timeline.parent / f"{chapter}.json"
        path.write_text(
            json.dumps(
                {
                    **timeline,
                    "title": f"HospitalSim: {chapter}",
                    "duration": round(durations[chapter], 2),
                    "frames": chapter_frames,
                },
                indent=2,
            )
            + "\n"
        )
        render(path, chapter)


if __name__ == "__main__":
    main()
