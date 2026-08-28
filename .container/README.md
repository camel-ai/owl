# OWL Docker Deployment

This document provides instructions on how to build and run the OWL application using Docker.

## Prerequisites

- Docker
- Docker Compose

## Building the Docker Image

To build the Docker image, run the following command from the `.container` directory:

```bash
docker-compose build
```

## Running the Application

To run the application, use the following command from the `.container` directory:

```bash
docker-compose up
```

The application will be accessible at `http://localhost:7860`.

## Environment Variables

You can configure the application by creating a `.env` file in the `owl` directory. A template file is provided at `owl/.env_template`.

## Stopping the Application

To stop the application, press `Ctrl+C` in the terminal where `docker-compose up` is running, and then run:

```bash
docker-compose down
```
