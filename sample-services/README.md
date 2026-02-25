# Sample Services

This directory contains all the sample services available for python to be used with the template web app repository

## Available Python Backends

1. FastAPI
2. Flask

## How to use a sample backend,

1. Copy the "backend" directory for your language / framework to the root of the directory and over-write the contents.
2. Apply any modifications you want to the backend

## Adding a new backend

In order to add a new backend create a new folder with the name of the framework name (Ex: "fastapi", "flask")

This directory must contain:
- a "backend" directory with:
    - the sample / starter code for the framework
    - a Dockerfile that tells docker how to build the image to be run on ECS / local docker
    - a requirements.txt file which contains the dependencies (for python)
    - a .dockerignore file which tells docker which files to ignore
    - a docker-compose.yaml file which which will be loaded into the main docker-compose.yaml when running the application using docker compose in a production environment
    - a docker-compose.dev.yaml file which will be loaded into the docker-compose.dev.yaml override to override any values for development environment use.
