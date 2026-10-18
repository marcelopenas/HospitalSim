# Dashboard walkthrough

This 30-second tour introduces the dashboard, simulation controls, metrics, department capacity, and documentation links.

<video controls preload="metadata" width="100%" poster="overview.png">
  <source src="walkthrough.mp4" type="video/mp4">
  Your browser can download the video using the link below.
</video>

[Download MP4](walkthrough.mp4) · [Animated GIF](walkthrough.gif) · [Timeline JSON](timeline.json) · [Original screenshot](overview.png)

![Captioned HospitalSim dashboard tour](walkthrough.gif)

## Media and timeline

All assets live in `docs/vid/`. The original is a genuine screenshot of the published dashboard. Detail images crop that capture, and the short GIFs zoom into those details. These camera movements do not represent changes to simulation state.

Each entry in `timeline.json` has a `timestamp` in seconds, a `file_path` relative to this folder, and a `caption`. An entry runs until the next timestamp; the final entry runs until `duration`. Animated GIFs play within their allotted interval. The source screenshot is also identified in the JSON.

## Rebuild the video

Install FFmpeg and make `ffmpeg` available on your PATH, then run from the repository root:

```bash
python -m pip install Pillow
python docs/vid/render.py
```

The renderer reads the JSON, stitches the referenced images and GIFs at their timestamps, adds captions, and writes `walkthrough.mp4` and `walkthrough.gif` in the same folder. It does not start or reset the application or database.

To change the sequence, edit the timestamps, captions, and file paths in the JSON and run the renderer again. The first timestamp must be zero and subsequent timestamps must increase strictly. Replace or add media files to include further captured views.
