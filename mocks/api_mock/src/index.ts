import "reflect-metadata";
import path from "node:path";
import { readFileSync } from "node:fs";
import express, { Request, Response } from "express";
import cors from "cors";
import swaggerUi from "swagger-ui-express";

import { RegisterRoutes } from "./generated/routes";
import { TestRunnerService } from "./services/TestRunnerService";
import { patchSseRoutes } from "./swagger-patch";

const app = express();
app.use(cors());
app.use(express.json());

// -- TSOA-generated routes for the documentable, JSON-bodied endpoints. ----
// TSOA's ``basePath`` only labels the spec; it doesn't prefix actual routes.
// Mount them under ``/api`` via a sub-router so the SSE routes below land
// at the same prefix.
const apiRouter = express.Router();
RegisterRoutes(apiRouter);
app.use("/api", apiRouter);

// -- Raw SSE routes for streaming pytest output. ----------------------------
app.post("/api/tests/run", (req: Request, res: Response) => {
  const testId: string | undefined = req.body?.test;
  const manifest = TestRunnerService.loadManifest();
  const entry = manifest.find((t) => t.id === testId);
  if (!entry) {
    res.status(404).json({ error: `unknown test: ${testId}` });
    return;
  }
  TestRunnerService.streamPytest(
    req,
    res,
    [`${entry.file}::${entry.name}`],
    `>> pytest ${entry.file}::${entry.name} -v -s --mock`
  );
});

app.post("/api/tests/run-all", (req: Request, res: Response) => {
  const targets = [
    "robot_mock/tests/",
    "vendor/spot-sdk/python/bosdyn-client/tests/",
    "vendor/spot-sdk/python/bosdyn-mission/tests/",
  ];
  TestRunnerService.streamPytest(
    req,
    res,
    targets,
    `>> pytest ${targets.join(" ")} -v -s --mock`
  );
});

// -- Swagger UI + raw spec ---------------------------------------------------
const swaggerPath = path.join(__dirname, "generated", "swagger.json");
const spec = patchSseRoutes(
  JSON.parse(readFileSync(swaggerPath, "utf-8"))
);

app.get("/api/docs/swagger.json", (_req, res) => res.json(spec));
app.use(
  "/api/docs",
  swaggerUi.serve,
  swaggerUi.setup(spec, { customSiteTitle: "Spot Mock API" })
);

const port = Number(process.env.PORT ?? 3001);
app.listen(port, "0.0.0.0", () => {
  console.log(`api_mock listening on ${port}`);
});
