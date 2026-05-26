import { Body, Controller, Get, Post, Response, Route, Tags } from "tsoa";
import type {
  PowerCommandRequest,
  PowerCommandResult,
  RobotStateSummary,
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
   * Issue ``REQUEST_ON_MOTORS`` / ``REQUEST_OFF_MOTORS`` to robot_mock's
   * ``PowerService``.
   */
  @Response<ErrorResponse>(503, "Unable to reach robot_mock")
  @Post("power")
  public async power(
    @Body() body: PowerCommandRequest
  ): Promise<PowerCommandResult> {
    try {
      return await GrpcService.powerCommand(body?.on === true);
    } catch (err) {
      this.setStatus(503);
      throw new Error(
        err instanceof Error ? err.message : String(err)
      );
    }
  }
}
