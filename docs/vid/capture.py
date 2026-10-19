"""Record the real local dashboard and rebuild the complete walkthrough.

Optional tools: python -m pip install playwright Pillow
Then: python -m playwright install chromium
Run against a fresh, running local stack: python docs/vid/capture.py
No mock API or fabricated screenshots are used. Existing records are not cleared.
"""

import argparse
import asyncio
import importlib
import json
import shutil
import sys
import time
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from PIL import Image


class Recorder:
    def __init__(self, page: Any, root: Path) -> None:
        self.page = page
        self.root = root
        self.frames: list[dict[str, Any]] = []
        self.timestamp = 0.0
        self.chapter = "startup"

    async def shot(self, name: str, caption: str, duration: float = 5) -> None:
        path = f"screens/{len(self.frames) + 1:02d}-{name}.png"
        await self.page.screenshot(path=str(self.root / path), animations="disabled")
        self.add(path, caption, duration)

    def add(self, path: str, caption: str, duration: float) -> None:
        self.frames.append(
            {
                "timestamp": round(self.timestamp, 2),
                "file_path": path,
                "caption": caption,
                "chapter": self.chapter,
            }
        )
        self.timestamp += duration

    async def nav(self, name: str) -> None:
        await (
            self.page.get_by_role("navigation", name="Main navigation")
            .get_by_role("button", name=name, exact=True)
            .click()
        )
        await self.page.get_by_role("heading", level=1).wait_for()
        if await self.page.evaluate("window.scrollY") != 0:
            raise RuntimeError("Sidebar navigation did not scroll to the top.")

    async def idle(self) -> None:
        # The UI sends sequential writes/reads; wait for the network and busy state.
        await self.page.wait_for_load_state("networkidle", timeout=60000)
        await (
            self.page.get_by_role("status")
            .filter(has_text="Waiting for the API")
            .wait_for(state="hidden", timeout=60000)
        )
        failure = self.page.get_by_role("alert")
        if await failure.count():
            raise RuntimeError(await failure.first.inner_text())

    async def expand(self, index: int = 0) -> None:
        detail = (
            self.page.get_by_role("dialog")
            .locator(".request-previews > details")
            .nth(index)
        )
        if await detail.get_attribute("open") is None:
            await detail.locator("summary").click()
        await detail.scroll_into_view_if_needed()

    async def edit(self, resource: str, values: dict[str, str], caption: str) -> None:
        self.chapter = resource.lower()
        await self.nav(resource)
        await (
            self.page.locator("tbody tr")
            .first.get_by_role("button", name="Edit", exact=True)
            .click()
        )
        dialog = self.page.get_by_role("dialog")
        for field, value in values.items():
            await dialog.get_by_label(field, exact=True).fill(value)
        await dialog.locator(".modal-heading").scroll_into_view_if_needed()
        await self.shot(f"edit-{resource.lower()}", caption)
        await dialog.get_by_role("button", name="Review request", exact=True).click()
        await self.expand()
        await self.shot(
            f"patch-{resource.lower()}",
            "Review the changed fields, JSON PATCH payload, and illustrative SQL before saving.",
        )
        await (
            self.page.get_by_role("dialog")
            .get_by_role("button", name="Send request", exact=True)
            .click()
        )
        await self.idle()
        await self.shot(
            f"saved-{resource.lower()}",
            "The saved values are returned by the API and displayed in the directory.",
        )
        await self.read(resource)

    async def read(self, resource: str) -> None:
        await (
            self.page.locator("tbody tr")
            .first.get_by_role("button", name="Read", exact=True)
            .click()
        )
        await self.expand()
        await self.shot(
            f"get-{resource.lower()}",
            f"Read an individual {resource.lower()} record: review the GET and its SQL example.",
        )
        await (
            self.page.get_by_role("dialog")
            .get_by_role("button", name="Read record", exact=True)
            .click()
        )
        await self.idle()
        detail = self.page.locator(".request-log > details").first
        if await detail.get_attribute("open") is None:
            await detail.locator("summary").first.click()
        await detail.scroll_into_view_if_needed()
        await self.shot(
            f"response-{resource.lower()}",
            "Inspect the HTTP status and response JSON in the request log.",
        )

    async def create(
        self,
        resource: str,
        values: dict[str, str],
        caption: str,
        hospital: str | None = None,
        clinician: str | None = None,
        role: str | None = None,
    ) -> None:
        self.chapter = resource.lower()
        await self.nav(resource)
        await self.page.get_by_role(
            "button", name="+ Create record", exact=True
        ).click()
        dialog = self.page.get_by_role("dialog")
        for field, value in values.items():
            await dialog.get_by_label(field, exact=True).fill(value)
        if hospital:
            await dialog.get_by_label("Hospital", exact=True).select_option(
                label=hospital
            )
        if clinician:
            await dialog.get_by_label(
                "Assigned staff (optional)", exact=True
            ).select_option(label=clinician)
        if role:
            await dialog.get_by_role("checkbox", name=role, exact=True).check()
        await dialog.locator(".modal-heading").scroll_into_view_if_needed()
        await self.shot(f"create-{resource.lower()}", caption, 6)
        await dialog.get_by_role("button", name="Review request", exact=True).click()
        await self.expand()
        await self.shot(
            f"post-{resource.lower()}",
            "Review the JSON request and example SQL. The browser sends HTTP and JSON, never SQL.",
            5,
        )
        await (
            self.page.get_by_role("dialog")
            .get_by_role("button", name="Send request", exact=True)
            .click()
        )
        await self.idle()

    async def test_gif(self) -> None:
        samples = []
        start = time.monotonic()
        directory = self.root / "screens" / "test-frames"
        directory.mkdir()
        for index in range(180):
            path = directory / f"{index:03d}.png"
            await self.page.screenshot(path=str(path))
            samples.append((time.monotonic() - start, path))
            if await self.page.get_by_text("Test completed", exact=True).count():
                break
            if await self.page.get_by_role("alert").count():
                raise RuntimeError(
                    await self.page.get_by_role("alert").first.inner_text()
                )
            await asyncio.sleep(0.35)
        else:
            raise RuntimeError("The test did not complete within the capture timeout.")
        await self.page.get_by_text(
            "Test complete. The persisted final demo state was verified through the API.",
            exact=True,
        ).wait_for(timeout=60000)
        frames = []
        for _, path in samples:
            with Image.open(path) as image:
                image.thumbnail((1008, 700))
                frames.append(image.convert("RGB").copy())
        durations = [
            max(20, round((b[0] - a[0]) * 1000 / 10) * 10) for a, b in pairwise(samples)
        ] + [1200]
        frames[0].save(
            self.root / "clips/test-running.gif",
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=0,
        )
        self.add(
            "clips/test-running.gif",
            "The predefined sequence sends real CRUD requests. Counts and assignments update after each committed response.",
            sum(durations) / 1000,
        )


