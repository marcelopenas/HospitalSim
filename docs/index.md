# HospitalSim

HospitalSim is an educational hospital operations project with two complementary components: a no-login browser dashboard for synthetic scenarios and a FastAPI service for relational CRUD backed by MySQL.

[Open project documentation](https://marcelopenas.github.io/HospitalSim/){ .md-button }
[Local dashboard](http://localhost:3000){ .md-button }
[Local Swagger API](http://localhost:8080/docs){ .md-button }

![HospitalSim dashboard showing simulation controls, hospital metrics, and department capacity](assets/dashboard.png)

## Start here

1. Follow [Getting started](getting-started.md) to launch the dashboard or full stack.
2. Use the [Dashboard guide](dashboard.md) to run scenarios and understand the metrics.
3. Explore [API usage](api/index.md) to create hospitals, roles, staff, and patients.
4. Read the [Data model](models/index.md) for fields and relationships.
5. See [Development](development.md) for source layout, tests, and documentation builds.

## What is simulated?

The website models admissions, department-specific bed capacity, waiting queues, care assignments, and discharges. It contains two fictional hospitals and synthetic patients. A seeded engine makes a fresh scenario reproducible. Each hospital has its own browser-saved state.

The backend stores hospitals, patients, staff, and roles using SQLModel and MySQL. It has no bed or queue tables and no simulation runner. Browser demo actions do not modify the database; Swagger requests do. See [Architecture](architecture.md).

!!! note "Educational scope"
    There is no authentication. This project is intended for trusted local development with synthetic data, not clinical use or storage of real patient information.
