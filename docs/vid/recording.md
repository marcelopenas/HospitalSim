# Recording and rebuilding

Record the real dashboard against a fresh, empty local FastAPI/MySQL stack. The script uses the browser UI, never a mock backend or fabricated screenshots. It checks for existing domain records before confirming startup and refuses to continue if records are present. Initialization must also be incomplete for the welcome choices to appear.

!!! warning "The recording modifies the database"
    The script creates and edits walkthrough records, demonstrates protected deletion, deletes temporary records in dependency order, populates the demo, and runs the predefined test. It leaves the final test state in MySQL. Use a disposable local instance. `bash run.sh -d` deliberately deletes all project Compose volumes and data before starting a clean instance.

Install FFmpeg on your PATH. From the repository root, with the full stack running:

```bash
uv run --with playwright --with pillow python -m playwright install chromium
uv run --with playwright --with pillow python docs/vid/capture.py --url http://localhost:3000
```

Add `--headed` to watch the browser. For Vite, use `--url http://localhost:5173` with the API running on port 8080. Capture tools are optional; they are not application dependencies.

## Outputs

Successful capture and rendering publish:

- `docs/vid/screens/`: original UI screenshots, including each resource form and request preview.
- `docs/vid/clips/test-running.gif`: real frames from the running test.
- `docs/vid/timeline.json`: complete chronological sequence with capture provenance, timestamps, file paths, captions, and chapter names.
- `docs/vid/walkthrough.mp4` and `walkthrough.gif`: complete overview.
- One MP4, GIF, and JSON timeline per chapter: startup, hospitals, roles, staff, patients, populate, testing, appearance, and navigation.
- `docs/assets/dashboard.png`: the current populated dashboard, embedded in both the README and docs home.
- The [Showcases](index.md) page with the new overview and individual videos.

Captures and rendering run in staging. A browser or rendering failure preserves the previously published media. Chapter videos collect each flow's recorded steps in their original relative order; the overview retains the entire chronological sequence. For example, resource deletion appears after dependent records are removed, even when creation happened earlier.

The single-instance recording previews and cancels welcome Pre-populate, completes Start empty, and later confirms the same population workflow from Testing. It does not independently complete both mutually exclusive first-start choices. Recording the alternate first-start completion needs another fresh instance.

## Stitch existing captures

The renderer does not start the app or send API requests. It stitches the captured images and GIFs using their timestamps and captions:

```bash
uv run --with pillow python docs/vid/render.py --showcases
```

Without `--showcases`, it rebuilds only the overview. Use `--timeline path/to/timeline.json` for a different recording. Media paths must stay inside the timeline's directory. The first timestamp must be zero, subsequent timestamps must increase, and `duration` must be greater than the final timestamp. GIF frame delays are retained within each allotted interval.

SQL previews are demo examples only: the browser sends HTTP and JSON, never SQL. FastAPI validates the request and executes parameterized ORM queries. The examples illustrate likely database changes, not an exact execution log.