async def capture(url: str, destination: Path, headed: bool) -> None:
    try:
        playwright = importlib.import_module("playwright.async_api")
    except ModuleNotFoundError as cause:
        raise RuntimeError(
            "Install capture tools: python -m pip install playwright Pillow"
        ) from cause
    if not shutil.which("ffmpeg"):
        raise RuntimeError("Install FFmpeg and add it to PATH before capturing.")
    # Capture into staging so interrupted captures leave the previous video intact.
    with TemporaryDirectory(prefix="capture-", dir=destination) as temporary:
        stage = Path(temporary)
        (stage / "screens").mkdir()
        (stage / "clips").mkdir()
        async with playwright.async_playwright() as engine:
            browser = await engine.chromium.launch(headless=not headed)
            try:
                page = await browser.new_page(
                    viewport={"width": 1440, "height": 1000},
                    device_scale_factor=1,
                    color_scheme="light",
                    reduced_motion="reduce",
                )
                page.set_default_timeout(30000)
                observed: dict[str, list[dict[str, Any]]] = {}
                pending = []

                async def observe(response: Any) -> None:
                    for resource in ("hospitals", "roles", "staff", "patients"):
                        if (
                            response.request.method == "GET"
                            and response.url.split("?")[0]
                            .rstrip("/")
                            .endswith(f"/{resource}")
                            and response.ok
                        ):
                            observed[resource] = await response.json()

                page.on(
                    "response",
                    lambda response: pending.append(
                        asyncio.create_task(observe(response))
                    ),
                )
                await page.goto(url, wait_until="networkidle")
                recorder = Recorder(page, stage)
                await page.get_by_role(
                    "heading", name="How would you like to begin?"
                ).wait_for()
                await asyncio.gather(*pending)
                if set(observed) != {"hospitals", "roles", "staff", "patients"} or any(
                    observed.values()
                ):
                    raise RuntimeError(
                        "Capture requires a fresh empty local instance. No existing records were cleared; use a disposable clean instance and rerun."
                    )
                await recorder.shot(
                    "welcome",
                    "Start empty to manage your own records, or review a predefined population. Dashboard and Swagger require the local stack.",
                    6,
                )
                await page.get_by_role(
                    "button", name="Review demo population", exact=True
                ).click()
                await recorder.expand()
                await recorder.shot(
                    "welcome-population-preview",
                    "Pre-populate opens the concrete INSERT and relationship write plan. Cancel returns to the startup choices without writes.",
                    7,
                )
                await (
                    page.get_by_role("dialog")
                    .get_by_role("button", name="Cancel", exact=True)
                    .click()
                )
                await page.get_by_role(
                    "button", name="Start without adding demo data", exact=True
                ).click()
                await recorder.expand()
                await recorder.shot(
                    "connection-preview",
                    "All requests have a preview. SQL is illustrative: the browser sends HTTP and JSON, never SQL.",
                    6,
                )
                await page.get_by_role(
                    "button", name="Start dashboard", exact=True
                ).click()
                await page.get_by_role("navigation", name="Main navigation").wait_for()
                await recorder.idle()
                await recorder.shot(
                    "empty-overview",
                    "Overview starts with zero records and reports actual API counts and care assignments.",
                )
                recorder.chapter = "testing"
                await recorder.nav("Testing")
                await page.get_by_role("button", name="Test", exact=True).click()
                await recorder.shot(
                    "populate-prerequisite",
                    "Test requires the exact baseline. This popup explains the prerequisite and offers a separate Populate review.",
                )
                await (
                    page.get_by_role("dialog")
                    .get_by_role("button", name="Cancel", exact=True)
                    .click()
                )
                await recorder.create(
                    "Hospitals",
                    {
                        "name": "[Capture] Harbor Hospital",
                        "location": "[Capture] Boston",
                    },
                    "Hospitals: use Create record and enter the hospital name and unique location.",
                )
                hospital_id = observed["hospitals"][0]["id"]
                hospital = f"[Capture] Harbor Hospital · #{hospital_id}"
                await recorder.edit(
                    "Hospitals",
                    {"location": "[Capture] Cambridge"},
                    "Hospitals: Edit opens the name and location fields; review the PATCH before saving.",
                )
                await recorder.create(
                    "Roles",
                    {"name": "[Capture] Clinician", "description": "Patient care"},
                    "Roles: edit occupation names and optional descriptions. Roles describe work, not access permissions.",
                )
                await recorder.edit(
                    "Roles",
                    {"description": "Provides clinical care"},
                    "Roles: change the description here. Clearing the optional field sends null.",
                )
                await recorder.create(
                    "Staff",
                    {"first name": "Olivia", "last name": "Chen"},
                    "Staff: enter names, choose a hospital, and check the roles to assign.",
                    hospital=hospital,
                    role="[Capture] Clinician",
                )
                staff_id = observed["staff"][0]["id"]
                await recorder.edit(
                    "Staff",
                    {"first name": "Liv"},
                    "Staff: Edit changes names, hospital, and role checkboxes. Assigned patients must be reassigned before a staff transfer.",
                )
                await recorder.create(
                    "Patients",
                    {
                        "first name": "Alex",
                        "last name": "Taylor",
                        "date of birth": "1990-05-12",
                    },
                    "Patients: enter names and birth date, select the hospital, and optionally assign staff from that hospital.",
                    hospital=hospital,
                    clinician=f"Liv Chen · #{staff_id}",
                )
                await recorder.edit(
                    "Patients",
                    {"last name": "Taylor-Smith"},
                    "Patients: Edit opens these fields. Changing hospital clears the staff choice so a compatible clinician can be selected.",
                )
                await page.get_by_role(
                    "textbox", name="Search records", exact=True
                ).fill("Taylor-Smith")
                await recorder.shot(
                    "search",
                    "Search filters loaded records by their values. It sends no request and makes no database changes.",
                )
                await page.get_by_role(
                    "textbox", name="Search records", exact=True
                ).fill("")
                await (
                    page.locator("tbody tr")
                    .first.get_by_role("button", name="Read", exact=True)
                    .click()
                )
                await recorder.expand()
                await recorder.shot(
                    "read-preview",
                    "Read fetches one record by ID. Review the GET and its illustrative SELECT before sending.",
                )
                await (
                    page.get_by_role("dialog")
                    .get_by_role("button", name="Read record", exact=True)
                    .click()
                )
                await recorder.idle()
                await (
                    page.locator(".request-log > details")
                    .first.locator("summary")
                    .first.click()
                )
                await page.locator(".request-log").scroll_into_view_if_needed()
                await recorder.shot(
                    "read-response",
                    "The request log shows the returned JSON, status, payload, and SQL example. API errors are shown here too.",
                )
                recorder.chapter = "hospitals"
                await recorder.nav("Hospitals")
                await (
                    page.locator("tbody tr")
                    .first.get_by_role("button", name="Delete", exact=True)
                    .click()
                )
                await (
                    page.get_by_role("dialog")
                    .get_by_role("button", name="Send request", exact=True)
                    .click()
                )
                await page.get_by_role("alert").filter(has_text="409").wait_for()
                await recorder.shot(
                    "protected-deletion",
                    "The API protects referenced records. Deleting a hospital with patients or staff returns 409 and leaves its data unchanged.",
                    6,
                )
                for resource in ("Patients", "Staff", "Roles", "Hospitals"):
                    recorder.chapter = resource.lower()
                    await recorder.nav(resource)
                    await (
                        page.locator("tbody tr")
                        .first.get_by_role("button", name="Delete", exact=True)
                        .click()
                    )
                    await recorder.expand()
                    await recorder.shot(
                        f"delete-{resource.lower()}",
                        f"Delete {resource.lower()} only after reviewing the request. Remove patients before staff and roles, then hospitals; referenced parents are protected.",
                        4,
                    )
                    await (
                        page.get_by_role("dialog")
                        .get_by_role("button", name="Send request", exact=True)
                        .click()
                    )
                    await recorder.idle()
                    await recorder.shot(
                        f"deleted-{resource.lower()}",
                        "The deleted record is absent from the refreshed API directory.",
                    )
                recorder.chapter = "testing"
                await recorder.nav("Testing")
                await recorder.shot(
                    "testing",
                    "Testing has two actions: Populate restores fixed demo records; Test executes the predetermined operations.",
                    6,
                )
                recorder.chapter = "populate"
                await page.get_by_role("button", name="Populate", exact=True).click()
                await recorder.expand(0)
                await recorder.shot(
                    "populate-preview",
                    "Populate shows INSERT, UPDATE, DELETE, and relationship writes before restoring 2 demo hospitals, 3 roles, 3 staff, and 4 patients.",
                    6,
                )
                await (
                    page.get_by_role("dialog")
                    .get_by_role("button", name="Populate database", exact=True)
                    .click()
                )
                await page.get_by_text(
                    "Demo baseline saved to MySQL: 2 hospitals, 3 roles, 3 staff, 4 patients.",
                    exact=True,
                ).wait_for(timeout=60000)
                await recorder.shot(
                    "populated-overview",
                    "Overview now shows the persisted baseline. Patient counts and care assignment bars come from API responses.",
                    6,
                )
                await page.screenshot(
                    path=str(stage / "dashboard.png"), animations="disabled"
                )
                recorder.chapter = "appearance"
                await page.get_by_role("switch", name="Dark mode", exact=True).click()
                await page.locator("html[data-theme=dark]").wait_for()
                await recorder.shot(
                    "dark-mode",
                    "The visible Dark mode switch is in the non-clickable local profile. A manual preference is saved in this browser.",
                    6,
                )
                await page.get_by_role(
                    "button", name="Use browser theme", exact=True
                ).click()
                await page.locator("html[data-theme=light]").wait_for()
                await recorder.shot(
                    "browser-theme",
                    "Use browser theme restores automatic appearance. Connection details stay in the bottom box, above the no-login profile.",
                    6,
                )
                for resource, caption in [
                    (
                        "Hospitals",
                        "Hospitals lists the two demo hospitals and their locations, with Read, Edit, and Delete on each row.",
                    ),
                    (
                        "Roles",
                        "Roles lists the physician, nurse, and shift coordinator definitions.",
                    ),
                    (
                        "Staff",
                        "Staff lists hospital membership and role assignments for Olivia, Noah, and Mia.",
                    ),
                    (
                        "Patients",
                        "Patients lists birth dates, hospital membership, and optional clinician assignments.",
                    ),
                ]:
                    recorder.chapter = resource.lower()
                    await recorder.nav(resource)
                    await recorder.shot(f"populated-{resource.lower()}", caption)
                recorder.chapter = "navigation"
                await page.get_by_role(
                    "combobox", name="Select hospital", exact=True
                ).select_option(label="[Demo] Riverside Medical Center")
                await recorder.shot(
                    "hospital-filter",
                    "Use the hospital selector to focus the directories and metrics. This filters loaded data without sending a request.",
                )
                await page.get_by_role(
                    "combobox", name="Select hospital", exact=True
                ).select_option("all")
                recorder.chapter = "testing"
                await recorder.nav("Testing")
                await page.get_by_role("button", name="Test", exact=True).click()
                await recorder.shot(
                    "test-story",
                    "Before the test runs, review the plain-English story, eight operations, and expected final state.",
                    7,
                )
                await recorder.expand(6)
                await recorder.shot(
                    "test-sql",
                    "The plan includes actual record IDs, HTTP payloads, and example SQL. A patient transfer updates hospital and clinician together.",
                    6,
                )
                await (
                    page.get_by_role("dialog")
                    .get_by_role("button", name="Run test on dashboard", exact=True)
                    .click()
                )
                await page.get_by_role("region", name="Test controls").wait_for()
                await page.get_by_role(
                    "button", name="Pause after request", exact=True
                ).click()
                await recorder.idle()
                await recorder.shot(
                    "paused-controls",
                    "The test opens Overview. Pause waits for an in-flight write; completed changes remain in MySQL.",
                )
                await page.get_by_role("button", name="Next hour", exact=True).click()
                await recorder.idle()
                await recorder.shot(
                    "step-controls",
                    "Next hour pauses automatic playback and sends the next operation. The committed-step counter advances.",
                )
                await page.get_by_role(
                    "combobox", name="Test speed", exact=True
                ).select_option("4")
                await page.get_by_role("button", name="Resume", exact=True).click()
                await recorder.test_gif()
                await recorder.shot(
                    "final-overview",
                    "The verified final demo state has 2 hospitals, 3 roles, 3 staff, and 5 patients: 4 assigned and 1 unassigned.",
                    7,
                )
                await page.get_by_role("button", name="End session", exact=True).click()
                await recorder.nav("Patients")
                await recorder.shot(
                    "final-patients",
                    "Final patients include Avery and Riley; Casey transferred; Sam was discharged by DELETE; Alex is unassigned.",
                    6,
                )
                await recorder.nav("Staff")
                await recorder.shot(
                    "final-staff",
                    "Mia now also has the shift coordinator role. These changes are persisted records, not browser fixtures.",
                )
                await recorder.nav("Hospitals")
                await recorder.shot(
                    "final-hospitals",
                    "Riverside now has its North campus location. Populate can restore the baseline for another identical logical run.",
                )
                recorder.chapter = "navigation"
                await page.get_by_role(
                    "button", name="Refresh records", exact=True
                ).click()
                await recorder.expand()
                await recorder.shot(
                    "refresh",
                    "Refresh reloads all four collections, including changes made through Swagger. Its read requests also have SQL previews.",
                )
                await (
                    page.get_by_role("dialog")
                    .get_by_role("button", name="Refresh records", exact=True)
                    .click()
                )
                await recorder.idle()
                await page.locator(".top-links").scroll_into_view_if_needed()
                await recorder.shot(
                    "documentation",
                    "Documentation and Swagger stay in the header. Run the local stack for dashboard and API links; documentation is online.",
                    6,
                )
                await asyncio.gather(*pending)
                timeline = {
                    "title": "HospitalSim complete dashboard overview",
                    "duration": round(recorder.timestamp, 2),
                    "fps": 10,
                    "size": [1440, 1100],
                    "time_unit": "seconds",
                    "path_base": "Directory containing timeline.json",
                    "source": {
                        "kind": "Actual local dashboard screenshots and screen-capture GIF",
                        "url": url,
                        "captured_at": datetime.now(UTC).isoformat(),
                        "description": "Real UI interactions with the running FastAPI/MySQL stack; no mock API.",
                    },
                    "frames": recorder.frames,
                }
                (stage / "timeline.json").write_text(
                    json.dumps(timeline, indent=2) + "\n"
                )
            finally:
                await browser.close()
        # Render in staging first: a rendering failure cannot replace published media.
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(destination / "render.py"),
            "--timeline",
            str(stage / "timeline.json"),
            "--showcases",
        )
        if await process.wait():
            raise RuntimeError(
                "Rendering failed; previous published media were preserved."
            )
        for path in stage.iterdir():
            target = destination / path.name
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
            shutil.move(str(path), str(target))
    publish(destination)
    print(
        "Dashboard screenshot, walkthrough, and chapter videos published in docs/vid/."
    )


