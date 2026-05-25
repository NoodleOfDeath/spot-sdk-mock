import { Controller, Get, Route, Tags } from "tsoa";
import { TestEntry } from "../models/TestManifest";
import { TestRunnerService } from "../services/TestRunnerService";

@Route("tests")
@Tags("Tests")
export class TestsController extends Controller {
  /**
   * List every discovered SDK test, scraped from the upstream
   * ``vendor/spot-sdk`` test directories by ``scrape_manifest.py`` at
   * container startup. Returns one entry per ``def test_*`` found.
   */
  @Get("/")
  public async list(): Promise<TestEntry[]> {
    return TestRunnerService.loadManifest();
  }
}
