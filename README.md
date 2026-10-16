# Hospital Sim

This project is a simulation of a hospital environment, designed to model various aspects of hospital operations and patient care. It includes both an API and a frontend interface for interacting with the simulation.

## Project Structure

The project is organized into the following main components:

### Backend

The backend service that handles the simulation logic and data management.

It is built using Python and FastAPI, and it provides a RESTful API for the frontend to interact with.

The code for the backend can be found in the `app` directory.

Also some of the files are on the project root directory, such as `run.sh`, which is used to start the backend service, and `requirements.txt`, which contains the dependencies for the backend and documentation.

### Frontend

The user interface that allows users to interact with the simulation.

It is built using React and provides a web-based interface for users to visualize and control the simulation.

The code for the frontend can be found in the `web` directory.

## Running the project

The recommended way to run the project is via docker compose, which will set up the necessary environment and start both the backend and frontend services.

To start the project, run the following command in the project root directory:

```bash
bash run.sh
```

This will generate the necessary files, environment variables, build the docker images, and start the services.

### API

The API can be started by running the `run.sh` script in the project root directory. This script will set up the necessary environment and start the backend service via the docker compose.

```bash
bash run.sh
```

#### API Development

To run the backend in development mode, you can use the following command:

```bash
fastapi dev
```

!!! NOTE
    Make sure to have the dependencies installed in your local environment before running the command above.
    Also make sure to have `DATABASE_URL` environment variable set to the database URL you want to use for development.

### Website

The frontend is atuomatically started when you run the docker compose, and it can be accessed at [http://localhost:3000](http://localhost:3000).

#### Website Development

To run the frontend in development mode, navigate to the `web` directory and install the dependencies:

```bash
cd web
npm install
npm run dev
```

## Documentation

The documentation for the project can be found at [https://hospital-sim.readthedocs.io](https://hospital-sim.readthedocs.io).

### Local Documentation

The project uses mkdocs for documentation. To view the documentation via the local development server, run the following command:

```bash
mkdocs serve
```
