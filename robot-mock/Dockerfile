FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN pip install --no-cache-dir bosdyn-client==5.1.4 bosdyn-core==5.1.4 grpcio==1.80.0

COPY robot_mock /app/robot_mock

EXPOSE 44444

CMD ["python", "-m", "robot_mock.server"]
