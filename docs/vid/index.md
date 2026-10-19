# Showcases

This section is reserved for recordings of the current dashboard connected to FastAPI and MySQL. The earlier interface video has been removed from this page because it does not represent the current UI. Current recordings and a replacement dashboard screenshot have not yet been captured.

## Flows

| Showcase | What the recording covers |
| --- | --- |
| Startup | Both welcome options, the Pre-populate write preview and cancellation, Start empty confirmation, and the empty dashboard |
| Hospitals | Create name/location, review POST, edit location and review PATCH, read response JSON, protected deletion, and successful deletion after dependencies are removed |
| Roles | Create and edit names/descriptions, request previews, individual reads, and deletion after staff references are removed |
| Staff | Name fields, hospital selection, role checkboxes, create/edit/read previews and responses, and deletion after patient references are removed |
| Patients | Names, birth date, hospital and optional staff selection, create/edit/read previews and responses, search, and deletion |
| Populate | Concrete INSERT/UPDATE/DELETE and relationship writes, confirmation, and the verified persisted baseline |
| Testing | Missing-baseline popup, story and request/SQL review, run, pause, next hour, speed, resume, completion, final records, and end session |
| Appearance | Visible Dark mode switch, saved manual preference, browser-theme reset, and bottom connection/profile area |
| Navigation | Sidebar scroll-to-top, hospital filtering, refresh request preview, request log, and documentation/Swagger links |

The capture script generates a complete overview and separate MP4/GIF videos for these flows. Each video has a JSON timeline with timestamps, file paths, and captions. Once capture and rendering succeed, the generated videos replace this status page and the same dashboard screenshot is added to the README and documentation home.

The welcome Pre-populate preview is recorded without committing that choice. Population is then executed through Testing after the Start empty flow. A separate fresh instance is needed to independently record committing Pre-populate directly from the welcome page; that alternate startup completion is not covered by this single-instance recording.

[Recording and rebuilding](recording.md)
