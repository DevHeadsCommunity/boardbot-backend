import { TestCase } from "./TestCase";

export interface TestResult extends TestCase {
  messageId: string;
  actualOutput: string;
  inputTokenCount: number;
  outputTokenCount: number;
  llmResponseTime: number;
  backendProcessingTime: number;
  totalResponseTime: number;
  isCorrect: boolean;
  productAccuracy: number;
  featureAccuracy: number;
  error?: string;
  metadata?: Record<string, unknown>;
}
