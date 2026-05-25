import "reflect-metadata";
import path from "node:path";
import { readFileSync } from "node:fs";
import express, { Request, Response } from "express";
import cors from "cors";
import swaggerUi from "swagger-ui-express";

import { RegisterRoutes } from "./generated/routes";
import {
  LOCAL_PYTEST_PATHS,
  TestRunnerService,
  VENDOR_PYTEST_PATHS,
} from "./services/TestRunnerService";
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
  const entry = TestRunnerService.flatManifest().find((t) => t.id === testId);
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
  const source = req.body?.source as "local" | "vendor" | null | undefined;
  const filter = (req.body?.filter as string | null | undefined) || null;
  let targets: string[];
  if (source === "local") {
    targets = [...LOCAL_PYTEST_PATHS];
  } else if (source === "vendor") {
    targets = [...VENDOR_PYTEST_PATHS];
  } else {
    targets = [...LOCAL_PYTEST_PATHS, ...VENDOR_PYTEST_PATHS];
  }
  const args = filter ? [...targets, "-k", filter] : [...targets];
  const preamble =
    `>> pytest ${args.join(" ")} -v -s --mock` +
    (source ? ` (source=${source})` : "");
  TestRunnerService.streamPytest(req, res, args, preamble);
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
