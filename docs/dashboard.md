# Dashboard and simulation

The English dashboard opens directly without authentication. Its **Overview**, **Patients**, **Staff & roles**, and **Hospitals** pages share a hospital selector and simulation toolbar. Documentation and Swagger links remain in the top header.

## Walkthrough

1. Start on Riverside Medical Center's overview at Day 1, 08:00.
2. Choose **Normal operations** and select **Run simulation**. Watch counts, department capacity, the chart, and activity update.
3. Select **Patient surge** or **Critical demand**, then use **+1 hour** to see pressure build.
4. Open **Patients**. Search by name, ID, department, or clinician and filter by status.
5. Select **Admit patient**, enter a synthetic name and age (0–120), and choose a department. The patient receives its department's lead clinician.
6. **Discharge** an in-care patient to free a bed. A waiting patient from the same department takes it automatically.
7. Inspect the care team or select the other hospital. Switching hospitals pauses the simulation and preserves both hospitals' progress.
8. Use **Reset simulation** and confirm to restore only the selected hospital.

## Clock and demand

The clock starts at Day 1, 08:00. One engine step is 15 simulated minutes. At 1×, the timer steps every three real seconds; 2× every 1.5 seconds; 4× every 0.75 seconds. Browser timer throttling can slow background tabs. No offline time is simulated, and a page reload starts paused. **+1 hour** immediately performs four steps using the selected scenario; it does not change the running/paused setting.

| Preset | Arrivals per step | What changes |
| --- | --- | --- |
| Normal operations | 1–3 | Lower incoming demand |
| Patient surge | 4–6 | Higher incoming demand |
| Critical demand | 7–9 | Highest incoming demand |

Scenario choice changes arrival counts only. It does not change severity, mortality, staffing, or care quality. Random choices come from a deterministic seeded generator; a fresh reset with the same sequence of actions produces the same results.

## Capacity and care

| Hospital | Emergency | General medicine | Intensive care | Surgery | Total beds | Staff |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Riverside Medical Center | 18 | 32 | 10 | 20 | 80 | 24 |
| Northview Community Hospital | 12 | 24 | 6 | 14 | 56 | 16 |

Riverside starts with 54 in-care patients; Northview starts with 38. Departments are chosen uniformly for generated arrivals, so a department may be full even when beds remain elsewhere. Patients wait for their chosen department; the model does not transfer them between departments.

Generated patients are 18–87 years old. New patients have a stay of 60–479 simulated minutes, checked at each 15-minute step. The baseline patients have varied remaining stays. A queued patient's care clock starts when a bed becomes available. Each step discharges eligible patients, promotes waiting patients in their arrival order within the department, and generates new arrivals. Manual discharges also promote the queue immediately.

Eight named clinicians represent care teams. Only the four lead clinicians receive automated patient assignments; nurses are shown as part of the representative roster. Total staff counts are fixed scenario inputs and do not constrain bed assignments. Roles are descriptive, not access permissions.

## Metric definitions

| Metric | Definition |
| --- | --- |
| Active patients | In-care patients plus waiting patients |
| Bed occupancy | In-care patients divided by total beds, rounded to a whole percentage |
| Staff on duty | Fixed hospital fixture: 24 or 16 |
| Waiting for care | Patients queued because their department has no free bed |
| Admissions | New generated and manually admitted patients since reset; excludes baseline patients |
| Discharges | Completed and manually discharged patients since reset; includes baseline patients who leave |
| Department capacity | In-care count divided by department beds; amber at 90% or more |
| Assigned patients | In-care patients currently assigned to that named clinician |

The chart plots cumulative admissions and discharges using at most 25 samples. During uninterrupted stepping, this spans the latest six simulated hours; labels show simulation clock time. The activity feed retains the latest 40 events, with four shown on Overview. The directory retains all active records and up to 200 discharged records after each step. Totals remain cumulative even when older history is removed.

## Persistence and reset

State is saved in local storage under `hospitalsim.demo.v1` for the current browser origin. Only simulation state is persisted; navigation, speed, hospital selection, and preset return to their defaults on refresh. Separate ports, browsers, devices, or private browsing sessions have independent state.

If storage is blocked or full, an on-screen notice explains that progress may not survive a refresh, but the simulation continues in memory. Resetting a hospital is confirmed in a dialog and leaves the other hospital intact. Clear site data to remove all browser demo progress.

## Data boundary

This dashboard makes no API data requests. The patient ages, departments, status, stay lengths, bed counts, and chart data are frontend simulation fields. They are not a representation of the backend's persisted schema. Opening Swagger lets you work with independent MySQL-backed CRUD records.
