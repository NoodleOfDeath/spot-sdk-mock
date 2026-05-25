import { Body, Controller, Get, Post, Response, Route, Tags } from "tsoa";
import type {
  ErrorResponse,
  MissionActionResult,
  MissionAnswerRequest,
  MissionStateSnapshot,
} from "../models/MissionState";
import { GrpcService } from "../services/GrpcService";

@Route("mission")
@Tags("Mission")
export class MissionController extends Controller {
  /** Start the mission. */
  @Response<ErrorResponse>(503, "Unable to reach robot_mock")
  @Post("play")
  public async play(): Promise<MissionActionResult> {
    return this._guard(() => GrpcService.missionAction("play"));
  }

  /** Pause the mission. */
  @Response<ErrorResponse>(503, "Unable to reach robot_mock")
  @Post("pause")
  public async pause(): Promise<MissionActionResult> {
    return this._guard(() => GrpcService.missionAction("pause"));
  }

  /** Restart the mission from the top. Clears answered questions. */
  @Response<ErrorResponse>(503, "Unable to reach robot_mock")
  @Post("restart")
  public async restart(): Promise<MissionActionResult> {
    return this._guard(() => GrpcService.missionAction("restart"));
  }

  /** Fetch the active question (if any) + mission state. */
  @Response<ErrorResponse>(503, "Unable to reach robot_mock")
  @Get("question")
  public async question(): Promise<MissionStateSnapshot> {
    return this._guard(() => GrpcService.getMissionQuestion());
  }

  /** Answer the active question with one of the allowed ``answer_code`` values. */
  @Response<ErrorResponse>(400, "Bad request")
  @Response<ErrorResponse>(503, "Unable to reach robot_mock")
  @Post("answer")
  public async answer(
    @Body() body: MissionAnswerRequest
  ): Promise<MissionActionResult> {
    if (
      !Number.isFinite(body.question_id) ||
      !Number.isFinite(body.answer_code)
    ) {
      this.setStatus(400);
      throw new Error("question_id and answer_code are required numbers");
    }
    return this._guard(() =>
      GrpcService.answerMissionQuestion(body.question_id, body.answer_code)
    );
  }

  private async _guard<T>(fn: () => Promise<T>): Promise<T> {
    try {
      return await fn();
    } catch (err) {
      this.setStatus(503);
      throw new Error(err instanceof Error ? err.message : String(err));
    }
  }
}
