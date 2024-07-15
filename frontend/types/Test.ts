import { TestCase } from "./TestCase";
import { TestResult } from "./TestResult";

export type TestStatus =
  | "PENDING"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "PAUSED";

export interface Test {
  id: string;
  name: string;
  testCases: TestCase[];
  results?: TestResult[];
  status: TestStatus;
  startTimestamp?: number;
  endTimestamp?: number;
  error?: string;
  metadata?: Record<string, unknown>;
}
