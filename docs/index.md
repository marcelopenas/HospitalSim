# HospitalSim

HospitalSim is a hospital management system built with a React dashboard and a FastAPI CRUD API backed by MySQL. Manual forms, deterministic population, Testing, and Swagger all operate on the same records. Hospitals have patient capacity limits; staff records include admission dates, check-in times, and exact salaries; roles carry access classifications; patients show default or uploaded profile images.

[Getting started](getting-started.md){ .md-button }
[Local dashboard](http://localhost:3000){ .md-button }
[Swagger API](http://localhost:8080/docs){ .md-button }

![HospitalSim dashboard screenshot](vid/dashboard.png)

## Start here

1. Launch the stack with [Getting started](getting-started.md). A new database starts empty.
2. On the first startup, choose **Start empty** to add records manually or **Pre-populate** to review the fixed demo baseline.
3. Use the [Dashboard guide](dashboard.md) for CRUD forms, SQL previews, and the Testing sequence.
4. Explore [API usage](api/index.md), the [Data model](models/index.md), and [Architecture](architecture.md).
5. See [Development](development.md) for checks and [Troubleshooting](troubleshooting.md) for connection and validation errors.

## Showcase

Watch the [current Overview tour](vid/index.md), or follow [Recording and rebuilding](vid/recording.md) to capture live CRUD and Testing workflows.

## Actual database operations

Populate restores two demo hospitals, three roles, three staff, and four patients. Test performs eight predefined CRUD operations and leaves five demo patients, with four assigned to staff. Each request commits to MySQL. The resulting values and relationships are repeatable; generated IDs may change.

Every dashboard request has an illustrative SQL preview. **This is a demo example only: the browser sends HTTP and JSON, never SQL.** FastAPI validates input and executes parameterized ORM queries. The preview shows what will probably run, rather than an exact SQL trace.

**`run.sh` deliberately deletes Compose volumes and MySQL records** to create a clean instance. See [Getting started](getting-started.md) for preserving data instead.
