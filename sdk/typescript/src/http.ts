import type { AxiosInstance } from "axios";
import { isAxiosError } from "axios";
import {
  AysioFlowError,
  JobNotFoundError,
  ServerError,
  ValidationError,
} from "./exceptions";

function mapError(err: unknown): never {
  if (isAxiosError(err)) {
    const status = err.response?.status;
    const message = String(err.response?.data ?? err.message);
    if (status === 400) throw new ValidationError(message);
    if (status === 404) throw new JobNotFoundError(message);
    if (status !== undefined && status >= 500) throw new ServerError(message);
    throw new AysioFlowError(message);
  }
  throw new AysioFlowError(String(err));
}

export interface HttpTransport {
  get(path: string): Promise<unknown>;
  post(path: string, data: unknown): Promise<unknown>;
  delete(path: string): Promise<void>;
}

export function createHttpTransport(axiosInstance: AxiosInstance): HttpTransport {
  return {
    async get(path: string): Promise<unknown> {
      try {
        const resp = await axiosInstance.get(path);
        return resp.data;
      } catch (err) {
        mapError(err);
      }
    },

    async post(path: string, data: unknown): Promise<unknown> {
      try {
        const resp = await axiosInstance.post(path, data);
        return resp.data;
      } catch (err) {
        mapError(err);
      }
    },

    async delete(path: string): Promise<void> {
      try {
        await axiosInstance.delete(path);
      } catch (err) {
        mapError(err);
      }
    },
  };
}
