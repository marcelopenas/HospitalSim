# Recording and rebuilding

## Rebuild the supplied screenshot tour

Install FFmpeg on your PATH, then run from the repository root:

```bash
uv run --with pillow python docs/vid/render.py
```

The renderer reads `timeline.json`, pans/zooms its source image at the specified timestamps, adds captions, and writes `walkthrough.mp4` and `walkthrough.gif`. Each `file_path` is relative to this folder. Optional `crop` and `zoom_to` boxes use `[x, y, width, height]` in source-image pixels. GIF inputs retain their frame delays. Rendering does not access the backend.

The first timestamp must be zero, later timestamps must increase, and `duration` must exceed the final timestamp. Crop boxes must stay within their source image. Use `--timeline path/to/timeline.json` for another recording.

## Record the live application

Start a fresh, uninitialized local FastAPI/MySQL instance. The recorder requires an empty database, operates the current UI, and does not use a mock API.

!!! warning "The recording writes to MySQL"
    It creates and edits walkthrough records, demonstrates protected deletion, removes temporary records, populates the baseline, and runs Test. It leaves the committed final state in the database. Use a disposable instance. `bash run.sh -d` deliberately deletes all project Compose volumes and data before starting.

Install FFmpeg and the optional capture tools:

```bash
uv run --with playwright --with pillow python -m playwright install chromium
uv run --with playwright --with pillow python docs/vid/capture.py --url http://localhost:3000
```

Add `--headed` to watch. For Vite, pass `--url http://localhost:5173` with the API running on port 8080. Capture tools are not application dependencies.

On success, the recorder replaces the Overview tour, its timeline, the showcase page, and `dashboard.png` with the live recording. The README and docs home already reference that image; publication does not rewrite those pages. Original captures go into `screens/`, and the running-test GIF goes into `clips/`. It also renders one MP4/GIF/JSON per chapter. Capture and rendering use staging so a failure preserves previously published media; confirmed database writes remain committed.

The single-instance flow previews/cancels welcome Pre-populate, completes Start empty, and later confirms population through Testing. Independently recording a committed welcome Pre-populate choice requires another fresh instance.

To rebuild all chapters of a live recording, run:

```bash
uv run --with pillow python docs/vid/render.py --showcases
```

SQL previews are illustrative. The browser sends HTTP and JSON, never SQL; FastAPI executes parameterized ORM queries.
