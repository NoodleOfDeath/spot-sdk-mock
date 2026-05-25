# spot-sdk-mock

A three-tier sandbox that lets you exercise the upstream Spot SDK test suite
in a browser, with no real robot required. Three services compose the stack:

| Service     | Folder         | Port  | Tech                    |
|-------------|----------------|-------|-------------------------|
| robot_mock  | `robot_mock/`  | 44444 | Python · gRPC           |
| api_mock    | `api_mock/`    | 3001  | TypeScript · Express    |
| web_mock    | `web_mock/`    | 4000  | React · Vite · Three.js |

## Layout

```
spot-sdk-mock/
  docker-compose.yml
  README.md
  .gitignore
  robot_mock/             # Python gRPC mock Spot — folder *is* the Python package (flat layout)
    Dockerfile
    pyproject.toml
    __init__.py
    server.py
    state.py
    servicers/
    tests/
      conftest.py
      sdk/                # verbatim upstream bosdyn-client tests (DO NOT EDIT)
        mission/          # bosdyn-mission upstream tests
  api_mock/               # Express/TS API
    Dockerfile
    eslint.config.js
    src/{index.ts, routes/*.ts, grpc/client.ts}
    helpers/              # python helpers: scrape_manifest.py, robot_mock_helpers/get_state.py
  web_mock/               # React + Vite + Three.js SPA
    Dockerfile
    eslint.config.js
    src/{App.tsx, components/*.tsx, hooks/*.ts}
  k8s/                    # Deployments, Services, Ingress (k8s resource names use
                          #   hyphens — DNS-1123 forbids underscores)
  tests/
    playwright/           # end-to-end Playwright specs (smoke + mission_smoke)
```

> Folder + Docker service + npm package names are **all snake_case**.
> Kubernetes resource names use hyphens because DNS-1123 doesn't allow
> underscores — that's a platform constraint, not a project style choice.

## Run locally (docker compose)

```bash
docker compose up --build
```

Once up:

- `curl -s http://localhost:3001/api/health` → `{"status":"ok"}`
- `curl -s http://localhost:4000` → HTTP 200, the React app
- Open `http://localhost:4000` in a browser to drive tests interactively.

## Smoke test

```bash
cd playwright
npm install
npx playwright install chromium
npx playwright test smoke.spec.ts
```

The smoke spec asserts:
1. Page title contains "Spot Mock"
2. At least one SDK test card renders
3. The Three.js robot canvas mounts
4. Clicking ▶ Run streams console output within 30 s

## Deploy to Kubernetes

```bash
kubectl apply -f k8s/
# (uses local images by default; build & push spot-sdk-mock/{robot-mock,api-mock,web}:latest first)
```

The Ingress routes `/api/*` to `api-mock` and `/` to `web`. Set your DNS or
`/etc/hosts` to point `spot-mock.local` at the cluster's ingress IP.

## Architecture

```
  ┌────────────┐    REST + SSE    ┌────────────┐   gRPC (proto)   ┌────────────┐
  │    web     │ ───────────────► │  api_mock  │ ────────────────►│ robot_mock │
  │ Vite/React │ ◄─ JSON, stream  │ Express/TS │ ◄─ RobotState pb │  Python    │
  └────────────┘                  └────────────┘                  └────────────┘
        :4000                          :3001                          :44444
```

- **robot_mock** speaks the full `bosdyn.api` surface clients need: `RobotId`,
  `Auth`, `Directory`, `TimeSync`, `EStop`, `Lease`, `Power`, `RobotCommand`,
  `RobotState`, `Image`, `DirectoryRegistration`. It listens insecure on 44444.
- **api_mock** does three things: scrapes `robot-mock/robot_mock/tests/sdk/*.py` into a
  manifest at startup (Python AST), exposes a `POST /api/tests/run` SSE endpoint
  that shells out to `pytest … --mock`, and proxies `/api/robot/state` over gRPC.
- **web** renders the test list, a Three.js Spot avatar driven by
  `/api/robot/state`, and a streaming console pane.

## Adding a new SDK test

1. Drop the test file into `robot-mock/robot_mock/tests/sdk/` and follow the upstream
   pattern. (Or add a `test_*` function to an existing module.)
2. Restart `api_mock` — the manifest is regenerated at container start.
3. The new test appears in the web TestList automatically.

## Configuration

| Variable          | Where        | Default                 | Purpose                                   |
|-------------------|--------------|-------------------------|-------------------------------------------|
| `MOCK_ROBOT_PORT` | robot_mock   | 44444                   | Override server port                      |
| `ROBOT_MOCK_HOST` | api_mock     | `robot_mock`            | Hostname of gRPC peer                     |
| `ROBOT_MOCK_PORT` | api_mock     | 44444                   | Port of gRPC peer                         |
| `PORT`            | api_mock     | 3001                    | API listen port                           |
| `VITE_API_BASE`   | web          | `http://localhost:3001` | API origin (only env the web app reads)   |

## Running tests outside the stack

```bash
# Python service-level tests for the mock itself
pytest robot-mock/robot_mock/tests/ --ignore=robot-mock/robot_mock/tests/sdk -v

# Upstream SDK suite routed through the in-process mock server
pytest robot-mock/robot_mock/tests/sdk/ -v --mock
```

`--mock` is registered in `robot-mock/robot_mock/tests/sdk/conftest.py`; without it,
upstream SDK tests behave exactly as they do upstream.

## Constraints respected

- `robot-mock/robot_mock/tests/sdk/*.py` is a verbatim copy of upstream and is never
  modified — only `conftest.py` is local to this project.
- `VITE_API_BASE` is the single GUI env var.
