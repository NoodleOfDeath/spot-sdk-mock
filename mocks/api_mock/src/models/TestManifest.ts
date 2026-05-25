/**
 * A single test entry as discovered by ``scrape_manifest.py``.
 *
 * @example {
 *   "id": "client/test_auth_client.py::test_auth",
 *   "file": "/app/vendor/spot-sdk/python/bosdyn-client/tests/test_auth_client.py",
 *   "name": "test_auth",
 *   "suite": "client"
 * }
 */
export interface TestEntry {
  /** Stable identifier: ``<suite>/<rel-path>::<test-name>``. */
  id: string;
  /** Absolute path to the test file inside the container. */
  file: string;
  /** Function name (or ``Class::method`` for class-bodied tests). */
  name: string;
  /** Logical suite: ``client``, ``mission``, etc. */
  suite: string;
}

/** Body for ``POST /api/tests/run`` (raw SSE route — not TSOA-decorated). */
export interface RunTestRequest {
  /** ``id`` of the test to run (must appear in ``GET /api/tests``). */
  test: string;
}

/** Final SSE event emitted when a pytest invocation closes. */
export interface RunTestExitEvent {
  /** Process exit code, or ``-1`` if the runner was killed. */
  exit_code: number;
}
