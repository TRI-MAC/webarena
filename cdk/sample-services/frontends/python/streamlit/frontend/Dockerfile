# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.9.6
FROM python:${PYTHON_VERSION}-slim as base
# We also install curl
RUN apt-get -y update; apt-get -y install curl

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
ARG GID=10001
RUN groupadd -g "${GID}" appuser
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/appuser" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    --gid "${GID}" \
    appuser

# NEW STAGE FOR BUILDING DEPENDENCIES
# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
FROM base as deps

RUN --mount=type=cache,target=/appuser/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# NOW WE RUN THE APPLICATION
# The docker file has to have a production target
FROM deps as frontend
# Switch to the non-privileged user to run the application.
USER appuser


# Copy the source code into the container.
COPY --chown=appuser:appuser . .

# We mount volumes at tmp and appuser
VOLUME ["/tmp"]
VOLUME ["/appuser"]

# Expose the port that the application listens on.
EXPOSE 3000

# Run the application.
CMD streamlit run app/main.py