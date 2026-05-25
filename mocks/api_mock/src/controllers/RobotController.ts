import { Body, Controller, Get, Post, Response, Route, Tags } from "tsoa";
import type {
  RobotStateSummary,
  WalkCommandRequest,
  WalkCommandResult,
} from "../models/RobotState";
import type { ErrorResponse } from "../models/MissionState";
import { GrpcService } from "../services/GrpcService";

@Route("robot")
@Tags("Robot")
export class RobotController extends Controller {
  /**
   * Proxy ``RobotStateService.GetRobotState`` and condense it into the
   * small JSON object the GUI polls every 2 s.
   */
  @Response<ErrorResponse>(503, "Unable to reach robot_mock")
  @Get("state")
  public async state(): Promise<RobotStateSummary> {
    try {
      return await GrpcService.getRobotState();
    } catch (err) {
      this.setStatus(503);
      throw new Error(
        err instanceof Error ? err.message : String(err)
      );
    }
  }

  /**
   * Kick off a straight-line walk along +X for ``distance_m`` metres.
   * Translates into an ``SE2TrajectoryCommand`` against robot_mock.
   */
  @Response<ErrorResponse>(503, "Unable to reach robot_mock")
  @Post("command")
  public async command(
    @Body() body: WalkCommandRequest
  ): Promise<WalkCommandResult> {
    if (body?.type !== "walk") {
      this.setStatus(400);
      throw new Error(`unsupported command type: ${body?.type}`);
    }
    try {
      return await GrpcService.walkCommand(body.distance_m);
    } catch (err) {
      this.setStatus(503);
      throw new Error(
        err instanceof Error ? err.message : String(err)
      );
    }
  }
}
