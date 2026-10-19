# Showcases

## Current dashboard Overview

This 54-second tour uses the dashboard screenshot supplied with this version. Camera movement highlights the navigation, metrics, care assignments, Testing entry point, patient profiles, appearance controls, and documentation links. It does not record browser clicks, CRUD operations, or a running test.

<video controls preload="metadata" width="100%" poster="dashboard.png">
  <source src="walkthrough.mp4" type="video/mp4">
  Your browser can download the video using the link below.
</video>

[MP4 video](walkthrough.mp4) · [Animated GIF](walkthrough.gif) · [Timestamped JSON](timeline.json) · [Source screenshot](dashboard.png)

The timeline records each frame's timestamp, file path, caption, and camera crop. Its source metadata identifies the supplied screenshot and its SHA-256 digest. Rebuilding this tour sends no API requests.

## Live workflow recordings

The optional [recorder](recording.md) drives a fresh local instance through:

- Start empty and the welcome Pre-populate preview.
- Hospital, role, staff, and patient CRUD forms, individual reads, and JSON/SQL reviews.
- Search, hospital filtering, protected deletion, and dependent-record cleanup.
- Populate, Test prerequisites, the ordered test, playback controls, and verified final records.
- Automatic browser theme, manual dark/light overrides, refresh, and header links.

The recorder produces a complete overview plus separate chapter videos after a successful run. See the [Dashboard guide](../dashboard.md) for the full operating flow and field descriptions.
