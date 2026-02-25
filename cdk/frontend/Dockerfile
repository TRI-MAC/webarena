# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG NODE_VERSION=24.11.0

################################################################################
# Use node image for base image for all stages.
FROM node:${NODE_VERSION}-alpine as base

# We install curl
RUN apk add --no-cache curl
# We setup a hostname to be :: for listening on both ipv4 and 6
ENV HOSTNAME ::

# Set working directory for all build stages.
WORKDIR /usr/src/app


################################################################################
# Create a stage for installing production dependecies.
FROM base as deps

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.yarn to speed up subsequent builds.
# Leverage bind mounts to package.json and yarn.lock to avoid having to copy them
# into this layer.
RUN --mount=type=bind,source=package.json,target=package.json \
    --mount=type=bind,source=yarn.lock,target=yarn.lock \
    --mount=type=cache,target=/root/.yarn \
    yarn install --production --frozen-lockfile

################################################################################
# Create a stage for building the application.
FROM deps as build

# Download additional development dependencies before building, as some projects require
# "devDependencies" to be installed to build. If you don't need this, remove this step.
RUN --mount=type=bind,source=package.json,target=package.json \
    --mount=type=bind,source=yarn.lock,target=yarn.lock \
    --mount=type=cache,target=/root/.yarn \
    yarn install --frozen-lockfile

# Copy the rest of the source files into the image.
COPY . .
# Run the build script.
RUN yarn run build

# Remove telemetry from any further stages
ENV NEXT_TELEMETRY_DISABLED 1

# Copy package.json so that package manager commands can be used in later stages
COPY package.json .

################################################################################
# We add a new stage for development build which doesn't use minified things
FROM base as development

# Use development node environment by default for dev image.
ENV NODE_ENV development

# Run the application as a non-root user.
USER node

COPY --chown=node:node --from=build /usr/src/app/ .

# Expose the port that the application listens on.
EXPOSE 3000

# Run the application.
CMD yarn next start

################################################################################
# Create a new stage to run the application with minimal runtime dependencies
# where the necessary files are copied from the build stage.
FROM base as frontend

# Use production node environment by default.
ENV NODE_ENV production

# Run the application as a non-root user.
USER node

# THIS WAS MODIFIED TO USE NEXT SANDALONE BUILD
# Copy the production dependencies from the deps stage and also
# the built application from the build stage into the image.
# COPY --from=deps /usr/src/app/node_modules ./node_modules

# Copy the .next standalone and static directories - This was added over the docker init
COPY --chown=node:node --from=build /usr/src/app/.next/standalone ./
COPY --from=build /usr/src/app/.next/static ./.next/static
# We also bring in the public directory (with images and such), this could be hosted in a separate CDN if needed
COPY --from=build /usr/src/app/public ./public

# Expose the port that the application listens on.
EXPOSE 3000

# Run the application.
CMD [ "node", "./server.js" ]
