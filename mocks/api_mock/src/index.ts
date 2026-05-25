import express from "express";
import cors from "cors";
import { healthRouter } from "./routes/health.js";
import { testsRouter } from "./routes/tests.js";
import { robotRouter } from "./routes/robot.js";
import { missionRouter } from "./routes/mission.js";

const app = express();
app.use(cors());
app.use(express.json());

app.use("/api", healthRouter);
app.use("/api", testsRouter);
app.use("/api", robotRouter);
app.use("/api", missionRouter);

const port = Number(process.env.PORT ?? 3001);
app.listen(port, "0.0.0.0", () => {
  console.log(`api_mock listening on ${port}`);
});
