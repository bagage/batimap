import { TestBed, inject } from "@angular/core/testing";

import { AppConfigService } from "./app-config.service";
import { HttpClientTestingModule } from "../../../node_modules/@angular/common/http/testing";

describe("AppConfigService", () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [AppConfigService],
      imports: [HttpClientTestingModule]
    });
  });

  it("should be created", inject(
    [AppConfigService],
    (service: AppConfigService) => {
      expect(service).toBeTruthy();
    }
  ));
});
