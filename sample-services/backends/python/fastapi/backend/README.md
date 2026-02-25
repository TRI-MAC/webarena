# FASTAPI Backend

This directory is for the backend services that will run in the deployed infrastructure

## FastAPI application
The backend services is a simple FastAPI application.
It provides a basis for customization.

## Build Pipeline
The docker image provided builds the FastAPI application into a container to be run.
Please view the readme file at the root of the repository for instructions on build the images

To build the image run:
docker build -t custom-backend .

To run the image:
docker run -it --rm -d -p 8000:8000 --name custom-backend custom-backend