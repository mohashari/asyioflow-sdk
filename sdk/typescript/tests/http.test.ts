import axios from "axios";
import MockAdapter from "axios-mock-adapter";
import { createHttpTransport } from "../src/http";
import {
  AysioFlowError,
  JobNotFoundError,
  ValidationError,
  ServerError,
} from "../src/exceptions";

const BASE_URL = "http://test-engine:8080";

describe("HttpTransport", () => {
  let mock: MockAdapter;
  let transport: ReturnType<typeof createHttpTransport>;

  beforeEach(() => {
    const axiosInstance = axios.create({ baseURL: BASE_URL });
    mock = new MockAdapter(axiosInstance);
    transport = createHttpTransport(axiosInstance);
  });

  afterEach(() => mock.restore());

  test("get returns parsed data on 200", async () => {
    mock.onGet("/api/v1/jobs/abc").reply(200, { id: "abc" });
    const result = await transport.get("/api/v1/jobs/abc");
    expect(result).toEqual({ id: "abc" });
  });

  test("post returns parsed data on 201", async () => {
    mock.onPost("/api/v1/jobs").reply(201, { id: "xyz" });
    const result = await transport.post("/api/v1/jobs", { type: "t" });
    expect(result).toEqual({ id: "xyz" });
  });

  test("delete succeeds on 204", async () => {
    mock.onDelete("/api/v1/jobs/abc").reply(204);
    await transport.delete("/api/v1/jobs/abc"); // no throw
  });

  test("400 throws ValidationError", async () => {
    mock.onPost("/api/v1/jobs").reply(400, "type required");
    await expect(transport.post("/api/v1/jobs", {})).rejects.toBeInstanceOf(ValidationError);
  });

  test("404 throws JobNotFoundError", async () => {
    mock.onGet("/api/v1/jobs/missing").reply(404, "not found");
    await expect(transport.get("/api/v1/jobs/missing")).rejects.toBeInstanceOf(JobNotFoundError);
  });

  test("500 throws ServerError", async () => {
    mock.onGet("/api/v1/jobs/abc").reply(500, "crash");
    await expect(transport.get("/api/v1/jobs/abc")).rejects.toBeInstanceOf(ServerError);
  });

  test("network error throws AysioFlowError", async () => {
    mock.onGet("/api/v1/jobs/abc").networkError();
    await expect(transport.get("/api/v1/jobs/abc")).rejects.toBeInstanceOf(AysioFlowError);
  });
});
