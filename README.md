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

### API

```bash
bash run.sh
```

### Website

```bash
cd frontend
npm install
npm start
```

## Documentation

The documentation for the project can be found at [https://hospital-sim.readthedocs.io](https://hospital-sim.readthedocs.io).

The project uses mkdocs for documentation. To view the documentation via the local development server, run the following command:

```bash
mkdocs serve
```
