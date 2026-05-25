FROM node:20-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_BREAK_SYSTEM_PACKAGES=1

# python + pip for pytest + bosdyn-client + the gRPC helper
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
      bosdyn-client==5.1.4 bosdyn-core==5.1.4 grpcio==1.80.0 pytest==9.0.3

WORKDIR /app

# Copy api source + helpers
COPY package.json tsconfig.json /app/
RUN npm install --no-audit --no-fund

COPY src /app/src
COPY helpers /app/helpers
ENV PYTHONPATH=/app/helpers

RUN npx tsc -p tsconfig.json

# robot_mock source is mounted at /app/robot_mock by docker-compose
ENV SDK_TESTS_DIR=/app/robot_mock/tests/sdk

EXPOSE 3001

# Generate manifest at startup, then run the compiled server.
CMD ["sh", "-c", "python3 helpers/scrape_manifest.py && node dist/index.js"]
