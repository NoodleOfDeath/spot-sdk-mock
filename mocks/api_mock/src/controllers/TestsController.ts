import { Controller, Get, Route, Tags } from "tsoa";
import type { TestManifest } from "../models/TestManifest";
import { TestRunnerService } from "../services/TestRunnerService";

@Route("tests")
@Tags("Tests")
export class TestsController extends Controller {
  /**
   * List every discovered test, grouped by source:
   *
   * - ``local``  — ``mocks/robot_mock/tests/`` (the mock's own service tests)
   * - ``vendor`` — ``vendor/spot-sdk/python/.../tests/`` (upstream SDK suite)
   *
   * Scraped by ``scrape_manifest.py`` at container startup; one entry per
   * ``def test_*`` found.
   */
  @Get("/")
  public async list(): Promise<TestManifest> {
    return TestRunnerService.loadManifest();
  }
}
