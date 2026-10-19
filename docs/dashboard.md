# Dashboard and Testing

The English dashboard opens without authentication. Its data comes from the FastAPI CRUD API and persists in MySQL. Documentation and Swagger links remain in the top navigation.

## Sidebar and appearance

Clicking a sidebar destination, including the current one or the HospitalSim brand, scrolls to the top. The connection box is anchored at the bottom of the desktop sidebar and includes the MySQL/FastAPI and no-login details. Below it, a non-clickable local profile shows **No login required** and the visible **Dark mode** switch.

The default theme follows the browser/operating system, including changes while the page is open. Toggling Dark mode saves a manual preference in this browser; **Use browser theme** restores automatic behavior. Only this display preference uses local storage, not domain records. If storage is unavailable, the toggle still works for the current visit. The controls remain visible on smaller screens below navigation and are also available on the welcome header.

## First visit

On each page load, the dashboard checks `GET /initialization` and loads the domain collections. Until a startup choice is completed, the full-screen welcome page offers two choices side by side:

- **Start empty:** retain loaded domain records and confirm saving only the initialization flag. A clean database has no domain records.
- **Pre-populate:** immediately review the population writes against the loaded records, before any writes are sent.

Choosing Start empty or successfully completing Populate sends idempotent `POST /initialization`, storing `was_initialized=true` in MySQL. Refreshes and other browsers then open Overview directly, even if domain records are still empty. Canceling or failing initial population leaves the flag false. Resetting the database with `run.sh` clears it. Startup reads and illustrative SQL are visible in the loading/welcome screen and request log; a connection error is shown instead of browser fixtures.

## Manual CRUD

Use **Hospitals**, **Roles**, **Staff**, or **Patients** to create, list, read, update, and delete records. Create a hospital before staff/patients and roles before assigning them. Staff may have no roles; patients may be unassigned. Patient forms restrict clinician choices to the selected hospital and clear that choice when the hospital changes.

1. Select **Create record** or **Edit**. The form shows a live HTTP/JSON and SQL preview.
2. Select **Review request**, inspect the payload, and confirm **Send request**.
3. The server validates and saves the record. All four collections reload from the API.
4. **Read** previews a GET for one item; its response JSON appears in the request log.
5. **Delete** has a separate confirmation. Referenced records may return 409 and remain unchanged.

Hospital and search filters work on loaded records and make no network requests. **Refresh records** previews and reloads all four collections. Use it after changes made through Swagger or another client. Metrics show patient count, assigned/unassigned patients, staff count, and hospital count. Care bars show each clinician's share of the loaded patient registry; they do not represent beds or capacity.

## SQL and request visibility

**Every SQL preview is a demo example only. The browser sends HTTP requests with JSON, never SQL.** The API uses parameterized SQLModel queries. Previews illustrate likely reads, validation checks, writes, and relationship changes; they do not promise exact SQL text, ORM ordering, or success. Enable `SQL_ECHO=true` to inspect actual SQL in API logs.

Previews show the HTTP method, endpoint, JSON body, and likely SQL. Named ID placeholders such as `$riverside` in JSON and `:riverside_id` in SQL refer to IDs returned by earlier requests. Numeric IDs are resolved before the request is sent. The request log keeps the latest 100 requests in memory and displays the latest 30, including errors and SQL examples. Refreshing the page clears this log, not the database.

## Populate

The **Testing** tab has **Populate** and **Test** buttons. Populate restores the fixed baseline:

| Entity | Baseline |
| --- | --- |
| Hospitals | `[Demo] Riverside Medical Center` in `[Demo] Boston, Massachusetts`; `[Demo] Lakeside Clinic` in `[Demo] Cambridge, Massachusetts` |
| Roles | `[Demo] Physician`, `[Demo] Nurse`, `[Demo] Shift coordinator` |
| Staff | Olivia Chen / physician / Riverside; Noah Patel / nurse / Riverside; Mia Brooks / physician / Lakeside |
| Patients | Alex Taylor / Olivia / Riverside; Sam Rivera / Noah / Riverside; Jamie Morgan / unassigned / Riverside; Casey Lee / Mia / Lakeside |

Names, birth dates, role descriptions, and assignments are defined in `web/src/demo.ts`. Population deletes patients first, then staff inside the two reserved demo hospitals, restores or creates those hospitals and the three reserved roles, then creates staff and patients. Other hospitals and their records remain intact. Existing demo hospitals and roles keep their IDs; recreated patients and staff receive new MySQL IDs. Reserved role definitions are restored even if assigned elsewhere.

The main confirmation expands the planned database writes, including INSERT values and staff-role links, rather than leading with GETs. Supporting preflight and final collection reads have their own collapsed section. SQL remains illustrative and is never sent by the browser. The confirmation lists every deletion and creation. Do not keep irreplaceable manual records in the reserved demo hospitals. Initial reads detect changes since the preview; if anything changed, no writes are sent and an updated preview opens for another confirmation. Final reads verify the exact baseline. Repeating Populate yields the same demo values and relationships, with potentially different generated IDs.

## Test prerequisites and preview

Test requires an exact match to the baseline, including staff roles, patient assignments, hospital locations, and no extra patients or staff in the demo hospitals. If it is missing or modified, a popup explains the prerequisite and offers **Review Populate**. After population succeeds, the test preview opens for a separate confirmation.

Before running, review:

1. The plain-English story and expected final state.
2. The ordered HTTP requests and payloads.
3. The illustrative SQL reads and writes, including join-table changes.

The plan includes initial collection reads and final verification reads. The database is checked again before starting. Population is required again after a completed or partially completed test.

## Predetermined operations

| Time | HTTP operation | Database effect |
| --- | --- | --- |
| 08:00 | POST `/patients` | Create Avery Stone at Riverside, assigned to Olivia |
| 09:00 | PATCH Jamie | Set `staff_id` to Noah |
| 10:00 | PATCH Casey | Set `hospital_id` to Riverside and `staff_id` to Olivia together |
| 11:00 | DELETE Sam | Remove the current patient record, representing discharge |
| 12:00 | POST `/patients` | Create Riley Quinn at Lakeside, assigned to Mia |
| 13:00 | PATCH Alex | Set `staff_id` to null |
| 14:00 | PATCH Mia | Replace `role_ids` with physician and coordinator IDs |
| 15:00 | PATCH Riverside | Set location to `[Demo] Boston, North campus` |

The final demo state has two hospitals, three roles, three staff, and five patients. Riverside has Alex (unassigned), Jamie (Noah), Casey (Olivia), and Avery (Olivia). Lakeside has Riley (Mia). Sam's record is absent. Unrelated records are excluded from these totals and preserved.

## Running controls

Confirming the test opens **Overview** with a top control bar. At 1×, a new request is scheduled three seconds after the previous step completes; 2× and 4× reduce that wait. Requests never overlap. **Next hour** pauses automatic playback and executes the next operation. **Pause after request** lets an in-flight request complete. **Resume** continues from the next step. **End session** stops future steps and returns to Testing; it does not undo committed operations.

Manual writes and refresh are disabled during an active test session, including while paused. Hospital filters and navigation remain available. On failure the test stops and preserves the log and committed data. No request is automatically retried: a timed-out write might already have committed. Refresh, inspect, and Populate before rerunning. Other clients should avoid changing demo records during execution; the sequence is not one database transaction.

The timer and cursor are page-session state. Closing or reloading the page stops scheduling further requests, while MySQL retains completed changes. There is no offline catch-up or browser-local data fallback.
