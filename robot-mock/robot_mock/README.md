# robot_mock

## Overview

`robot_mock` is a Python gRPC server that impersonates a Spot robot's API
surface so that SDK clients and example scripts can be developed and tested
without real hardware. It speaks the same `bosdyn.api` protobufs as a real
Spot — `RobotIdService`, `AuthService`, `DirectoryService`, `TimeSyncService`,
`EstopService`, `LeaseService`, `PowerService`, `RobotCommandService`,
`RobotStateService`, `ImageService`, and `DirectoryRegistrationService` — and
listens on `localhost:44444` by default.

## Prerequisites

Python 3.10+ in a clean virtualenv:

```
python -m venv .venv && source .venv/bin/activate
pip install bosdyn-client bosdyn-core grpcio pytest
```

## Running the server

```
python robot_mock/server.py
# Optional: MOCK_ROBOT_PORT=55444 python robot_mock/server.py
```

Ready output is a single line like
`... INFO robot_mock: robot_mock server listening on port 44444` — the
process then blocks until `SIGINT`/`SIGTERM`.

## Running the tests

```
# robot_mock's own service tests
pytest robot_mock/tests/ -v

# Upstream Spot SDK test suite, routed through the in-process mock server
pytest robot_mock/tests/sdk/ -v --mock
```

`tests/conftest.py` starts the server in a background thread on an ephemeral
port for the test session, so no separate server process is needed.

### SDK suite (`tests/sdk/`)

`tests/sdk/` holds a verbatim copy of the upstream
`python/bosdyn-client/tests/` suite (do not edit those files). The `--mock`
flag, registered in `tests/sdk/conftest.py`, points every
`Sdk.create_robot()` call at the in-process mock server (`localhost:$port`)
while preserving the caller-supplied address in `sdk.robots` so upstream
assertions still hold. Without `--mock` the conftest is inert and the
suite behaves exactly like upstream.

`MOCK_ROBOT_PORT` overrides the default port for both the server and the
session-scoped `mock_server` fixture consumed by `tests/sdk/conftest.py`.

## Connecting with the SDK

Spot's `Robot` object authenticates over TLS by default. The mock listens on
an insecure channel, so the snippet below patches
`bosdyn.client.channel.create_secure_channel` to use an insecure channel
before creating the `Robot`. With that one shim in place, the rest of the
SDK flow (auth, time-sync, `get_id`) is real:

```python
import bosdyn.client
import bosdyn.client.channel
import grpc


def _insecure(address, port, creds, authority, options=[]):
    return grpc.insecure_channel(f"{address}:{port}", options=list(options))


bosdyn.client.channel.create_secure_channel = _insecure

sdk = bosdyn.client.create_standard_sdk("dev")
robot = sdk.create_robot("localhost")
robot._secure_channel_port = 44444
robot.authenticate("user", "password")
robot.time_sync.wait_for_sync()
print(robot.get_id())
```

Save this as `connect_demo.py` and run it while `robot_mock/server.py` is
listening; it prints the mock's `RobotId` proto.

## Filesystem layout

```
robot_mock/
  server.py        # entry point — registers all servicers, starts gRPC server
  state.py         # shared RobotState dataclass (thread-safe)
  servicers/       # one file per gRPC service
    robot_id.py    # RobotIdService
    auth.py        # AuthService — stub JWT, no real validation
    directory.py   # DirectoryService + DirectoryRegistrationService
    time_sync.py   # TimeSyncService
    estop.py       # EstopService — gates motor power
    lease.py       # LeaseService — body + mobility sub-resources
    power.py       # PowerService — OFF -> POWERING_ON -> ON state machine
    robot_command.py  # RobotCommandService — stand/sit/velocity/etc.
    robot_state.py    # RobotStateService — synthetic state + kinematics
    image.py          # ImageService — synthetic 640x480 grayscale JPEGs
  tests/
    conftest.py    # pytest fixtures: server lifecycle, session-scoped mock_server
    test_*.py      # one file per service area
    sdk/           # verbatim copy of upstream bosdyn-client tests
      conftest.py  # registers --mock; redirects Sdk.create_robot at mock_server
      test_*.py    # do not edit — copied from python/bosdyn-client/tests
```

## Adding a new service

1. Create `robot_mock/servicers/my_service.py`. Subclass the generated
   `MyServiceServicer` base from `bosdyn.api.my_service_pb2_grpc`, implement
   each RPC, and read or write the shared `ROBOT_STATE` from
   `robot_mock.state` while holding `ROBOT_STATE.lock`.
2. Register it in `server.py`: import
   `add_MyServiceServicer_to_server` from the generated module and call it
   with your servicer instance and the gRPC `server` already built in
   `build_server()`.
3. Add an entry tuple `("my-service", "bosdyn.api.MyService", "my-service.spot.robot")`
   to `SERVICE_CATALOG` in `robot_mock/servicers/directory.py` so SDK
   `DirectoryClient.list()` advertises it.
4. Add a test file `robot_mock/tests/test_my_service.py` that uses the
   `make_client` fixture from `conftest.py` to build an SDK client bound to
   the test server.

## Known limitations

- `AuthService` issues unsigned, stub JWTs; the token signature is not
  validated on subsequent calls.
- No persistent state across server restarts — every restart resets power,
  estop, lease ownership, and command history.
- `ImageService` returns a synthetic grayscale gradient, not real camera
  frames; metadata (`transforms_snapshot`, intrinsics) is minimal.
- Autonomy services (GraphNav, Mission, AutoReturn, etc.) are not
  implemented.
- The mock listens on an insecure channel only; clients using the SDK's
  default `Robot` flow need the `create_secure_channel` shim shown above.
- `tests/sdk/test_image_service_helpers.py` imports `cv2` (not part of
  `bosdyn-client`) and is dropped from collection under `--mock`. Install
  `opencv-python` if you need to run it.

## Recent changes

- Added `tests/sdk/` — verbatim copy of the upstream
  `python/bosdyn-client/tests/` suite (51 files), runnable in-tree against
  the mock server.
- Added `tests/sdk/conftest.py` — registers the `--mock` flag and an
  autouse fixture that patches `bosdyn.client.sdk.Sdk.create_robot` to
  attach the mock server endpoint to each new `Robot` without changing
  the address recorded in `sdk.robots`. Inert when `--mock` is not passed.
- Added a session-scoped `mock_server` fixture to `tests/conftest.py`
  (exposes `.port`) so the gRPC server is bound once and reused across
  the entire SDK test run.
- Goal state: `pytest robot_mock/tests/sdk/ -v --mock` exits 0 with all
  558 collected tests passing, no skips or xfails.
