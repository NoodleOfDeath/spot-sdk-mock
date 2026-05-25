/**
 * Merges manual path entries (the SSE pytest streams) into the TSOA-generated
 * spec so swagger-ui surfaces them. SSE endpoints can't be TSOA-decorated —
 * the return type is a streaming text/event-stream, not a typed JSON body.
 */
export function patchSseRoutes(spec: Record<string, unknown>): Record<string, unknown> {
  const paths = (spec.paths ?? {}) as Record<string, unknown>;

  paths["/tests/run"] = {
    post: {
      tags: ["Tests"],
      summary: "Run one SDK test and stream pytest output via SSE.",
      description:
        "Spawns ``pytest <file>::<name> -v -s --mock`` and streams stdout/stderr " +
        "back as ``data: <line>`` SSE events. The final event is " +
        "``data: {\"exit_code\": <n>}``.",
      requestBody: {
        required: true,
        content: {
          "application/json": {
            schema: {
              type: "object",
              required: ["test"],
              properties: {
                test: {
                  type: "string",
                  description: "Test ``id`` from ``GET /api/tests``.",
                  example: "client/test_auth_client.py::test_auth",
                },
              },
            },
          },
        },
      },
      responses: {
        "200": {
          description: "SSE stream of pytest output.",
          content: {
            "text/event-stream": {
              schema: { type: "string", example: "data: PASSED\n\n" },
            },
          },
        },
        "404": {
          description: "Unknown test id.",
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: { error: { type: "string" } },
              },
            },
          },
        },
      },
    },
  };

  paths["/tests/run-all"] = {
    post: {
      tags: ["Tests"],
      summary: "Run the entire SDK suite and stream pytest output via SSE.",
      description:
        "Spawns pytest against ``robot_mock/tests/``, " +
        "``vendor/spot-sdk/python/bosdyn-client/tests/``, and " +
        "``vendor/spot-sdk/python/bosdyn-mission/tests/`` with ``--mock``.",
      responses: {
        "200": {
          description: "SSE stream of pytest output.",
          content: {
            "text/event-stream": {
              schema: { type: "string", example: "data: 560 passed\n\n" },
            },
          },
        },
      },
    },
  };

  spec.paths = paths;
  return spec;
}