def publish(destination: Path) -> None:
    project = destination.parent.parent
    shutil.copyfile(
        destination / "dashboard.png", project / "docs/assets/dashboard.png"
    )
    for relative, image in [
        ("README.md", "docs/assets/dashboard.png"),
        ("docs/index.md", "assets/dashboard.png"),
    ]:
        path = project / relative
        content = path.read_text()
        start, end = (
            "<!-- dashboard-capture:start -->",
            "<!-- dashboard-capture:end -->",
        )
        before, marked = content.split(start, 1)
        _, after = marked.split(end, 1)
        after = after.replace(
            "; current replacement media have not yet been recorded.", "."
        )
        after = after.replace(
            "Replacement recordings are pending capture against the current local stack.",
            "Watch the overview or choose an individual flow in Showcases.",
        )
        path.write_text(
            before
            + start
            + f"\n![HospitalSim dashboard with API-backed metrics and the sidebar theme control]({image})\n"
            + end
            + after
        )
    titles = {
        "startup": "Startup choices",
        "hospitals": "Hospitals",
        "roles": "Roles",
        "staff": "Staff",
        "patients": "Patients",
        "populate": "Populate demo data",
        "testing": "Testing and playback",
        "appearance": "Dark mode and browser theme",
        "navigation": "Filtering, refresh, and links",
    }
    content = [
        "# Showcases",
        "",
        "Captured from the current dashboard connected to FastAPI and MySQL. These interactions write to the local database. SQL previews are demo examples only: the browser sends HTTP and JSON, never SQL.",
        "",
        "The startup chapter previews and cancels Pre-populate, then completes Start empty. The Populate chapter confirms the population through Testing; it does not record completing Pre-populate directly from the first-start screen.",
        "",
        "## Complete overview",
        "",
        '<video controls preload="metadata" width="100%" poster="dashboard.png"><source src="walkthrough.mp4" type="video/mp4"></video>',
        "",
        "[MP4](walkthrough.mp4) · [GIF](walkthrough.gif) · [Timestamped JSON](timeline.json)",
        "",
    ]
    for chapter, title in titles.items():
        content.extend(
            [
                f"## {title}",
                "",
                f'<video controls preload="none" width="100%"><source src="{chapter}.mp4" type="video/mp4"></video>',
                "",
                f"[MP4]({chapter}.mp4) · [GIF]({chapter}.gif) · [Timestamped JSON]({chapter}.json)",
                "",
            ]
        )
    content.extend(
        [
            "See [Recording and rebuilding](recording.md) for capture instructions and the exact flow coverage.",
            "",
        ]
    )
    (destination / "index.md").write_text("\n".join(content))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:3000")
    parser.add_argument(
        "--headed", action="store_true", help="Show the browser during capture"
    )
    args = parser.parse_args()
    asyncio.run(capture(args.url, Path(__file__).resolve().parent, args.headed))


if __name__ == "__main__":
    main()
