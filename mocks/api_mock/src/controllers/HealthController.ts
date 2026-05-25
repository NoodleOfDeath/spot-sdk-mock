import { Controller, Get, Route, Tags } from "tsoa";

/** Liveness probe used by docker-compose / k8s readiness checks. */
export interface HealthResponse {
  status: "ok";
}

@Route("health")
@Tags("Health")
export class HealthController extends Controller {
  /**
   * Returns ``{"status":"ok"}`` if the API is up.
   */
  @Get("/")
  public async getHealth(): Promise<HealthResponse> {
    return { status: "ok" };
  }
}
